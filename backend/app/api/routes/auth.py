"""
Nexus360 — Authentication & Session Endpoints.

POST /api/v1/auth/login       Authenticate user and obtain JWT token
GET  /api/v1/auth/me          Retrieve profile of the currently authenticated user
GET  /api/v1/auth/demo-users  List available demo accounts for testing / frontend selector
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.audit_service import log_action
from app.services.auth_service import (
    DEFAULT_DEMO_USERS,
    authenticate_user,
    generate_user_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to obtain JWT access token",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with username/email and password.
    Returns a signed JWT bearer token and user role.
    """
    client_ip = get_client_ip(request)
    user = await authenticate_user(db, payload.username_or_email, payload.password)

    if not user:
        # Audit failed login
        await log_action(
            db,
            action=AuditAction.LOGIN,
            actor_username=payload.username_or_email,
            actor_role="Anonymous",
            entity_type="Auth",
            entity_id="FAILURE",
            new_value={"status": "FAILED", "reason": "Invalid credentials"},
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Audit successful login
    await log_action(
        db,
        action=AuditAction.LOGIN,
        actor_username=user.username,
        actor_role=user.role.value,
        entity_type="Auth",
        entity_id=str(user.id),
        new_value={"status": "SUCCESS", "role": user.role.value},
        ip_address=client_ip,
    )

    return generate_user_token(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Retrieve profile and role permissions of the currently authenticated user."""
    return current_user


@router.get(
    "/demo-users",
    summary="List demo accounts for hackathon evaluation",
)
async def list_demo_users():
    """
    Returns available demo accounts across all 4 RBAC roles
    for evaluation and role-switching demonstrations.
    Disabled in production environments for security.
    """
    from app.core.config import settings
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo credentials endpoint is disabled in production environments",
        )

    return [
        {
            "username": u["username"],
            "email": u["email"],
            "password": u["password"],
            "full_name": u["full_name"],
            "role": u["role"].value,
            "description": f"Demo account with {u['role'].value} role",
        }
        for u in DEFAULT_DEMO_USERS
    ]

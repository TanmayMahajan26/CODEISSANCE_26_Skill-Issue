"""
Nexus360 — Authentication Service.

Handles user verification, token generation, user retrieval,
and idempotent seeding of default demo users for the 4 RBAC roles.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserCreate

logger = logging.getLogger(__name__)

# Default seed users for hackathon demo & testing
DEFAULT_DEMO_USERS = [
    {
        "username": "admin",
        "email": "admin@nexus360.com",
        "password": "adminpassword123",
        "full_name": "System Administrator",
        "role": UserRole.ADMIN,
    },
    {
        "username": "reviewer_sarah",
        "email": "reviewer@nexus360.com",
        "password": "reviewerpassword123",
        "full_name": "Sarah Jenkins (Lead Reviewer)",
        "role": UserRole.REVIEWER,
    },
    {
        "username": "rm_rajesh",
        "email": "rm@nexus360.com",
        "password": "rmpassword123",
        "full_name": "Rajesh Varma (Relationship Manager)",
        "role": UserRole.RELATIONSHIP_MANAGER,
    },
    {
        "username": "analyst_priya",
        "email": "analyst@nexus360.com",
        "password": "analystpassword123",
        "full_name": "Priya Nair (BI Analyst)",
        "role": UserRole.ANALYST,
    },
]


async def authenticate_user(
    db: AsyncSession,
    username_or_email: str,
    password: str,
) -> Optional[User]:
    """
    Authenticate a user by username or email and password.
    Returns User if valid and active, else None.
    """
    term = username_or_email.strip().lower()
    stmt = select(User).where(
        or_(
            User.username.ilike(term),
            User.email.ilike(term),
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        return None

    if not user.is_active:
        logger.warning("Authentication failed: user '%s' is inactive", user.username)
        return None

    if not verify_password(password, user.hashed_password):
        return None

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Retrieve a user by primary key."""
    return await db.get(User, user_id)


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Retrieve a user by exact username."""
    stmt = select(User).where(User.username == username)
    res = await db.execute(stmt)
    return res.scalars().first()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user with a hashed password."""
    existing = await get_user_by_username(db, user_data.username)
    if existing:
        raise ValueError(f"Username '{user_data.username}' already exists")

    email_stmt = select(User).where(User.email == user_data.email.lower())
    email_res = await db.execute(email_stmt)
    if email_res.scalars().first():
        raise ValueError(f"Email '{user_data.email}' already registered")

    user = User(
        username=user_data.username.strip().lower(),
        email=user_data.email.strip().lower(),
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


def generate_user_token(user: User) -> TokenResponse:
    """Generate a TokenResponse for an authenticated user."""
    claims = {
        "sub": user.username,
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
    }
    from app.core.config import settings
    token = create_access_token(claims)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
    )


async def seed_default_users(db: AsyncSession) -> int:
    """
    Seed default demo accounts on startup (idempotent).
    Returns count of newly created users.
    """
    created = 0
    for u in DEFAULT_DEMO_USERS:
        stmt = select(User).where(
            or_(
                User.username == u["username"],
                User.email == u["email"],
            )
        )
        res = await db.execute(stmt)
        if not res.scalars().first():
            user = User(
                username=u["username"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                is_active=True,
            )
            db.add(user)
            created += 1

    if created > 0:
        await db.flush()
        logger.info("Seeded %d default demo users across RBAC roles", created)

    return created

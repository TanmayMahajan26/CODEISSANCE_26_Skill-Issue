"""
Nexus360 — FastAPI Request Dependencies & RBAC Guards.

Provides:
- `get_current_user`: extracts and validates JWT Bearer token
- `require_roles(*roles)`: role-based access control dependency
- `get_client_ip`: retrieves caller IP address from headers / connection
"""

from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_username

# HTTP Bearer token extractor
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate JWT Bearer token from the Authorization header.
    Returns the authenticated User model instance.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{username}' associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional user extractor for endpoints that support both public & authenticated views."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory to enforce Role-Based Access Control (RBAC).

    Usage
    -----
    ```python
    @router.post("/run", dependencies=[Depends(require_roles(UserRole.ADMIN))])
    async def run_matching(): ...
    ```
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: User '{current_user.username}' with role '{current_user.role.value}' "
                    f"does not have required privileges (requires one of: {role_names})"
                ),
            )
        return current_user

    return role_checker


def get_client_ip(request: Request) -> str:
    """Extract real client IP address from proxy headers or connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in comma-separated list is the client IP
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"

"""
Nexus360 — Authentication & User Pydantic Schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Payload for username/password authentication."""
    username_or_email: str = Field(..., description="Username or registered email address")
    password: str = Field(..., min_length=4, description="User password")


class TokenResponse(BaseModel):
    """Returned upon successful login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    username: str
    email: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Payload for creating a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.ANALYST
    full_name: Optional[str] = None

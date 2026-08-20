"""
Nexus360 — User & RBAC Model.

Defines the User entity and UserRole enumeration for Role-Based Access Control (RBAC).
Roles supported:
- ADMIN: Full system access (ingestion, BRE configuration, unmerging, matching runs, audit logs)
- REVIEWER: Manual review queue operations (approvals, rejections, manual merges, Customer 360)
- RELATIONSHIP_MANAGER: Customer 360 access, opportunities management, customer search
- ANALYST: Read-only access to customer profiles (with PII masking), stats, reports, what-if simulator
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER"
    RELATIONSHIP_MANAGER = "RELATIONSHIP_MANAGER"
    ANALYST = "ANALYST"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ANALYST, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}' role='{self.role.value}'>"

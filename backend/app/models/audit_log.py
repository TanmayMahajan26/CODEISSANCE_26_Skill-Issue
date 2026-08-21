"""
AuditLog ORM Model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, func
)
from app.core.database import Base


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    MERGE = "MERGE"
    VERIFY = "VERIFY"
    LOGIN = "LOGIN"
    EXPORT = "EXPORT"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_name = Column(String(255), nullable=False)
    actor_role = Column(String(100), nullable=False)
    
    module = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    entity_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} action={self.action} module={self.module}>"

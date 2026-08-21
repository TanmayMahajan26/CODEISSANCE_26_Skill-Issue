"""
AuditLog ORM Model.

Stores detailed audit trail of all sensitive system actions (config changes,
merges, unmerges, ingestion runs, matching runs, opportunity updates).
"""

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class AuditAction(str, enum.Enum):
    LOGIN = "LOGIN"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    MERGE_APPROVE = "MERGE_APPROVE"
    MERGE_REJECT = "MERGE_REJECT"
    MANUAL_MERGE = "MANUAL_MERGE"
    UNMERGE = "UNMERGE"
    OPPORTUNITY_UPDATE = "OPPORTUNITY_UPDATE"
    DATA_INGEST = "DATA_INGEST"
    MATCHING_RUN = "MATCHING_RUN"
    REVIEW_CREATED = "REVIEW_CREATED"
    COMMUNICATION_SENT = "COMMUNICATION_SENT"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(String(100))
    actor_username = Column(String(100))
    actor_role = Column(String(50))
    action = Column(Enum(AuditAction), nullable=False, index=True)
    entity_type = Column(String(100), index=True)
    entity_id = Column(String(100), index=True)
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog action={self.action} actor='{self.actor_username}' "
            f"entity='{self.entity_type}:{self.entity_id}'>"
        )

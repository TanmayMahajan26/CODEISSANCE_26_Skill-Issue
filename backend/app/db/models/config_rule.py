from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base


class ConfigRule(Base):
    """Centralized matching weights, survivorship rule configs, and product eligibility criteria."""

    __tablename__ = "config_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String(50), nullable=False, unique=True, index=True)  # matching, survivorship, eligibility
    version = Column(Integer, default=1, nullable=False)
    config = Column(JSONB, nullable=False)  # JSON configuration representation

    updated_by_id = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

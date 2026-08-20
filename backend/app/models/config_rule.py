"""
ConfigRule ORM Model.

Stores configurable business rules for identity resolution, scoring weights,
thresholds, normalization rules, and source precedence.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, func
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class RuleCategory(str, enum.Enum):
    MATCHING_WEIGHTS = "MATCHING_WEIGHTS"
    THRESHOLDS = "THRESHOLDS"
    OPPORTUNITY_RULES = "OPPORTUNITY_RULES"
    NORMALIZATION = "NORMALIZATION"
    SOURCE_PRECEDENCE = "SOURCE_PRECEDENCE"
    SCORING_WEIGHTS = "SCORING_WEIGHTS"


class ConfigRule(Base):
    __tablename__ = "config_rules"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(Enum(RuleCategory), nullable=False, index=True)
    rule_key = Column(String(100), unique=True, nullable=False, index=True)
    rule_value = Column(JSONB, nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    updated_by = Column(String(100))
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<ConfigRule key='{self.rule_key}' category={self.category} "
            f"version={self.version}>"
        )

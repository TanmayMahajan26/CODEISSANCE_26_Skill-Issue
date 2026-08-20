"""
AttributeHistory ORM Model.

Tracks survivorship decisions — every time a golden customer attribute
is updated, the old value, new value, source, and reason are recorded.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AttributeHistory(Base):
    __tablename__ = "attribute_history"

    id = Column(Integer, primary_key=True, index=True)
    golden_customer_id = Column(
        String(20), ForeignKey("golden_customers.golden_customer_id"),
        nullable=False, index=True
    )

    attribute_name = Column(String(50), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    selected_source = Column(String(20))
    change_reason = Column(Text)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    golden_customer = relationship("GoldenCustomer", back_populates="attribute_history")

    def __repr__(self) -> str:
        return (
            f"<AttributeHistory {self.attribute_name}: "
            f"'{self.old_value}' → '{self.new_value}'>"
        )

"""
CommunicationLog ORM Model.

Stores persistent record of outbound customer communications (e.g. WhatsApp via Twilio).
Tracks sender identity, recipient phone number, delivery status, and provider message SIDs.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.core.database import Base


class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    communication_id = Column(String(50), unique=True, nullable=False, index=True)

    customer_id = Column(String(50), nullable=False, index=True)
    golden_customer_id = Column(String(50), nullable=True, index=True)

    sent_by_user_id = Column(Integer, nullable=True)
    sent_by_username = Column(String(100), nullable=False, index=True)

    channel = Column(String(20), nullable=False, default="whatsapp", index=True)
    recipient = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)

    status = Column(String(20), nullable=False, default="SENT", index=True)  # "SENT" | "FAILED" | "PENDING"
    provider_message_id = Column(String(100), nullable=True, index=True)  # Twilio Message SID (e.g. SM...)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<CommunicationLog id={self.communication_id} "
            f"channel='{self.channel}' status='{self.status}' sent_by='{self.sent_by_username}'>"
        )

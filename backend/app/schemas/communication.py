"""
Nexus360 — Communication Pydantic Schemas.

Defines request/response models for customer communication endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CommunicationSendRequest(BaseModel):
    """Payload for sending outbound customer communications."""

    customer_id: str = Field(..., description="Golden customer ID or source customer ID")
    channel: Optional[str] = Field("whatsapp", description="Primary communication channel")
    channels: Optional[List[str]] = Field(None, description="Optional list of supported channels")
    subject: Optional[str] = Field(None, description="Email subject line")
    message: str = Field(..., min_length=1, max_length=4096, description="Message text to send")


class CommunicationSendResponse(BaseModel):
    """Response returned after processing outbound communication request."""

    success: bool
    communication_id: str
    channel: str
    customer_id: str
    status: str  # "sent" | "failed" | "pending"
    provider_message_id: Optional[str] = None
    timestamp: str
    recipient: Optional[str] = None
    error: Optional[str] = None


class CommunicationLogResponse(BaseModel):
    """Response item for customer communication history list."""

    id: int
    communication_id: str
    customer_id: str
    golden_customer_id: Optional[str] = None
    channel: str
    message: str
    status: str
    sent_by: str
    recipient: str
    created_at: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

"""
Nexus360 — Communications Router.

Provides endpoints for sending customer WhatsApp messages via Twilio API
and retrieving historical communication logs.
"""

from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.deps import get_current_user, require_roles, get_client_ip
from app.schemas.communication import (
    CommunicationSendRequest,
    CommunicationSendResponse,
    CommunicationLogResponse,
)
from app.services.communication_service import (
    send_whatsapp_message,
    send_email_message,
    send_customer_communication,
    get_customer_communication_history,
)

router = APIRouter(prefix="/communications", tags=["Communications"])


@router.post(
    "/send",
    response_model=CommunicationSendResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(UserRole.RELATIONSHIP_MANAGER, UserRole.ADMIN))],
)
async def send_communication(
    request: CommunicationSendRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send an outbound communication (WhatsApp or Email) to a customer.

    - **Permissions**: RELATIONSHIP_MANAGER, ADMIN
    - **Sender Identity**: Derived strictly from the authenticated JWT token.
    - **Persistence**: Saved to CommunicationLog & AuditLog.
    """
    ip_addr = get_client_ip(req)
    return await send_customer_communication(
        db=db,
        request=request,
        current_user=current_user,
        ip_address=ip_addr,
    )


@router.get(
    "/customer/{customer_id}",
    response_model=List[CommunicationLogResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(UserRole.RELATIONSHIP_MANAGER, UserRole.ADMIN, UserRole.REVIEWER))],
)
async def get_customer_history(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve historical communications for a customer.

    - **Permissions**: RELATIONSHIP_MANAGER, ADMIN, REVIEWER
    - **Ordering**: Newest first
    """
    return await get_customer_communication_history(db=db, customer_id=customer_id)

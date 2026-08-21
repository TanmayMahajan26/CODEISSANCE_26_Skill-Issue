"""
Nexus360 — Customer Communication Service.

Handles outbound customer WhatsApp communications via Twilio REST API,
canonical mobile survivorship resolution, database persistence, and audit log tracking.
"""

import os
import re
import uuid
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.golden_customer import GoldenCustomer
from app.models.source_record import SourceRecord
from app.models.communication_log import CommunicationLog
from app.models.audit_log import AuditAction
from app.services.audit_service import log_action
from app.schemas.communication import (
    CommunicationSendRequest,
    CommunicationSendResponse,
    CommunicationLogResponse,
)

logger = logging.getLogger(__name__)


def normalize_e164(phone: str) -> str:
    """
    Normalize phone number into standard E.164 format.
    Example: '9920602745' -> '+919920602745'
    """
    if not phone:
        return ""
    # Strip whitespace, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)\.]", "", str(phone).strip())

    if cleaned.startswith("+"):
        return cleaned
    if cleaned.startswith("whatsapp:"):
        cleaned = cleaned.replace("whatsapp:", "")
        if cleaned.startswith("+"):
            return cleaned

    # If 10 digits (Standard India mobile), prepend +91
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+91{cleaned}"
    # If 12 digits starting with 91, prepend +
    if len(cleaned) == 12 and cleaned.startswith("91") and cleaned.isdigit():
        return f"+{cleaned}"
    # If 11 digits starting with 0, replace 0 with +91
    if len(cleaned) == 11 and cleaned.startswith("0") and cleaned.isdigit():
        return f"+91{cleaned[1:]}"

    return f"+{cleaned}" if cleaned.isdigit() else cleaned


async def resolve_customer_mobile(
    db: AsyncSession, customer_id: str
) -> Tuple[Optional[GoldenCustomer], Optional[str]]:
    """
    Locate Golden Customer or Source Record and determine the canonical mobile number
    using survivorship rules.

    Raises:
        HTTPException 404: If customer does not exist.
        HTTPException 400: If conflicting mobile numbers exist without canonical resolution.
    """
    clean_id = str(customer_id).strip()

    # 1. Search GoldenCustomer by golden_customer_id or numeric primary key
    if clean_id.isdigit():
        stmt = select(GoldenCustomer).where(
            or_(
                GoldenCustomer.golden_customer_id == clean_id,
                GoldenCustomer.golden_customer_id == f"GOLD-{clean_id.zfill(6)}",
                GoldenCustomer.id == int(clean_id),
            )
        )
    else:
        stmt = select(GoldenCustomer).where(
            or_(
                GoldenCustomer.golden_customer_id == clean_id,
                GoldenCustomer.golden_customer_id == f"GOLD-{clean_id.zfill(6)}",
            )
        )

    res = await db.execute(stmt)
    golden = res.scalars().first()

    if golden:
        if golden.canonical_mobile and golden.canonical_mobile.strip():
            return golden, normalize_e164(golden.canonical_mobile)

        # Canonical mobile missing on GoldenCustomer -> check linked SourceRecords
        source_ids = golden.source_record_ids or []
        if source_ids:
            src_stmt = select(SourceRecord).where(SourceRecord.id.in_(source_ids))
            src_res = await db.execute(src_stmt)
            sources = src_res.scalars().all()

            mobiles = set()
            for s in sources:
                mob = s.normalized_mobile or s.original_mobile
                if mob and str(mob).strip():
                    mobiles.add(normalize_e164(mob))

            if len(mobiles) == 1:
                return golden, list(mobiles)[0]
            elif len(mobiles) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Multiple conflicting mobile numbers exist for customer contact. "
                        "Contact information requires review."
                    ),
                )

        return golden, None

    # 2. Search SourceRecord if not found as GoldenCustomer
    src_stmt = select(SourceRecord).where(
        or_(
            SourceRecord.source_record_id == clean_id,
            SourceRecord.id == (int(clean_id) if clean_id.isdigit() else -1),
        )
    )
    src_res = await db.execute(src_stmt)
    source_rec = src_res.scalars().first()

    if source_rec:
        mob = source_rec.normalized_mobile or source_rec.original_mobile
        return None, normalize_e164(mob) if mob else None

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Customer '{customer_id}' not found.",
    )


async def resolve_customer_email(
    db: AsyncSession, customer_id: str
) -> Tuple[Optional[GoldenCustomer], str]:
    """
    Locate Golden Customer or Source Record and determine the target email address.
    """
    clean_id = str(customer_id).strip()

    stmt = select(GoldenCustomer).where(
        or_(
            GoldenCustomer.golden_customer_id == clean_id,
            GoldenCustomer.golden_customer_id == f"GOLD-{clean_id.zfill(6)}",
        )
    )
    if clean_id.isdigit():
        stmt = select(GoldenCustomer).where(
            or_(
                GoldenCustomer.golden_customer_id == clean_id,
                GoldenCustomer.id == int(clean_id),
            )
        )

    res = await db.execute(stmt)
    golden = res.scalars().first()

    if golden and golden.canonical_email and golden.canonical_email.strip():
        return golden, golden.canonical_email.strip()

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No email address available for this customer.",
    )


async def send_whatsapp_message(
    db: AsyncSession,
    request: CommunicationSendRequest,
    current_user: User,
    ip_address: str = "127.0.0.1",
) -> CommunicationSendResponse:
    """
    Send an outbound WhatsApp message via Twilio API, persist to CommunicationLog,
    and record an AuditLog event.
    """
    # 1. Resolve customer mobile
    golden_customer, mobile_number = await resolve_customer_mobile(db, request.customer_id)

    if not mobile_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No mobile number available for this customer.",
        )

    # 2. Format Twilio recipient (e.g. 'whatsapp:+919920602745')
    if mobile_number.startswith("whatsapp:"):
        formatted_to = mobile_number
    else:
        formatted_to = f"whatsapp:{mobile_number}"

    # Generate unique communication tracking ID
    comm_id = f"COMM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    # 3. Retrieve Twilio configuration
    account_sid = (getattr(settings, "TWILIO_ACCOUNT_SID", "") or "").strip()
    auth_token = (getattr(settings, "TWILIO_AUTH_TOKEN", "") or "").strip()
    from_number = (getattr(settings, "TWILIO_WHATSAPP_FROM", "") or "").strip()
    content_sid = (getattr(settings, "TWILIO_CONTENT_SID", "") or "").strip()

    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}" if from_number else "whatsapp:+14155238886"

    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    status_str = "FAILED"
    provider_sid = None
    error_msg = None

    # 4. Dispatch WhatsApp message via Twilio API
    if not account_sid or not auth_token or "PASTE_" in account_sid or "YOUR_" in account_sid:
        error_msg = "Twilio API configuration is missing or using placeholder credentials."
        logger.warning("Twilio API dispatch skipped: %s", error_msg)
    else:
        try:
            payload = {
                "To": formatted_to,
                "From": from_number,
                "Body": request.message,
            }
            if content_sid and content_sid.strip():
                payload["ContentSid"] = content_sid.strip()
                # Include custom message as content variable 1 for Twilio template rendering
                payload["ContentVariables"] = json.dumps({"1": request.message})
                payload.pop("Body", None)

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    twilio_url,
                    data=payload,
                    auth=(account_sid, auth_token),
                )
                resp_json = resp.json()

                if resp.status_code in (200, 201):
                    status_str = "SENT"
                    provider_sid = resp_json.get("sid")
                    logger.info(
                        "Twilio WhatsApp sent successfully to %s. SID: %s",
                        formatted_to, provider_sid
                    )
                else:
                    status_str = "FAILED"
                    err_code = resp_json.get("code")
                    err_detail = resp_json.get("message", resp.text)
                    error_msg = f"Twilio API Error [{err_code}]: {err_detail}"
                    logger.error("Twilio WhatsApp failed for %s: %s", formatted_to, error_msg)

        except Exception as e:
            status_str = "FAILED"
            error_msg = f"Network or HTTP error communicating with Twilio: {str(e)}"
            logger.error("Twilio request exception: %s", error_msg)

    # 5. Persist CommunicationLog
    comm_log = CommunicationLog(
        communication_id=comm_id,
        customer_id=request.customer_id,
        golden_customer_id=golden_customer.golden_customer_id if golden_customer else None,
        sent_by_user_id=current_user.id,
        sent_by_username=current_user.username,
        channel=request.channel or "whatsapp",
        recipient=mobile_number,
        message=request.message,
        status=status_str,
        provider_message_id=provider_sid,
        error_message=error_msg,
    )
    db.add(comm_log)
    await db.flush()

    # 6. Audit Log Entry (never exposing secrets)
    customer_name = golden_customer.canonical_name if golden_customer else None
    try:
        # Fallback to OPPORTUNITY_UPDATE if database auditaction enum constraint requires it
        audit_act = getattr(AuditAction, "COMMUNICATION_SENT", AuditAction.OPPORTUNITY_UPDATE)
        await log_action(
            db=db,
            action=audit_act,
            actor_username=current_user.username,
            actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            entity_type="WhatsAppCommunication",
            entity_id=golden_customer.golden_customer_id if golden_customer else request.customer_id,
            new_value={
                "communication_id": comm_id,
                "channel": request.channel or "whatsapp",
                "recipient": mobile_number,
                "customer_name": customer_name,
                "status": status_str,
                "provider_message_id": provider_sid,
            },
            ip_address=ip_address,
        )
    except Exception as audit_err:
        logger.warning("Audit log write skipped due to enum constraint: %s", audit_err)

    await db.commit()

    return CommunicationSendResponse(
        success=(status_str == "SENT"),
        communication_id=comm_id,
        channel=request.channel or "whatsapp",
        customer_id=request.customer_id,
        status=status_str.lower(),
        provider_message_id=provider_sid,
        timestamp=datetime.utcnow().isoformat(),
        recipient=mobile_number,
        error=error_msg if status_str == "FAILED" else None,
    )


async def send_email_message(
    db: AsyncSession,
    request: CommunicationSendRequest,
    current_user: User,
    ip_address: str = "127.0.0.1",
) -> CommunicationSendResponse:
    """
    Send an outbound Email via Twilio Comms API (https://comms.twilio.com/v1/Emails),
    persist to CommunicationLog, and record an AuditLog event.
    """
    golden_customer, target_email = await resolve_customer_email(db, request.customer_id)

    comm_id = f"COMM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    account_sid = (getattr(settings, "TWILIO_ACCOUNT_SID", "") or "").strip()
    auth_token = (getattr(settings, "TWILIO_AUTH_TOKEN", "") or "").strip()

    email_url = "https://comms.twilio.com/v1/Emails"
    status_str = "FAILED"
    provider_sid = None
    error_msg = None

    if not account_sid or not auth_token:
        error_msg = "Twilio API configuration is missing or using placeholder credentials."
        logger.warning("Twilio Email API dispatch skipped: %s", error_msg)
    else:
        try:
            # Twilio Comms trial approved template content payload
            user_html_template = (
                "<p><b>This is a test email from Twilio.</b></p>"
                "<h2>Appointment Reminder</h2>"
                "<p>This is a friendly reminder about your upcoming appointment.</p>"
                "<p><strong>Date:</strong> Tomorrow at 2:00 PM</p>"
                "<p><strong>Location:</strong> 123 Main Street, Suite 100</p>"
                "<p>Please arrive 10 minutes early to complete any necessary paperwork.</p>"
                "<p>If you need to reschedule, please contact us as soon as possible.</p>"
                "<p>We look forward to seeing you!</p>"
            )

            payload = {
                "from": {
                    "address": f"{account_sid}@twilio.email",
                    "name": "Trial with Twilio"
                },
                "to": [
                    {"address": target_email}
                ],
                "content": {
                    "subject": request.subject or "Reminder: Your Upcoming Appointment",
                    "html": user_html_template
                }
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    email_url,
                    json=payload,
                    auth=(account_sid, auth_token),
                )
                resp_json = resp.json()

                if resp.status_code in (200, 201, 202):
                    status_str = "SENT"
                    provider_sid = resp_json.get("operationId") or resp_json.get("id")
                    logger.info("Twilio Email sent successfully to %s. Operation ID: %s", target_email, provider_sid)
                else:
                    status_str = "FAILED"
                    err_detail = resp_json.get("message", resp.text)
                    error_msg = f"Twilio Email API Error [{resp.status_code}]: {err_detail}"
                    logger.error("Twilio Email failed for %s: %s", target_email, error_msg)

        except Exception as e:
            status_str = "FAILED"
            error_msg = f"Network or HTTP error communicating with Twilio Email API: {str(e)}"
            logger.error("Twilio Email request exception: %s", error_msg)

    # Persist CommunicationLog
    comm_log = CommunicationLog(
        communication_id=comm_id,
        customer_id=request.customer_id,
        golden_customer_id=golden_customer.golden_customer_id if golden_customer else None,
        sent_by_user_id=current_user.id,
        sent_by_username=current_user.username,
        channel="email",
        recipient=target_email,
        message=request.message,
        status=status_str,
        provider_message_id=provider_sid,
        error_message=error_msg,
    )
    db.add(comm_log)
    await db.flush()

    # Audit Log Entry
    customer_name = golden_customer.canonical_name if golden_customer else None
    try:
        audit_act = getattr(AuditAction, "COMMUNICATION_SENT", AuditAction.OPPORTUNITY_UPDATE)
        await log_action(
            db=db,
            action=audit_act,
            actor_username=current_user.username,
            actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            entity_type="EmailCommunication",
            entity_id=golden_customer.golden_customer_id if golden_customer else request.customer_id,
            new_value={
                "communication_id": comm_id,
                "channel": "email",
                "recipient": target_email,
                "customer_name": customer_name,
                "status": status_str,
                "provider_message_id": provider_sid,
            },
            ip_address=ip_address,
        )
    except Exception as audit_err:
        logger.warning("Audit log write skipped: %s", audit_err)

    await db.commit()

    return CommunicationSendResponse(
        success=(status_str == "SENT"),
        communication_id=comm_id,
        channel="email",
        customer_id=request.customer_id,
        status=status_str.lower(),
        provider_message_id=provider_sid,
        timestamp=datetime.utcnow().isoformat(),
        recipient=target_email,
        error=error_msg if status_str == "FAILED" else None,
    )


async def send_customer_communication(
    db: AsyncSession,
    request: CommunicationSendRequest,
    current_user: User,
    ip_address: str = "127.0.0.1",
) -> CommunicationSendResponse:
    """
    Route outbound customer communication to WhatsApp or Email channel based on request.
    """
    channel = (request.channel or "whatsapp").lower()
    if channel == "email":
        return await send_email_message(db, request, current_user, ip_address)
    else:
        return await send_whatsapp_message(db, request, current_user, ip_address)


async def get_customer_communication_history(
    db: AsyncSession, customer_id: str
) -> List[CommunicationLogResponse]:
    """Retrieve communication logs for a customer ordered newest first."""
    clean_id = str(customer_id).strip()

    stmt = (
        select(CommunicationLog)
        .where(
            or_(
                CommunicationLog.customer_id == clean_id,
                CommunicationLog.golden_customer_id == clean_id,
            )
        )
        .order_by(CommunicationLog.created_at.desc())
    )

    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        CommunicationLogResponse(
            id=log.id,
            communication_id=log.communication_id,
            customer_id=log.customer_id,
            golden_customer_id=log.golden_customer_id,
            channel=log.channel,
            message=log.message,
            status=log.status.lower(),
            sent_by=log.sent_by_username,
            recipient=log.recipient,
            created_at=log.created_at.isoformat() if log.created_at else datetime.utcnow().isoformat(),
            error_message=log.error_message,
        )
        for log in logs
    ]

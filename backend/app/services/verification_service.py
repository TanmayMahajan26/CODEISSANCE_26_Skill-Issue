import logging
import os
import json
import httpx
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_case import ReviewCase, VerificationClassification, VerificationStatus
from app.models.match_decision import MatchDecision
from app.models.source_record import SourceRecord
from app.models.audit_log import AuditAction
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

BOLNA_API_KEY = os.getenv("BOLNA_API_KEY", "bn-5d61aad059d54aaa8a087e4ad4b5de08")
BOLNA_AGENT_ID = os.getenv("BOLNA_AGENT_ID", "eb9494b9-3d3d-4111-aa12-27bfac34a0a3")
BOLNA_API_URL = "https://api.bolna.dev/call"

async def trigger_ai_verification(db: AsyncSession, review_id: int, admin_username: str, target_phone: str = None) -> ReviewCase:
    """
    Triggers an AI phone call for a verification case that is AI_VERIFICATION_ELIGIBLE.
    """
    review = await db.get(ReviewCase, review_id)
    if not review:
        raise ValueError(f"Review case {review_id} not found")
        
    if review.verification_classification != VerificationClassification.AI_VERIFICATION_ELIGIBLE:
        raise ValueError(f"Review case {review_id} is not eligible for AI verification.")
        
    decision = await db.get(MatchDecision, review.match_decision_id)
    rec_a = await db.get(SourceRecord, decision.record_a_id)
    
    # Retrieve the phone number to call
    phone_number = target_phone
    if not phone_number:
        phone_number = rec_a.original_mobile or rec_a.normalized_mobile
        if not phone_number:
            phone_number = "+1234567890"  # fallback for demo
            
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"
        
    # Extract only the relevant context for the AI agent (e.g. what is conflicting)
    reasoning = decision.reasoning or {}
    
    # Construct a prompt context. We don't expose AI confidence, just the conflicting attribute.
    conflict_context = "Please verify the customer's information."
    if "mobile" in str(reasoning):
        conflict_context = "Please verify the customer's registered mobile number."
    elif "email" in str(reasoning):
        conflict_context = "Please verify the customer's registered email address."
        
    payload = {
        "agent_id": BOLNA_AGENT_ID,
        "recipient_phone_number": phone_number,
        "user_data": {
            "customer_name": rec_a.original_name,
            "verification_context": conflict_context
        }
    }
    
    headers = {
        "Authorization": f"Bearer {BOLNA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    review.verification_status = VerificationStatus.AI_CALL_REQUESTED
    
    # Send request to Bolna
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BOLNA_API_URL, json=payload, headers=headers, timeout=10.0)
            
            if response.status_code in (200, 201):
                data = response.json()
                call_id = data.get("call_id") or "mock-call-id-12345"
                review.ai_call_id = call_id
                review.verification_status = VerificationStatus.AI_CALL_IN_PROGRESS
                logger.info(f"Initiated Bolna call {call_id} for review {review_id}")
            else:
                logger.error(f"Bolna API error: {response.status_code} {response.text}")
                review.verification_status = VerificationStatus.AI_FAILED
                review.verification_classification = VerificationClassification.HUMAN_VERIFICATION_REQUIRED
    except Exception as e:
        logger.error(f"Failed to call Bolna API: {e}")
        review.verification_status = VerificationStatus.AI_FAILED
        review.verification_classification = VerificationClassification.HUMAN_VERIFICATION_REQUIRED
        
    await log_action(
        db,
        action=AuditAction.UPDATE,
        actor_username=admin_username,
        actor_role="Admin",
        entity_type="ReviewCase",
        entity_id=str(review_id),
        old_value={"verification_status": "PENDING"},
        new_value={"verification_status": review.verification_status.value, "ai_call_id": review.ai_call_id}
    )
    
    await db.flush()
    return review

async def handle_bolna_webhook(db: AsyncSession, payload: dict):
    """
    Handles webhook from Bolna to update the ReviewCase with call results.
    """
    call_id = payload.get("call_id")
    status = payload.get("status")
    result_data = payload.get("result", {})
    
    from sqlalchemy import select
    stmt = select(ReviewCase).where(ReviewCase.ai_call_id == call_id)
    res = await db.execute(stmt)
    review = res.scalars().first()
    
    if not review:
        logger.error(f"No review case found for call_id {call_id}")
        return
        
    review.ai_call_result = payload
    
    if status == "completed":
        review.verification_status = VerificationStatus.AI_VERIFIED
        review.ai_call_confidence = str(result_data.get("confidence", "High"))
    else:
        review.verification_status = VerificationStatus.AI_FAILED
        review.verification_classification = VerificationClassification.HUMAN_VERIFICATION_REQUIRED
        
    await log_action(
        db,
        action=AuditAction.UPDATE,
        actor_username="system",
        actor_role="System",
        entity_type="ReviewCase",
        entity_id=str(review.id),
        old_value={"verification_status": VerificationStatus.AI_CALL_IN_PROGRESS.value},
        new_value={"verification_status": review.verification_status.value, "call_result": payload}
    )
    
    await db.flush()

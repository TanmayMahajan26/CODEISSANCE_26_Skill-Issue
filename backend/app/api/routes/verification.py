from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.review_case import ReviewCase, VerificationClassification
from app.schemas.review import ReviewCaseResponse
from pydantic import BaseModel
from app.services.verification_service import trigger_ai_verification, handle_bolna_webhook

class TriggerAIPayload(BaseModel):
    target_phone: str = None

router = APIRouter(prefix="/verification", tags=["Verification"])

@router.get("/cases", response_model=List[ReviewCaseResponse])
async def get_verification_cases(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all verification cases for the Admin Verification Center.
    Requires Admin privileges.
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access Verification Center"
        )
        
    stmt = select(ReviewCase).where(
        ReviewCase.verification_classification.is_not(None)
    ).order_by(ReviewCase.created_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{review_id}/trigger-ai", response_model=ReviewCaseResponse)
async def trigger_ai_call(
    review_id: int,
    payload: TriggerAIPayload,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger an AI verification call for an eligible case.
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to trigger AI verification"
        )
        
    if review_id == 999:
        # DEMO PATH: Trigger Bolna API directly for the mock case
        import httpx
        import os
        BOLNA_API_KEY = os.getenv("BOLNA_API_KEY", "bn-5d61aad059d54aaa8a087e4ad4b5de08")
        BOLNA_AGENT_ID = os.getenv("BOLNA_AGENT_ID", "eb9494b9-3d3d-4111-aa12-27bfac34a0a3")
        BOLNA_API_URL = "https://api.bolna.dev/call"
        
        phone_number = payload.target_phone or "+919920602745"
        if not phone_number.startswith("+"): 
            phone_number = f"+{phone_number}"
            
        bolna_payload = {
            "agent_id": BOLNA_AGENT_ID,
            "recipient_phone_number": phone_number,
            "user_data": {
                "customer_name": "Rohit P. Raghavan",
                "verification_context": "Please verify the customer's PAN card."
            }
        }
        headers = {"Authorization": f"Bearer {BOLNA_API_KEY}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(BOLNA_API_URL, json=bolna_payload, headers=headers, timeout=10.0)
        except Exception as e:
            print("Bolna test call failed:", e)
            
        # Raise error to trigger frontend fallback mock state
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Demo call triggered")

    try:
        review = await trigger_ai_verification(
            db, 
            review_id=review_id, 
            admin_username=current_user.get("username", "admin"),
            target_phone=payload.target_phone
        )
        return review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/bolna-webhook")
async def bolna_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint to receive AI call results from Bolna.
    """
    try:
        payload = await request.json()
        await handle_bolna_webhook(db, payload)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")

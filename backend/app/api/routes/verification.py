from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.review_case import ReviewCase, VerificationClassification
from app.schemas.review import ReviewCaseResponse
from app.services.verification_service import trigger_ai_verification, handle_bolna_webhook

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
        
    try:
        review = await trigger_ai_verification(
            db, 
            review_id=review_id, 
            admin_username=current_user.get("username", "admin")
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

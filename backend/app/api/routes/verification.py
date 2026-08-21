from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.verification_case import VerificationCase, VerificationStatus
from app.models.verification_result import VerificationResult
from app.schemas.review import VerificationCaseResponse, VerificationResultResponse

router = APIRouter(tags=["Verification"])

@router.get(
    "/verification/cases",
    response_model=List[dict],
    summary="List verification cases",
)
async def list_verification_cases(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(VerificationCase)
    if status:
        query = query.where(VerificationCase.status == status)
        
    result = await db.execute(query)
    cases = result.scalars().all()
    
    resp_cases = []
    for c in cases:
        c_dict = c.__dict__.copy()
        
        # Attach result if any
        res = await db.execute(select(VerificationResult).where(VerificationResult.verification_case_id == c.id))
        result_obj = res.scalar_one_or_none()
        if result_obj:
            c_dict['result'] = result_obj.__dict__
        else:
            c_dict['result'] = None
            
        resp_cases.append(c_dict)
        
    return resp_cases

@router.post(
    "/verification/cases/{case_id}/ai-call/start",
    summary="Start Kovi AI verification call",
)
async def start_kovi_call(
    case_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VerificationCase).where(VerificationCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.status = VerificationStatus.CALL_QUEUED
    await db.commit()
    return {"message": "Call Queued", "case_id": case.id}
    
@router.post(
    "/verification/cases/{case_id}/ai-call/complete",
    summary="Mock complete Kovi AI verification call (Demo)",
)
async def complete_kovi_call(
    case_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VerificationCase).where(VerificationCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.status = VerificationStatus.CALL_COMPLETED
    
    # Check if result already exists
    res = await db.execute(select(VerificationResult).where(VerificationResult.verification_case_id == case.id))
    if not res.scalar_one_or_none():
        new_res = VerificationResult(
            verification_case_id=case.id,
            language_detected="English",
            call_summary="Customer confirmed their mobile number is correct as seeded.",
            customer_response="Yes, that's my number.",
            confidence=0.91,
            outcome="VERIFIED_EXPLANATION"
        )
        db.add(new_res)
        
    await db.commit()
    return {"message": "Call Completed", "case_id": case.id}

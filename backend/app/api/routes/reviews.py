from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.match_case import MatchCase, MatchClassification
from app.schemas.matching import MatchCaseResponse
from app.models.source_record import SourceRecord

router = APIRouter(tags=["Reviews", "Matching Pipeline"])

@router.get(
    "/reviews/queue",
    response_model=List[MatchCaseResponse],
    summary="List matching pipeline queue / review queue",
)
async def list_review_queue(
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(MatchCase)
    if status:
        query = query.where(MatchCase.status == status)
        
    result = await db.execute(query)
    cases = result.scalars().all()
    
    resp_cases = []
    for c in cases:
        # Fetch related records manually to avoid complex joins for demo
        record_a = (await db.execute(select(SourceRecord).where(SourceRecord.id == c.record_a_id))).scalar_one_or_none()
        record_b = (await db.execute(select(SourceRecord).where(SourceRecord.id == c.record_b_id))).scalar_one_or_none()
        
        c_dict = c.__dict__.copy()
        c_dict['record_a'] = record_a
        c_dict['record_b'] = record_b
        resp_cases.append(c_dict)
        
    return resp_cases

@router.post(
    "/reviews/{case_id}/decision",
    summary="Make a decision on a review case",
)
async def review_decision(
    case_id: int,
    action: str = Query(..., description="APPROVE, REJECT, HUMAN_REQUIRED"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MatchCase).where(MatchCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.status = action
    await db.commit()
    return {"message": "Success", "case_id": case.id, "status": action}

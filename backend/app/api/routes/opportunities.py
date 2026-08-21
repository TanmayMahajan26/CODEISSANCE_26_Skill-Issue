from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.schemas.opportunity import OpportunityResponse

router = APIRouter(tags=["Opportunities"])

class MinimalOpp(OpportunityResponse):
    pass

@router.get(
    "/opportunities",
    response_model=List[dict],
    summary="List all opportunities",
)
async def list_opportunities(
    db: AsyncSession = Depends(get_db),
):
    query = select(Opportunity).order_by(Opportunity.created_at.desc())
    result = await db.execute(query)
    return [o.__dict__ for o in result.scalars().all()]

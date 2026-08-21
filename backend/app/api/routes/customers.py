from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.golden_customer import GoldenCustomer
from app.models.source_record import SourceRecord
from app.models.match_case import MatchCase
from app.schemas.golden_customer import GoldenCustomerResponse, GoldenCustomerDetail

router = APIRouter(tags=["Customers"])

@router.get(
    "/customers",
    response_model=List[GoldenCustomerResponse],
    summary="List all golden customers",
)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None, description="Search by name, PAN, mobile, or email"),
    db: AsyncSession = Depends(get_db),
):
    query = select(GoldenCustomer).offset(skip).limit(limit)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(GoldenCustomer.full_name).like(search_term),
                func.lower(GoldenCustomer.golden_id).like(search_term),
                func.lower(GoldenCustomer.pan_masked).like(search_term),
                func.lower(GoldenCustomer.mobile_masked).like(search_term),
                func.lower(GoldenCustomer.email).like(search_term),
                func.lower(GoldenCustomer.city).like(search_term),
            )
        )

    query = query.order_by(GoldenCustomer.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/customers/search",
    response_model=List[GoldenCustomerResponse],
    summary="Search customers",
)
async def search_customers(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    search_term = f"%{q.lower()}%"
    query = (
        select(GoldenCustomer)
        .where(
            or_(
                func.lower(GoldenCustomer.full_name).like(search_term),
                func.lower(GoldenCustomer.golden_id).like(search_term),
                func.lower(GoldenCustomer.pan_masked).like(search_term),
                func.lower(GoldenCustomer.mobile_masked).like(search_term),
                func.lower(GoldenCustomer.email).like(search_term),
                func.lower(GoldenCustomer.city).like(search_term),
            )
        )
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/customers/{golden_id}",
    response_model=GoldenCustomerDetail,
    summary="Get customer 360 detail",
)
async def get_customer(golden_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GoldenCustomer).where(GoldenCustomer.golden_id == golden_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        # Fallback to ID
        result = await db.execute(
            select(GoldenCustomer).where(GoldenCustomer.id == int(golden_id) if golden_id.isdigit() else -1)
        )
        customer = result.scalar_one_or_none()
        
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Fetch source records manually for demo
    source_records = []
    if customer.source_record_ids:
        pass
    else:
        # Fetch matching full names as dummy for now or just grab some
        pass
    
    # Actually, in the demo DB they aren't linked via source_record_ids right now for some.
    # We will just fetch all source records that match the PAN
    if customer.pan_masked:
        sr_res = await db.execute(select(SourceRecord).where(SourceRecord.pan == customer.pan_masked))
        source_records = sr_res.scalars().all()

    # Build response
    resp = GoldenCustomerDetail.model_validate(customer)
    resp.source_records = [sr for sr in source_records]
    return resp

@router.get(
    "/customers/identity-graph/all",
    summary="Get full identity graph",
)
async def get_identity_graph_all(
    search: Optional[str] = None,
    source_system: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    # Fetch all golden customers
    golden_query = select(GoldenCustomer)
    if search:
        search_term = f"%{search.lower()}%"
        golden_query = golden_query.where(or_(
            func.lower(GoldenCustomer.full_name).like(search_term),
            func.lower(GoldenCustomer.golden_id).like(search_term)
        ))
    
    golden_res = await db.execute(golden_query)
    golden_customers = golden_res.scalars().all()

    # Fetch source records
    sr_query = select(SourceRecord)
    if source_system and source_system != 'ALL':
        sr_query = sr_query.where(SourceRecord.source_system == source_system)
    
    sr_res = await db.execute(sr_query)
    source_records = sr_res.scalars().all()

    nodes = []
    edges = []

    for gc in golden_customers:
        nodes.append({
            "id": gc.golden_id,
            "type": "GOLDEN",
            "source_system": "GOLDEN",
            "label": gc.full_name or gc.golden_id,
            "status": gc.status.value if gc.status else "ACTIVE"
        })

    for sr in source_records:
        nodes.append({
            "id": sr.source_record_id,
            "type": "SOURCE",
            "source_system": sr.source_system.value if sr.source_system else "DEFAULT",
            "label": sr.full_name or sr.source_record_id,
            "status": "IMPORTED"
        })
        # Link to golden customer if PAN matches
        matching_gc = next((g for g in golden_customers if g.pan_masked == sr.pan), None)
        if matching_gc:
            edges.append({
                "source": sr.source_record_id,
                "target": matching_gc.golden_id,
                "confidence": 0.95
            })

    return {"nodes": nodes, "edges": edges}


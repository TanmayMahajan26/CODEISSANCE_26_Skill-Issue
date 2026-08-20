"""
Nexus360 — Customer Endpoints.

GET /api/v1/customers                        List golden customers
GET /api/v1/customers/search                 Search customers by query
GET /api/v1/customers/{golden_customer_id}   Get customer 360 detail with lineage
GET /api/v1/customers/{golden_customer_id}/graph      D3.js identity graph data
GET /api/v1/customers/{golden_customer_id}/waterfall  Confidence waterfall data
"""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.golden_customer import GoldenCustomer
from app.models.identity_link import IdentityLink
from app.models.source_record import SourceRecord
from app.models.match_decision import MatchDecision
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
    """Retrieve all golden (unified) customer records."""
    query = select(GoldenCustomer).offset(skip).limit(limit)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                GoldenCustomer.canonical_name.ilike(search_term),
                GoldenCustomer.canonical_pan.ilike(search_term),
                GoldenCustomer.canonical_mobile.ilike(search_term),
                GoldenCustomer.canonical_email.ilike(search_term),
            )
        )

    query = query.order_by(GoldenCustomer.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/customers/search",
    response_model=List[GoldenCustomerResponse],
    summary="Search customers by name, PAN, mobile, or email",
)
async def search_customers(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Dedicated customer search endpoint."""
    search_term = f"%{q.lower()}%"
    query = (
        select(GoldenCustomer)
        .where(
            or_(
                GoldenCustomer.canonical_name.ilike(search_term),
                GoldenCustomer.canonical_pan.ilike(search_term),
                GoldenCustomer.canonical_mobile.ilike(search_term),
                GoldenCustomer.canonical_email.ilike(search_term),
            )
        )
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/customers/{golden_customer_id}",
    response_model=GoldenCustomerDetail,
    summary="Get Customer 360 profile",
)
async def get_customer(
    golden_customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single Customer 360 golden record with lineage and holdings."""
    result = await db.execute(
        select(GoldenCustomer).where(GoldenCustomer.golden_customer_id == golden_customer_id)
    )
    golden = result.scalars().first()

    if not golden:
        raise HTTPException(status_code=404, detail=f"Golden customer '{golden_customer_id}' not found")

    # Fetch linked source records
    links_result = await db.execute(
        select(IdentityLink).where(IdentityLink.golden_customer_id == golden_customer_id)
    )
    links = links_result.scalars().all()

    linked_sources = []
    for link in links:
        src = await db.get(SourceRecord, link.source_record_id)
        if src:
            linked_sources.append({
                "source_record_id": src.id,
                "source_system": src.source_system.value if src.source_system else None,
                "source_customer_id": src.source_record_id,
                "original_name": src.original_name,
                "original_mobile": src.original_mobile,
                "original_email": src.original_email,
                "original_pan": src.original_pan,
                "original_city": src.original_city,
                "segment": src.segment,
                "product_type": src.product_type,
                "balance_aum": float(src.balance_aum) if src.balance_aum is not None else 0.0,
                "relationship_value": float(src.relationship_value) if src.relationship_value is not None else 0.0,
                "match_confidence": link.match_confidence,
                "match_method": link.match_method.value if link.match_method else None,
                "status": link.status.value if link.status else None,
                "linked_at": link.linked_at.isoformat() if link.linked_at else None,
            })

    return GoldenCustomerDetail(
        id=golden.id,
        golden_customer_id=golden.golden_customer_id,
        canonical_name=golden.canonical_name,
        canonical_dob=golden.canonical_dob,
        canonical_mobile=golden.canonical_mobile,
        canonical_email=golden.canonical_email,
        canonical_pan=golden.canonical_pan,
        canonical_city=golden.canonical_city,
        canonical_segment=golden.canonical_segment,
        total_relationship_value=golden.total_relationship_value,
        products_held=golden.products_held or [],
        source_record_ids=golden.source_record_ids or [],
        attribute_provenance=golden.attribute_provenance or {},
        match_confidence=golden.match_confidence or 1.0,
        version=golden.version or 1,
        status=golden.status.value if golden.status else "ACTIVE",
        merged_into_id=golden.merged_into_id,
        assigned_rm_id=golden.assigned_rm_id,
        created_at=golden.created_at,
        updated_at=golden.updated_at,
        linked_sources=linked_sources,
    )


@router.get(
    "/customers/{golden_customer_id}/graph",
    summary="Get D3.js force-directed identity graph data",
)
async def get_customer_identity_graph(
    golden_customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns nodes (golden node + source system nodes) and edges formatted for D3.js graph visualization."""
    res = await db.execute(select(GoldenCustomer).where(GoldenCustomer.golden_customer_id == golden_customer_id))
    golden = res.scalars().first()
    if not golden:
        raise HTTPException(status_code=404, detail=f"Golden customer '{golden_customer_id}' not found")

    links_res = await db.execute(
        select(IdentityLink).where(IdentityLink.golden_customer_id == golden_customer_id)
    )
    links = links_res.scalars().all()

    nodes = [{
        "id": golden.golden_customer_id,
        "name": golden.canonical_name or golden.golden_customer_id,
        "type": "GOLDEN",
        "group": "GOLDEN",
        "value": float(golden.total_relationship_value or 0.0),
    }]

    edges = []
    for link in links:
        src = await db.get(SourceRecord, link.source_record_id)
        if src:
            node_id = f"SRC-{src.id}"
            sys_name = src.source_system.value if src.source_system else "UNKNOWN"
            nodes.append({
                "id": node_id,
                "name": src.original_name or src.source_record_id,
                "type": "SOURCE",
                "group": sys_name,
                "source_system": sys_name,
                "balance_aum": float(src.balance_aum) if src.balance_aum is not None else 0.0,
            })
            edges.append({
                "source": golden.golden_customer_id,
                "target": node_id,
                "confidence": link.match_confidence,
                "method": link.match_method.value if link.match_method else "DETERMINISTIC",
                "status": link.status.value if link.status else "MATCH",
            })

    return {
        "golden_customer_id": golden_customer_id,
        "nodes": nodes,
        "edges": edges,
    }


@router.get(
    "/customers/{golden_customer_id}/waterfall",
    summary="Get confidence waterfall breakdown",
)
async def get_customer_waterfall(
    golden_customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns step-by-step contribution breakdown for confidence score visualization."""
    res = await db.execute(select(GoldenCustomer).where(GoldenCustomer.golden_customer_id == golden_customer_id))
    golden = res.scalars().first()
    if not golden:
        raise HTTPException(status_code=404, detail=f"Golden customer '{golden_customer_id}' not found")

    links_res = await db.execute(
        select(IdentityLink).where(IdentityLink.golden_customer_id == golden_customer_id)
    )
    links = links_res.scalars().all()
    source_ids = [l.source_record_id for l in links]

    decisions_breakdown = []
    if len(source_ids) >= 2:
        dec_res = await db.execute(
            select(MatchDecision).where(
                or_(
                    MatchDecision.record_a_id.in_(source_ids),
                    MatchDecision.record_b_id.in_(source_ids),
                )
            )
        )
        decisions = dec_res.scalars().all()
        for d in decisions:
            decisions_breakdown.append({
                "match_decision_id": d.id,
                "pair": (d.record_a_id, d.record_b_id),
                "final_score": d.final_score,
                "decision": d.decision.value,
                "reasoning": d.reasoning,
            })

    return {
        "golden_customer_id": golden_customer_id,
        "overall_confidence": golden.match_confidence,
        "attribute_provenance": golden.attribute_provenance,
        "decisions_breakdown": decisions_breakdown,
    }

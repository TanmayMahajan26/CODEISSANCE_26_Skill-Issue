"""
Nexus360 — Opportunity Engine Service Interface.

Provides interface and baseline implementation for Next-Best-Opportunity generation,
retrieval, and status tracking. Aligned with PRD v3.0 §5.4 / §7.5.
The ML/AI intelligence layer developer will attach their custom RAG / recommendation logic here.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, OpportunityType, OpportunityStatus
from app.models.golden_customer import GoldenCustomer
from app.services.audit_service import log_action
from app.models.audit_log import AuditAction

logger = logging.getLogger(__name__)


async def generate_opportunities_for_golden(
    db: AsyncSession,
    golden: GoldenCustomer,
) -> List[Opportunity]:
    """
    Generate product gap recommendations for a golden customer per PRD §5.4.
    Analyses held products vs universe [Equity, MutualFunds, Insurance, Loans, Wealth].
    """
    existing_types = set()
    held_products = golden.products_held or []
    for item in held_products:
        sys = item.get("source_system", "").upper()
        if sys:
            existing_types.add(sys)

    val = float(golden.total_relationship_value or 0.0)
    created_opps = []

    # Rule 1: Insurance Cross-Sell (if has Equity or MF, relationship value >= 100k, missing Insurance)
    if ("EQUITY" in existing_types or "MUTUAL_FUND" in existing_types) and "INSURANCE" not in existing_types and val >= 100000:
        opp = Opportunity(
            golden_customer_id=golden.golden_customer_id,
            opportunity_type=OpportunityType.CROSS_SELL,
            product_recommended="Term & Health Life Insurance Cover",
            score=0.78,
            score_breakdown={"rel_val_score": 0.35, "product_affinity": 0.25, "recency": 0.18},
            ai_reasoning=(
                f"Customer has ₹{val:,.0f} in investments across {len(held_products)} products but no insurance protection. "
                "High affinity for wealth protection cross-sell."
            ),
            potential_value=Decimal(str(round(val * 0.05, 2))),
            eligibility_met={"min_balance": True, "has_investments": True, "age_eligible": True},
            status=OpportunityStatus.NEW,
            assigned_rm_id=golden.assigned_rm_id,
        )
        db.add(opp)
        created_opps.append(opp)

    # Rule 2: Wealth Management Upsell (if relationship value >= 2,500,000, missing Wealth)
    if val >= 2500000 and "WEALTH" not in existing_types:
        opp = Opportunity(
            golden_customer_id=golden.golden_customer_id,
            opportunity_type=OpportunityType.UPSELL,
            product_recommended="Bespoke Wealth Advisory Portfolio",
            score=0.88,
            score_breakdown={"rel_val_score": 0.45, "hni_segment": 0.25, "engagement": 0.18},
            ai_reasoning=(
                f"Customer cumulative relationship value of ₹{val:,.0f} satisfies HNI Wealth threshold. "
                "Recommended for dedicated RM Wealth portfolio management."
            ),
            potential_value=Decimal(str(round(val * 0.02, 2))),
            eligibility_met={"min_balance": True, "hni_tier": True},
            status=OpportunityStatus.NEW,
            assigned_rm_id=golden.assigned_rm_id,
        )
        db.add(opp)
        created_opps.append(opp)

    # Rule 3: Home/Personal Loans Cross-Sell (if relationship value >= 200k, missing Loans)
    if val >= 200000 and "LOAN" not in existing_types:
        opp = Opportunity(
            golden_customer_id=golden.golden_customer_id,
            opportunity_type=OpportunityType.CROSS_SELL,
            product_recommended="Pre-Approved Asset Backed Credit Line / Loan",
            score=0.65,
            score_breakdown={"rel_val_score": 0.25, "credit_worthiness": 0.25, "tenure": 0.15},
            ai_reasoning=(
                f"Customer maintains healthy relationship value of ₹{val:,.0f}. "
                "Eligible for pre-approved collateralized loan offering."
            ),
            potential_value=Decimal("500000.00"),
            eligibility_met={"min_balance": True, "credit_check": True},
            status=OpportunityStatus.NEW,
            assigned_rm_id=golden.assigned_rm_id,
        )
        db.add(opp)
        created_opps.append(opp)

    if created_opps:
        await db.flush()

    return created_opps


async def generate_all_opportunities(db: AsyncSession) -> int:
    """Generate opportunities for all active golden customers."""
    res = await db.execute(select(GoldenCustomer))
    goldens = res.scalars().all()

    total_created = 0
    for golden in goldens:
        created = await generate_opportunities_for_golden(db, golden)
        total_created += len(created)

    logger.info("Generated %d total opportunities across %d golden customers", total_created, len(goldens))
    return total_created


async def list_opportunities(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    rm_id: Optional[str] = None,
) -> List[Opportunity]:
    """Retrieve opportunities with optional status and rm_id filtering."""
    query = select(Opportunity).offset(skip).limit(limit)

    if status:
        try:
            st_enum = OpportunityStatus(status.upper())
            query = query.where(Opportunity.status == st_enum)
        except ValueError:
            pass

    if rm_id:
        query = query.where(Opportunity.assigned_rm_id == rm_id)

    query = query.order_by(Opportunity.score.desc())
    res = await db.execute(query)
    return res.scalars().all()


async def get_opportunity_dashboard(db: AsyncSession) -> Dict[str, Any]:
    """Aggregated opportunities dashboard for managers/RMs."""
    res_tot = await db.execute(select(func.count(Opportunity.id)))
    total_count = res_tot.scalar() or 0

    res_val = await db.execute(select(func.sum(Opportunity.potential_value)))
    total_val = res_val.scalar() or Decimal("0.0")

    by_type: Dict[str, int] = {}
    for op_type in OpportunityType:
        r = await db.execute(select(func.count(Opportunity.id)).where(Opportunity.opportunity_type == op_type))
        by_type[op_type.value] = r.scalar() or 0

    by_status: Dict[str, int] = {}
    for op_st in OpportunityStatus:
        r = await db.execute(select(func.count(Opportunity.id)).where(Opportunity.status == op_st))
        by_status[op_st.value] = r.scalar() or 0

    return {
        "total_opportunities": total_count,
        "total_potential_value": total_val,
        "by_type": by_type,
        "by_status": by_status,
    }


async def update_opportunity_status(
    db: AsyncSession,
    opportunity_id: int,
    new_status: str,
    assigned_rm_id: Optional[str] = None,
    actor: str = "RM",
) -> Opportunity:
    """Update status of an opportunity recommendation."""
    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    old_st = opp.status.value if opp.status else None
    st_enum = OpportunityStatus(new_status.upper())
    opp.status = st_enum

    if assigned_rm_id:
        opp.assigned_rm_id = assigned_rm_id

    await log_action(
        db,
        action=AuditAction.OPPORTUNITY_UPDATE,
        actor_username=actor,
        actor_role="RM",
        entity_type="Opportunity",
        entity_id=str(opportunity_id),
        old_value={"status": old_st},
        new_value={"status": st_enum.value, "assigned_rm_id": opp.assigned_rm_id},
    )

    await db.flush()
    return opp

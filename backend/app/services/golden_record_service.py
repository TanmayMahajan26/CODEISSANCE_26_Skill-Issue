"""
Nexus360 — Golden Record Service.

Creates and updates Golden Customer records using survivorship rules.
Tracks every attribute change in the attribute_history table and builds provenance,
product holdings, and total relationship value. Aligned with PRD v3.0 §5.3 / §6.1.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus
from app.models.identity_link import IdentityLink, MatchMethod, LinkStatus
from app.models.source_record import SourceRecord
from app.models.attribute_history import AttributeHistory
from app.utils.normalization import normalize_segment

logger = logging.getLogger(__name__)

# Attributes participating in survivorship
CANONICAL_ATTRS = [
    ("canonical_name", "normalized_name"),
    ("canonical_dob", "normalized_dob"),
    ("canonical_mobile", "normalized_mobile"),
    ("canonical_email", "normalized_email"),
    ("canonical_pan", "normalized_pan"),
    ("canonical_city", "normalized_city"),
    ("canonical_segment", "segment"),
]


async def get_next_golden_id(db: AsyncSession) -> str:
    """Generate the next GOLD-NNNNNN identifier."""
    result = await db.execute(select(func.count(GoldenCustomer.id)))
    count = result.scalar() or 0
    return f"GOLD-{count + 1:06d}"


async def create_golden_customer(
    db: AsyncSession,
    source_record: SourceRecord,
    match_method: MatchMethod = MatchMethod.DETERMINISTIC,
    confidence: float = 1.0,
) -> GoldenCustomer:
    """
    Create a new Golden Customer from a source record.
    Also creates the initial IdentityLink and computes holdings.
    """
    golden_id = await get_next_golden_id(db)

    sys_name = source_record.source_system.value if source_record.source_system else "UNKNOWN"
    initial_provenance = {}
    for g_attr, s_attr in CANONICAL_ATTRS:
        val = getattr(source_record, s_attr)
        if val is not None:
            initial_provenance[g_attr] = {
                "value": str(val),
                "source": sys_name,
                "rule": "INITIAL_CREATION",
                "timestamp": datetime.utcnow().isoformat(),
            }

    golden = GoldenCustomer(
        golden_customer_id=golden_id,
        canonical_name=source_record.normalized_name or source_record.original_name,
        canonical_dob=source_record.normalized_dob or source_record.original_dob,
        canonical_mobile=source_record.normalized_mobile or source_record.original_mobile,
        canonical_email=source_record.normalized_email or source_record.original_email,
        canonical_pan=source_record.normalized_pan or source_record.original_pan,
        canonical_city=source_record.normalized_city or source_record.original_city,
        canonical_segment=normalize_segment(source_record.segment),
        match_confidence=confidence,
        status=GoldenCustomerStatus.ACTIVE,
        version=1,
        source_record_ids=[source_record.id],
        attribute_provenance=initial_provenance,
        assigned_rm_id=source_record.rm_id,
    )
    db.add(golden)
    await db.flush()

    # Create identity link
    link = IdentityLink(
        source_record_id=source_record.id,
        golden_customer_id=golden_id,
        match_confidence=confidence,
        match_method=match_method,
        status=LinkStatus.MATCH,
    )
    db.add(link)
    await db.flush()

    # Recalculate holdings & total value
    await recalculate_golden_customer(db, golden)

    logger.info(
        "Created golden customer %s from source record %d (%s)",
        golden_id, source_record.id, sys_name,
    )
    return golden


async def link_to_golden(
    db: AsyncSession,
    source_record: SourceRecord,
    golden: GoldenCustomer,
    match_method: MatchMethod,
    confidence: float,
    status: LinkStatus = LinkStatus.MATCH,
) -> IdentityLink:
    """
    Link a source record to an existing Golden Customer and
    apply survivorship rules to update canonical attributes.
    """
    link = IdentityLink(
        source_record_id=source_record.id,
        golden_customer_id=golden.golden_customer_id,
        match_confidence=confidence,
        match_method=match_method,
        status=status,
    )
    db.add(link)

    if status == LinkStatus.MATCH:
        await _apply_survivorship(db, golden, source_record)
        await recalculate_golden_customer(db, golden)

    await db.flush()

    logger.info(
        "Linked source record %d to %s (method=%s, confidence=%.2f, status=%s)",
        source_record.id, golden.golden_customer_id,
        match_method.value, confidence, status.value,
    )
    return link


async def merge_golden_customers(
    db: AsyncSession,
    golden_a: GoldenCustomer,
    golden_b: GoldenCustomer,
) -> GoldenCustomer:
    """
    Safely merge GoldenCustomer B into GoldenCustomer A.
    1. Re-links all IdentityLinks from B to A.
    2. Marks B as MERGED_INTO A.
    3. Re-evaluates survivorship across all combined source records ordered deterministically by precedence.
    4. Recalculates total relationship value, holdings, and source record IDs without duplicate counting.
    """
    if golden_a.golden_customer_id == golden_b.golden_customer_id:
        return golden_a

    # 1. Mark golden_b as merged into golden_a
    golden_b.status = GoldenCustomerStatus.MERGED_INTO
    golden_b.merged_into_id = golden_a.golden_customer_id

    # 2. Re-link all identity links from golden_b to golden_a
    b_links_res = await db.execute(
        select(IdentityLink).where(IdentityLink.golden_customer_id == golden_b.golden_customer_id)
    )
    b_links = b_links_res.scalars().all()
    for link in b_links:
        link.golden_customer_id = golden_a.golden_customer_id

    # 3. Collect all linked source records across both Golden Customers
    all_links_res = await db.execute(
        select(IdentityLink)
        .where(IdentityLink.golden_customer_id == golden_a.golden_customer_id)
        .where(IdentityLink.status == LinkStatus.MATCH)
    )
    all_links = all_links_res.scalars().all()
    source_ids = list({l.source_record_id for l in all_links})

    source_records: List[SourceRecord] = []
    for sid in source_ids:
        src = await db.get(SourceRecord, sid)
        if src:
            source_records.append(src)

    # 4. Sort source records deterministically by system precedence (lowest index rank first)
    precedence = settings.SOURCE_PRECEDENCE
    def _rank(src: SourceRecord) -> int:
        sys_str = src.source_system.value if src.source_system else "UNKNOWN"
        try:
            return precedence.index(sys_str)
        except ValueError:
            return 999

    # Reverse order so higher precedence is applied last (overrides lower precedence)
    source_records_sorted = sorted(source_records, key=_rank, reverse=True)

    # Reset golden_a canonical attributes and provenance before full re-evaluation
    golden_a.canonical_name = None
    golden_a.canonical_dob = None
    golden_a.canonical_mobile = None
    golden_a.canonical_email = None
    golden_a.canonical_pan = None
    golden_a.canonical_city = None
    golden_a.canonical_segment = None
    golden_a.attribute_provenance = {}

    for src in source_records_sorted:
        await _apply_survivorship(db, golden_a, src)

    await recalculate_golden_customer(db, golden_a)
    golden_a.version = (golden_a.version or 1) + 1
    await db.flush()

    logger.info("Merged golden customer %s into %s", golden_b.golden_customer_id, golden_a.golden_customer_id)
    return golden_a


async def _apply_survivorship(
    db: AsyncSession,
    golden: GoldenCustomer,
    source_record: SourceRecord,
) -> None:
    """
    Apply survivorship rules to update Golden Customer attributes based on relative precedence.
    Tracks changes in attribute_history and updates attribute_provenance.
    """
    source_system = source_record.source_system.value if source_record.source_system else "UNKNOWN"
    source_precedence = settings.SOURCE_PRECEDENCE
    provenance = dict(golden.attribute_provenance or {})

    for golden_attr, source_attr in CANONICAL_ATTRS:
        old_value = getattr(golden, golden_attr)
        new_value = getattr(source_record, source_attr)

        if new_value is None:
            continue

        if golden_attr == "canonical_segment":
            new_value = normalize_segment(new_value)

        current_prov = provenance.get(golden_attr, {})
        current_winning_system = current_prov.get("source") if isinstance(current_prov, dict) else None

        if old_value is None:
            setattr(golden, golden_attr, new_value)
            provenance[golden_attr] = {
                "value": str(new_value),
                "source": source_system,
                "rule": "FILL_MISSING",
                "timestamp": datetime.utcnow().isoformat(),
            }
            history = AttributeHistory(
                golden_customer_id=golden.golden_customer_id,
                attribute_name=golden_attr,
                old_value=None,
                new_value=str(new_value),
                selected_source=source_system,
                change_reason="Filled missing attribute from source",
            )
            db.add(history)
            continue

        if _should_override(source_system, current_winning_system, source_precedence):
            old_str = str(old_value) if old_value else None
            new_str = str(new_value)
            if old_str != new_str or current_winning_system != source_system:
                setattr(golden, golden_attr, new_value)
                provenance[golden_attr] = {
                    "value": new_str,
                    "source": source_system,
                    "rule": "SOURCE_PRIORITY",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                history = AttributeHistory(
                    golden_customer_id=golden.golden_customer_id,
                    attribute_name=golden_attr,
                    old_value=old_str,
                    new_value=new_str,
                    selected_source=source_system,
                    change_reason=f"Higher-precedence source ({source_system}) overrode {current_winning_system}",
                )
                db.add(history)

    golden.attribute_provenance = provenance
    golden.version = (golden.version or 1) + 1


def _should_override(
    incoming_system: str,
    current_winning_system: Optional[str],
    precedence: List[str],
) -> bool:
    """
    Determine if incoming_system should override current_winning_system
    based on relative rank in precedence list (lower index = higher priority).
    """
    if not current_winning_system or current_winning_system == "UNKNOWN":
        return True

    try:
        incoming_rank = precedence.index(incoming_system)
    except ValueError:
        return False

    try:
        current_rank = precedence.index(current_winning_system)
    except ValueError:
        return True

    return incoming_rank < current_rank


async def recalculate_golden_customer(
    db: AsyncSession,
    golden: GoldenCustomer,
) -> None:
    """
    Recalculate total_relationship_value, products_held list, source_record_ids,
    and assigned_rm_id across all linked source records without duplicates.
    """
    result = await db.execute(
        select(IdentityLink)
        .where(IdentityLink.golden_customer_id == golden.golden_customer_id)
        .where(IdentityLink.status == LinkStatus.MATCH)
    )
    links = result.scalars().all()

    source_ids = []
    products = []
    total_val = Decimal("0.0")
    rm_id = golden.assigned_rm_id
    seen_sources = set()

    for link in links:
        if link.source_record_id in seen_sources:
            continue
        seen_sources.add(link.source_record_id)

        src = await db.get(SourceRecord, link.source_record_id)
        if src:
            source_ids.append(src.id)
            if src.rm_id and not rm_id:
                rm_id = src.rm_id

            val = src.relationship_value or src.balance_aum or Decimal("0.0")
            total_val += Decimal(str(val))

            products.append({
                "source_record_id": src.id,
                "source_system": src.source_system.value if src.source_system else None,
                "product_type": src.product_type or f"{src.source_system.value if src.source_system else ''} Account",
                "balance_aum": float(src.balance_aum) if src.balance_aum is not None else 0.0,
                "relationship_value": float(src.relationship_value) if src.relationship_value is not None else 0.0,
                "last_activity_date": src.last_activity_date.isoformat() if src.last_activity_date else None,
                "rm_id": src.rm_id,
            })

    golden.source_record_ids = source_ids
    golden.products_held = products
    golden.total_relationship_value = total_val
    golden.assigned_rm_id = rm_id


async def find_golden_by_source_record(
    db: AsyncSession,
    source_record_id: int,
) -> Optional[GoldenCustomer]:
    """Find the golden customer linked to a given source record."""
    result = await db.execute(
        select(IdentityLink)
        .where(IdentityLink.source_record_id == source_record_id)
        .where(IdentityLink.status == LinkStatus.MATCH)
    )
    link = result.scalars().first()
    if link:
        result = await db.execute(
            select(GoldenCustomer)
            .where(GoldenCustomer.golden_customer_id == link.golden_customer_id)
        )
        return result.scalars().first()
    return None

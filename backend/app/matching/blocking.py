"""
Nexus360 — Candidate Blocking Module.

Generates candidate pairs for matching by grouping records on
shared blocking keys.  Prevents O(n²) pair explosion via indexed lookups
and compound fallback blocking for oversized buckets.

Blocking strategies implemented:
1. Exact PAN
2. Exact normalized mobile
3. Exact normalized email
4. Name prefix (first 4 characters)
5. DOB
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_record import SourceRecord

logger = logging.getLogger(__name__)

# Type alias for a candidate pair (always ordered by smaller id first)
CandidatePair = Tuple[int, int]

# Configurable bucket size cap to prevent O(B^2) pair explosion
MAX_BUCKET_SIZE: int = 100


def _make_pair(id_a: int, id_b: int) -> CandidatePair:
    """Return a canonically ordered pair to avoid duplicates."""
    return (min(id_a, id_b), max(id_a, id_b))


def _emit_pairs_with_oversized_protection(
    buckets: Dict[str, Set[int]],
    records_map: Dict[int, SourceRecord],
    strategy_name: str,
    max_bucket_size: int = MAX_BUCKET_SIZE,
) -> Set[CandidatePair]:
    """
    Emit intra-bucket candidate pairs.
    If a bucket exceeds max_bucket_size, applies a tighter compound fallback
    blocking key (NamePrefix + DOB or City + NamePrefix) to prevent O(B^2) pair explosion.
    """
    pairs: Set[CandidatePair] = set()

    for key, ids in buckets.items():
        id_list = list(ids)
        bucket_size = len(id_list)

        if bucket_size <= max_bucket_size:
            # Emit standard pairwise combinations for normal sized buckets
            for i in range(bucket_size):
                for j in range(i + 1, bucket_size):
                    pairs.add(_make_pair(id_list[i], id_list[j]))
        else:
            # Oversized bucket protection: apply tighter compound secondary blocking
            logger.warning(
                "Oversized bucket detected in strategy '%s' (key='%s', size=%d > max %d). "
                "Applying compound fallback blocking (NamePrefix + DOB / City + NamePrefix)...",
                strategy_name, key, bucket_size, max_bucket_size,
            )

            compound_buckets: Dict[str, Set[int]] = defaultdict(set)
            for rid in id_list:
                rec = records_map.get(rid)
                if not rec:
                    continue

                name_prefix = (rec.normalized_name[:4] if rec.normalized_name and len(rec.normalized_name) >= 4 else "NONE")
                dob_str = str(rec.normalized_dob) if rec.normalized_dob else "NODOB"
                city_str = rec.normalized_city if rec.normalized_city else "NOCITY"

                # Secondary compound blocking key
                compound_key = f"{name_prefix}_{dob_str}_{city_str}"
                compound_buckets[compound_key].add(rid)

            # Emit pairs from compound sub-buckets
            sub_pair_count = 0
            for sub_ids in compound_buckets.values():
                sub_list = list(sub_ids)
                for i in range(len(sub_list)):
                    for j in range(i + 1, len(sub_list)):
                        pairs.add(_make_pair(sub_list[i], sub_list[j]))
                        sub_pair_count += 1

            logger.info(
                "Compound secondary blocking for oversized key '%s' reduced pairs from %d to %d",
                key, (bucket_size * (bucket_size - 1)) // 2, sub_pair_count,
            )

    return pairs


def generate_candidate_pairs(
    records: List[SourceRecord],
    max_bucket_size: int = MAX_BUCKET_SIZE,
) -> Set[CandidatePair]:
    """
    Generate candidate pairs using multiple blocking keys with oversized bucket protection.

    Parameters
    ----------
    records : list[SourceRecord]
        All source records to consider.
    max_bucket_size : int
        Maximum allowed bucket size before triggering compound secondary blocking.

    Returns
    -------
    set[CandidatePair]
        De-duplicated set of (record_id_a, record_id_b) tuples.
    """
    records_map: Dict[int, SourceRecord] = {r.id: r for r in records}
    candidates: Set[CandidatePair] = set()

    strategies = [
        ("PAN", _block_by_pan),
        ("Mobile", _block_by_mobile),
        ("Email", _block_by_email),
        ("NamePrefix", _block_by_name_prefix),
        ("DOB", _block_by_dob),
    ]

    for name, strategy_fn in strategies:
        buckets = strategy_fn(records)
        pairs = _emit_pairs_with_oversized_protection(buckets, records_map, name, max_bucket_size)
        logger.info("Blocking strategy '%s' produced %d pairs", name, len(pairs))
        candidates.update(pairs)

    logger.info("Total unique candidate pairs generated: %d", len(candidates))
    return candidates


def _block_by_pan(records: List[SourceRecord]) -> Dict[str, Set[int]]:
    buckets: Dict[str, Set[int]] = defaultdict(set)
    for r in records:
        if r.normalized_pan:
            buckets[r.normalized_pan].add(r.id)
    return buckets


def _block_by_mobile(records: List[SourceRecord]) -> Dict[str, Set[int]]:
    buckets: Dict[str, Set[int]] = defaultdict(set)
    for r in records:
        if r.normalized_mobile:
            buckets[r.normalized_mobile].add(r.id)
    return buckets


def _block_by_email(records: List[SourceRecord]) -> Dict[str, Set[int]]:
    buckets: Dict[str, Set[int]] = defaultdict(set)
    for r in records:
        if r.normalized_email:
            buckets[r.normalized_email].add(r.id)
    return buckets


def _block_by_name_prefix(
    records: List[SourceRecord], prefix_len: int = 4
) -> Dict[str, Set[int]]:
    buckets: Dict[str, Set[int]] = defaultdict(set)
    for r in records:
        if r.normalized_name and len(r.normalized_name) >= prefix_len:
            key = r.normalized_name[:prefix_len]
            buckets[key].add(r.id)
    return buckets


def _block_by_dob(records: List[SourceRecord]) -> Dict[str, Set[int]]:
    buckets: Dict[str, Set[int]] = defaultdict(set)
    for r in records:
        if r.normalized_dob:
            buckets[str(r.normalized_dob)].add(r.id)
    return buckets


async def get_incremental_candidate_records(
    db: AsyncSession,
    target_record: SourceRecord,
) -> List[SourceRecord]:
    """
    Database-backed incremental candidate lookup for a single target record.
    Uses PostgreSQL B-Tree indexes to retrieve only likely candidate SourceRecords
    directly from Supabase without loading all historical records into memory.

    Parameters
    ----------
    db : AsyncSession
    target_record : SourceRecord

    Returns
    -------
    List[SourceRecord]
        List of matching candidate records from database.
    """
    conditions = []
    if target_record.normalized_pan:
        conditions.append(SourceRecord.normalized_pan == target_record.normalized_pan)
    if target_record.normalized_mobile:
        conditions.append(SourceRecord.normalized_mobile == target_record.normalized_mobile)
    if target_record.normalized_email:
        conditions.append(SourceRecord.normalized_email == target_record.normalized_email)
    if target_record.normalized_dob:
        conditions.append(SourceRecord.normalized_dob == target_record.normalized_dob)
    if target_record.normalized_name and len(target_record.normalized_name) >= 4:
        name_prefix = target_record.normalized_name[:4]
        conditions.append(SourceRecord.normalized_name.startswith(name_prefix))

    if not conditions:
        return []

    stmt = select(SourceRecord).where(
        SourceRecord.id != target_record.id,
        or_(*conditions),
    )
    res = await db.execute(stmt)
    candidates = res.scalars().all()
    logger.info(
        "Incremental DB lookup for target record ID %d ('%s') returned %d candidate records",
        target_record.id, target_record.original_name, len(candidates),
    )
    return list(candidates)

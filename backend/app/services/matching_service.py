"""
Nexus360 — Matching Service.

Orchestrates the full identity resolution pipeline:
1. Load source records (batch or incremental database candidate lookup)
2. Generate candidate pairs via blocking with oversized bucket protection
3. Run deterministic matching
4. Extract 8 attribute features (including Jaro-Winkler and vector ML semantic embeddings)
5. Compute weighted scores (0.0 to 1.0)
6. Make decisions (MATCH / REVIEW / NON_MATCH)
7. Create / update / merge golden customers
8. Create review cases with review_type, priority, and details for REVIEW decisions
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_record import SourceRecord
from app.models.match_decision import MatchDecision, Decision
from app.models.identity_link import IdentityLink, MatchMethod, LinkStatus
from app.models.review_case import ReviewCase, ReviewPriority, ReviewStatus, ReviewType, VerificationClassification, VerificationStatus
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus

from app.matching.blocking import (
    generate_candidate_pairs,
    _make_pair,
    get_incremental_candidate_records,
)
from app.matching.deterministic import run_deterministic_rules
from app.matching.fuzzy import extract_features
from app.matching.scoring import compute_score, make_decision

from app.models.audit_log import AuditAction
from app.services.audit_service import log_action
from app.services.golden_record_service import (
    create_golden_customer,
    link_to_golden,
    find_golden_by_source_record,
    recalculate_golden_customer,
    merge_golden_customers,
)
from app.services.explanation_service import (
    generate_ai_explanation_text,
    generate_review_suggestion,
)

logger = logging.getLogger(__name__)


from sqlalchemy import select, or_

async def _get_already_decided_pairs(
    db: AsyncSession, candidate_pairs: Set[Tuple[int, int]]
) -> Set[Tuple[int, int]]:
    """Check Supabase for existing match decisions on candidate pairs using indexed queries."""
    if not candidate_pairs:
        return set()

    all_ids = set()
    canonical_candidates = set()
    for a, b in candidate_pairs:
        all_ids.add(a)
        all_ids.add(b)
        canonical_candidates.add(_make_pair(a, b))

    if not all_ids:
        return set()

    stmt = select(MatchDecision.record_a_id, MatchDecision.record_b_id).where(
        or_(
            MatchDecision.record_a_id.in_(all_ids),
            MatchDecision.record_b_id.in_(all_ids),
        )
    )
    res = await db.execute(stmt)
    already_decided: Set[Tuple[int, int]] = set()
    for ra, rb in res.all():
        pair = _make_pair(ra, rb)
        if pair in canonical_candidates:
            already_decided.add(pair)
    return already_decided


async def run_matching_pipeline(
    db: AsyncSession,
) -> Dict[str, int]:
    """
    Execute the full matching pipeline on all source records.

    Returns
    -------
    dict
        Summary statistics: pairs_evaluated, matches, reviews,
        non_matches, golden_customers_created, golden_customers_updated.
    """
    stats = {
        "pairs_evaluated": 0,
        "matches": 0,
        "reviews": 0,
        "non_matches": 0,
        "golden_customers_created": 0,
        "golden_customers_updated": 0,
    }

    # 1. Load all source records
    result = await db.execute(select(SourceRecord))
    all_records = result.scalars().all()

    if len(all_records) < 2:
        logger.info("Not enough records to match (found %d)", len(all_records))
        return stats

    logger.info("Starting matching pipeline with %d records", len(all_records))

    # Build lookup map
    record_map: Dict[int, SourceRecord] = {r.id: r for r in all_records}

    # 2. Generate candidate pairs via blocking (with oversized bucket protection)
    candidate_pairs = generate_candidate_pairs(list(all_records))
    logger.info("Generated %d candidate pairs", len(candidate_pairs))

    # 3. Check which candidate pairs already have decisions using indexed DB lookup
    already_decided = await _get_already_decided_pairs(db, candidate_pairs)
    logger.info("Skipping %d previously decided candidate pairs", len(already_decided))

    # 4. Process each candidate pair
    for id_a, id_b in candidate_pairs:
        if (id_a, id_b) in already_decided:
            continue

        rec_a = record_map.get(id_a)
        rec_b = record_map.get(id_b)
        if not rec_a or not rec_b:
            continue

        stats["pairs_evaluated"] += 1

        # ── Step 3a: Deterministic matching ──────────────────────
        det_result = run_deterministic_rules(rec_a, rec_b)

        # ── Step 4: Feature extraction (8 attributes) ─────────────
        features = extract_features(rec_a, rec_b)

        # ── Step 5: Weighted scoring (0.0 to 1.0) ─────────────────
        score_breakdown = compute_score(features)

        # ── Step 6: Decision ─────────────────────────────────────
        if det_result and det_result.is_match:
            decision_str = "MATCH"
            final_score = det_result.confidence
            reasoning = {
                "deterministic": det_result.reason,
                "features": features.model_dump(),
                "score_breakdown": score_breakdown.model_dump(),
            }
        elif det_result and det_result.is_review:
            decision_str = "REVIEW"
            final_score = det_result.confidence
            reasoning = {
                "deterministic": det_result.reason,
                "features": features.model_dump(),
                "score_breakdown": score_breakdown.model_dump(),
            }
        else:
            scoring_decision = make_decision(features, score_breakdown, rec_a, rec_b)
            decision_str = scoring_decision.decision
            final_score = scoring_decision.score
            reasoning = {
                "features": features.model_dump(),
                "score_breakdown": score_breakdown.model_dump(),
                "scoring_reasoning": scoring_decision.reasoning,
            }

        # ── Generate AI explanation ────────────────────────────
        ai_explanation = generate_ai_explanation_text(
            features=features.model_dump(),
            contributions=score_breakdown.contributions,
            final_score=final_score,
            decision=decision_str,
            reasoning=reasoning,
        )

        # ── Persist MatchDecision ────────────────────────────────
        match_decision = MatchDecision(
            record_a_id=id_a,
            record_b_id=id_b,
            pan_match=features.pan_exact,
            mobile_match=features.mobile_exact,
            email_match=features.email_exact,
            name_similarity=features.name_similarity,
            name_semantic_similarity=features.name_semantic_similarity,
            dob_match=features.dob_exact,
            city_similarity=features.city_similarity,
            segment_match=features.segment_exact,
            final_score=final_score,
            decision=Decision(decision_str),
            reasoning=reasoning,
            ai_explanation=ai_explanation,
        )
        db.add(match_decision)
        await db.flush()

        # ── Handle decision outcomes ─────────────────────────────
        if decision_str == "MATCH":
            stats["matches"] += 1
            await _handle_match(db, rec_a, rec_b, final_score, stats)

        elif decision_str == "REVIEW":
            stats["reviews"] += 1
            priority = (
                ReviewPriority.HIGH if final_score >= 0.80 or "pan_conflict" in str(reasoning)
                else ReviewPriority.MEDIUM if final_score >= 0.60
                else ReviewPriority.LOW
            )
            r_type = (
                ReviewType.ATTRIBUTE_CONFLICT if ("conflict" in str(reasoning).lower())
                else ReviewType.LOW_CONFIDENCE_MATCH
            )
            ai_suggestion = generate_review_suggestion(
                features=features.model_dump(),
                contributions=score_breakdown.contributions,
                final_score=final_score,
                decision=decision_str,
                reasoning=reasoning,
            )
            # Determine Verification Classification
            v_class = VerificationClassification.HUMAN_VERIFICATION_REQUIRED
            if final_score >= 0.70 and "pan_conflict" not in str(reasoning) and features.name_similarity > 0.8:
                v_class = VerificationClassification.AI_VERIFICATION_ELIGIBLE

            review = ReviewCase(
                match_decision_id=match_decision.id,
                priority=priority,
                review_type=r_type,
                status=ReviewStatus.PENDING,
                verification_classification=v_class,
                verification_status=VerificationStatus.PENDING,
                source_record_ids=[rec_a.id, rec_b.id],
                details={
                    "record_a": {"id": rec_a.id, "system": rec_a.source_system.value, "name": rec_a.original_name},
                    "record_b": {"id": rec_b.id, "system": rec_b.source_system.value, "name": rec_b.original_name},
                    "score": final_score,
                    "reasoning": reasoning,
                },
                ai_suggestion=ai_suggestion,
            )
            db.add(review)
            await db.flush()
            await log_action(
                db,
                action=AuditAction.REVIEW_CREATED,
                actor_username="system",
                actor_role="System",
                entity_type="ReviewCase",
                entity_id=str(review.id),
                new_value={
                    "match_decision_id": match_decision.id,
                    "priority": priority.value,
                    "review_type": r_type.value,
                    "source_record_ids": [rec_a.id, rec_b.id],
                    "final_score": final_score,
                },
            )

        else:  # NON_MATCH
            stats["non_matches"] += 1

    # 5. Create golden customers for unlinked records
    await _create_golden_for_unlinked(db, all_records, stats)

    await db.flush()
    logger.info("Matching pipeline complete: %s", stats)
    return stats


async def run_incremental_matching_for_record(
    db: AsyncSession,
    target_record: SourceRecord,
) -> Dict[str, int]:
    """
    Run database-backed incremental matching for a single target record
    against likely candidates retrieved from Supabase indexes, without loading all records into RAM.
    """
    stats = {
        "pairs_evaluated": 0,
        "matches": 0,
        "reviews": 0,
        "non_matches": 0,
        "golden_customers_created": 0,
        "golden_customers_updated": 0,
    }

    # 1. Query Supabase database indexes for candidate records matching target_record
    candidates = await get_incremental_candidate_records(db, target_record)
    if not candidates:
        logger.info("No DB candidate records found for target record %d", target_record.id)
        golden = await create_golden_customer(db, target_record, MatchMethod.DETERMINISTIC, 1.0)
        stats["golden_customers_created"] += 1
        return stats

    # 2. Build candidate pair set and check existing decisions
    candidate_pairs = {_make_pair(target_record.id, c.id) for c in candidates}
    already_decided = await _get_already_decided_pairs(db, candidate_pairs)

    record_map: Dict[int, SourceRecord] = {c.id: c for c in candidates}
    record_map[target_record.id] = target_record

    # 3. Process candidate pairs
    for id_a, id_b in candidate_pairs:
        if (id_a, id_b) in already_decided:
            continue

        rec_a = record_map.get(id_a)
        rec_b = record_map.get(id_b)
        if not rec_a or not rec_b:
            continue

        stats["pairs_evaluated"] += 1

        det_result = run_deterministic_rules(rec_a, rec_b)
        features = extract_features(rec_a, rec_b)
        score_breakdown = compute_score(features)

        if det_result and det_result.is_match:
            decision_str = "MATCH"
            final_score = det_result.confidence
            reasoning = {
                "deterministic": det_result.reason,
                "features": features.model_dump(),
                "score_breakdown": score_breakdown.model_dump(),
            }
        elif det_result and det_result.is_review:
            decision_str = "REVIEW"
            final_score = det_result.confidence
            reasoning = {
                "deterministic": det_result.reason,
                "features": features.model_dump(),
                "score_breakdown": score_breakdown.model_dump(),
            }
        else:
            scoring_decision = make_decision(features, score_breakdown, rec_a, rec_b)
            decision_str = scoring_decision.decision
            final_score = scoring_decision.score
            reasoning = {
                "features": features.model_dump(),
                "score_breakdown": score_breakdown.model_dump(),
                "scoring_reasoning": scoring_decision.reasoning,
            }

        ai_explanation = generate_ai_explanation_text(
            features=features.model_dump(),
            contributions=score_breakdown.contributions,
            final_score=final_score,
            decision=decision_str,
            reasoning=reasoning,
        )

        match_decision = MatchDecision(
            record_a_id=id_a,
            record_b_id=id_b,
            pan_match=features.pan_exact,
            mobile_match=features.mobile_exact,
            email_match=features.email_exact,
            name_similarity=features.name_similarity,
            name_semantic_similarity=features.name_semantic_similarity,
            dob_match=features.dob_exact,
            city_similarity=features.city_similarity,
            segment_match=features.segment_exact,
            final_score=final_score,
            decision=Decision(decision_str),
            reasoning=reasoning,
            ai_explanation=ai_explanation,
        )
        db.add(match_decision)
        await db.flush()

        if decision_str == "MATCH":
            stats["matches"] += 1
            await _handle_match(db, rec_a, rec_b, final_score, stats)
        elif decision_str == "REVIEW":
            stats["reviews"] += 1
            priority = (
                ReviewPriority.HIGH if final_score >= 0.80 or "pan_conflict" in str(reasoning)
                else ReviewPriority.MEDIUM if final_score >= 0.60
                else ReviewPriority.LOW
            )
            r_type = (
                ReviewType.ATTRIBUTE_CONFLICT if ("conflict" in str(reasoning).lower())
                else ReviewType.LOW_CONFIDENCE_MATCH
            )
            ai_suggestion = generate_review_suggestion(
                features=features.model_dump(),
                contributions=score_breakdown.contributions,
                final_score=final_score,
                decision=decision_str,
                reasoning=reasoning,
            )
            # Determine Verification Classification
            v_class = VerificationClassification.HUMAN_VERIFICATION_REQUIRED
            if final_score >= 0.70 and "pan_conflict" not in str(reasoning) and features.name_similarity > 0.8:
                v_class = VerificationClassification.AI_VERIFICATION_ELIGIBLE

            review = ReviewCase(
                match_decision_id=match_decision.id,
                priority=priority,
                review_type=r_type,
                status=ReviewStatus.PENDING,
                verification_classification=v_class,
                verification_status=VerificationStatus.PENDING,
                source_record_ids=[rec_a.id, rec_b.id],
                details={
                    "record_a": {"id": rec_a.id, "system": rec_a.source_system.value, "name": rec_a.original_name},
                    "record_b": {"id": rec_b.id, "system": rec_b.source_system.value, "name": rec_b.original_name},
                    "score": final_score,
                    "reasoning": reasoning,
                },
                ai_suggestion=ai_suggestion,
            )
            db.add(review)
            await db.flush()
            await log_action(
                db,
                action=AuditAction.REVIEW_CREATED,
                actor_username="system",
                actor_role="System",
                entity_type="ReviewCase",
                entity_id=str(review.id),
                new_value={
                    "match_decision_id": match_decision.id,
                    "priority": priority.value,
                    "review_type": r_type.value,
                    "source_record_ids": [rec_a.id, rec_b.id],
                    "final_score": final_score,
                },
            )
        else:
            stats["non_matches"] += 1

    # Check if target record remains unlinked
    await _create_golden_for_unlinked(db, [target_record], stats)
    await db.flush()
    return stats


async def _handle_match(
    db: AsyncSession,
    rec_a: SourceRecord,
    rec_b: SourceRecord,
    confidence: float,
    stats: Dict[str, int],
) -> None:
    """
    Handle a MATCH decision between two records.

    If both records already belong to different Golden Customers, merge golden_b into golden_a.
    If one record belongs to a Golden Customer, link the other.
    If neither belongs to a Golden Customer, create a new Golden Customer.
    """
    golden_a = await find_golden_by_source_record(db, rec_a.id)
    golden_b = await find_golden_by_source_record(db, rec_b.id)

    if golden_a and golden_b:
        if golden_a.golden_customer_id == golden_b.golden_customer_id:
            return  # Already same customer

        await merge_golden_customers(db, golden_a, golden_b)
        stats["golden_customers_updated"] += 1

    elif golden_a:
        await link_to_golden(
            db, rec_b, golden_a, MatchMethod.DETERMINISTIC, confidence
        )
        stats["golden_customers_updated"] += 1
    elif golden_b:
        await link_to_golden(
            db, rec_a, golden_b, MatchMethod.DETERMINISTIC, confidence
        )
        stats["golden_customers_updated"] += 1
    else:
        golden = await create_golden_customer(
            db, rec_a, MatchMethod.DETERMINISTIC, confidence
        )
        stats["golden_customers_created"] += 1
        await link_to_golden(
            db, rec_b, golden, MatchMethod.DETERMINISTIC, confidence
        )
        stats["golden_customers_updated"] += 1


async def _create_golden_for_unlinked(
    db: AsyncSession,
    all_records: list,
    stats: Dict[str, int],
) -> None:
    """Create golden customers for source records with no identity links."""
    linked_result = await db.execute(select(IdentityLink.source_record_id))
    linked_ids = {row[0] for row in linked_result.all()}

    for record in all_records:
        if record.id not in linked_ids:
            await create_golden_customer(
                db, record, MatchMethod.DETERMINISTIC, 1.0
            )
            stats["golden_customers_created"] += 1

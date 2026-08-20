"""
Nexus360 — Explainable Rule-Based Scoring Engine.

Computes a weighted confidence score (0.0 to 1.0) from a FeatureVector across 8 attributes,
then applies safety rules to produce a final decision (MATCH / REVIEW / NON_MATCH).
Aligned with PRD v3.0 §5.2 scoring matrix:
  PAN:              0.35
  Mobile:           0.20
  Email:            0.15
  Name (String):    0.12
  Name (Semantic):  0.08
  DOB:              0.05
  City:             0.03
  Segment:          0.02
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict

from app.core.config import settings
from app.models.source_record import SourceRecord
from app.schemas.matching import FeatureVector, ScoreBreakdown

logger = logging.getLogger(__name__)


@dataclass
class ScoringDecision:
    """Complete scoring output including decision and reasoning."""
    score: float
    decision: str  # MATCH | REVIEW | NON_MATCH
    contributions: Dict[str, float]
    reasoning: Dict[str, str]


def compute_score(features: FeatureVector) -> ScoreBreakdown:
    """
    Compute a weighted confidence score normalized to 0.0–1.0 per PRD §5.2.

    Parameters
    ----------
    features : FeatureVector
        8 feature scores for a record pair.

    Returns
    -------
    ScoreBreakdown
        Contains final_score (0.0–1.0) and per-feature contributions.
    """
    contributions = {
        "pan": round(features.pan_exact * settings.WEIGHT_PAN, 4),
        "mobile": round(features.mobile_exact * settings.WEIGHT_MOBILE, 4),
        "email": round(features.email_exact * settings.WEIGHT_EMAIL, 4),
        "name_string": round(features.name_similarity * settings.WEIGHT_NAME, 4),
        "name_semantic": round(features.name_semantic_similarity * getattr(settings, "WEIGHT_NAME_SEMANTIC", 0.08), 4),
        "dob": round(features.dob_exact * settings.WEIGHT_DOB, 4),
        "city": round(features.city_similarity * settings.WEIGHT_CITY, 4),
        "segment": round(features.segment_exact * getattr(settings, "WEIGHT_SEGMENT", 0.02), 4),
    }

    raw_score = sum(contributions.values())
    final_score = max(0.0, min(1.0, round(raw_score, 4)))

    return ScoreBreakdown(
        final_score=final_score,
        contributions=contributions,
    )


def make_decision(
    features: FeatureVector,
    score_breakdown: ScoreBreakdown,
    rec_a: SourceRecord,
    rec_b: SourceRecord,
) -> ScoringDecision:
    """
    Apply thresholds and safety rules to produce a final decision.

    Thresholds (PRD §5.2):
    - auto_merge_threshold >= 0.85 -> MATCH
    - review_threshold in [0.60, 0.85) -> REVIEW
    - < 0.60 -> NON_MATCH

    Safety rules:
    1. PAN conflict (both present, differ) -> force REVIEW
    2. DOB conflict without strong identifiers -> downgrade decision

    Returns
    -------
    ScoringDecision
    """
    score = score_breakdown.final_score
    contributions = score_breakdown.contributions
    reasoning: Dict[str, str] = {}

    match_thresh = settings.MATCH_THRESHOLD if settings.MATCH_THRESHOLD <= 1.0 else settings.MATCH_THRESHOLD / 100.0
    review_thresh = settings.REVIEW_THRESHOLD if settings.REVIEW_THRESHOLD <= 1.0 else settings.REVIEW_THRESHOLD / 100.0

    # Default threshold-based decision
    if score >= match_thresh:
        decision = "MATCH"
        reasoning["threshold"] = f"Score {score:.4f} >= match threshold {match_thresh:.2f}"
    elif score >= review_thresh:
        decision = "REVIEW"
        reasoning["threshold"] = f"Score {score:.4f} in [{review_thresh:.2f}, {match_thresh:.2f})"
    else:
        decision = "NON_MATCH"
        reasoning["threshold"] = f"Score {score:.4f} < review threshold {review_thresh:.2f}"

    # ── Safety Rule 1: PAN conflict ──────────────────────────────
    pan_a = rec_a.normalized_pan
    pan_b = rec_b.normalized_pan
    if pan_a and pan_b and pan_a != pan_b:
        decision = "REVIEW"
        reasoning["pan_conflict"] = (
            f"PAN conflict: {pan_a} vs {pan_b} — forcing REVIEW"
        )
        logger.warning(
            "PAN conflict detected between records %d and %d", rec_a.id, rec_b.id
        )

    # ── Safety Rule 2: DOB conflict without strong identifiers ──
    dob_a = rec_a.normalized_dob
    dob_b = rec_b.normalized_dob
    if dob_a and dob_b and dob_a != dob_b:
        if features.pan_exact < 1.0 and features.mobile_exact < 1.0:
            if score >= review_thresh:
                decision = "REVIEW"
                reasoning["dob_conflict"] = (
                    "DOB conflict without PAN/mobile match — downgraded to REVIEW"
                )
            else:
                decision = "NON_MATCH"
                reasoning["dob_conflict"] = (
                    "DOB conflict without PAN/mobile match — NON_MATCH"
                )

    return ScoringDecision(
        score=score,
        decision=decision,
        contributions=contributions,
        reasoning=reasoning,
    )

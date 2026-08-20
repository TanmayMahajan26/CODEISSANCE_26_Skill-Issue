"""
Nexus360 — Deterministic Matching Rules.

High-confidence rules that produce MATCH or REVIEW decisions based
on exact identifier agreement. These run BEFORE fuzzy scoring and
can short-circuit the pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from rapidfuzz.distance import JaroWinkler

from app.models.source_record import SourceRecord

logger = logging.getLogger(__name__)


@dataclass
class DeterministicResult:
    """Outcome of the deterministic matching step."""
    is_match: bool = False
    is_review: bool = False
    reason: str = ""
    confidence: float = 0.0


def run_deterministic_rules(
    rec_a: SourceRecord,
    rec_b: SourceRecord,
) -> Optional[DeterministicResult]:
    """
    Apply deterministic matching rules to a record pair.

    Rules (evaluated in order):
    1. Exact PAN match (both non-null) → Strong MATCH candidate (confidence=1.0)
    2. PAN conflict (both present but differ) → REVIEW (confidence=0.50)
    3. Exact mobile + high name overlap → MATCH candidate (confidence=0.92)
    4. Exact email + high name overlap → MATCH candidate (confidence=0.90)

    Returns None when no deterministic rule fires (fall through to fuzzy).
    """
    pan_a = rec_a.normalized_pan
    pan_b = rec_b.normalized_pan

    # ── Rule 1 & 2: PAN-based ───────────────────────────────────
    if pan_a and pan_b:
        if pan_a == pan_b:
            logger.debug(
                "Deterministic MATCH (PAN): %s == %s", pan_a, pan_b
            )
            return DeterministicResult(
                is_match=True,
                reason="Exact PAN match",
                confidence=1.0,
            )
        else:
            # Both PANs present but different — suspicious
            logger.debug(
                "Deterministic REVIEW (PAN conflict): %s != %s", pan_a, pan_b
            )
            return DeterministicResult(
                is_review=True,
                reason="PAN conflict — both present but differ",
                confidence=0.50,
            )

    # Helper: name similarity using Jaro-Winkler
    name_a = rec_a.normalized_name or ""
    name_b = rec_b.normalized_name or ""
    name_sim = JaroWinkler.similarity(name_a, name_b) if (name_a and name_b) else 0.0

    # ── Rule 3: Mobile + high name similarity ────────────────────
    mob_a = rec_a.normalized_mobile
    mob_b = rec_b.normalized_mobile
    if mob_a and mob_b and mob_a == mob_b and name_sim >= 0.80:
        logger.debug(
            "Deterministic MATCH (Mobile + Name): mobile=%s name_sim=%.2f",
            mob_a, name_sim,
        )
        return DeterministicResult(
            is_match=True,
            reason=f"Exact mobile match + name similarity {name_sim:.2f}",
            confidence=0.92,
        )

    # ── Rule 4: Email + high name similarity ─────────────────────
    email_a = rec_a.normalized_email
    email_b = rec_b.normalized_email
    if email_a and email_b and email_a == email_b and name_sim >= 0.80:
        logger.debug(
            "Deterministic MATCH (Email + Name): email=%s name_sim=%.2f",
            email_a, name_sim,
        )
        return DeterministicResult(
            is_match=True,
            reason=f"Exact email match + name similarity {name_sim:.2f}",
            confidence=0.90,
        )

    return None  # no deterministic rule fired

"""
Nexus360 — Explanation Service.

Deterministic explanation engine that converts structured match decision data
into human-readable explanations.  Zero external API dependencies.

LAYER 1: Rule-based template engine using existing MatchDecision.reasoning JSONB.
LAYER 2: ExplanationProvider protocol for optional future AI/LLM integration.

Aligned with PRD v3.0 §7.4 and the Review Queue audit findings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Friendly display names for feature keys ────────────────────────
_FEATURE_LABELS: Dict[str, str] = {
    "pan": "PAN",
    "mobile": "Mobile",
    "email": "Email",
    "name_string": "Name (string similarity)",
    "name_semantic": "Name (semantic similarity)",
    "dob": "DOB",
    "city": "City",
    "segment": "Segment",
}

# Map FeatureVector field names → contribution keys
_FEATURE_TO_CONTRIB: Dict[str, str] = {
    "pan_exact": "pan",
    "mobile_exact": "mobile",
    "email_exact": "email",
    "name_similarity": "name_string",
    "name_semantic_similarity": "name_semantic",
    "dob_exact": "dob",
    "city_similarity": "city",
    "segment_exact": "segment",
}


# ── Data classes ───────────────────────────────────────────────────
@dataclass
class FieldComparison:
    """Per-field comparison result for reviewer UI."""
    field_name: str
    label: str
    score: float
    status: str  # "MATCH" | "DIFFERENT" | "PARTIAL" | "MISSING"
    weighted_contribution: float
    weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "label": self.label,
            "score": self.score,
            "status": self.status,
            "weighted_contribution": self.weighted_contribution,
            "weight": self.weight,
        }


@dataclass
class MatchExplanation:
    """Complete structured explanation for a match decision."""
    summary: str
    decision_reason: str
    strongest_signals: List[str]
    conflicting_signals: List[str]
    field_comparisons: List[FieldComparison]
    recommendation: str      # "LIKELY_MATCH" | "LIKELY_NON_MATCH" | "UNCERTAIN"
    confidence_level: str    # "High" | "Moderate" | "Low"
    safety_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "decision_reason": self.decision_reason,
            "strongest_signals": self.strongest_signals,
            "conflicting_signals": self.conflicting_signals,
            "field_comparisons": [fc.to_dict() for fc in self.field_comparisons],
            "recommendation": self.recommendation,
            "confidence_level": self.confidence_level,
            "safety_flags": self.safety_flags,
        }


# ── Layer 2 Protocol (future AI/LLM integration) ──────────────────
class ExplanationProvider(Protocol):
    """
    Swappable explanation backend.

    Default: DeterministicExplanationProvider (Layer 1, rule-based).
    Future:  LLMExplanationProvider (Layer 2, optional AI).
    """

    def generate(
        self,
        features: Dict[str, float],
        contributions: Dict[str, float],
        final_score: float,
        decision: str,
        reasoning: Dict[str, Any],
    ) -> MatchExplanation:
        ...


# ── Layer 1 Implementation ────────────────────────────────────────
class DeterministicExplanationProvider:
    """
    Rule-based explanation engine.  Uses existing structured match data
    to generate deterministic, repeatable human-readable explanations.
    """

    def __init__(
        self,
        match_threshold: float | None = None,
        review_threshold: float | None = None,
    ) -> None:
        self.match_threshold = match_threshold or settings.MATCH_THRESHOLD
        self.review_threshold = review_threshold or settings.REVIEW_THRESHOLD
        # Normalise thresholds to 0-1 range
        if self.match_threshold > 1.0:
            self.match_threshold /= 100.0
        if self.review_threshold > 1.0:
            self.review_threshold /= 100.0

    # ── Public API ─────────────────────────────────────────────────
    def generate(
        self,
        features: Dict[str, float],
        contributions: Dict[str, float],
        final_score: float,
        decision: str,
        reasoning: Dict[str, Any],
    ) -> MatchExplanation:
        """
        Generate a complete MatchExplanation from structured scoring data.

        Parameters
        ----------
        features : dict
            FeatureVector as dict  (pan_exact, mobile_exact, … segment_exact).
        contributions : dict
            Per-feature weighted contributions (pan, mobile, … segment).
        final_score : float
            0.0–1.0 confidence score.
        decision : str
            "MATCH" | "REVIEW" | "NON_MATCH".
        reasoning : dict
            Full reasoning dict from MatchDecision.reasoning JSONB.
        """
        field_comparisons = self._build_field_comparisons(features, contributions)
        strongest = self._strongest_signals(field_comparisons)
        conflicting = self._conflicting_signals(field_comparisons)
        safety_flags = self._extract_safety_flags(reasoning)
        decision_reason = self._decision_reason(final_score, decision, reasoning)
        recommendation = self._recommendation(final_score, decision, strongest, conflicting)
        confidence_level = self._confidence_level(final_score)
        summary = self._build_summary(
            final_score, decision, strongest, conflicting, safety_flags,
            features, recommendation,
        )

        return MatchExplanation(
            summary=summary,
            decision_reason=decision_reason,
            strongest_signals=strongest,
            conflicting_signals=conflicting,
            field_comparisons=field_comparisons,
            recommendation=recommendation,
            confidence_level=confidence_level,
            safety_flags=safety_flags,
        )

    # ── Internal helpers ───────────────────────────────────────────
    def _build_field_comparisons(
        self,
        features: Dict[str, float],
        contributions: Dict[str, float],
    ) -> List[FieldComparison]:
        """Build per-field comparison list from features and contributions."""
        weights = {
            "pan": settings.WEIGHT_PAN,
            "mobile": settings.WEIGHT_MOBILE,
            "email": settings.WEIGHT_EMAIL,
            "name_string": settings.WEIGHT_NAME,
            "name_semantic": settings.WEIGHT_NAME_SEMANTIC,
            "dob": settings.WEIGHT_DOB,
            "city": settings.WEIGHT_CITY,
            "segment": settings.WEIGHT_SEGMENT,
        }

        comparisons: List[FieldComparison] = []
        for feat_key, contrib_key in _FEATURE_TO_CONTRIB.items():
            score = features.get(feat_key, 0.0)
            contrib = contributions.get(contrib_key, 0.0)
            weight = weights.get(contrib_key, 0.0)
            label = _FEATURE_LABELS.get(contrib_key, contrib_key)

            # Determine human-readable status
            if score >= 1.0:
                status = "MATCH"
            elif score >= 0.80:
                status = "PARTIAL"
            elif score <= 0.0:
                status = "DIFFERENT"
            else:
                status = "PARTIAL"

            comparisons.append(FieldComparison(
                field_name=contrib_key,
                label=label,
                score=round(score, 4),
                status=status,
                weighted_contribution=round(contrib, 4),
                weight=weight,
            ))

        return comparisons

    def _strongest_signals(self, comparisons: List[FieldComparison]) -> List[str]:
        """Top contributing matching signals (contribution > 0, sorted desc)."""
        matching = [
            fc for fc in comparisons
            if fc.weighted_contribution > 0 and fc.score >= 0.80
        ]
        matching.sort(key=lambda fc: fc.weighted_contribution, reverse=True)
        signals = []
        for fc in matching[:4]:
            if fc.score >= 1.0:
                signals.append(f"{fc.label} matches exactly (contribution: {fc.weighted_contribution:.2f})")
            else:
                signals.append(f"{fc.label} similarity {fc.score:.2f} (contribution: {fc.weighted_contribution:.2f})")
        return signals

    def _conflicting_signals(self, comparisons: List[FieldComparison]) -> List[str]:
        """Features that disagree (score < 0.5 but weight > 0)."""
        conflicts = [
            fc for fc in comparisons
            if fc.score < 0.5 and fc.weight > 0
        ]
        conflicts.sort(key=lambda fc: fc.weight, reverse=True)
        return [
            f"{fc.label} differs (contribution: {fc.weighted_contribution:.2f})"
            for fc in conflicts[:4]
        ]

    def _extract_safety_flags(self, reasoning: Dict[str, Any]) -> List[str]:
        """Extract safety rule explanations from reasoning dict."""
        flags: List[str] = []
        # Check scoring_reasoning (fuzzy path)
        scoring_reasoning = reasoning.get("scoring_reasoning", {})
        if isinstance(scoring_reasoning, dict):
            if "pan_conflict" in scoring_reasoning:
                flags.append(scoring_reasoning["pan_conflict"])
            if "dob_conflict" in scoring_reasoning:
                flags.append(scoring_reasoning["dob_conflict"])

        # Check deterministic reason (deterministic path)
        det_reason = reasoning.get("deterministic", "")
        if isinstance(det_reason, str) and "conflict" in det_reason.lower():
            flags.append(det_reason)

        return flags

    def _decision_reason(
        self, final_score: float, decision: str, reasoning: Dict[str, Any]
    ) -> str:
        """Generate a human-readable reason for the decision."""
        mt = self.match_threshold
        rt = self.review_threshold

        if decision == "MATCH":
            # Check for deterministic match
            det = reasoning.get("deterministic", "")
            if det:
                return f"Deterministic rule matched: {det}. Confidence score {final_score:.2f}."
            return f"Score {final_score:.2f} meets or exceeds the auto-merge threshold ({mt:.2f})."

        if decision == "REVIEW":
            parts = [f"Score {final_score:.2f} falls between review threshold ({rt:.2f}) and auto-merge threshold ({mt:.2f})."]
            # Append safety flag reasons
            scoring_reasoning = reasoning.get("scoring_reasoning", {})
            if isinstance(scoring_reasoning, dict):
                if "pan_conflict" in scoring_reasoning:
                    parts.append("PAN conflict detected — forced to manual review.")
                if "dob_conflict" in scoring_reasoning:
                    parts.append("DOB conflict without strong identifier match.")
            det = reasoning.get("deterministic", "")
            if isinstance(det, str) and "conflict" in det.lower():
                parts.append(f"Deterministic flag: {det}")
            return " ".join(parts)

        # NON_MATCH
        return f"Score {final_score:.2f} is below the review threshold ({rt:.2f})."

    def _recommendation(
        self,
        final_score: float,
        decision: str,
        strongest: List[str],
        conflicting: List[str],
    ) -> str:
        """Generate a reviewer recommendation."""
        if decision == "MATCH":
            return "LIKELY_MATCH"
        if decision == "NON_MATCH":
            return "LIKELY_NON_MATCH"

        # REVIEW — use signals to recommend
        mt = self.match_threshold
        rt = self.review_threshold
        midpoint = (mt + rt) / 2

        if final_score >= midpoint and len(strongest) > len(conflicting):
            return "LIKELY_MATCH"
        elif final_score < midpoint and len(conflicting) >= len(strongest):
            return "LIKELY_NON_MATCH"
        return "UNCERTAIN"

    def _confidence_level(self, final_score: float) -> str:
        """Map score to a human confidence level."""
        if final_score >= 0.85:
            return "High"
        elif final_score >= 0.60:
            return "Moderate"
        return "Low"

    def _build_summary(
        self,
        final_score: float,
        decision: str,
        strongest: List[str],
        conflicting: List[str],
        safety_flags: List[str],
        features: Dict[str, float],
        recommendation: str,
    ) -> str:
        """Build a 2-3 sentence human-readable summary."""
        parts: List[str] = []

        # Opening — decision summary
        if decision == "MATCH":
            parts.append(f"Auto-matched with confidence score {final_score:.2f}.")
        elif decision == "REVIEW":
            parts.append(f"Manual review recommended. Final confidence score is {final_score:.2f}.")
        else:
            parts.append(f"Non-match. Confidence score {final_score:.2f} is below threshold.")

        # Matching signals
        if strongest:
            match_labels = [s.split(" (")[0] for s in strongest[:3]]
            parts.append(f"{', '.join(match_labels)} contribute strongly to identity confidence.")

        # Name semantic detail
        name_sem = features.get("name_semantic_similarity", 0.0)
        if name_sem >= 0.80:
            parts.append(f"Name semantic similarity is high ({name_sem:.2f}).")
        elif name_sem > 0 and name_sem < 0.60:
            parts.append(f"Name semantic similarity is low ({name_sem:.2f}).")

        # Conflicts
        if conflicting:
            conflict_labels = [s.split(" differs")[0] for s in conflicting[:3]]
            parts.append(f"However, {', '.join(conflict_labels).lower()} differ.")

        # Safety flags
        if safety_flags:
            parts.append(f"Safety flag: {safety_flags[0]}")

        # Recommendation
        rec_map = {
            "LIKELY_MATCH": "Recommended action: Approve.",
            "LIKELY_NON_MATCH": "Recommended action: Reject.",
            "UNCERTAIN": "Requires careful manual review.",
        }
        parts.append(rec_map.get(recommendation, ""))

        return " ".join(p for p in parts if p)


# ── Module-level singleton ─────────────────────────────────────────
_provider: ExplanationProvider = DeterministicExplanationProvider()


def get_explanation_provider() -> ExplanationProvider:
    """Get the active explanation provider."""
    return _provider


def set_explanation_provider(provider: ExplanationProvider) -> None:
    """Swap in a different explanation provider (e.g. future LLM layer)."""
    global _provider
    _provider = provider
    logger.info("Registered ExplanationProvider: %s", provider.__class__.__name__)


# ── Convenience functions ──────────────────────────────────────────
def generate_explanation(
    features: Dict[str, float],
    contributions: Dict[str, float],
    final_score: float,
    decision: str,
    reasoning: Dict[str, Any],
) -> MatchExplanation:
    """Generate explanation using the active provider."""
    return _provider.generate(features, contributions, final_score, decision, reasoning)


def generate_ai_explanation_text(
    features: Dict[str, float],
    contributions: Dict[str, float],
    final_score: float,
    decision: str,
    reasoning: Dict[str, Any],
) -> str:
    """Generate the summary text suitable for MatchDecision.ai_explanation."""
    explanation = generate_explanation(features, contributions, final_score, decision, reasoning)
    return explanation.summary


def generate_review_suggestion(
    features: Dict[str, float],
    contributions: Dict[str, float],
    final_score: float,
    decision: str,
    reasoning: Dict[str, Any],
) -> str:
    """Generate reviewer-friendly suggestion for ReviewCase.ai_suggestion."""
    explanation = generate_explanation(features, contributions, final_score, decision, reasoning)

    # Build a concise suggestion for the reviewer
    rec_map = {
        "LIKELY_MATCH": "Approve",
        "LIKELY_NON_MATCH": "Reject",
        "UNCERTAIN": "Review carefully",
    }
    rec_action = rec_map.get(explanation.recommendation, "Review")

    parts = [f"{explanation.confidence_level} confidence match."]

    # Add top 2 strongest signals (compact form)
    for sig in explanation.strongest_signals[:2]:
        parts.append(sig.split(" (")[0] + ".")

    # Add top conflict
    if explanation.conflicting_signals:
        parts.append(explanation.conflicting_signals[0].split(" (")[0] + ".")

    parts.append(f"Score: {final_score:.2f}. Recommended action: {rec_action}.")

    return " ".join(parts)

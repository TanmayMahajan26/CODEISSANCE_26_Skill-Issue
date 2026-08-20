"""
Pydantic schemas for Review Cases.

Includes the lightweight list response, enriched detail response with
full source record comparison, and request payloads.
"""

from datetime import date, datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class ReviewCaseResponse(BaseModel):
    """API response for a review case (list endpoint)."""
    id: int
    match_decision_id: int
    priority: str
    status: str
    review_type: str = "LOW_CONFIDENCE_MATCH"
    reviewer: Optional[str] = None
    assigned_to: Optional[str] = None
    review_notes: Optional[str] = None
    ai_suggestion: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    source_record_ids: Optional[List[int]] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Enriched Detail Schemas ──────────────────────────────────────


class SourceRecordSummary(BaseModel):
    """Source record fields relevant for side-by-side review comparison."""
    id: int
    source_system: Optional[str] = None
    source_record_id: Optional[str] = None
    original_name: Optional[str] = None
    normalized_name: Optional[str] = None
    original_dob: Optional[date] = None
    normalized_dob: Optional[date] = None
    original_mobile: Optional[str] = None
    normalized_mobile: Optional[str] = None
    original_email: Optional[str] = None
    normalized_email: Optional[str] = None
    original_pan: Optional[str] = None
    normalized_pan: Optional[str] = None
    original_city: Optional[str] = None
    normalized_city: Optional[str] = None
    segment: Optional[str] = None
    product_type: Optional[str] = None
    balance_aum: Optional[float] = None
    relationship_value: Optional[float] = None


class FieldComparisonItem(BaseModel):
    """Per-field comparison entry for the review UI."""
    field_name: str
    label: str
    score: float
    status: str  # MATCH | DIFFERENT | PARTIAL
    weighted_contribution: float
    weight: float


class MatchDecisionSummary(BaseModel):
    """Summarised match decision for the review detail response."""
    id: int
    record_a_id: int
    record_b_id: int
    pan_match: Optional[float] = None
    mobile_match: Optional[float] = None
    email_match: Optional[float] = None
    name_similarity: Optional[float] = None
    name_semantic_similarity: Optional[float] = None
    dob_match: Optional[float] = None
    city_similarity: Optional[float] = None
    segment_match: Optional[float] = None
    final_score: float
    decision: str
    reasoning: Optional[Dict[str, Any]] = None
    ai_explanation: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GoldenCustomerSummary(BaseModel):
    """Minimal golden customer info relevant to the review."""
    golden_customer_id: str
    canonical_name: Optional[str] = None
    status: str = "ACTIVE"
    source_record_ids: List[int] = []


class ReviewCaseDetailResponse(BaseModel):
    """
    Enriched review case detail response for the reviewer UI.

    Contains:
    - Full review case metadata
    - Both source records side-by-side
    - Linked MatchDecision with scoring details
    - Field-by-field comparison table
    - Human-readable explanation and recommendation
    - Golden customer context (if any)
    """
    # ── Review Case ───────────────────────────────────────────────
    id: int
    match_decision_id: int
    priority: str
    status: str
    review_type: str
    reviewer: Optional[str] = None
    assigned_to: Optional[str] = None
    review_notes: Optional[str] = None
    ai_suggestion: Optional[str] = None
    source_record_ids: Optional[List[int]] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    # ── Source Records ────────────────────────────────────────────
    record_a: Optional[SourceRecordSummary] = None
    record_b: Optional[SourceRecordSummary] = None

    # ── Match Decision ────────────────────────────────────────────
    match_decision: Optional[MatchDecisionSummary] = None

    # ── Explainability ────────────────────────────────────────────
    field_comparisons: List[FieldComparisonItem] = []
    explanation: Optional[Dict[str, Any]] = None

    # ── Golden Customer context ───────────────────────────────────
    golden_customer_a: Optional[GoldenCustomerSummary] = None
    golden_customer_b: Optional[GoldenCustomerSummary] = None


# ── Request Schemas ──────────────────────────────────────────────


class ReviewActionRequest(BaseModel):
    """Payload for approving or rejecting a review case."""
    reviewer: str
    review_notes: Optional[str] = None


class ManualMergeRequest(BaseModel):
    """Payload for manual merge with custom field selection."""
    reviewer: str
    review_notes: Optional[str] = None
    selected_attributes: Dict[str, Any]  # e.g. {"canonical_name": "Rajesh Kumar Sharma", "canonical_mobile": "9876543210"}

"""
Pydantic schemas for Matching decisions and features.
"""

from datetime import datetime
from typing import Any, Dict, Optional, List

from pydantic import BaseModel


class FeatureVector(BaseModel):
    """Feature extraction result for a record pair."""
    pan_exact: float = 0.0
    mobile_exact: float = 0.0
    email_exact: float = 0.0
    name_similarity: float = 0.0
    name_semantic_similarity: float = 0.0
    dob_exact: float = 0.0
    city_similarity: float = 0.0
    segment_exact: float = 0.0


class ScoreBreakdown(BaseModel):
    """Explainable scoring result."""
    final_score: float
    contributions: Dict[str, float]


class MatchDecisionResponse(BaseModel):
    """API response for a match decision."""
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


class MatchRunResponse(BaseModel):
    """Response after running the matching engine."""
    message: str
    pairs_evaluated: int
    matches: int
    reviews: int
    non_matches: int
    golden_customers_created: int
    golden_customers_updated: int


class MatchingStatsResponse(BaseModel):
    """Matching statistics for Data Quality Dashboard."""
    total_source_records: int
    total_golden_records: int
    match_rate_pct: float
    total_pairs_evaluated: int
    total_matches: int
    total_reviews_pending: int
    total_non_matches: int
    ai_eligible: int = 0
    human_required: int = 0
    by_source_system: Dict[str, Dict[str, Any]] = {}

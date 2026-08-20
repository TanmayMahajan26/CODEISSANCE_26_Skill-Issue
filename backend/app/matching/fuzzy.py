"""
Nexus360 — Feature Extraction Engine.

Computes attribute similarity features for record pairs according to PRD §5.2:
- Exact binary features (0.0 or 1.0): PAN, Mobile, Email, DOB, City (after alias normalization), Segment
- String similarity (0.0 to 1.0): Name (Jaro-Winkler distance)
- Semantic similarity (0.0 to 1.0): Name (Semantic vector cosine similarity / ML model / token fallback)

Returns a FeatureVector that feeds into the scoring engine.
"""

from __future__ import annotations

import logging
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from app.models.source_record import SourceRecord
from app.schemas.matching import FeatureVector
from app.utils.normalization import normalize_segment

logger = logging.getLogger(__name__)


def _vector_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    sim = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, round(sim, 4)))


def extract_features(
    rec_a: SourceRecord,
    rec_b: SourceRecord,
) -> FeatureVector:
    """
    Compute a 8-feature vector for a pair of source records per PRD §5.2.

    Parameters
    ----------
    rec_a, rec_b : SourceRecord
        The two records to compare.

    Returns
    -------
    FeatureVector
        A Pydantic model with all 8 feature scores.
    """
    features = FeatureVector()

    # 1. PAN (exact binary 0/1)
    pan_a = rec_a.normalized_pan
    pan_b = rec_b.normalized_pan
    if pan_a and pan_b:
        features.pan_exact = 1.0 if pan_a == pan_b else 0.0

    # 2. Mobile (exact binary 0/1)
    mob_a = rec_a.normalized_mobile
    mob_b = rec_b.normalized_mobile
    if mob_a and mob_b:
        features.mobile_exact = 1.0 if mob_a == mob_b else 0.0

    # 3. Email (exact binary 0/1)
    email_a = rec_a.normalized_email
    email_b = rec_b.normalized_email
    if email_a and email_b:
        features.email_exact = 1.0 if email_a == email_b else 0.0

    # 4. Name String (Jaro-Winkler distance, PRD §5.2)
    name_a = rec_a.normalized_name or ""
    name_b = rec_b.normalized_name or ""
    if name_a and name_b:
        features.name_similarity = round(JaroWinkler.similarity(name_a, name_b), 4)
    else:
        features.name_similarity = 0.0

    # 5. Name Semantic (real vector cosine similarity / ML model / token fallback)
    if name_a and name_b:
        emb_a = getattr(rec_a, "name_embedding", None)
        emb_b = getattr(rec_b, "name_embedding", None)
        # Check if pre-computed vectors are available and non-zero
        if (
            isinstance(emb_a, list) and isinstance(emb_b, list)
            and len(emb_a) == 384 and len(emb_b) == 384
            and any(x != 0.0 for x in emb_a) and any(x != 0.0 for x in emb_b)
        ):
            features.name_semantic_similarity = _vector_cosine_similarity(emb_a, emb_b)
        else:
            # Fallback: compute dynamically using active embedding service
            from app.services.embedding_service import get_embedding_service
            emb_service = get_embedding_service()
            features.name_semantic_similarity = emb_service.compute_similarity_sync(name_a, name_b)
    else:
        features.name_semantic_similarity = 0.0

    # 6. DOB (exact binary 0/1)
    dob_a = rec_a.normalized_dob
    dob_b = rec_b.normalized_dob
    if dob_a and dob_b:
        features.dob_exact = 1.0 if dob_a == dob_b else 0.0

    # 7. City (exact or alias match binary 0/1, PRD §5.2)
    city_a = rec_a.normalized_city or ""
    city_b = rec_b.normalized_city or ""
    if city_a and city_b:
        features.city_similarity = 1.0 if city_a == city_b else 0.0
    else:
        features.city_similarity = 0.0

    # 8. Segment (exact match binary 0/1, PRD §5.2)
    seg_a = normalize_segment(rec_a.segment)
    seg_b = normalize_segment(rec_b.segment)
    if seg_a and seg_b:
        features.segment_exact = 1.0 if seg_a == seg_b else 0.0
    else:
        features.segment_exact = 0.0

    return features

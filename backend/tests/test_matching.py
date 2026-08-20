"""
Nexus360 — Tests for Matching Components.
"""

import pytest
from unittest.mock import MagicMock
from datetime import date

from app.matching.fuzzy import extract_features
from app.matching.scoring import compute_score, make_decision
from app.matching.deterministic import run_deterministic_rules
from app.matching.blocking import generate_candidate_pairs


def _make_record(**kwargs):
    """Create a mock SourceRecord with given attributes."""
    record = MagicMock()
    record.id = kwargs.get("id", 1)
    record.normalized_pan = kwargs.get("pan", None)
    record.normalized_mobile = kwargs.get("mobile", None)
    record.normalized_email = kwargs.get("email", None)
    record.normalized_name = kwargs.get("name", None)
    record.normalized_dob = kwargs.get("dob", None)
    record.normalized_city = kwargs.get("city", None)
    record.original_name = kwargs.get("name", None)
    record.segment = kwargs.get("segment", None)
    record.source_system = kwargs.get("source_system", "EQUITY")
    return record


# ── Feature Extraction Tests ────────────────────────────────────

class TestFeatureExtraction:
    def test_identical_records(self):
        rec_a = _make_record(
            pan="ABCDE1234F", mobile="9876543210",
            email="test@gmail.com", name="rohita raghavan",
            dob=date(1988, 6, 12), city="mumbai",
        )
        rec_b = _make_record(
            id=2, pan="ABCDE1234F", mobile="9876543210",
            email="test@gmail.com", name="rohita raghavan",
            dob=date(1988, 6, 12), city="mumbai",
        )
        features = extract_features(rec_a, rec_b)

        assert features.pan_exact == 1.0
        assert features.mobile_exact == 1.0
        assert features.email_exact == 1.0
        assert features.name_similarity >= 0.99
        assert features.dob_exact == 1.0
        assert features.city_similarity >= 0.99

    def test_completely_different(self):
        rec_a = _make_record(
            pan="AAAAA1111A", mobile="9999999999",
            email="alpha@gmail.com", name="alpha person",
            dob=date(1990, 1, 1), city="mumbai",
        )
        rec_b = _make_record(
            id=2, pan="ZZZZZ9999Z", mobile="1111111111",
            email="omega@yahoo.com", name="omega different",
            dob=date(1970, 12, 31), city="delhi",
        )
        features = extract_features(rec_a, rec_b)

        assert features.pan_exact == 0.0
        assert features.mobile_exact == 0.0
        assert features.email_exact == 0.0
        assert features.dob_exact == 0.0

    def test_partial_match(self):
        rec_a = _make_record(
            pan="ABCDE1234F", mobile="9876543210",
            name="rohita raghavan", city="mumbai",
        )
        rec_b = _make_record(
            id=2, pan="ABCDE1234F", mobile="1111111111",
            name="rohita p raghavan", city="mumbai",
        )
        features = extract_features(rec_a, rec_b)

        assert features.pan_exact == 1.0
        assert features.mobile_exact == 0.0
        assert features.name_similarity > 0.7


# ── Scoring Tests ────────────────────────────────────────────────

class TestScoring:
    def test_perfect_score(self):
        from app.schemas.matching import FeatureVector
        features = FeatureVector(
            pan_exact=1.0, mobile_exact=1.0, email_exact=1.0,
            name_similarity=1.0, name_semantic_similarity=1.0,
            dob_exact=1.0, city_similarity=1.0, segment_exact=1.0,
        )
        breakdown = compute_score(features)
        assert breakdown.final_score == 1.0

    def test_zero_score(self):
        from app.schemas.matching import FeatureVector
        features = FeatureVector(
            pan_exact=0.0, mobile_exact=0.0, email_exact=0.0,
            name_similarity=0.0, name_semantic_similarity=0.0,
            dob_exact=0.0, city_similarity=0.0, segment_exact=0.0,
        )
        breakdown = compute_score(features)
        assert breakdown.final_score == 0.0

    def test_pan_only_match(self):
        from app.schemas.matching import FeatureVector
        features = FeatureVector(pan_exact=1.0)
        breakdown = compute_score(features)
        assert breakdown.final_score == 0.35  # PAN weight = 0.35


# ── Deterministic Rules Tests ────────────────────────────────────

class TestDeterministicRules:
    def test_exact_pan_match(self):
        rec_a = _make_record(pan="ABCDE1234F", name="rohita raghavan")
        rec_b = _make_record(id=2, pan="ABCDE1234F", name="rohita raghavan")
        result = run_deterministic_rules(rec_a, rec_b)

        assert result is not None
        assert result.is_match is True
        assert "PAN" in result.reason

    def test_pan_conflict(self):
        rec_a = _make_record(pan="AAAAA1111A", name="rohita raghavan")
        rec_b = _make_record(id=2, pan="BBBBB2222B", name="rohita raghavan")
        result = run_deterministic_rules(rec_a, rec_b)

        assert result is not None
        assert result.is_review is True
        assert "conflict" in result.reason.lower()

    def test_mobile_and_name_match(self):
        rec_a = _make_record(mobile="9876543210", name="rohita raghavan")
        rec_b = _make_record(id=2, mobile="9876543210", name="rohita raghavan")
        result = run_deterministic_rules(rec_a, rec_b)

        assert result is not None
        assert result.is_match is True

    def test_no_deterministic_rule_fires(self):
        rec_a = _make_record(name="alpha person", mobile="9999999999")
        rec_b = _make_record(id=2, name="omega different", mobile="1111111111")
        result = run_deterministic_rules(rec_a, rec_b)

        assert result is None  # falls through to fuzzy


# ── Blocking Tests ───────────────────────────────────────────────

class TestBlocking:
    def test_same_pan_generates_pair(self):
        rec_a = _make_record(id=1, pan="ABCDE1234F")
        rec_b = _make_record(id=2, pan="ABCDE1234F")
        rec_c = _make_record(id=3, pan="ZZZZZ9999Z")

        # Mock the missing attributes
        for r in [rec_a, rec_b, rec_c]:
            if not hasattr(r, 'normalized_mobile') or r.normalized_mobile is None:
                r.normalized_mobile = None
            if not hasattr(r, 'normalized_email') or r.normalized_email is None:
                r.normalized_email = None
            if not hasattr(r, 'normalized_name') or r.normalized_name is None:
                r.normalized_name = None
            if not hasattr(r, 'normalized_dob') or r.normalized_dob is None:
                r.normalized_dob = None

        pairs = generate_candidate_pairs([rec_a, rec_b, rec_c])
        assert (1, 2) in pairs
        assert (1, 3) not in pairs

    def test_empty_records(self):
        pairs = generate_candidate_pairs([])
        assert len(pairs) == 0

    def test_single_record(self):
        rec = _make_record(id=1, pan="ABCDE1234F")
        rec.normalized_mobile = None
        rec.normalized_email = None
        rec.normalized_name = None
        rec.normalized_dob = None
        pairs = generate_candidate_pairs([rec])
        assert len(pairs) == 0

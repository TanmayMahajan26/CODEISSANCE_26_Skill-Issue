"""
Nexus360 — Review Queue + Explainability Verification Suite.

Tests:
A. Approve review — state transitions and golden customer behaviour
B. Reject review — state transitions
C. Manual merge security — whitelist enforcement
D. Explainability — deterministic explanation engine
E. Provenance — manual override tracking
F. GET /reviews/{id} — detail endpoint
G. Concurrency — concurrent reviewer safety
H. Idempotency — repeated calls after resolution
"""

import asyncio
import pytest
import sys
import os
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

# ── Ensure project root is importable ────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app.services.review_service  # noqa: F401


# ═══════════════════════════════════════════════════════════════════
#  SECTION D — Explainability (pure unit tests, no DB required)
# ═══════════════════════════════════════════════════════════════════

class TestExplainabilityEngine:
    """Tests for the deterministic explanation engine (explanation_service.py)."""

    def _make_features(self, **overrides):
        base = {
            "pan_exact": 1.0,
            "mobile_exact": 1.0,
            "email_exact": 0.0,
            "name_similarity": 0.92,
            "name_semantic_similarity": 0.94,
            "dob_exact": 0.0,
            "city_similarity": 1.0,
            "segment_exact": 1.0,
        }
        base.update(overrides)
        return base

    def _make_contributions(self, **overrides):
        base = {
            "pan": 0.35,
            "mobile": 0.20,
            "email": 0.0,
            "name_string": 0.1104,
            "name_semantic": 0.0752,
            "dob": 0.0,
            "city": 0.03,
            "segment": 0.02,
        }
        base.update(overrides)
        return base

    def test_generate_explanation_review_decision(self):
        """D1: Explanation correctly reflects REVIEW decision with matching and conflicting signals."""
        from app.services.explanation_service import generate_explanation

        features = self._make_features()
        contributions = self._make_contributions()
        reasoning = {
            "features": features,
            "score_breakdown": {"final_score": 0.7856, "contributions": contributions},
            "scoring_reasoning": {
                "threshold": "Score 0.7856 in [0.60, 0.85)",
            },
        }

        explanation = generate_explanation(
            features=features,
            contributions=contributions,
            final_score=0.7856,
            decision="REVIEW",
            reasoning=reasoning,
        )

        # Verify structure
        assert explanation.summary, "Summary should not be empty"
        assert explanation.decision_reason, "Decision reason should not be empty"
        assert explanation.recommendation in ("LIKELY_MATCH", "LIKELY_NON_MATCH", "UNCERTAIN")
        assert explanation.confidence_level in ("High", "Moderate", "Low")

        # Verify field comparisons
        assert len(explanation.field_comparisons) == 8, "Should have 8 field comparisons"

        # Verify strongest signals include PAN and Mobile (both 1.0)
        signal_text = " ".join(explanation.strongest_signals)
        assert "PAN" in signal_text, "PAN should be a top signal"
        assert "Mobile" in signal_text, "Mobile should be a top signal"

        # Verify conflicting signals include Email and DOB (both 0.0)
        conflict_text = " ".join(explanation.conflicting_signals)
        assert "Email" in conflict_text or "DOB" in conflict_text, \
            "Email or DOB should be a conflicting signal"

        # Verify score is mentioned in summary
        assert "0.79" in explanation.summary or "0.78" in explanation.summary, \
            "Score should appear in summary"

        # Verify no debug f-string garbage
        assert "features=" not in explanation.summary
        assert "model_dump" not in explanation.summary

    def test_generate_explanation_match_decision(self):
        """D2: Explanation correctly reflects MATCH decision."""
        from app.services.explanation_service import generate_explanation

        features = self._make_features(email_exact=1.0, dob_exact=1.0)
        contributions = self._make_contributions(email=0.15, dob=0.05)
        reasoning = {
            "deterministic": "Exact PAN match",
            "features": features,
            "score_breakdown": {"final_score": 1.0, "contributions": contributions},
        }

        explanation = generate_explanation(
            features=features,
            contributions=contributions,
            final_score=1.0,
            decision="MATCH",
            reasoning=reasoning,
        )

        assert explanation.recommendation == "LIKELY_MATCH"
        assert explanation.confidence_level == "High"
        assert "Auto-matched" in explanation.summary or "Deterministic" in explanation.decision_reason

    def test_generate_explanation_non_match_decision(self):
        """D3: Explanation correctly reflects NON_MATCH decision."""
        from app.services.explanation_service import generate_explanation

        features = self._make_features(
            pan_exact=0.0, mobile_exact=0.0, email_exact=0.0,
            name_similarity=0.3, name_semantic_similarity=0.2,
            dob_exact=0.0, city_similarity=0.0, segment_exact=0.0,
        )
        contributions = {k: 0.0 for k in self._make_contributions()}
        contributions["name_string"] = 0.036
        reasoning = {
            "features": features,
            "score_breakdown": {"final_score": 0.036, "contributions": contributions},
            "scoring_reasoning": {"threshold": "Score 0.0360 < review threshold 0.60"},
        }

        explanation = generate_explanation(
            features=features,
            contributions=contributions,
            final_score=0.036,
            decision="NON_MATCH",
            reasoning=reasoning,
        )

        assert explanation.recommendation == "LIKELY_NON_MATCH"
        assert explanation.confidence_level == "Low"
        assert "Non-match" in explanation.summary or "below" in explanation.summary.lower()

    def test_generate_explanation_pan_conflict(self):
        """D4: PAN conflict safety flag is extracted and surfaced."""
        from app.services.explanation_service import generate_explanation

        features = self._make_features(pan_exact=0.0)
        contributions = self._make_contributions(pan=0.0)
        reasoning = {
            "features": features,
            "score_breakdown": {"final_score": 0.50, "contributions": contributions},
            "scoring_reasoning": {
                "threshold": "Score 0.5000 in [0.60, 0.85)",
                "pan_conflict": "PAN conflict: ABCDE1234F vs XYZAB5678P — forcing REVIEW",
            },
        }

        explanation = generate_explanation(
            features=features,
            contributions=contributions,
            final_score=0.50,
            decision="REVIEW",
            reasoning=reasoning,
        )

        assert len(explanation.safety_flags) > 0, "Safety flags should contain PAN conflict"
        assert "PAN conflict" in explanation.safety_flags[0]

    def test_generate_ai_explanation_text(self):
        """D5: ai_explanation text is human-readable, not a debug f-string."""
        from app.services.explanation_service import generate_ai_explanation_text

        features = self._make_features()
        contributions = self._make_contributions()
        reasoning = {
            "features": features,
            "score_breakdown": {"final_score": 0.78, "contributions": contributions},
        }

        text = generate_ai_explanation_text(
            features=features,
            contributions=contributions,
            final_score=0.78,
            decision="REVIEW",
            reasoning=reasoning,
        )

        assert isinstance(text, str)
        assert len(text) > 20, "Explanation should be a meaningful sentence"
        assert "features=" not in text, "Should not contain debug output"
        assert "model_dump" not in text, "Should not contain debug output"
        assert "{" not in text or "}" not in text, "Should not contain raw dict"

    def test_generate_review_suggestion(self):
        """D6: Review suggestion is reviewer-friendly with recommendation."""
        from app.services.explanation_service import generate_review_suggestion

        features = self._make_features()
        contributions = self._make_contributions()
        reasoning = {
            "features": features,
            "score_breakdown": {"final_score": 0.78, "contributions": contributions},
        }

        suggestion = generate_review_suggestion(
            features=features,
            contributions=contributions,
            final_score=0.78,
            decision="REVIEW",
            reasoning=reasoning,
        )

        assert isinstance(suggestion, str)
        assert "Recommended action:" in suggestion, "Should contain recommended action"
        assert "0.78" in suggestion, "Should contain the score"

    def test_explanation_to_dict(self):
        """D7: MatchExplanation.to_dict() produces a clean serializable dict."""
        from app.services.explanation_service import generate_explanation

        features = self._make_features()
        contributions = self._make_contributions()
        reasoning = {"features": features, "score_breakdown": {"final_score": 0.78, "contributions": contributions}}

        explanation = generate_explanation(
            features=features,
            contributions=contributions,
            final_score=0.78,
            decision="REVIEW",
            reasoning=reasoning,
        )

        d = explanation.to_dict()
        assert isinstance(d, dict)
        assert "summary" in d
        assert "field_comparisons" in d
        assert isinstance(d["field_comparisons"], list)
        assert len(d["field_comparisons"]) == 8
        assert "recommendation" in d

    def test_field_comparison_statuses(self):
        """D8: Field comparison statuses correctly reflect match/different/partial."""
        from app.services.explanation_service import generate_explanation

        features = self._make_features(
            pan_exact=1.0,        # MATCH
            mobile_exact=0.0,     # DIFFERENT
            name_similarity=0.85, # PARTIAL
        )
        contributions = self._make_contributions()
        reasoning = {"features": features, "score_breakdown": {"final_score": 0.78, "contributions": contributions}}

        explanation = generate_explanation(
            features=features,
            contributions=contributions,
            final_score=0.78,
            decision="REVIEW",
            reasoning=reasoning,
        )

        fc_map = {fc.field_name: fc for fc in explanation.field_comparisons}

        assert fc_map["pan"].status == "MATCH"
        assert fc_map["mobile"].status == "DIFFERENT"
        assert fc_map["name_string"].status == "PARTIAL"


# ═══════════════════════════════════════════════════════════════════
#  SECTION C — Manual Merge Security (unit tests)
# ═══════════════════════════════════════════════════════════════════

class TestManualMergeSecurity:
    """Tests for manual merge attribute whitelist enforcement."""

    def test_allowed_attributes_defined(self):
        """C1: ALLOWED_MERGE_ATTRIBUTES whitelist exists and contains canonical fields."""
        from app.services.review_service import ALLOWED_MERGE_ATTRIBUTES

        assert "canonical_name" in ALLOWED_MERGE_ATTRIBUTES
        assert "canonical_pan" in ALLOWED_MERGE_ATTRIBUTES
        assert "canonical_mobile" in ALLOWED_MERGE_ATTRIBUTES
        assert "canonical_email" in ALLOWED_MERGE_ATTRIBUTES
        assert "canonical_dob" in ALLOWED_MERGE_ATTRIBUTES
        assert "canonical_city" in ALLOWED_MERGE_ATTRIBUTES
        assert "canonical_segment" in ALLOWED_MERGE_ATTRIBUTES

    def test_disallowed_attributes_not_in_whitelist(self):
        """C2: Internal/dangerous fields are NOT in the whitelist."""
        from app.services.review_service import ALLOWED_MERGE_ATTRIBUTES

        # These should never be in the whitelist
        assert "id" not in ALLOWED_MERGE_ATTRIBUTES
        assert "status" not in ALLOWED_MERGE_ATTRIBUTES
        assert "version" not in ALLOWED_MERGE_ATTRIBUTES
        assert "golden_customer_id" not in ALLOWED_MERGE_ATTRIBUTES
        assert "created_at" not in ALLOWED_MERGE_ATTRIBUTES
        assert "updated_at" not in ALLOWED_MERGE_ATTRIBUTES
        assert "attribute_provenance" not in ALLOWED_MERGE_ATTRIBUTES
        assert "source_record_ids" not in ALLOWED_MERGE_ATTRIBUTES
        assert "total_relationship_value" not in ALLOWED_MERGE_ATTRIBUTES
        assert "merged_into_id" not in ALLOWED_MERGE_ATTRIBUTES

    def test_whitelist_size(self):
        """C3: Whitelist contains exactly 7 canonical attributes."""
        from app.services.review_service import ALLOWED_MERGE_ATTRIBUTES
        assert len(ALLOWED_MERGE_ATTRIBUTES) == 7


# ═══════════════════════════════════════════════════════════════════
#  SECTION: ReviewConflictError exists
# ═══════════════════════════════════════════════════════════════════

class TestReviewConflictError:
    """Tests for the ReviewConflictError exception class."""

    def test_error_class_exists(self):
        """ReviewConflictError should be importable."""
        from app.services.review_service import ReviewConflictError
        assert issubclass(ReviewConflictError, Exception)

    def test_error_message(self):
        """ReviewConflictError should carry a message."""
        from app.services.review_service import ReviewConflictError
        err = ReviewConflictError("Already processed")
        assert str(err) == "Already processed"


# ═══════════════════════════════════════════════════════════════════
#  SECTION: Schema validation
# ═══════════════════════════════════════════════════════════════════

class TestReviewSchemas:
    """Tests for review request/response Pydantic schemas."""

    def test_review_case_detail_response_fields(self):
        """Schema should include enriched fields for the review UI."""
        from app.schemas.review import ReviewCaseDetailResponse
        fields = set(ReviewCaseDetailResponse.model_fields.keys())

        # Core review fields
        assert "id" in fields
        assert "match_decision_id" in fields
        assert "priority" in fields
        assert "status" in fields
        assert "review_type" in fields
        assert "ai_suggestion" in fields

        # Enriched fields
        assert "record_a" in fields
        assert "record_b" in fields
        assert "match_decision" in fields
        assert "field_comparisons" in fields
        assert "explanation" in fields
        assert "golden_customer_a" in fields
        assert "golden_customer_b" in fields

    def test_source_record_summary_fields(self):
        """SourceRecordSummary should expose identity fields without internal ORM fields."""
        from app.schemas.review import SourceRecordSummary
        fields = set(SourceRecordSummary.model_fields.keys())

        assert "original_name" in fields
        assert "normalized_name" in fields
        assert "original_pan" in fields
        assert "normalized_pan" in fields
        assert "original_mobile" in fields
        assert "normalized_mobile" in fields
        assert "segment" in fields

        # Should NOT contain raw_data, name_embedding, etc.
        assert "raw_data" not in fields
        assert "name_embedding" not in fields

    def test_manual_merge_request(self):
        """ManualMergeRequest should accept reviewer and selected_attributes."""
        from app.schemas.review import ManualMergeRequest

        req = ManualMergeRequest(
            reviewer="admin",
            selected_attributes={"canonical_name": "Test Name"},
        )
        assert req.reviewer == "admin"
        assert req.selected_attributes == {"canonical_name": "Test Name"}

    def test_field_comparison_item(self):
        """FieldComparisonItem should hold per-field comparison data."""
        from app.schemas.review import FieldComparisonItem

        item = FieldComparisonItem(
            field_name="pan",
            label="PAN",
            score=1.0,
            status="MATCH",
            weighted_contribution=0.35,
            weight=0.35,
        )
        assert item.status == "MATCH"
        assert item.weighted_contribution == 0.35


# ═══════════════════════════════════════════════════════════════════
#  SECTION: AuditAction enum
# ═══════════════════════════════════════════════════════════════════

class TestAuditAction:
    """Tests for audit action enum values."""

    def test_review_created_action_exists(self):
        """REVIEW_CREATED audit action should be in the enum."""
        from app.models.audit_log import AuditAction
        assert hasattr(AuditAction, "REVIEW_CREATED")
        assert AuditAction.REVIEW_CREATED.value == "REVIEW_CREATED"

    def test_all_review_actions_exist(self):
        """All review-related audit actions should be in the enum."""
        from app.models.audit_log import AuditAction
        assert hasattr(AuditAction, "MERGE_APPROVE")
        assert hasattr(AuditAction, "MERGE_REJECT")
        assert hasattr(AuditAction, "MANUAL_MERGE")
        assert hasattr(AuditAction, "UNMERGE")


# ═══════════════════════════════════════════════════════════════════
#  SECTION: Explanation provider protocol
# ═══════════════════════════════════════════════════════════════════

class TestExplanationProvider:
    """Tests for the ExplanationProvider abstraction layer."""

    def test_default_provider_exists(self):
        """DeterministicExplanationProvider should be the default."""
        from app.services.explanation_service import (
            get_explanation_provider,
            DeterministicExplanationProvider,
        )
        provider = get_explanation_provider()
        assert isinstance(provider, DeterministicExplanationProvider)

    def test_provider_swap(self):
        """set_explanation_provider should replace the active provider."""
        from app.services.explanation_service import (
            get_explanation_provider,
            set_explanation_provider,
            DeterministicExplanationProvider,
        )

        original = get_explanation_provider()

        class MockProvider:
            def generate(self, features, contributions, final_score, decision, reasoning):
                pass

        mock = MockProvider()
        set_explanation_provider(mock)
        assert get_explanation_provider() is mock

        # Restore
        set_explanation_provider(original)
        assert isinstance(get_explanation_provider(), DeterministicExplanationProvider)


# ═══════════════════════════════════════════════════════════════════
#  SECTION A, B, C, E, G, H — Async Service Logic Tests (Mocked DB)
# ═══════════════════════════════════════════════════════════════════

class TestReviewServiceAsyncLogic:
    """Async unit tests for review_service functions with mocked DB objects."""

    @pytest.mark.asyncio
    async def test_approve_updates_match_decision_to_match(self):
        """A1: Approving review updates MatchDecision.decision from REVIEW to MATCH."""
        from app.services.review_service import approve_review
        from app.models.review_case import ReviewCase, ReviewStatus
        from app.models.match_decision import MatchDecision, Decision
        from app.models.source_record import SourceRecord, SourceSystem
        from app.models.golden_customer import GoldenCustomer

        mock_db = AsyncMock()

        # Mock review
        mock_review = ReviewCase(
            id=1,
            match_decision_id=10,
            status=ReviewStatus.PENDING,
        )
        # Mock match decision
        mock_decision = MatchDecision(
            id=10,
            record_a_id=101,
            record_b_id=102,
            final_score=0.78,
            decision=Decision.REVIEW,
        )
        # Mock source records
        mock_rec_a = SourceRecord(id=101, source_system=SourceSystem.EQUITY, original_name="Rajesh")
        mock_rec_b = SourceRecord(id=102, source_system=SourceSystem.MUTUAL_FUND, original_name="Rajesh")
        # Mock golden customer
        mock_golden = GoldenCustomer(
            id=1,
            golden_customer_id="GOLD-000001",
            canonical_name="Rajesh",
            attribute_provenance={},
        )

        # Configure db.execute for _get_and_lock_pending_review
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db.execute.return_value = mock_result

        # Configure db.get
        async def mock_get(model, pk):
            if model == MatchDecision and pk == 10:
                return mock_decision
            elif model == SourceRecord and pk == 101:
                return mock_rec_a
            elif model == SourceRecord and pk == 102:
                return mock_rec_b
            return None

        mock_db.get.side_effect = mock_get

        with patch("app.services.review_service.find_golden_by_source_record", new_callable=AsyncMock) as mock_find_golden, \
             patch("app.services.review_service.create_golden_customer", new_callable=AsyncMock) as mock_create_golden, \
             patch("app.services.review_service.link_to_golden", new_callable=AsyncMock) as mock_link_golden, \
             patch("app.services.review_service.log_action", new_callable=AsyncMock) as mock_log:

            mock_find_golden.return_value = None
            mock_create_golden.return_value = mock_golden
            mock_link_mock = MagicMock()
            mock_link_golden.return_value = mock_link_mock

            result = await approve_review(mock_db, review_id=1, reviewer="admin_jane", notes="Looks good")

            # Check review status
            assert result.status == ReviewStatus.APPROVED
            assert result.reviewer == "admin_jane"
            assert result.review_notes == "Looks good"
            assert result.resolved_at is not None

            # Check MatchDecision updated to MATCH
            assert mock_decision.decision == Decision.MATCH

            # Check audit logged
            assert mock_log.called

    @pytest.mark.asyncio
    async def test_reject_updates_match_decision_to_non_match(self):
        """B1: Rejecting review updates MatchDecision.decision from REVIEW to NON_MATCH."""
        from app.services.review_service import reject_review
        from app.models.review_case import ReviewCase, ReviewStatus
        from app.models.match_decision import MatchDecision, Decision
        from app.models.source_record import SourceRecord, SourceSystem

        mock_db = AsyncMock()

        mock_review = ReviewCase(
            id=2,
            match_decision_id=20,
            status=ReviewStatus.PENDING,
        )
        mock_decision = MatchDecision(
            id=20,
            record_a_id=201,
            record_b_id=202,
            final_score=0.65,
            decision=Decision.REVIEW,
        )
        mock_rec_a = SourceRecord(id=201, source_system=SourceSystem.EQUITY, original_name="Anita")
        mock_rec_b = SourceRecord(id=202, source_system=SourceSystem.INSURANCE, original_name="Sunita")

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db.execute.return_value = mock_result

        async def mock_get(model, pk):
            if model == MatchDecision and pk == 20:
                return mock_decision
            elif model == SourceRecord and pk == 201:
                return mock_rec_a
            elif model == SourceRecord and pk == 202:
                return mock_rec_b
            return None

        mock_db.get.side_effect = mock_get

        with patch("app.services.review_service.find_golden_by_source_record", new_callable=AsyncMock) as mock_find_golden, \
             patch("app.services.review_service.create_golden_customer", new_callable=AsyncMock) as mock_create_golden, \
             patch("app.services.review_service.log_action", new_callable=AsyncMock) as mock_log:

            mock_find_golden.return_value = None
            mock_create_golden.return_value = MagicMock()

            result = await reject_review(mock_db, review_id=2, reviewer="admin_jane", notes="Different people")

            assert result.status == ReviewStatus.REJECTED
            assert mock_decision.decision == Decision.NON_MATCH
            assert mock_log.called

    @pytest.mark.asyncio
    async def test_manual_merge_rejects_invalid_attributes(self):
        """C4: Manual merge raises ValueError when invalid attributes are submitted."""
        from app.services.review_service import manual_merge_review

        mock_db = AsyncMock()

        with pytest.raises(ValueError, match="Invalid attribute"):
            await manual_merge_review(
                db=mock_db,
                review_id=1,
                reviewer="admin",
                selected_attributes={
                    "status": "HACKED",
                    "id": 9999,
                    "canonical_name": "Valid Name",
                },
            )

    @pytest.mark.asyncio
    async def test_manual_merge_updates_provenance_and_history(self):
        """E1: Manual merge updates attribute_provenance and adds AttributeHistory entries."""
        from app.services.review_service import manual_merge_review
        from app.models.review_case import ReviewCase, ReviewStatus
        from app.models.match_decision import MatchDecision, Decision
        from app.models.source_record import SourceRecord, SourceSystem
        from app.models.golden_customer import GoldenCustomer
        from app.models.attribute_history import AttributeHistory

        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        mock_review = ReviewCase(
            id=3,
            match_decision_id=30,
            status=ReviewStatus.PENDING,
        )
        mock_decision = MatchDecision(
            id=30,
            record_a_id=301,
            record_b_id=302,
            final_score=0.75,
            decision=Decision.REVIEW,
        )
        mock_rec_a = SourceRecord(id=301, source_system=SourceSystem.EQUITY, original_name="Vikram")
        mock_rec_b = SourceRecord(id=302, source_system=SourceSystem.WEALTH, original_name="Vikram Seth")
        mock_golden = GoldenCustomer(
            id=1,
            golden_customer_id="GOLD-000003",
            canonical_name="Vikram",
            canonical_city="Delhi",
            attribute_provenance={"canonical_name": {"source": "EQUITY"}},
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db.execute.return_value = mock_result

        async def mock_get(model, pk):
            if model == MatchDecision and pk == 30:
                return mock_decision
            elif model == SourceRecord and pk == 301:
                return mock_rec_a
            elif model == SourceRecord and pk == 302:
                return mock_rec_b
            return None

        mock_db.get.side_effect = mock_get

        added_history = []
        def mock_add(obj):
            if isinstance(obj, AttributeHistory):
                added_history.append(obj)
        mock_db.add.side_effect = mock_add

        with patch("app.services.review_service.find_golden_by_source_record", new_callable=AsyncMock) as mock_find_golden, \
             patch("app.services.review_service.link_to_golden", new_callable=AsyncMock) as mock_link_golden, \
             patch("app.services.review_service.recalculate_golden_customer", new_callable=AsyncMock) as mock_recalc, \
             patch("app.services.review_service.log_action", new_callable=AsyncMock) as mock_log:

            mock_find_golden.return_value = mock_golden
            mock_link_golden.return_value = MagicMock()

            result = await manual_merge_review(
                db=mock_db,
                review_id=3,
                reviewer="senior_admin",
                selected_attributes={"canonical_name": "Vikram Seth", "canonical_city": "Mumbai"},
                notes="Verified via KYC documents",
            )

            assert result.status == ReviewStatus.APPROVED
            # Verify golden customer attribute updated
            assert mock_golden.canonical_name == "Vikram Seth"
            assert mock_golden.canonical_city == "Mumbai"

            # Verify attribute_provenance updated
            prov = mock_golden.attribute_provenance
            assert "canonical_name" in prov
            assert prov["canonical_name"]["source"] == "MANUAL_MERGE"
            assert prov["canonical_name"]["reviewer"] == "senior_admin"
            assert prov["canonical_city"]["source"] == "MANUAL_MERGE"

            # Verify AttributeHistory created
            assert len(added_history) == 2
            hist_attrs = {h.attribute_name for h in added_history}
            assert hist_attrs == {"canonical_name", "canonical_city"}

    @pytest.mark.asyncio
    async def test_concurrency_conflict_when_already_processed(self):
        """G1: Attempting to approve/reject an already resolved review raises ReviewConflictError."""
        from app.services.review_service import approve_review, ReviewConflictError
        from app.models.review_case import ReviewCase, ReviewStatus

        mock_db = AsyncMock()

        # Review that is ALREADY APPROVED
        mock_review = ReviewCase(
            id=5,
            match_decision_id=50,
            status=ReviewStatus.APPROVED,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db.execute.return_value = mock_result

        with pytest.raises(ReviewConflictError, match="already APPROVED"):
            await approve_review(mock_db, review_id=5, reviewer="late_reviewer")

    @pytest.mark.asyncio
    async def test_idempotency_reject_after_resolved_raises_conflict(self):
        """H1: Reject called after resolution raises ReviewConflictError rather than corrupting state."""
        from app.services.review_service import reject_review, ReviewConflictError
        from app.models.review_case import ReviewCase, ReviewStatus

        mock_db = AsyncMock()

        mock_review = ReviewCase(
            id=6,
            match_decision_id=60,
            status=ReviewStatus.REJECTED,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_review
        mock_db.execute.return_value = mock_result

        with pytest.raises(ReviewConflictError, match="already REJECTED"):
            await reject_review(mock_db, review_id=6, reviewer="another_reviewer")


# ═══════════════════════════════════════════════════════════════════
#  Run all tests
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


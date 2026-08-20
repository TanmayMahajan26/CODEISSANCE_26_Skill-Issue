"""Baseline initial schema for Nexus360.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-20 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Users Table ──────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column(
            "role",
            sa.Enum("ADMIN", "REVIEWER", "RELATIONSHIP_MANAGER", "ANALYST", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── 2. Source Records Table ──────────────────────────────────────
    op.create_table(
        "source_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "source_system",
            sa.Enum("EQUITY", "MUTUAL_FUND", "INSURANCE", "LOAN", "WEALTH", name="sourcesystem"),
            nullable=False,
        ),
        sa.Column("source_record_id", sa.String(length=100), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("original_dob", sa.Date(), nullable=True),
        sa.Column("original_mobile", sa.String(length=20), nullable=True),
        sa.Column("original_email", sa.String(length=255), nullable=True),
        sa.Column("original_pan", sa.String(length=20), nullable=True),
        sa.Column("original_city", sa.String(length=100), nullable=True),
        sa.Column("normalized_name", sa.String(length=255), nullable=True),
        sa.Column("normalized_dob", sa.Date(), nullable=True),
        sa.Column("normalized_mobile", sa.String(length=15), nullable=True),
        sa.Column("normalized_email", sa.String(length=255), nullable=True),
        sa.Column("normalized_pan", sa.String(length=10), nullable=True),
        sa.Column("normalized_city", sa.String(length=100), nullable=True),
        sa.Column("segment", sa.String(length=50), nullable=True),
        sa.Column("product_type", sa.String(length=100), nullable=True),
        sa.Column("balance_aum", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("relationship_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
        sa.Column("rm_id", sa.String(length=100), nullable=True),
        sa.Column("name_embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_source_records_id", "source_records", ["id"])
    op.create_index("ix_source_records_source_system", "source_records", ["source_system"])
    op.create_index("ix_source_records_source_record_id", "source_records", ["source_record_id"])
    op.create_index("ix_source_records_normalized_name", "source_records", ["normalized_name"])
    op.create_index("ix_source_records_normalized_pan", "source_records", ["normalized_pan"])
    op.create_index("ix_source_records_normalized_mobile", "source_records", ["normalized_mobile"])
    op.create_index("ix_source_records_normalized_email", "source_records", ["normalized_email"])
    op.create_index("ix_source_records_normalized_dob", "source_records", ["normalized_dob"])

    # ── 3. Golden Customers Table ───────────────────────────────────
    op.create_table(
        "golden_customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("golden_customer_id", sa.String(length=20), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=True),
        sa.Column("canonical_dob", sa.Date(), nullable=True),
        sa.Column("canonical_mobile", sa.String(length=15), nullable=True),
        sa.Column("canonical_email", sa.String(length=255), nullable=True),
        sa.Column("canonical_pan", sa.String(length=10), nullable=True),
        sa.Column("canonical_city", sa.String(length=100), nullable=True),
        sa.Column("canonical_segment", sa.String(length=50), nullable=True),
        sa.Column("total_relationship_value", sa.Numeric(precision=15, scale=2), server_default="0.0"),
        sa.Column("products_held", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_record_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attribute_provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("match_confidence", sa.Float(), server_default="1.0"),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "UNDER_REVIEW", "MERGED_INTO", name="goldencustomerstatus"),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column("merged_into_id", sa.String(length=20), nullable=True),
        sa.Column("assigned_rm_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("golden_customer_id"),
    )
    op.create_index("ix_golden_customers_id", "golden_customers", ["id"])
    op.create_index("ix_golden_customers_golden_customer_id", "golden_customers", ["golden_customer_id"], unique=True)
    op.create_index("ix_golden_customers_status", "golden_customers", ["status"])

    # ── 4. Identity Links Table ──────────────────────────────────────
    op.create_table(
        "identity_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_record_id", sa.Integer(), nullable=False),
        sa.Column("golden_customer_id", sa.String(length=20), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=True),
        sa.Column(
            "match_method",
            sa.Enum("DETERMINISTIC", "FUZZY", "SEMANTIC", "ML", "MANUAL", name="matchmethod"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum("MATCH", "REVIEW", "NON_MATCH", name="linkstatus"),
            nullable=False,
        ),
        sa.Column("ai_explanation", sa.String(), nullable=True),
        sa.Column("linked_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["golden_customer_id"], ["golden_customers.golden_customer_id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_identity_links_id", "identity_links", ["id"])
    op.create_index("ix_identity_links_source_record_id", "identity_links", ["source_record_id"])
    op.create_index("ix_identity_links_golden_customer_id", "identity_links", ["golden_customer_id"])

    # ── 5. Match Decisions Table ────────────────────────────────────
    op.create_table(
        "match_decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_a_id", sa.Integer(), nullable=False),
        sa.Column("record_b_id", sa.Integer(), nullable=False),
        sa.Column("pan_match", sa.Float(), server_default="0.0"),
        sa.Column("mobile_match", sa.Float(), server_default="0.0"),
        sa.Column("email_match", sa.Float(), server_default="0.0"),
        sa.Column("name_similarity", sa.Float(), server_default="0.0"),
        sa.Column("name_semantic_similarity", sa.Float(), server_default="0.0"),
        sa.Column("dob_match", sa.Float(), server_default="0.0"),
        sa.Column("city_similarity", sa.Float(), server_default="0.0"),
        sa.Column("segment_match", sa.Float(), server_default="0.0"),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("decision", sa.Enum("MATCH", "REVIEW", "NON_MATCH", name="decision"), nullable=False),
        sa.Column("reasoning", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_explanation", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["record_a_id"], ["source_records.id"]),
        sa.ForeignKeyConstraint(["record_b_id"], ["source_records.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_a_id", "record_b_id", name="uq_match_decisions_canonical_pair"),
    )
    op.create_index("ix_match_decisions_id", "match_decisions", ["id"])
    op.create_index("ix_match_decisions_record_a_id", "match_decisions", ["record_a_id"])
    op.create_index("ix_match_decisions_record_b_id", "match_decisions", ["record_b_id"])
    op.create_index("ix_match_decisions_pair", "match_decisions", ["record_a_id", "record_b_id"], unique=True)

    # ── 6. Review Cases Table ───────────────────────────────────────
    op.create_table(
        "review_cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_decision_id", sa.Integer(), nullable=False),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="reviewpriority"),
            server_default="MEDIUM",
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", name="reviewstatus"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "review_type",
            sa.Enum("LOW_CONFIDENCE_MATCH", "ATTRIBUTE_CONFLICT", "DUPLICATE_SUSPECT", "AI_FLAGGED", name="reviewtype"),
            server_default="LOW_CONFIDENCE_MATCH",
            nullable=False,
        ),
        sa.Column("reviewer", sa.String(length=100), nullable=True),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("ai_suggestion", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_record_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["match_decision_id"], ["match_decisions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_decision_id"),
    )
    op.create_index("ix_review_cases_id", "review_cases", ["id"])
    op.create_index("ix_review_cases_status", "review_cases", ["status"])

    # ── 7. Attribute History Table ──────────────────────────────────
    op.create_table(
        "attribute_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("golden_customer_id", sa.String(length=20), nullable=False),
        sa.Column("attribute_name", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("selected_source", sa.String(length=20), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["golden_customer_id"], ["golden_customers.golden_customer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attribute_history_id", "attribute_history", ["id"])
    op.create_index("ix_attribute_history_golden_customer_id", "attribute_history", ["golden_customer_id"])

    # ── 8. Config Rules Table ───────────────────────────────────────
    op.create_table(
        "config_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "MATCHING_WEIGHTS", "THRESHOLDS", "OPPORTUNITY_RULES",
                "NORMALIZATION", "SOURCE_PRECEDENCE", "SCORING_WEIGHTS",
                name="rulecategory",
            ),
            nullable=False,
        ),
        sa.Column("rule_key", sa.String(length=100), nullable=False),
        sa.Column("rule_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_key"),
    )
    op.create_index("ix_config_rules_id", "config_rules", ["id"])
    op.create_index("ix_config_rules_category", "config_rules", ["category"])
    op.create_index("ix_config_rules_rule_key", "config_rules", ["rule_key"], unique=True)

    # ── 9. Audit Logs Table ─────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("actor_username", sa.String(length=100), nullable=True),
        sa.Column("actor_role", sa.String(length=50), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "LOGIN", "CONFIG_CHANGE", "MERGE_APPROVE", "MERGE_REJECT",
                "MANUAL_MERGE", "UNMERGE", "OPPORTUNITY_UPDATE", "DATA_INGEST",
                "MATCHING_RUN", "REVIEW_CREATED", name="auditaction",
            ),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # ── 10. Opportunities Table ─────────────────────────────────────
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("golden_customer_id", sa.String(length=20), nullable=False),
        sa.Column(
            "opportunity_type",
            sa.Enum("CROSS_SELL", "UPSELL", "RETENTION", "PROTECTION", name="opportunitytype"),
            nullable=False,
        ),
        sa.Column("product_recommended", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_reasoning", sa.String(), nullable=True),
        sa.Column("potential_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("eligibility_met", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            sa.Enum("NEW", "VIEWED", "ASSIGNED", "IN_PROGRESS", "CONVERTED", "DISMISSED", name="opportunitystatus"),
            server_default="NEW",
            nullable=False,
        ),
        sa.Column("assigned_rm_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["golden_customer_id"], ["golden_customers.golden_customer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_id", "opportunities", ["id"])
    op.create_index("ix_opportunities_golden_customer_id", "opportunities", ["golden_customer_id"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])


def downgrade() -> None:
    op.drop_table("opportunities")
    op.drop_table("audit_logs")
    op.drop_table("config_rules")
    op.drop_table("attribute_history")
    op.drop_table("review_cases")
    op.drop_table("match_decisions")
    op.drop_table("identity_links")
    op.drop_table("golden_customers")
    op.drop_table("source_records")
    op.drop_table("users")

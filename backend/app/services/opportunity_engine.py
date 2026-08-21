import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.models.golden_record import GoldenRecord
from app.db.models.opportunity import Opportunity
from app.db.models.config_rule import ConfigRule

logger = logging.getLogger(__name__)

PRODUCT_UNIVERSE = ["Equity", "Mutual Fund", "Insurance", "Loan", "Wealth Management", "Credit Card"]


def get_opportunity_rules(db: Session) -> dict:
    """Fetch eligibility rules from ConfigRule table, fallback to defaults."""
    rule_record = db.query(ConfigRule).filter_by(rule_type="opportunity_rules").first()
    if rule_record and rule_record.config:
        return rule_record.config

    # Default fallback rules
    return {
        "Insurance": {
            "type": "CROSS_SELL",
            "min_relationship_value": 100000,
            "required_products_any": ["Equity", "Mutual Fund"],
        },
        "Wealth Management": {
            "type": "UPSELL",
            "min_relationship_value": 2500000,
            "required_products_all": ["Equity", "Mutual Fund"],
        },
        "Loan": {
            "type": "CROSS_SELL",
            "min_relationship_value": 200000,
        },
        "Credit Card": {
            "type": "CROSS_SELL",
            "min_relationship_value": 50000,
        }
    }


def get_scoring_weights(db: Session) -> dict:
    """Fetch scoring weights from ConfigRule table, fallback to defaults."""
    rule_record = db.query(ConfigRule).filter_by(rule_type="scoring_weights").first()
    if rule_record and rule_record.config:
        return rule_record.config
    return {
        "relationship_value": 0.35,
        "product_affinity": 0.25,
        "recency": 0.20,
        "engagement": 0.20
    }


def generate_opportunities(db: Session) -> int:
    """
    Generate next-best-product opportunities for all Golden Records.
    Returns the number of new opportunities generated.
    """
    logger.info("Starting opportunity generation...")

    # Cleanup old NEW opportunities (idempotent re-runs)
    db.query(Opportunity).filter(Opportunity.status == "NEW").delete()
    db.commit()

    rules = get_opportunity_rules(db)
    weights = get_scoring_weights(db)

    golden_records = db.query(GoldenRecord).all()
    opportunities_created = 0

    for gr in golden_records:
        # Extract held products from the JSONB products_held column
        held_products = set()
        if gr.products_held:
            for p in gr.products_held:
                if isinstance(p, dict):
                    held_products.add(p.get("product", p.get("product_type", p.get("type", ""))))
                elif isinstance(p, str):
                    held_products.add(p)

        # Gap Analysis: find products not yet held
        missing_products = [p for p in PRODUCT_UNIVERSE if p not in held_products]

        for product in missing_products:
            rule = rules.get(product)
            if not rule:
                continue

            # Eligibility Check
            trv = float(gr.total_relationship_value or 0)
            if trv < rule.get("min_relationship_value", 0):
                continue

            if "required_products_any" in rule:
                if not held_products.intersection(set(rule["required_products_any"])):
                    continue

            if "required_products_all" in rule:
                if not set(rule["required_products_all"]).issubset(held_products):
                    continue

            # Composite Scoring
            trv_norm = min(trv / 10000000.0, 1.0)
            rel_val_score = weights.get("relationship_value", 0.35) * trv_norm

            affinity_norm = min(len(held_products) / 5.0, 1.0)
            affinity_score = weights.get("product_affinity", 0.25) * affinity_norm

            source_count = gr.source_record_count or 1
            engagement_norm = min(source_count / 3.0, 1.0)
            engagement_score = weights.get("engagement", 0.20) * engagement_norm

            recency_score = weights.get("recency", 0.20) * 0.8  # Static for MVP

            total_score = rel_val_score + affinity_score + recency_score + engagement_score

            if total_score >= 0.40:
                score_breakdown = {
                    "relationship_value": {"weight": weights.get("relationship_value"), "value": round(trv_norm, 3), "contribution": round(rel_val_score, 3)},
                    "product_affinity": {"weight": weights.get("product_affinity"), "value": round(affinity_norm, 3), "contribution": round(affinity_score, 3)},
                    "engagement": {"weight": weights.get("engagement"), "value": round(engagement_norm, 3), "contribution": round(engagement_score, 3)},
                    "recency": {"weight": weights.get("recency"), "value": 0.8, "contribution": round(recency_score, 3)},
                }

                # Use ACTUAL Opportunity model columns
                opp = Opportunity(
                    golden_record_id=gr.id,
                    product_name=product,
                    product_category=rule.get("type", "CROSS_SELL"),
                    score=round(total_score, 2),
                    score_breakdown=score_breakdown,
                    explanation=None,  # Will be filled by RAG on demand
                    insights={
                        "potential_value": round(trv * 0.1, 2),
                        "eligibility_met": True,
                        "held_products": list(held_products),
                        "trv": trv,
                    },
                    status="NEW",
                )
                db.add(opp)
                opportunities_created += 1

    db.commit()
    logger.info(f"Opportunity generation complete. Created {opportunities_created} new opportunities.")
    return opportunities_created

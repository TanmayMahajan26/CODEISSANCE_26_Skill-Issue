"""
Nexus360 — Config & Business Rules Engine (BRE) Service.

Manages dynamic system configurations, matching weights, thresholds,
source precedence, normalization rules, and what-if impact previews.
Aligned with PRD v3.0 §5.6 / §7.6 / §10.1.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config_rule import ConfigRule, RuleCategory
from app.models.match_decision import MatchDecision

logger = logging.getLogger(__name__)

# Default rules from PRD §10.1
DEFAULT_CONFIG_RULES = [
    {
        "category": RuleCategory.MATCHING_WEIGHTS,
        "rule_key": "matching_weights",
        "rule_value": {
            "pan": 0.35,
            "mobile": 0.20,
            "email": 0.15,
            "name_string": 0.12,
            "name_semantic": 0.08,
            "dob": 0.05,
            "city": 0.03,
            "segment": 0.02,
        },
        "description": "Attribute weights for composite confidence scoring",
    },
    {
        "category": RuleCategory.THRESHOLDS,
        "rule_key": "thresholds",
        "rule_value": {
            "auto_merge": 0.85,
            "manual_review": 0.60,
            "semantic_similarity_min": 0.90,
        },
        "description": "Decision thresholds for auto-merge and manual review",
    },
    {
        "category": RuleCategory.SOURCE_PRECEDENCE,
        "rule_key": "source_precedence",
        "rule_value": {
            "name": ["WEALTH", "INSURANCE", "EQUITY", "MUTUAL_FUND", "LOAN"],
            "mobile": "MOST_RECENT",
            "email": "MOST_RECENT",
            "dob": "MOST_FREQUENT",
            "city": ["INSURANCE", "LOAN", "WEALTH", "EQUITY", "MUTUAL_FUND"],
            "segment": "HIGHEST_VALUE_SOURCE",
        },
        "description": "Source system precedence order for survivorship",
    },
    {
        "category": RuleCategory.NORMALIZATION,
        "rule_key": "normalization_rules",
        "rule_value": {
            "city_aliases": {
                "Bombay": "Mumbai",
                "Bangalore": "Bengaluru",
                "Calcutta": "Kolkata",
                "Madras": "Chennai",
                "Poona": "Pune",
            },
            "mobile_strip_prefixes": ["+91", "0091", "0"],
            "pan_regex": "^[A-Z]{5}[0-9]{4}[A-Z]$",
            "name_remove_titles": ["Mr", "Mrs", "Ms", "Dr", "Shri", "Smt"],
        },
        "description": "Data cleaning and standardization rules",
    },
]


async def seed_default_config_rules(db: AsyncSession) -> None:
    """Seed default BRE configuration rules if empty."""
    res = await db.execute(select(ConfigRule))
    existing = res.scalars().all()

    if not existing:
        for item in DEFAULT_CONFIG_RULES:
            rule = ConfigRule(
                category=item["category"],
                rule_key=item["rule_key"],
                rule_value=item["rule_value"],
                description=item["description"],
                is_active=True,
                version=1,
            )
            db.add(rule)
        await db.flush()
        logger.info("Seeded default BRE config rules")


async def get_all_rules(db: AsyncSession) -> List[ConfigRule]:
    """Get all active config rules."""
    await seed_default_config_rules(db)
    res = await db.execute(select(ConfigRule).where(ConfigRule.is_active == True))
    return res.scalars().all()


async def get_rule_by_key(db: AsyncSession, rule_key: str) -> Optional[ConfigRule]:
    """Fetch a single rule by rule_key."""
    await seed_default_config_rules(db)
    res = await db.execute(select(ConfigRule).where(ConfigRule.rule_key == rule_key))
    return res.scalars().first()


async def update_rule(
    db: AsyncSession,
    rule_key: str,
    new_value: Dict[str, Any],
    updated_by: str = "Admin",
) -> ConfigRule:
    """Update a config rule and increment its version."""
    rule = await get_rule_by_key(db, rule_key)
    if not rule:
        raise ValueError(f"Rule with key '{rule_key}' not found")

    rule.rule_value = new_value
    rule.version = (rule.version or 1) + 1
    rule.updated_by = updated_by
    await db.flush()
    logger.info("Updated rule '%s' to v%d by %s", rule_key, rule.version, updated_by)
    return rule


async def preview_impact(
    db: AsyncSession,
    rule_key: str,
    new_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    What-If Simulator per PRD §5.6.
    Previews impact of changing a rule (e.g. changing auto_merge threshold from 0.85 to 0.70).
    """
    res = await db.execute(select(MatchDecision))
    decisions = res.scalars().all()

    if rule_key == "thresholds" or "auto_merge" in new_value:
        new_auto = new_value.get("auto_merge", 0.85)
        new_review = new_value.get("manual_review", 0.60)

        current_auto_merges = sum(1 for d in decisions if d.decision.value == "MATCH")
        current_reviews = sum(1 for d in decisions if d.decision.value == "REVIEW")

        projected_auto_merges = sum(1 for d in decisions if d.final_score >= new_auto)
        projected_reviews = sum(
            1 for d in decisions if new_review <= d.final_score < new_auto
        )

        return {
            "rule_key": rule_key,
            "current_auto_merges": current_auto_merges,
            "projected_auto_merges": projected_auto_merges,
            "net_auto_merge_change": projected_auto_merges - current_auto_merges,
            "current_pending_reviews": current_reviews,
            "projected_pending_reviews": projected_reviews,
            "net_review_change": projected_reviews - current_reviews,
            "total_decisions_evaluated": len(decisions),
        }

    return {
        "rule_key": rule_key,
        "message": "Impact preview calculated successfully",
        "total_decisions_evaluated": len(decisions),
    }

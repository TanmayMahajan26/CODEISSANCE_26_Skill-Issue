from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime, timezone

from app.api.deps import get_db, RoleChecker
from app.db.models.config_rule import ConfigRule
from app.db.models.audit import AuditLog
from app.db.models.user import User

router = APIRouter()

admin_only = RoleChecker(["ADMIN"])


class ConfigRuleUpdate(BaseModel):
    config: dict
    description: Optional[str] = None


@router.get("/rules")
def list_config_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """List all configurable rules. Admin only."""
    rules = db.query(ConfigRule).all()
    return {"rules": rules}


@router.get("/rules/{rule_type}")
def get_config_rule(
    rule_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Get a specific config rule by type."""
    rule = db.query(ConfigRule).filter(ConfigRule.rule_type == rule_type).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Config rule '{rule_type}' not found")
    return rule


@router.put("/rules/{rule_type}")
def update_config_rule(
    rule_type: str,
    update: ConfigRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """
    Update a config rule. Creates audit log entry.
    If the rule doesn't exist, creates it.
    """
    rule = db.query(ConfigRule).filter(ConfigRule.rule_type == rule_type).first()

    old_value = None
    if rule:
        old_value = rule.config
        rule.config = update.config
        rule.version = (rule.version or 1) + 1
        rule.updated_by_id = current_user.id
        rule.updated_at = datetime.now(timezone.utc)
    else:
        rule = ConfigRule(
            rule_type=rule_type,
            config=update.config,
            version=1,
            updated_by_id=current_user.id,
        )
        db.add(rule)

    # Create audit log entry
    audit = AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        action_type="CONFIG_CHANGE",
        entity_type="ConfigRule",
        entity_id=rule_type,
        old_value=old_value,
        new_value=update.config,
        description=update.description or f"Updated config rule '{rule_type}'",
    )
    db.add(audit)
    db.commit()
    db.refresh(rule)

    return {
        "message": f"Config rule '{rule_type}' updated successfully",
        "rule": rule,
        "version": rule.version,
    }


@router.post("/rules/seed-defaults")
def seed_default_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    """Seed default config rules for the hackathon demo."""
    defaults = {
        "matching_weights": {
            "pan": 0.35,
            "mobile": 0.20,
            "email": 0.15,
            "name": 0.20,
            "dob": 0.05,
            "city": 0.03,
            "segment": 0.02,
        },
        "thresholds": {
            "auto_merge": 0.85,
            "review": 0.60,
            "semantic_distance": 0.10,
        },
        "opportunity_rules": {
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
            },
        },
        "scoring_weights": {
            "relationship_value": 0.35,
            "product_affinity": 0.25,
            "recency": 0.20,
            "engagement": 0.20,
        },
        "survivorship_rules": {
            "name": {"strategy": "SOURCE_PRIORITY", "priority": ["WEALTH_MGMT", "CORE_BANKING", "CRM"]},
            "mobile": {"strategy": "MOST_RECENT"},
            "email": {"strategy": "MOST_RECENT"},
            "dob": {"strategy": "MOST_FREQUENT"},
            "city": {"strategy": "SOURCE_PRIORITY", "priority": ["CORE_BANKING", "LOAN_SYS"]},
            "segment": {"strategy": "HIGHEST_VALUE_SOURCE"},
        },
    }

    created = 0
    for rule_type, config in defaults.items():
        existing = db.query(ConfigRule).filter(ConfigRule.rule_type == rule_type).first()
        if not existing:
            rule = ConfigRule(rule_type=rule_type, config=config, version=1, updated_by_id=current_user.id)
            db.add(rule)
            created += 1

    db.commit()
    return {"message": f"Seeded {created} default config rules", "total_rules": len(defaults)}

# Models package — import all models so Alembic/Base can discover them.

from app.models.source_record import SourceRecord, SourceSystem  # noqa: F401
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus  # noqa: F401
from app.models.identity_link import IdentityLink, MatchMethod, LinkStatus  # noqa: F401
from app.models.match_decision import MatchDecision, Decision  # noqa: F401
from app.models.review_case import ReviewCase, ReviewStatus, ReviewPriority, ReviewType  # noqa: F401
from app.models.attribute_history import AttributeHistory  # noqa: F401
from app.models.config_rule import ConfigRule, RuleCategory  # noqa: F401
from app.models.audit_log import AuditLog, AuditAction  # noqa: F401
from app.models.opportunity import Opportunity, OpportunityType, OpportunityStatus  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401

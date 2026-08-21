# Models package — import all models so Alembic/Base can discover them.

from app.models.source_record import SourceRecord, SourceSystem  # noqa: F401
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus  # noqa: F401
from app.models.match_case import MatchCase, MatchClassification, MatchStatus, RiskLevel  # noqa: F401
from app.models.verification_case import VerificationCase, VerificationMethod, VerificationStatus  # noqa: F401
from app.models.verification_result import VerificationResult  # noqa: F401
from app.models.opportunity import Opportunity, OpportunityType, OpportunityStatus  # noqa: F401
from app.models.audit_log import AuditLog, AuditAction  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401

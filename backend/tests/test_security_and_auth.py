"""
Nexus360 — Security, Authentication & RBAC Verification Suite.

Tests:
1. Password hashing and verification
2. JWT generation, decoding, expiry, and tampering detection
3. PII masking functions (PAN, Mobile, Email, DOB) and role-based masking
4. RBAC dependency enforcement (ADMIN, REVIEWER, RELATIONSHIP_MANAGER, ANALYST)
5. User authentication service logic
6. Security settings and upload limit safeguards
"""

import sys
import os
import time
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException, status

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app.services.auth_service  # noqa: F401
import app.models.user  # noqa: F401


# ═══════════════════════════════════════════════════════════════════
#  SECTION 1: Password Hashing & Verification
# ═══════════════════════════════════════════════════════════════════

class TestPasswordSecurity:
    """Tests for secure password hashing and verification."""

    def test_hash_and_verify_password(self):
        """Verify password hashing produces verifiable hashes and rejects bad passwords."""
        from app.core.security import get_password_hash, verify_password

        plain = "SecureP@ssw0rd2026!"
        hashed = get_password_hash(plain)

        assert hashed != plain, "Hash must not equal plaintext"
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or len(hashed) > 20, "Should be bcrypt hash"
        assert verify_password(plain, hashed) is True, "Valid password must verify"
        assert verify_password("WrongPassword123", hashed) is False, "Invalid password must fail"

    def test_unique_salts(self):
        """Hashing the same password twice produces different salt hashes."""
        from app.core.security import get_password_hash

        plain = "IdenticalPassword"
        hash1 = get_password_hash(plain)
        hash2 = get_password_hash(plain)

        assert hash1 != hash2, "Unique salt per hash required"


# ═══════════════════════════════════════════════════════════════════
#  SECTION 2: JWT Token Generation & Verification
# ═══════════════════════════════════════════════════════════════════

class TestJWTTokenSecurity:
    """Tests for HMAC-SHA256 JWT generation, decoding, and tampering guards."""

    def test_create_and_decode_jwt_token(self):
        """Creating and decoding a token preserves claims and verifies signature."""
        from app.core.security import create_access_token, decode_access_token

        claims = {
            "sub": "admin_user",
            "user_id": 42,
            "role": "ADMIN",
            "email": "admin@nexus360.com",
        }
        token = create_access_token(claims)

        assert isinstance(token, str)
        assert len(token.split(".")) == 3, "JWT must have 3 segments"

        payload = decode_access_token(token)
        assert payload is not None, "Valid token must decode successfully"
        assert payload["sub"] == "admin_user"
        assert payload["user_id"] == 42
        assert payload["role"] == "ADMIN"
        assert payload["email"] == "admin@nexus360.com"
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_jwt_rejected(self):
        """Expired JWT tokens are strictly rejected."""
        from app.core.security import create_access_token, decode_access_token

        claims = {"sub": "expired_user", "role": "REVIEWER"}
        # Negative delta = expired in the past
        token = create_access_token(claims, expires_delta=timedelta(seconds=-10))

        payload = decode_access_token(token)
        assert payload is None, "Expired token must return None"

    def test_tampered_jwt_rejected(self):
        """Tampered payload or signature is rejected."""
        from app.core.security import create_access_token, decode_access_token

        token = create_access_token({"sub": "legit_user", "role": "ANALYST"})
        parts = token.split(".")

        # Tamper with signature
        tampered_sig = parts[0] + "." + parts[1] + ".invalidSignature123"
        assert decode_access_token(tampered_sig) is None, "Bad signature must be rejected"

        # Tamper with payload
        tampered_payload = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJzdWIiOiAiaGFja2VyIiwgInJvbGUiOiAiQURNSU4ifQ.faketag"
        assert decode_access_token(tampered_payload) is None, "Forged token must be rejected"


# ═══════════════════════════════════════════════════════════════════
#  SECTION 3: PII & Financial Data Masking
# ═══════════════════════════════════════════════════════════════════

class TestPIIMasking:
    """Tests for role-aware PII masking."""

    def test_mask_pan(self):
        """PAN masking preserves first 5 and last 1 characters: ABCDE1234F -> ABCDE****F."""
        from app.utils.masking import mask_pan

        assert mask_pan("ABCDE1234F") == "ABCDE****F"
        assert mask_pan("XYZAB5678P") == "XYZAB****P"
        assert mask_pan(None) is None
        assert mask_pan("") == ""

    def test_mask_mobile(self):
        """Mobile masking preserves first 5 and last 1 digits: 9876543210 -> 98765****0."""
        from app.utils.masking import mask_mobile

        assert mask_mobile("9876543210") == "98765****0"
        assert mask_mobile("919876543210") == "91987****0"
        assert mask_mobile(None) is None

    def test_mask_email(self):
        """Email masking masks username portion while preserving domain."""
        from app.utils.masking import mask_email

        assert mask_email("rajesh.kumar@gmail.com") == "r*****r@gmail.com"
        assert mask_email("ab@domain.com") == "a*@domain.com"
        assert mask_email(None) is None

    def test_mask_dob(self):
        """DOB masking reveals only birth year."""
        from app.utils.masking import mask_dob

        assert mask_dob(date(1985, 5, 20)) == "1985-**-**"
        assert mask_dob("1990-12-31") == "1990-**-**"
        assert mask_dob(None) is None

    def test_role_based_customer_masking(self):
        """ANALYST role receives masked dictionary while ADMIN receives unmasked."""
        from app.utils.masking import apply_pii_masking_to_customer_dict
        from app.models.user import UserRole

        raw_customer = {
            "canonical_name": "Rajesh Kumar",
            "canonical_pan": "ABCDE1234F",
            "canonical_mobile": "9876543210",
            "canonical_email": "rajesh@example.com",
            "canonical_dob": date(1980, 1, 1),
        }

        # ANALYST view -> MASKED
        analyst_view = apply_pii_masking_to_customer_dict(raw_customer, role=UserRole.ANALYST)
        assert analyst_view["canonical_pan"] == "ABCDE****F"
        assert analyst_view["canonical_mobile"] == "98765****0"
        assert analyst_view["canonical_email"] == "r****h@example.com"
        assert analyst_view["canonical_dob"] == "1980-**-**"

        # ADMIN view -> UNMASKED
        admin_view = apply_pii_masking_to_customer_dict(raw_customer, role=UserRole.ADMIN)
        assert admin_view["canonical_pan"] == "ABCDE1234F"
        assert admin_view["canonical_mobile"] == "9876543210"
        assert admin_view["canonical_email"] == "rajesh@example.com"


# ═══════════════════════════════════════════════════════════════════
#  SECTION 4: RBAC Dependency Guards
# ═══════════════════════════════════════════════════════════════════

class TestRBACGuards:
    """Tests for role-based access control dependencies."""

    @pytest.mark.asyncio
    async def test_require_roles_allows_authorized_role(self):
        """Authorized user passes the require_roles dependency."""
        from app.api.deps import require_roles
        from app.models.user import User, UserRole

        guard = require_roles(UserRole.ADMIN, UserRole.REVIEWER)
        admin_user = User(id=1, username="admin_jane", role=UserRole.ADMIN, is_active=True)

        result = await guard(current_user=admin_user)
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_require_roles_blocks_unauthorized_role(self):
        """Unauthorized role raises HTTP 403 Forbidden."""
        from app.api.deps import require_roles
        from app.models.user import User, UserRole

        guard = require_roles(UserRole.ADMIN)
        analyst_user = User(id=2, username="analyst_priya", role=UserRole.ANALYST, is_active=True)

        with pytest.raises(HTTPException) as exc_info:
            await guard(current_user=analyst_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Access forbidden" in exc_info.value.detail


# ═══════════════════════════════════════════════════════════════════
#  SECTION 5: User & Authentication Service Logic
# ═══════════════════════════════════════════════════════════════════

class TestAuthServiceLogic:
    """Tests for user authentication and demo user seeding."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Valid credentials return authenticated user."""
        from app.services.auth_service import authenticate_user
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole

        mock_db = AsyncMock()
        hashed = get_password_hash("SecretPassword123")
        mock_user = User(
            id=1,
            username="admin",
            email="admin@nexus360.com",
            hashed_password=hashed,
            role=UserRole.ADMIN,
            is_active=True,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await authenticate_user(mock_db, "admin", "SecretPassword123")
        assert user is not None
        assert user.username == "admin"
        assert user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Wrong password returns None."""
        from app.services.auth_service import authenticate_user
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole

        mock_db = AsyncMock()
        mock_user = User(
            id=1,
            username="admin",
            email="admin@nexus360.com",
            hashed_password=get_password_hash("CorrectPassword"),
            role=UserRole.ADMIN,
            is_active=True,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await authenticate_user(mock_db, "admin", "WrongPassword")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user_rejected(self):
        """Inactive user account returns None."""
        from app.services.auth_service import authenticate_user
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole

        mock_db = AsyncMock()
        mock_user = User(
            id=1,
            username="disabled_user",
            email="disabled@nexus360.com",
            hashed_password=get_password_hash("SomePassword"),
            role=UserRole.ANALYST,
            is_active=False,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await authenticate_user(mock_db, "disabled_user", "SomePassword")
        assert user is None

    def test_demo_users_defined_across_all_roles(self):
        """Default demo accounts cover all 4 RBAC roles."""
        from app.services.auth_service import DEFAULT_DEMO_USERS
        from app.models.user import UserRole

        roles = {u["role"] for u in DEFAULT_DEMO_USERS}
        assert UserRole.ADMIN in roles
        assert UserRole.REVIEWER in roles
        assert UserRole.RELATIONSHIP_MANAGER in roles
        assert UserRole.ANALYST in roles


# ═══════════════════════════════════════════════════════════════════
#  SECTION 6: Security Settings & Upload Constraints
# ═══════════════════════════════════════════════════════════════════

class TestSecuritySettings:
    """Tests for application security configuration parameters."""

    def test_settings_security_fields(self):
        """Settings must contain JWT, CORS, upload size, and environment configurations."""
        from app.core.config import settings

        assert hasattr(settings, "SECRET_KEY") and len(settings.SECRET_KEY) >= 16
        assert hasattr(settings, "JWT_ALGORITHM") and settings.JWT_ALGORITHM == "HS256"
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES") and settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert hasattr(settings, "ALLOWED_ORIGINS") and isinstance(settings.ALLOWED_ORIGINS, list)
        assert "*" not in settings.ALLOWED_ORIGINS, "Wildcard '*' must not be present with credentials"
        assert hasattr(settings, "MAX_UPLOAD_SIZE_MB") and settings.MAX_UPLOAD_SIZE_MB == 10
        assert hasattr(settings, "ENVIRONMENT")

    @pytest.mark.asyncio
    async def test_demo_users_endpoint_disabled_in_production(self):
        """GET /auth/demo-users returns 404 in production environment."""
        from app.api.routes.auth import list_demo_users

        with patch("app.core.config.settings.ENVIRONMENT", "production"):
            with pytest.raises(HTTPException) as exc_info:
                await list_demo_users()
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "disabled in production" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_demo_users_endpoint_allowed_in_development(self):
        """GET /auth/demo-users returns demo list in development environment."""
        from app.api.routes.auth import list_demo_users

        with patch("app.core.config.settings.ENVIRONMENT", "development"):
            users = await list_demo_users()
            assert isinstance(users, list)
            assert len(users) == 4
            usernames = [u["username"] for u in users]
            assert "admin" in usernames
            assert "reviewer_sarah" in usernames


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

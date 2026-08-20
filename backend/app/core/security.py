"""
Nexus360 — Security & Cryptography Utilities.

Provides password hashing (OWASP standard PBKDF2-HMAC-SHA256), verification,
and standard HMAC-SHA256 JWT token generation and decoding with zero external cloud dependencies.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import timedelta
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

PBKDF2_ITERATIONS = 100_000


# ── Password Hashing (PBKDF2-HMAC-SHA256) ───────────────────────────

def get_password_hash(password: str) -> str:
    """Generate a cryptographically secure PBKDF2-HMAC-SHA256 hash with unique salt."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${salt}${key}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against stored PBKDF2 hash."""
    if not hashed_password or not plain_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3 or parts[0] != "pbkdf2_sha256":
            return False
        salt = parts[1]
        expected_key = parts[2]
        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS,
        ).hex()
        return hmac.compare_digest(expected_key, computed_key)
    except Exception as exc:
        logger.warning("Password verification error: %s", exc)
        return False


# ── JWT Token Utilities (HS256) ───────────────────────────────────

def _b64_url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 without trailing '=' padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64_url_decode(data: str) -> bytes:
    """Decode URL-safe base64 string with restored padding."""
    pad = 4 - (len(data) % 4)
    if pad < 4:
        data += "=" * pad
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generate an RFC 7519 compliant HMAC-SHA256 JWT access token.

    Parameters
    ----------
    data : dict
        Claims to include in the payload (sub, role, user_id, email, etc.).
    expires_delta : timedelta, optional
        Custom expiration delta. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns
    -------
    str
        Signed JWT string formatted as `header.payload.signature`.
    """
    payload = data.copy()
    now_ts = int(time.time())

    if expires_delta:
        expire_ts = now_ts + int(expires_delta.total_seconds())
    else:
        expire_ts = now_ts + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    payload.update({
        "iat": now_ts,
        "exp": expire_ts,
        "iss": settings.APP_NAME,
    })

    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}

    header_b64 = _b64_url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64_url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64_url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode, verify signature, and validate expiration of an access token.

    Returns
    -------
    dict or None
        Decoded payload claims if valid, None if invalid or expired.
    """
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        expected_sig_b64 = _b64_url_encode(expected_sig)

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            logger.debug("JWT signature mismatch")
            return None

        # Decode payload
        payload_bytes = _b64_url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if not exp or int(exp) < int(time.time()):
            logger.debug("JWT token expired")
            return None

        return payload

    except Exception as exc:
        logger.debug("Error decoding JWT token: %s", exc)
        return None

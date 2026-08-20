"""
Nexus360 — PII & Financial Data Masking Utilities.

Provides masking functions for sensitive personal & financial attributes
(PAN, Mobile, Email, DOB) to comply with data privacy standards (DPDP Act, GDPR)
and support role-based visibility (e.g. masked for ANALYST, unmasked for ADMIN/REVIEWER).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from app.models.user import UserRole


def mask_pan(pan: Optional[str]) -> Optional[str]:
    """Mask a 10-character PAN number: 'ABCDE1234F' -> 'ABCDE****F'."""
    if not pan or len(pan) < 6:
        return pan
    pan = pan.strip()
    if len(pan) == 10:
        return f"{pan[:5]}****{pan[-1]}"
    return f"{pan[:2]}****{pan[-2:]}"


def mask_mobile(mobile: Optional[str]) -> Optional[str]:
    """Mask a mobile number: '9876543210' -> '98765****0'."""
    if not mobile:
        return mobile
    clean = mobile.strip()
    if len(clean) >= 10:
        return f"{clean[:5]}****{clean[-1]}"
    if len(clean) >= 6:
        return f"{clean[:2]}****{clean[-2:]}"
    return "****"


def mask_email(email: Optional[str]) -> Optional[str]:
    """Mask an email address: 'rajesh.kumar@gmail.com' -> 'r*****r@gmail.com'."""
    if not email or "@" not in email:
        return email
    parts = email.strip().split("@", 1)
    user_part = parts[0]
    domain_part = parts[1]

    if len(user_part) <= 2:
        masked_user = f"{user_part[0]}*"
    else:
        masked_user = f"{user_part[0]}{'*' * (min(len(user_part) - 2, 5))}{user_part[-1]}"

    return f"{masked_user}@{domain_part}"


def mask_dob(dob_val: Optional[Any]) -> Optional[str]:
    """Mask date of birth to reveal only the birth year: '1985-05-20' -> '1985-**-**'."""
    if not dob_val:
        return None
    if isinstance(dob_val, date):
        return f"{dob_val.year}-**-**"
    dob_str = str(dob_val).strip()
    if len(dob_str) >= 4:
        return f"{dob_str[:4]}-**-**"
    return "****-**-**"


def apply_pii_masking_to_customer_dict(
    customer_dict: Dict[str, Any],
    role: Optional[UserRole] = None,
    force_mask: bool = False,
) -> Dict[str, Any]:
    """
    Apply PII masking to a GoldenCustomer data dictionary if caller is an ANALYST
    or if masking is explicitly requested.
    """
    # ADMIN and REVIEWER see unmasked by default unless force_mask is True
    if not force_mask and role in (UserRole.ADMIN, UserRole.REVIEWER, UserRole.RELATIONSHIP_MANAGER):
        return customer_dict

    out = dict(customer_dict)
    if "canonical_pan" in out:
        out["canonical_pan"] = mask_pan(out.get("canonical_pan"))
    if "canonical_mobile" in out:
        out["canonical_mobile"] = mask_mobile(out.get("canonical_mobile"))
    if "canonical_email" in out:
        out["canonical_email"] = mask_email(out.get("canonical_email"))
    if "canonical_dob" in out:
        out["canonical_dob"] = mask_dob(out.get("canonical_dob"))

    # Mask linked sources if present
    if "linked_sources" in out and isinstance(out["linked_sources"], list):
        masked_sources = []
        for src in out["linked_sources"]:
            s = dict(src)
            s["original_pan"] = mask_pan(s.get("original_pan"))
            s["original_mobile"] = mask_mobile(s.get("original_mobile"))
            s["original_email"] = mask_email(s.get("original_email"))
            masked_sources.append(s)
        out["linked_sources"] = masked_sources

    return out

"""
Sensitive data masking utilities.
Applied based on user role to protect PII.
"""


def mask_pan(pan: str, role: str = "RM") -> str:
    """Mask PAN to show only first 5 and last 1 character.
    ADMIN sees full PAN, others see masked."""
    if not pan:
        return None
    if role == "ADMIN":
        return pan
    if len(pan) >= 6:
        return f"{pan[:5]}{'*' * (len(pan) - 6)}{pan[-1]}"
    return "*" * len(pan)


def mask_mobile(mobile: str, role: str = "RM") -> str:
    """Mask mobile to show last 4 digits only.
    ADMIN/MANAGER see full mobile."""
    if not mobile:
        return None
    if role in ("ADMIN", "MANAGER"):
        return mobile
    if len(mobile) >= 4:
        return f"{'*' * (len(mobile) - 4)}{mobile[-4:]}"
    return "*" * len(mobile)


def mask_email(email: str, role: str = "RM") -> str:
    """Mask email to show first 2 chars and domain.
    ADMIN/MANAGER see full email."""
    if not email:
        return None
    if role in ("ADMIN", "MANAGER"):
        return email
    if "@" in email:
        user, domain = email.split("@", 1)
        masked_user = f"{user[:2]}{'*' * max(len(user) - 2, 0)}"
        return f"{masked_user}@{domain}"
    return "*" * len(email)


def mask_record(record: dict, role: str = "RM") -> dict:
    """Apply masking to all PII fields in a record dict based on role."""
    masked = dict(record)
    if "pan" in masked:
        masked["pan"] = mask_pan(masked["pan"], role)
    if "mobile" in masked:
        masked["mobile"] = mask_mobile(masked["mobile"], role)
    if "email" in masked:
        masked["email"] = mask_email(masked["email"], role)
    if "raw_pan" in masked:
        masked["raw_pan"] = mask_pan(masked["raw_pan"], role)
    if "raw_mobile" in masked:
        masked["raw_mobile"] = mask_mobile(masked["raw_mobile"], role)
    if "raw_email" in masked:
        masked["raw_email"] = mask_email(masked["raw_email"], role)
    return masked

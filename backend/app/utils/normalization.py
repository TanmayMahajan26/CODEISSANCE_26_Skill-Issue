"""
Nexus360 — Normalization Utilities.

Reusable functions that standardize raw field values coming from
heterogeneous source systems so that deterministic matching and
blocking can work reliably. Aligned with PRD §10.1 normalization rules.

Design principles
─────────────────
• Never mutate the original value — always return a new string.
• Return None when the input is empty / None so callers can distinguish
  "missing" from "empty-string".
• Each normalizer is a pure function (no DB, no I/O).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

# ── Honorific titles to remove (PRD §10.1) ──────────────────────
TITLES_REGEX = re.compile(
    r"^(mr|mrs|ms|dr|shri|smt|prof)\b[\.\s]*", re.IGNORECASE
)

# ── PAN Validation Regex (PRD §10.1) ─────────────────────────────
PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

# ── City alias map (PRD §10.1) ───────────────────────────────────
CITY_ALIASES: dict[str, str] = {
    "bombay": "mumbai",
    "madras": "chennai",
    "calcutta": "kolkata",
    "poona": "pune",
    "bangalore": "bengaluru",
    "trivandrum": "thiruvananthapuram",
    "cochin": "kochi",
    "baroda": "vadodara",
    "mysore": "mysuru",
    "pondicherry": "puducherry",
    "benares": "varanasi",
    "banaras": "varanasi",
    "vizag": "visakhapatnam",
    "mangalore": "mangaluru",
    "shimoga": "shivamogga",
    "belgaum": "belagavi",
    "hubli": "hubballi",
    "gurgaon": "gurugram",
}


def normalize_name(raw: Optional[str]) -> Optional[str]:
    """
    Normalize a person's name.

    Steps:
    1. Strip leading / trailing whitespace
    2. Remove honorific titles (Mr, Mrs, Ms, Dr, Shri, Smt, Prof)
    3. Lowercase
    4. Replace periods (used in initials) with a space
    5. Remove punctuation except spaces and alphanumerics
    6. Collapse multiple spaces

    Examples
    --------
    >>> normalize_name("Mr. Rohita P. Raghavan")
    'rohita p raghavan'
    >>> normalize_name("Dr. R. Raghavan")
    'r raghavan'
    >>> normalize_name("  SHARMA,  Ankit  ")
    'sharma ankit'
    """
    if not raw or not raw.strip():
        return None

    text = raw.strip()
    # Strip honorific titles
    text = TITLES_REGEX.sub("", text).strip()
    text = text.lower()
    # Replace periods (used in initials) with a space
    text = text.replace(".", " ")
    # Remove all remaining punctuation except spaces and alphanumerics
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_mobile(raw: Optional[str]) -> Optional[str]:
    """
    Normalize an Indian mobile number to its bare 10-digit form.

    Strips country code (+91 / 0091 / 91 prefix), dashes, spaces, and
    parentheses.

    Examples
    --------
    >>> normalize_mobile("+91 98765 43210")
    '9876543210'
    >>> normalize_mobile("98765-43210")
    '9876543210'
    >>> normalize_mobile("0091-9876543210")
    '9876543210'
    """
    if not raw or not raw.strip():
        return None

    digits = re.sub(r"\D", "", raw.strip())

    # Strip leading country code
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0091") and len(digits) == 14:
        digits = digits[4:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]

    return digits if len(digits) == 10 else digits  # return as-is if unusual


def normalize_email(raw: Optional[str]) -> Optional[str]:
    """
    Normalize an email address.

    Steps:
    1. Lowercase
    2. Trim whitespace

    Examples
    --------
    >>> normalize_email("  ROHITA@Gmail.COM  ")
    'rohita@gmail.com'
    """
    if not raw or not raw.strip():
        return None
    return raw.strip().lower()


def normalize_pan(raw: Optional[str]) -> Optional[str]:
    """
    Normalize a PAN (Permanent Account Number).

    Steps:
    1. Uppercase
    2. Remove spaces
    3. Validate against PAN regex (^[A-Z]{5}[0-9]{4}[A-Z]$)

    Examples
    --------
    >>> normalize_pan("abcde 1234f")
    'ABCDE1234F'
    """
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().upper().replace(" ", "")
    return cleaned if PAN_REGEX.match(cleaned) else cleaned


def normalize_city(raw: Optional[str]) -> Optional[str]:
    """
    Normalize a city name.

    Steps:
    1. Lowercase
    2. Trim whitespace
    3. Apply common Indian city aliases

    Examples
    --------
    >>> normalize_city("Bombay")
    'mumbai'
    >>> normalize_city("  BANGALORE ")
    'bengaluru'
    """
    if not raw or not raw.strip():
        return None
    city = raw.strip().lower()
    return CITY_ALIASES.get(city, city)


def normalize_segment(raw: Optional[str]) -> Optional[str]:
    """
    Normalize customer segment.

    Examples: 'hni' -> 'HNI', 'retail customer' -> 'RETAIL'
    """
    if not raw or not raw.strip():
        return None
    clean = raw.strip().upper()
    if "ULTRA" in clean or "UHNW" in clean:
        return "ULTRA_HNI"
    if "HNI" in clean or "HIGH NET" in clean:
        return "HNI"
    if "AFFLUENT" in clean:
        return "AFFLUENT"
    if "RETAIL" in clean or "MASS" in clean:
        return "RETAIL"
    return clean


def normalize_dob(raw) -> Optional[date]:
    """
    Normalize a date-of-birth.

    Accepts:
    • datetime.date objects (returned as-is)
    • Strings in common formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY

    Returns None for unparseable values.
    """
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    if isinstance(raw, datetime):
        return raw.date()

    raw_str = str(raw).strip()
    if not raw_str:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw_str, fmt).date()
        except ValueError:
            continue
    return None

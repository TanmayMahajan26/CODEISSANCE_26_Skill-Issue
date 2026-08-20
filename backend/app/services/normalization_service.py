"""
Nexus360 — Normalization Service.

Applies all normalization functions to a SourceRecord so that
the normalized_* columns are populated while the original_* columns
remain untouched.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.models.source_record import SourceRecord
from app.utils.normalization import (
    normalize_name,
    normalize_mobile,
    normalize_email,
    normalize_pan,
    normalize_city,
    normalize_dob,
)

logger = logging.getLogger(__name__)


def normalize_record(record: SourceRecord) -> SourceRecord:
    """
    Populate the normalized_* fields of a SourceRecord in-place.

    The original_* fields are never modified.

    Parameters
    ----------
    record : SourceRecord
        An ORM object with original_* fields already set.

    Returns
    -------
    SourceRecord
        The same object with normalized_* fields populated.
    """
    record.normalized_name = normalize_name(record.original_name)
    record.normalized_dob = normalize_dob(record.original_dob)
    record.normalized_mobile = normalize_mobile(record.original_mobile)
    record.normalized_email = normalize_email(record.original_email)
    record.normalized_pan = normalize_pan(record.original_pan)
    record.normalized_city = normalize_city(record.original_city)

    logger.debug(
        "Normalized record %s/%s: name=%s mobile=%s email=%s pan=%s city=%s",
        record.source_system,
        record.source_record_id,
        record.normalized_name,
        record.normalized_mobile,
        record.normalized_email,
        record.normalized_pan,
        record.normalized_city,
    )
    return record


def normalize_raw_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a dict of normalized values from a raw data dictionary.

    Useful for preview / dry-run without touching the ORM.
    """
    return {
        "normalized_name": normalize_name(raw.get("name") or raw.get("original_name")),
        "normalized_dob": normalize_dob(raw.get("dob") or raw.get("original_dob")),
        "normalized_mobile": normalize_mobile(raw.get("mobile") or raw.get("original_mobile")),
        "normalized_email": normalize_email(raw.get("email") or raw.get("original_email")),
        "normalized_pan": normalize_pan(raw.get("pan") or raw.get("original_pan")),
        "normalized_city": normalize_city(raw.get("city") or raw.get("original_city")),
    }

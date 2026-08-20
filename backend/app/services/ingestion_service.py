"""
Nexus360 — Ingestion Service.

Handles CSV file parsing, validation, SourceRecord creation, idempotency checks,
and normalization. Preserves original values while parsing financial and business fields.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Tuple, Set

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_record import SourceRecord, SourceSystem
from app.services.normalization_service import normalize_record
from app.services.embedding_service import get_embedding_service
from app.utils.normalization import normalize_dob

logger = logging.getLogger(__name__)

# Accept these column aliases
COLUMN_ALIASES = {
    "full_name": "name",
    "customer_name": "name",
    "date_of_birth": "dob",
    "birth_date": "dob",
    "phone": "mobile",
    "phone_number": "mobile",
    "mobile_number": "mobile",
    "email_address": "email",
    "pan_number": "pan",
    "pan_no": "pan",
    "city_name": "city",
    "location": "city",
    "customer_segment": "segment",
    "cust_segment": "segment",
    "product": "product_type",
    "aum": "balance_aum",
    "balance": "balance_aum",
    "aum_balance": "balance_aum",
    "rel_value": "relationship_value",
    "rel_val": "relationship_value",
    "total_value": "relationship_value",
    "last_active": "last_activity_date",
    "last_activity": "last_activity_date",
    "assigned_rm": "rm_id",
    "relationship_manager": "rm_id",
}


async def ingest_csv(
    db: AsyncSession,
    source_system: str,
    file_content: bytes,
) -> Tuple[int, List[str]]:
    """
    Parse a CSV file and create SourceRecord rows with idempotency support.

    Parameters
    ----------
    db : AsyncSession
    source_system : str
        One of EQUITY, MUTUAL_FUND, INSURANCE, LOAN, WEALTH.
    file_content : bytes
        Raw bytes of the uploaded CSV.

    Returns
    -------
    (records_ingested, errors)
        Count of successfully ingested records and a list of
        per-row error messages (or skip notes).
    """
    # Validate source system
    try:
        system_enum = SourceSystem(source_system.upper())
    except ValueError:
        raise ValueError(
            f"Invalid source_system '{source_system}'. "
            f"Must be one of: {[s.value for s in SourceSystem]}"
        )

    # Parse CSV
    try:
        df = pd.read_csv(io.BytesIO(file_content), dtype=str, keep_default_na=False)
    except Exception as exc:
        raise ValueError(f"Failed to parse CSV: {exc}")

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Apply column aliases
    df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if k in df.columns}, inplace=True)

    # Check for at least 'name' column
    if "name" not in df.columns:
        raise ValueError(
            f"CSV must contain at least a 'name' column. "
            f"Found columns: {list(df.columns)}"
        )

    # Idempotency check: fetch existing source_record_ids for this system
    result = await db.execute(
        select(SourceRecord.source_record_id).where(
            SourceRecord.source_system == system_enum
        )
    )
    existing_ids: Set[str] = {r[0] for r in result.all()}

    records_created = 0
    errors: List[str] = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed + header
        try:
            # Determine source_record_id
            raw_id = (
                row.get("source_record_id", "").strip()
                or row.get("id", "").strip()
                or row.get("customer_id", "").strip()
            )
            source_record_id = raw_id if raw_id else f"{system_enum.value}-{uuid.uuid4().hex[:8].upper()}"

            # Skip duplicate re-uploads (idempotency requirement)
            if source_record_id in existing_ids:
                logger.debug("Skipping duplicate record %s for %s", source_record_id, system_enum.value)
                continue

            # Parse dates and numbers
            raw_dob = row.get("dob", "").strip() or None
            parsed_dob = normalize_dob(raw_dob) if raw_dob else None

            raw_act_date = row.get("last_activity_date", "").strip() or None
            parsed_act_date = normalize_dob(raw_act_date) if raw_act_date else None

            balance_aum = _parse_decimal(row.get("balance_aum", ""))
            relationship_val = _parse_decimal(row.get("relationship_value", ""))

            record = SourceRecord(
                source_system=system_enum,
                source_record_id=source_record_id,
                original_name=row.get("name", "").strip() or None,
                original_dob=parsed_dob,
                original_mobile=row.get("mobile", "").strip() or None,
                original_email=row.get("email", "").strip() or None,
                original_pan=row.get("pan", "").strip() or None,
                original_city=row.get("city", "").strip() or None,
                segment=row.get("segment", "").strip() or None,
                product_type=row.get("product_type", "").strip() or None,
                balance_aum=balance_aum,
                relationship_value=relationship_val,
                last_activity_date=parsed_act_date,
                rm_id=row.get("rm_id", "").strip() or None,
                raw_data=row.to_dict(),
            )

            # Apply normalization (populates normalized_* fields)
            normalize_record(record)

            # Generate semantic vector embedding for name
            name_to_embed = record.normalized_name or record.original_name
            if name_to_embed:
                try:
                    emb_service = get_embedding_service()
                    record.name_embedding = await emb_service.get_embedding(name_to_embed)
                except Exception as emb_exc:
                    logger.warning("Embedding error at row %d for '%s': %s", row_num, name_to_embed, emb_exc)
                    record.name_embedding = None

            db.add(record)
            existing_ids.add(source_record_id)
            records_created += 1

        except Exception as exc:
            errors.append(f"Row {row_num}: {exc}")
            logger.warning("Ingestion error at row %d: %s", row_num, exc)

    if records_created > 0:
        await db.flush()

    logger.info(
        "Ingested %d records from %s (%d errors/skips)",
        records_created, system_enum.value, len(errors),
    )
    return records_created, errors


def _parse_decimal(raw: str) -> Decimal | None:
    """Parse numeric string to Decimal or return None."""
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().replace(",", "").replace("$", "").replace("₹", "")
    try:
        return Decimal(cleaned)
    except Exception:
        return None

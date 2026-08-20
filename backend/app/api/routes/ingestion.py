"""
Nexus360 — Ingestion Endpoints.

POST /api/v1/ingest                 Upload CSV records (ADMIN only, file size limit enforced)
POST /api/v1/ingest/seed            Seed synthetic datasets (ADMIN only)
GET  /api/v1/ingest/quality-report  Data Quality Scorecard (ALL authenticated roles)
GET  /api/v1/source-records         List all source records (ADMIN, REVIEWER)
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.source_record import SourceRecord, SourceSystem
from app.models.user import User, UserRole
from app.schemas.source_record import (
    IngestionResponse,
    SourceRecordResponse,
)
from app.services.audit_service import log_action
from app.services.ingestion_service import ingest_csv

router = APIRouter(tags=["Ingestion"])


@router.post(
    "/ingest",
    response_model=IngestionResponse,
    summary="Ingest CSV records from a source system",
)
async def ingest(
    request: Request,
    source_system: str = Form(
        ...,
        description="Source system: EQUITY | MUTUAL_FUND | INSURANCE | LOAN | WEALTH",
    ),
    file: UploadFile = File(..., description="CSV file to ingest"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV file containing customer records from one of the 5 source systems (ADMIN only).
    Enforces maximum upload size ceiling and UTF-8 text validation.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are accepted")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # File size validation (DoS / Memory exhaustion protection)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Basic text validation
    try:
        content[:512].decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be a valid UTF-8 encoded text/CSV file")

    client_ip = get_client_ip(request)

    try:
        records_ingested, errors = await ingest_csv(db, source_system, content)
        await log_action(
            db,
            action=AuditAction.DATA_INGEST,
            actor_username=current_user.username,
            actor_role=current_user.role.value,
            entity_type="SourceSystem",
            entity_id=source_system.upper(),
            new_value={"filename": file.filename, "records_ingested": records_ingested, "errors": len(errors)},
            ip_address=client_ip,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return IngestionResponse(
        message=f"Successfully ingested {records_ingested} records from {source_system.upper()}",
        records_ingested=records_ingested,
        source_system=source_system.upper(),
        errors=errors,
    )


@router.post(
    "/ingest/seed",
    summary="Programmatically seed synthetic data files",
)
async def seed_data(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Seed synthetic customer dataset from scripts/data CSV files per PRD §7.8 (ADMIN only)."""
    client_ip = get_client_ip(request)
    data_dir = Path(__file__).resolve().parent.parent.parent.parent / "scripts" / "data"
    
    if not data_dir.exists():
        from scripts.seed_data import main as generate_seed
        generate_seed()

    results = {}
    total_ingested = 0
    
    file_map = {
        "EQUITY": "equity_records.csv",
        "MUTUAL_FUND": "mutual_fund_records.csv",
        "INSURANCE": "insurance_records.csv",
        "LOAN": "loan_records.csv",
        "WEALTH": "wealth_records.csv",
    }

    for sys_name, filename in file_map.items():
        filepath = data_dir / filename
        if filepath.exists():
            content = filepath.read_bytes()
            count, errs = await ingest_csv(db, sys_name, content)
            results[sys_name] = {"ingested": count, "errors": len(errs)}
            total_ingested += count

    await log_action(
        db,
        action=AuditAction.DATA_INGEST,
        actor_username=current_user.username,
        actor_role=current_user.role.value,
        entity_type="SeedData",
        entity_id="ALL_SYSTEMS",
        new_value=results,
        ip_address=client_ip,
    )

    return {
        "message": f"Successfully seeded {total_ingested} synthetic records across 5 business systems",
        "details": results,
    }


@router.get(
    "/ingest/quality-report",
    summary="Data Quality Scorecard",
)
async def data_quality_report(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.RELATIONSHIP_MANAGER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve data quality metrics per source system per PRD §7.8 / §9.2 Screen 2."""
    scorecard: Dict[str, Any] = {}
    
    for sys_enum in SourceSystem:
        sys_key = sys_enum.value
        total_res = await db.execute(
            select(func.count(SourceRecord.id)).where(SourceRecord.source_system == sys_enum)
        )
        total = total_res.scalar() or 0

        if total == 0:
            scorecard[sys_key] = {"total_records": 0, "quality_score_pct": 100.0}
            continue

        # Check completeness of key fields
        pan_res = await db.execute(
            select(func.count(SourceRecord.id))
            .where(SourceRecord.source_system == sys_enum)
            .where(SourceRecord.normalized_pan != None)
        )
        pan_count = pan_res.scalar() or 0

        mob_res = await db.execute(
            select(func.count(SourceRecord.id))
            .where(SourceRecord.source_system == sys_enum)
            .where(SourceRecord.normalized_mobile != None)
        )
        mob_count = mob_res.scalar() or 0

        email_res = await db.execute(
            select(func.count(SourceRecord.id))
            .where(SourceRecord.source_system == sys_enum)
            .where(SourceRecord.normalized_email != None)
        )
        email_count = email_res.scalar() or 0

        pan_pct = round((pan_count / total * 100), 1)
        mob_pct = round((mob_count / total * 100), 1)
        email_pct = round((email_count / total * 100), 1)
        overall_score = round((pan_pct * 0.5 + mob_pct * 0.3 + email_pct * 0.2), 1)

        scorecard[sys_key] = {
            "total_records": total,
            "overall_quality_score_pct": overall_score,
            "pan_completeness_pct": pan_pct,
            "mobile_completeness_pct": mob_pct,
            "email_completeness_pct": email_pct,
            "missing_pan_count": total - pan_count,
            "missing_mobile_count": total - mob_count,
            "missing_email_count": total - email_count,
        }

    return {
        "scorecard": scorecard,
        "summary": "Data quality analysis completed across 5 business systems",
    }


@router.get(
    "/source-records",
    response_model=List[SourceRecordResponse],
    summary="List all source records",
)
async def list_source_records(
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve source records, optionally filtered by source system (ADMIN & REVIEWER only)."""
    query = select(SourceRecord).offset(skip).limit(limit)

    if source_system:
        try:
            system_enum = SourceSystem(source_system.upper())
            query = query.where(SourceRecord.source_system == system_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source_system. Must be one of: {[s.value for s in SourceSystem]}",
            )

    query = query.order_by(SourceRecord.ingested_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

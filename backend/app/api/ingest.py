from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.schemas.ingest import IngestRecord
from app.services.ingestion import IngestionService
from app.db.models.user import User

router = APIRouter()

@router.post("/seed", response_model=Dict[str, Any])
def seed_synthetic_data(
    db: Session = Depends(get_db),
    # Requires authentication to prevent anonymous seeding in production
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Seed the database with synthetic banking data for the hackathon.
    Generates ~250 mock records across multiple source systems and processes them.
    """
    result = IngestionService.seed_synthetic_data(db)
    return result

@router.post("/upload", response_model=Dict[str, Any])
def upload_records(
    records: List[IngestRecord],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload and process a batch of records from an external source system.
    """
    result = IngestionService.process_records(db, records)
    return result

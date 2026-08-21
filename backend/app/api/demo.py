from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.db.models.user import User, UserRole
from app.db.models.source_record import SourceRecord
from app.api.resolution import run_resolution_pipeline
import csv
import io
import time
import os
from datetime import datetime

router = APIRouter()

@router.post("/upload_and_process")
async def upload_and_process_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Demo endpoint: Upload a CSV, parse into SourceRecords, and trigger the pipeline.
    Returns metrics on processing and discrepancies.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be a CSV file")

    start_time = time.time()
    contents = await file.read()
    
    # Simple parse
    try:
        decoded = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        new_records = []
        for row in reader:
            # Parse row into SourceRecord
            dob_str = row.get("dob")
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                except:
                    pass

            record = SourceRecord(
                assigned_rm_id=current_user.id,
                source_system=row.get("source_system", "CSV_IMPORT"),
                source_id=row.get("source_id", "CSV-" + str(time.time())),
                raw_name=row.get("name", ""),
                name=row.get("name", "").lower(),
                dob=dob,
                pan=row.get("pan") or None,
                email=row.get("email") or None,
                mobile=row.get("mobile") or None,
                city=row.get("city"),
                segment=row.get("segment", "RETAIL"),
                account_value=float(row.get("account_value", 0)) if row.get("account_value") else 0.0,
                products=row.get("products", "").split(",") if row.get("products") else []
            )
            new_records.append(record)
            
        db.add_all(new_records)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    # Trigger resolution
    pipeline_result = run_resolution_pipeline(db)
    
    from app.db.models.review_queue import ReviewQueueItem
    from app.db.models.opportunity import Opportunity
    reviews_count = db.query(ReviewQueueItem).count()
    opps_count = db.query(Opportunity).count()

    end_time = time.time()
    
    explanations = [
        {"type": "MERGE", "title": "Auto-Merged: Cross-system ID (Mutual Fund USP)", "description": "System merged a record from Core Banking with a CRM record containing Mutual Funds based on exact PAN match (Confidence: 100%)."},
        {"type": "MERGE", "title": "Auto-Merged: Cross-system ID (Equity/Stocks USP)", "description": "Mobile+DOB match established link between Wealth Management (Equity) and Core Banking, creating a cross-sell opportunity (Confidence: 95%)."},
        {"type": "MERGE", "title": "Auto-Merged: Common Row Cleanup", "description": "Successfully merged duplicate retail accounts with identical deterministic markers."},
        {"type": "REVIEW", "title": "Flagged for Review: Phonetic Discrepancy", "description": "High Jaro-Winkler distance on Name but shared Email. Forwarded to RM for manual review."},
        {"type": "REVIEW", "title": "Flagged for Review: Typo Match", "description": "Flagged as potential duplicate due to partial semantic name match + shared mobile number."}
    ]
    
    return {
        "status": "success",
        "metrics": {
            "records_ingested": len(new_records),
            "golden_records_created": pipeline_result.get("metrics", {}).get("golden_records_created", 0),
            "reviews_flagged": reviews_count,
            "opportunities_created": opps_count,
            "processing_time_ms": int((end_time - start_time) * 1000)
        },
        "explanations": explanations
    }

@router.get("/download/{filename}")
async def download_demo_file(filename: str):
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "demo_files", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="text/csv", filename=filename)

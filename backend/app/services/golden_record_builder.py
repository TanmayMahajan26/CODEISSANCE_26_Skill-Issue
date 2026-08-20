import logging
from typing import List, Set
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.db.models.source_record import SourceRecord
from app.db.models.golden_record import GoldenRecord

logger = logging.getLogger(__name__)

def build_golden_records(db: Session, clusters: List[Set[int]]) -> int:
    """
    Takes connected components (clusters), applies survivorship rules to compile a unified GoldenRecord,
    and updates the SourceRecords to point to the new GoldenRecord.
    Returns the number of new GoldenRecords generated.
    """
    logger.info("Starting Phase 2 - Step 5: Golden Record Builder")
    golden_records_created = 0
    
    for cluster_ids in clusters:
        # Fetch all source records in this cluster
        records = db.query(SourceRecord).filter(SourceRecord.id.in_(cluster_ids)).all()
        if not records:
            continue
            
        # Survivorship logic: Sort by recently updated, then pick the first non-null value for each attribute
        # In a real system, we might prioritize by `source_system` tier (e.g. KYC systems first).
        records_sorted = sorted(records, key=lambda r: r.updated_at, reverse=True)
        
        resolved_attributes = {
            "pan": None, "mobile": None, "email": None,
            "name": None, "dob": None, "city": None, "segment": None
        }
        provenance = {}
        total_relationship_value = 0.0
        products_held = []
        source_systems = []
        
        for r in records_sorted:
            # Survivorship
            for attr in resolved_attributes.keys():
                val = getattr(r, attr)
                if val and not resolved_attributes[attr]:
                    resolved_attributes[attr] = val
                    
                    val_serialized = val.isoformat() if isinstance(val, (datetime, date)) else val
                    
                    provenance[attr] = {
                        "value": val_serialized,
                        "source_system": r.source_system,
                        "rule": "most_recent_non_null"
                    }
                    
            # Financials & Aggregations
            if r.account_value:
                total_relationship_value += r.account_value
                
            if r.products:
                if isinstance(r.products, list):
                    products_held.extend(r.products)
                else:
                    products_held.append(r.products)
                
            if r.source_system not in source_systems:
                source_systems.append(r.source_system)
                
        # Check if golden record already exists for any record in this cluster
        existing_golden = next((r.golden_record_id for r in records if r.golden_record_id), None)
        
        if existing_golden:
            gr = db.query(GoldenRecord).filter(GoldenRecord.id == existing_golden).first()
        else:
            gr = GoldenRecord()
            db.add(gr)
            db.flush() # get ID
            golden_records_created += 1
            
        # Assign compiled values directly to columns
        for attr, val in resolved_attributes.items():
            setattr(gr, attr, val)
            
        gr.provenance = provenance
        gr.total_relationship_value = round(total_relationship_value, 2)
        
        # Deduplicate products by forcing them into a consistent structure if needed,
        # but for now, just storing the list is fine.
        gr.products_held = products_held
        gr.source_systems = source_systems
        gr.source_record_count = len(records)
        
        # Link source records to this Golden Record
        for r in records:
            r.golden_record_id = gr.id
            
    db.commit()
    logger.info(f"Golden Record generation complete. Created {golden_records_created} new golden records.")
    return golden_records_created

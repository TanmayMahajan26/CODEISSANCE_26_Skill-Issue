import logging
from sqlalchemy.orm import Session
from typing import List

from app.db.models.source_record import SourceRecord
from app.db.models.identity_edge import IdentityEdge

logger = logging.getLogger(__name__)

def run_deterministic_matching(db: Session) -> int:
    """
    Finds exact matches on PAN, mobile, or email across all source records.
    Generates IdentityEdge records with confidence = 1.0 and match_phase = 'deterministic'.
    Returns the number of new edges created.
    """
    logger.info("Starting Phase 2 - Step 1: Deterministic Matching")
    new_edges = 0
    
    # Load all records to build exact match indices
    records = db.query(SourceRecord).all()
    
    pan_map = {}
    mobile_map = {}
    email_map = {}
    
    for r in records:
        if r.pan:
            pan_map.setdefault(r.pan, []).append(r)
        if r.mobile:
            mobile_map.setdefault(r.mobile, []).append(r)
        if r.email:
            email_map.setdefault(r.email, []).append(r)
            
    # Load existing edges to avoid duplicates (undirected pair matching)
    existing_edges = set()
    for edge in db.query(IdentityEdge).all():
        pair = tuple(sorted([edge.source_record_a_id, edge.source_record_b_id]))
        existing_edges.add(pair)
        
    def _create_edges_for_group(group: List[SourceRecord], match_field: str):
        nonlocal new_edges
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                ra = group[i]
                rb = group[j]
                
                # We only match records across different source systems, or we can match within the same system if they are distinct records.
                # Standard MDM typically matches everything. We'll match everything.
                
                pair = tuple(sorted([ra.id, rb.id]))
                if pair not in existing_edges:
                    edge = IdentityEdge(
                        source_record_a_id=pair[0],
                        source_record_b_id=pair[1],
                        match_phase="deterministic",
                        confidence=1.0,
                        confidence_breakdown={
                            "matched_on": match_field,
                            "value": getattr(ra, match_field)
                        }
                    )
                    db.add(edge)
                    existing_edges.add(pair)
                    new_edges += 1

    # Generate edges
    for val, group in pan_map.items():
        if len(group) > 1:
            _create_edges_for_group(group, "pan")
            
    for val, group in mobile_map.items():
        if len(group) > 1:
            _create_edges_for_group(group, "mobile")
            
    for val, group in email_map.items():
        if len(group) > 1:
            _create_edges_for_group(group, "email")
            
    db.commit()
    logger.info(f"Deterministic matching complete. Created {new_edges} edges.")
    return new_edges

import logging
from sqlalchemy.orm import Session
from typing import List

from app.db.models.source_record import SourceRecord
from app.db.models.identity_edge import IdentityEdge

logger = logging.getLogger(__name__)

SEMANTIC_DISTANCE_THRESHOLD = 0.10  # Cosine distance <= 0.10 means similarity >= 0.90

def run_semantic_matching(db: Session) -> int:
    """
    Finds matches using pgvector cosine distance (<= 0.10 / similarity >= 0.90).
    Specifically targets unkeyed records (missing PAN, mobile, and email) that 
    couldn't be linked by deterministic means, checking them against all other records.
    """
    logger.info("Starting Phase 2 - Step 3: Semantic Vector Matching")
    new_edges = 0
    
    # 1. Identify unkeyed records
    unkeyed_records = db.query(SourceRecord).filter(
        SourceRecord.pan.is_(None),
        SourceRecord.mobile.is_(None),
        SourceRecord.email.is_(None),
        SourceRecord.vector_embedding.is_not(None)
    ).all()
    
    logger.info(f"Found {len(unkeyed_records)} unkeyed records to run semantic search against.")
    
    # 2. Load existing edges to avoid duplicates
    existing_edges = set()
    for edge in db.query(IdentityEdge).all():
        pair = tuple(sorted([edge.source_record_a_id, edge.source_record_b_id]))
        existing_edges.add(pair)
        
    for record in unkeyed_records:
        # Query pgvector for closest records
        # .cosine_distance() is provided by pgvector.sqlalchemy
        matches = db.query(SourceRecord).filter(
            SourceRecord.id != record.id,
            SourceRecord.vector_embedding.is_not(None),
            SourceRecord.vector_embedding.cosine_distance(record.vector_embedding) <= SEMANTIC_DISTANCE_THRESHOLD
        ).all()
        
        for match in matches:
            pair = tuple(sorted([record.id, match.id]))
            
            if pair not in existing_edges:
                # We need to calculate the actual distance in Python to store it, 
                # or just fetch it in the query. For simplicity, we just know it's <= threshold.
                # If we want exact score, we could compute it using numpy, or just log >=0.90
                
                edge = IdentityEdge(
                    source_record_a_id=pair[0],
                    source_record_b_id=pair[1],
                    match_phase="semantic_auto_merged",
                    confidence=0.90, # baseline
                    confidence_breakdown={
                        "semantic_match": True,
                        "vector_distance_threshold": SEMANTIC_DISTANCE_THRESHOLD
                    }
                )
                db.add(edge)
                existing_edges.add(pair)
                new_edges += 1
                
    db.commit()
    logger.info(f"Semantic matching complete. Created {new_edges} edges.")
    return new_edges

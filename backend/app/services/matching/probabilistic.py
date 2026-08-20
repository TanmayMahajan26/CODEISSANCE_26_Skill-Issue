import logging
from sqlalchemy.orm import Session
from typing import List
from rapidfuzz import fuzz

from app.db.models.source_record import SourceRecord
from app.db.models.identity_edge import IdentityEdge

logger = logging.getLogger(__name__)

# Configurable Weights (REQ-MATCH-02)
WEIGHTS = {
    "pan": 0.35,
    "mobile": 0.20,
    "email": 0.15,
    "name": 0.20,      # Combines string (0.12) + semantic (0.08) for simplicity in fuzzy step
    "dob": 0.05,
    "city": 0.03,
    "segment": 0.02
}

AUTO_MERGE_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.60

def run_probabilistic_matching(db: Session) -> int:
    """
    Evaluates pairs using weighted multi-attribute scoring.
    Generates IdentityEdge records for pairs meeting the threshold.
    Returns the number of new edges created.
    """
    logger.info("Starting Phase 2 - Step 2: Probabilistic Matching")
    new_edges = 0
    
    records = db.query(SourceRecord).all()
    
    # Load existing edges to avoid duplicates
    existing_edges = set()
    for edge in db.query(IdentityEdge).all():
        pair = tuple(sorted([edge.source_record_a_id, edge.source_record_b_id]))
        existing_edges.add(pair)
        
    for i in range(len(records)):
        ra = records[i]
        for j in range(i + 1, len(records)):
            rb = records[j]
            
            pair = tuple(sorted([ra.id, rb.id]))
            if pair in existing_edges:
                continue
                
            # Calculate score
            score = 0.0
            breakdown = {}
            
            # PAN (Exact)
            if ra.pan and rb.pan and ra.pan == rb.pan:
                score += WEIGHTS["pan"]
                breakdown["pan"] = WEIGHTS["pan"]
                
            # Mobile (Exact)
            if ra.mobile and rb.mobile and ra.mobile == rb.mobile:
                score += WEIGHTS["mobile"]
                breakdown["mobile"] = WEIGHTS["mobile"]
                
            # Email (Exact)
            if ra.email and rb.email and ra.email == rb.email:
                score += WEIGHTS["email"]
                breakdown["email"] = WEIGHTS["email"]
                
            # Name (Fuzzy)
            if ra.name and rb.name:
                name_sim = fuzz.ratio(ra.name.lower(), rb.name.lower()) / 100.0
                name_score = name_sim * WEIGHTS["name"]
                score += name_score
                breakdown["name"] = round(name_score, 3)
                
            # DOB (Exact)
            if ra.dob and rb.dob and ra.dob == rb.dob:
                score += WEIGHTS["dob"]
                breakdown["dob"] = WEIGHTS["dob"]
                
            # City (Fuzzy)
            if ra.city and rb.city:
                city_sim = fuzz.ratio(ra.city.lower(), rb.city.lower()) / 100.0
                city_score = city_sim * WEIGHTS["city"]
                score += city_score
                breakdown["city"] = round(city_score, 3)
                
            # Segment (Exact)
            if ra.segment and rb.segment and ra.segment == rb.segment:
                score += WEIGHTS["segment"]
                breakdown["segment"] = WEIGHTS["segment"]
                
            if score >= REVIEW_THRESHOLD:
                status = "AUTO_MERGED" if score >= AUTO_MERGE_THRESHOLD else "PENDING_REVIEW"
                # For IdentityEdge, we don't have a status column in the base schema, it's just 'match_phase'
                # Let's append the status to the phase name or confidence breakdown
                breakdown["status"] = status
                breakdown["total_score"] = round(score, 3)
                
                edge = IdentityEdge(
                    source_record_a_id=pair[0],
                    source_record_b_id=pair[1],
                    match_phase=f"probabilistic_{status.lower()}",
                    confidence=round(score, 3),
                    confidence_breakdown=breakdown
                )
                db.add(edge)
                existing_edges.add(pair)
                new_edges += 1

    db.commit()
    logger.info(f"Probabilistic matching complete. Created {new_edges} edges.")
    return new_edges

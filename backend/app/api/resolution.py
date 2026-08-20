from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, RoleChecker

from app.services.matching.deterministic import run_deterministic_matching
from app.services.matching.probabilistic import run_probabilistic_matching
from app.services.matching.semantic import run_semantic_matching
from app.services.matching.graph_clustering import run_graph_clustering
from app.services.golden_record_builder import build_golden_records
from app.db.models.golden_record import GoldenRecord

router = APIRouter()

# Role definitions
allow_admin = RoleChecker(["ADMIN"])
allow_all_roles = RoleChecker(["ADMIN", "MANAGER", "RM", "CREDIT_APPROVER"])

@router.post("/run", dependencies=[Depends(allow_admin)])
def run_resolution_pipeline(db: Session = Depends(get_db)):
    """
    Executes the full 3-phase matching and golden record builder pipeline.
    Requires ADMIN privileges.
    """
    # 1. Matching Engines (Phase 1, 2, 3 of Entity Resolution)
    det_edges = run_deterministic_matching(db)
    prob_edges = run_probabilistic_matching(db)
    sem_edges = run_semantic_matching(db)
    
    total_edges = det_edges + prob_edges + sem_edges
    
    # 2. Graph Clustering (Transitive Closure)
    clusters = run_graph_clustering(db)
    
    # 3. Golden Record Builder (Survivorship)
    golden_created = build_golden_records(db, clusters)
    
    return {
        "status": "success",
        "message": "Resolution pipeline completed successfully.",
        "metrics": {
            "edges_created": {
                "deterministic": det_edges,
                "probabilistic": prob_edges,
                "semantic": sem_edges,
                "total": total_edges
            },
            "clusters_found": len(clusters),
            "golden_records_created": golden_created
        }
    }

@router.get("/golden-records", dependencies=[Depends(allow_all_roles)])
def get_golden_records(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List golden records with basic info."""
    records = db.query(GoldenRecord).offset(skip).limit(limit).all()
    
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "total_relationship_value": r.total_relationship_value,
            "products_held": r.products_held,
            "source_systems": r.source_systems,
            "source_record_count": r.source_record_count,
            "match_confidence": r.match_confidence,
            "confidence_breakdown": r.confidence_breakdown,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })
    return result

@router.get("/golden-records/{record_id}", dependencies=[Depends(allow_all_roles)])
def get_golden_record(record_id: int, db: Session = Depends(get_db)):
    """Get detailed golden record including provenance and source records."""
    record = db.query(GoldenRecord).options(joinedload(GoldenRecord.source_records)).filter(GoldenRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Golden Record not found")
    
    source_records_list = []
    for sr in record.source_records:
        source_records_list.append({
            "id": sr.id,
            "source_system": sr.source_system,
            "name": sr.name,
            "dob": sr.dob,
            "pan": sr.pan,
            "email": sr.email,
            "mobile": sr.mobile,
            "city": sr.city,
            "segment": sr.segment,
            "account_value": sr.account_value,
            "products": sr.products,
        })
        
    return {
        "id": record.id,
        "total_relationship_value": record.total_relationship_value,
        "products_held": record.products_held,
        "source_systems": record.source_systems,
        "source_record_count": record.source_record_count,
        "match_confidence": record.match_confidence,
        "confidence_breakdown": record.confidence_breakdown,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "provenance": getattr(record, 'provenance', {}), # It's not in the model but let's check
        "source_records": source_records_list
    }

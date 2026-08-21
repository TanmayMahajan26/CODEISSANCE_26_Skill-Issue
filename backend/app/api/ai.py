from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.services.rag_engine import rag_engine
from app.api.deps import RoleChecker, get_db
from app.db.models.golden_record import GoldenRecord
from app.db.models.review_queue import ReviewQueueItem
from app.db.models.source_record import SourceRecord

router = APIRouter()

admin_only = RoleChecker(["ADMIN"])


@router.get("/health", summary="Test AI Connection")
async def ai_health_check(current_user=Depends(admin_only)):
    """Test the connection to the Groq LLM API. Must be called by an Admin."""
    response = await rag_engine.test_llm_connection()
    if response.startswith("ERROR"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response,
        )
    return {"status": "success", "response": response}


class NLQueryRequest(BaseModel):
    query: str


@router.post("/nl-query")
async def nl_query(request: NLQueryRequest, db: Session = Depends(get_db)):
    """Translate natural language query to filter params and fetch results."""
    filters = await rag_engine.translate_nl_query(request.query)
    
    # If AI is disabled or fails, use a mock response
    if "error" in filters or not filters:
        records = db.query(GoldenRecord).limit(3).all()
        return {
            "answer": "Since the AI service is currently disabled (API key missing), here is a mocked response showing recent customers.",
            "results": [{"id": r.id, "name": r.name, "city": r.city, "segment": r.segment} for r in records]
        }
        
    # Execute actual query based on translated filters (simplified for MVP)
    query = db.query(GoldenRecord)
    
    if "filters" in filters:
        f = filters["filters"]
        if "segment" in f:
            query = query.filter(GoldenRecord.segment == f["segment"])
        if "city" in f:
            query = query.filter(GoldenRecord.city.ilike(f"%{f['city']}%"))
            
    if "limit" in filters:
        query = query.limit(filters["limit"])
    else:
        query = query.limit(10)
        
    records = query.all()
    
    return {
        "answer": f"I found {len(records)} customers matching your query.",
        "results": [{"id": r.id, "name": r.name, "city": r.city, "segment": r.segment} for r in records]
    }


@router.post("/explain-match/{golden_id}")
async def explain_match(golden_id: int, db: Session = Depends(get_db)):
    """Generate AI explanation for why source records were merged into this golden record."""
    gr = db.query(GoldenRecord).filter(GoldenRecord.id == golden_id).first()
    if not gr:
        raise HTTPException(status_code=404, detail="Golden Record not found")

    # Gather source records for context
    source_records = db.query(SourceRecord).filter(
        SourceRecord.golden_record_id == golden_id
    ).all()

    source_data = [
        {"id": sr.id, "source_system": sr.source_system, "name": sr.name,
         "pan": sr.pan, "mobile": sr.mobile, "email": sr.email, "city": sr.city}
        for sr in source_records
    ]

    explanation = await rag_engine.explain_match(
        golden_record_data={
            "name": gr.name,
            "pan": gr.pan,
            "city": gr.city,
            "trv": float(gr.total_relationship_value or 0),
            "source_systems": gr.source_systems,
            "provenance": gr.provenance,
        },
        source_records=source_data,
    )
    return {"golden_record_id": golden_id, "explanation": explanation}


@router.post("/explain-opportunity/{opportunity_id}")
async def explain_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    """Generate AI explanation for an opportunity recommendation."""
    from app.db.models.opportunity import Opportunity

    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    gr = db.query(GoldenRecord).filter(GoldenRecord.id == opp.golden_record_id).first()

    explanation = await rag_engine.explain_opportunity(
        golden_record_data={
            "name": gr.name if gr else "Unknown",
            "trv": float(gr.total_relationship_value or 0) if gr else 0,
            "products_held": gr.products_held if gr else [],
            "segment": gr.segment if gr else None,
        },
        opportunity_data={
            "product_category": opp.product_category,
            "product_name": opp.product_name,
            "score": opp.score,
            "score_breakdown": opp.score_breakdown,
        },
    )

    # Persist the explanation
    opp.explanation = explanation
    db.commit()

    return {"opportunity_id": opportunity_id, "explanation": explanation}


@router.post("/suggest-resolution/{review_id}")
async def suggest_resolution(review_id: int, db: Session = Depends(get_db)):
    """AI-powered suggestion for a review queue item."""
    item = db.query(ReviewQueueItem).filter(ReviewQueueItem.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review Item not found")

    # Fetch the two source records
    record_a = db.query(SourceRecord).filter(SourceRecord.id == item.source_record_a_id).first()
    record_b = db.query(SourceRecord).filter(SourceRecord.id == item.source_record_b_id).first()

    suggestion = await rag_engine.suggest_conflict_resolution(
        record_a={"id": record_a.id, "name": record_a.name, "pan": record_a.pan,
                   "mobile": record_a.mobile, "email": record_a.email,
                   "source_system": record_a.source_system} if record_a else {"id": "unknown"},
        record_b={"id": record_b.id, "name": record_b.name, "pan": record_b.pan,
                   "mobile": record_b.mobile, "email": record_b.email,
                   "source_system": record_b.source_system} if record_b else {"id": "unknown"},
        match_score=item.match_score,
    )

    # Save the AI suggestion
    item.ai_suggestions = suggestion
    db.commit()

    return {"review_id": review_id, "suggestion": suggestion}

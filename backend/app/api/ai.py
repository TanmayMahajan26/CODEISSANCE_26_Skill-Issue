from fastapi import APIRouter, Depends, HTTPException, status
from app.services.rag_engine import rag_engine
from app.api.deps import RoleChecker

router = APIRouter()

# For health check, we can restrict to MANAGER or ADMIN
# or make it public if we just want to test locally. 
# We'll secure it with RoleChecker for ADMIN to be safe.
admin_only = RoleChecker(["ADMIN"])


@router.get("/health", summary="Test AI Connection")
async def ai_health_check(current_user=Depends(admin_only)):
    """
    Test the connection to the Groq LLM API.
    Must be called by an Admin.
    """
    response = await rag_engine.test_llm_connection()
    if response.startswith("ERROR"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response,
        )
    return {"status": "success", "response": response}

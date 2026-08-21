"""
Nexus360 — Health Check Endpoint.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns application health status including database connectivity.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {exc}"

    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.post("/reset-demo", summary="Reset Demo Data")
async def reset_demo_data():
    """
    Safely resets the database to the original seeded hackathon demo state.
    """
    import subprocess
    import os
    
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "seed_demo_data.py")
    script_path = os.path.abspath(script_path)
    
    try:
        # Run the seed script
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "message": "Demo data reset successfully.", "logs": result.stdout}
    except subprocess.CalledProcessError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to reset demo data: {e.stderr}")

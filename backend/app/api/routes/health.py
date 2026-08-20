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

from fastapi import FastAPI
from app.core.config import get_settings
from app.api import auth, ingest

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="IdentityForge - Financial Customer 360 & Next-Best-Opportunity Engine",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.APP_NAME}

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingestion"])

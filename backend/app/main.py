from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api import auth, ingest, ai, resolution, customers, opportunities, dashboard, config, audit, review, demo

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Kovi - Financial Customer 360 & Next-Best-Opportunity Engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.APP_NAME}

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingestion"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(resolution.router, prefix="/api/resolution", tags=["resolution"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(review.router, prefix="/api/review", tags=["review"])

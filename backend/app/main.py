"""
Nexus360 — FastAPI Application Entry Point.

Registers all API routers, configures secure CORS, logging, and lifespan
events (DB table creation, default user seeding, BRE seeding, and ML embedding initialization).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, async_session_factory, Base

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401

# Import routers
from app.api.routes import (
    health,
    auth,
    ingestion,
    matching,
    customers,
    reviews,
    config,
    audit,
    opportunities,
    ai,
    market,
    communications,
    verification,
)
from app.services.config_service import seed_default_config_rules
from app.services.auth_service import seed_default_users
from app.services.embedding_service import init_embedding_service

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables, seed default demo users & BRE rules on startup (idempotent)."""
    logger.info("Starting %s v%s in [%s] mode", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    # ── Production Security Guard ──────────────────────────────────
    if settings.ENVIRONMENT == "production":
        default_secret = "nexus360-hackathon-super-secret-jwt-key-2026-financial-ai"
        if not settings.SECRET_KEY or settings.SECRET_KEY == default_secret or len(settings.SECRET_KEY) < 32:
            raise ValueError(
                "FATAL PRODUCTION SECURITY MISCONFIGURATION: SECRET_KEY is missing, too short, "
                "or using the default development placeholder. Please configure a unique 32+ character "
                "SECRET_KEY in production."
            )

    # Non-blocking DB table & seed check (so HTTP server starts instantly)
    async def init_db_async():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                try:
                    from sqlalchemy import text
                    await conn.execute(text("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'COMMUNICATION_SENT';"))
                except Exception:
                    pass
            
            async with async_session_factory() as session:
                await seed_default_config_rules(session)
                await seed_default_users(session)
                await session.commit()
            logger.info("Database tables and seed data ready")
        except Exception as db_err:
            logger.warning("Background DB init notice: %s", db_err)

    import asyncio
    asyncio.create_task(init_db_async())

    # Initialize local ML Embedding service (sentence-transformers)
    init_embedding_service()

    logger.info("Database tables, BRE rules, and ML Embedding Service ready")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await engine.dispose()


# ── FastAPI app ──────────────────────────────────────────────────
docs_url = "/docs" if settings.ENVIRONMENT != "production" or settings.DEBUG else None
redoc_url = "/redoc" if settings.ENVIRONMENT != "production" or settings.DEBUG else None

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered Customer Identity Resolution & Next-Best-Opportunity platform. "
        "Resolves duplicate customer identities across Equity, Mutual Funds, "
        "Insurance, Loans, and Wealth Management systems."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ────────────────────────────────────────────
API_V1 = "/api/v1"

app.include_router(health.router, prefix=API_V1)
app.include_router(auth.router, prefix=API_V1)
app.include_router(ingestion.router, prefix=API_V1)
app.include_router(matching.router, prefix=API_V1)
app.include_router(customers.router, prefix=API_V1)
app.include_router(reviews.router, prefix=API_V1)
app.include_router(config.router, prefix=API_V1)
app.include_router(audit.router, prefix=API_V1)
app.include_router(opportunities.router, prefix=API_V1)
app.include_router(market.router, prefix=API_V1)
app.include_router(communications.router, prefix=API_V1)
app.include_router(ai.router, prefix=API_V1)
app.include_router(verification.router, prefix=API_V1)


@app.get("/", tags=["Root"])
async def root():
    """Landing page — redirects to docs or health status."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": docs_url or "disabled in production",
        "health": f"{API_V1}/health",
        "auth": f"{API_V1}/auth/login",
    }

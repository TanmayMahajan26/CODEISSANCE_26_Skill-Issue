"""
Nexus360 — Core Configuration Module.

Loads application settings from environment variables via pydantic-settings.
Default thresholds and weights aligned with PRD v3.0 §5.2 and §10.1.
Includes Security, JWT, CORS, and Upload limits for production readiness.
"""

from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from .env file."""

    # ── Application & Environment ────────────────────────────────
    APP_NAME: str = "Nexus360"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # "development" | "staging" | "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Security & Authentication ────────────────────────────────
    SECRET_KEY: str = "nexus360-hackathon-super-secret-jwt-key-2026-financial-ai"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── CORS Settings ────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]

    # ── File Upload / Ingestion Limits ───────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_INGESTION_ROWS: int = 25000

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nexus360"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/nexus360"
    DB_SSL_VERIFY: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        """Ensure DATABASE_URL uses the asyncpg driver prefix."""
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ── Matching Thresholds (0.0 to 1.0) ─────────────────────────
    MATCH_THRESHOLD: float = 0.85
    REVIEW_THRESHOLD: float = 0.60

    # ── Matching Weights (must sum to 1.0) ───────────────────────
    WEIGHT_PAN: float = 0.35
    WEIGHT_MOBILE: float = 0.20
    WEIGHT_EMAIL: float = 0.15
    WEIGHT_NAME: float = 0.12
    WEIGHT_NAME_SEMANTIC: float = 0.08
    WEIGHT_DOB: float = 0.05
    WEIGHT_CITY: float = 0.03
    WEIGHT_SEGMENT: float = 0.02

    # ── Source Precedence (highest → lowest) ─────────────────────
    SOURCE_PRECEDENCE: List[str] = [
        "WEALTH",
        "MUTUAL_FUND",
        "EQUITY",
        "INSURANCE",
        "LOAN",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

"""
Nexus360 — Database Engine & Session Management.

Provides async SQLAlchemy engine, session factory, and Base declarative class.
Supports local PostgreSQL and remote Supabase PostgreSQL with configurable SSL verification.
"""

import ssl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── SQLite Compatibility Compilers for PostgreSQL Dialects ────────────────
from sqlalchemy.ext.compiler import compiles
try:
    from sqlalchemy.dialects.postgresql import JSONB, ARRAY
    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

    @compiles(ARRAY, "sqlite")
    def compile_array_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass

# Pass ssl context in connect_args if connecting to a remote PostgreSQL database (such as Supabase)
connect_args = {}
if "sqlite" not in settings.DATABASE_URL and "localhost" not in settings.DATABASE_URL and "127.0.0.1" not in settings.DATABASE_URL:
    ctx = ssl.create_default_context()
    if not settings.DB_SSL_VERIFY:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    else:
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
    connect_args["ssl"] = ctx

engine_args = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}
if "sqlite" not in settings.DATABASE_URL:
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20
    engine_args["connect_args"] = connect_args

engine = create_async_engine(settings.DATABASE_URL, **engine_args)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

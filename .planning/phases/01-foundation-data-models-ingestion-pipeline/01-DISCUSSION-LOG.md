# Phase 1: Foundation, Data Models & Ingestion Pipeline - Discussion Log

## Database bootstrapping strategy
**Options presented:**
- Alembic migrations
- Raw SQL init scripts

**User selected:** Alembic migrations
**Notes:** Provides version control and repeatable deployments.

## Synthetic data generation timing
**Options presented:**
- Auto-loaded on startup
- Explicit `/api/ingest/seed` call

**User selected:** Explicit `/api/ingest/seed` call
**Notes:** Cleaner architecture, controlled demo flow.

## Local development environment
**Options presented:**
- Full docker-compose stack
- Direct connection to remote Supabase+Upstash

**User selected:** Direct connection to remote Supabase+Upstash
**Notes:** Faster to get started; services already provisioned. No docker-compose overhead.

## Embedding computation strategy
**Options presented:**
- Synchronous during ingestion
- Async background task queue

**User selected:** Synchronous during ingestion
**Notes:** Simpler, blocks on batch upload but acceptable for ~600 records at hackathon scale.

## General Guidance
**User selected:**
- Use the existing PRD and implementation plan as the single source of truth.
- Optimize for a polished 24-hour hackathon MVP.
- Use FastAPI, PostgreSQL, Alembic, pgvector, Redis, explicit /api/ingest/seed data loading, synchronous embedding generation, JWT authentication with RBAC, configurable matching rules, and a modular service-oriented architecture.
- Prioritize delivering a complete vertical slice that satisfies the judging criteria.
- Defer optional features unless all core requirements are complete.

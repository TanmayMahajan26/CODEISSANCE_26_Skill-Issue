# Phase 1 Context: Foundation, Data Models & Ingestion Pipeline

**Domain:** Establish the core backend infrastructure, database schemas with pgvector extension, JWT authentication, immutable audit logger, and data normalization pipeline with 384-dimensional vector embeddings.

## Decisions

### Database Bootstrapping
- **Decision:** Use Alembic (SQLAlchemy migrations) for schema management.
- **Rationale:** Provides version control and repeatable deployments.

### Synthetic Data Generation Timing
- **Decision:** Explicit `/api/ingest/seed` endpoint call.
- **Rationale:** Cleaner architecture, controlled demo flow (not auto-loaded on startup).

### Local Development Environment
- **Decision:** Direct connection to remote Supabase + Upstash from day 1.
- **Rationale:** No docker-compose overhead; faster to get started; services already provisioned.

### Embedding Computation Strategy
- **Decision:** Synchronous during ingestion.
- **Rationale:** Simpler, no background task queue. Acceptable for ~600 records at hackathon scale.

### General Implementation Guidance
- **Decision:** PRD + `implementation_plan.md` are the single source of truth. Optimize for a polished 24-hour hackathon MVP.
- **Rationale:** Ensure delivery of a complete vertical slice satisfying all judging criteria. Defer optional features until core requirements are complete. Modular service-oriented architecture.

## Prior Context Carried Forward
- **Tech stack:** FastAPI + Supabase PostgreSQL + pgvector + Upstash Redis.
- **Schemas:** 8 database tables (source_records, golden_records, identity_edges, opportunities, config_rules, audit_logs, review_queue, users).
- **Security:** JWT auth with bcrypt (cost 12), access token 30m, refresh 7d.
- **Data Normalization:** PAN regex, mobile prefix stripping, city aliases, name title removal.
- **AI/Embeddings:** `all-MiniLM-L6-v2` (384-dim).
- **Scale:** Synthetic data generator for ~250 customers, ~600 source records, 6 pre-seeded users.

## Canonical References
- `PRD.md`
- `implementation_plan.md`

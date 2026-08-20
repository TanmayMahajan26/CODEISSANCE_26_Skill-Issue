# Phase 1 Research: Foundation, Data Models & Ingestion Pipeline

## Objective
Establish the core backend infrastructure, database schemas (with pgvector), JWT auth, audit logging, and data normalization/ingestion pipeline with 384-dim embeddings.

## Technical Context & Decisions
Based on `01-CONTEXT.md`, the following implementation decisions are locked:
1. **Database:** Supabase PostgreSQL with `pgvector` extension.
2. **Schema Management:** SQLAlchemy ORM with Alembic migrations.
3. **Synthetic Data:** Explicit `/api/ingest/seed` endpoint (not auto-loaded).
4. **Local Dev:** Direct connection to remote Supabase + Upstash from Day 1.
5. **Embeddings:** Synchronous computation during ingestion using `all-MiniLM-L6-v2` (384 dimensions).

## Core Requirements & Implementation Strategies

### 1. Database & Models (Alembic + SQLAlchemy + pgvector)
We need to define 8 database tables. For Phase 1, we must focus on the foundation, but defining the full schema now ensures the migrations are correct.
- `users`: ID, email, password_hash, role (RM, MANAGER, ADMIN, CREDIT_APPROVER), created_at, updated_at.
- `audit_logs`: ID, actor_id, action_type, entity_type, entity_id, old_value (JSONB), new_value (JSONB), ip_address, timestamp.
- `source_records`: ID, source_system, source_id, pan, mobile, email, name, dob, city, segment, metadata (JSONB), vector_embedding (vector(384)), created_at, updated_at.
- (Other tables like `golden_records`, `identity_edges`, `opportunities`, `config_rules`, `review_queue` should be stubbed or fully defined based on the PRD).
**Dependencies:** `sqlalchemy`, `alembic`, `psycopg2-binary`, `pgvector`.

### 2. JWT Authentication & RBAC (REQ-SEC-01)
- **Library:** `passlib[bcrypt]` (cost=12), `python-jose[cryptography]`.
- **Flow:** `/api/auth/login`, `/api/auth/me`, `/api/auth/refresh`.
- **RBAC:** A FastAPI dependency `get_current_user(required_roles=[...])` to enforce role-based access.

### 3. Data Normalization & Ingestion (REQ-INGEST-01, REQ-INGEST-02)
- Need standardizing functions for:
  - PAN: Regex validation, uppercase.
  - Mobile: Strip prefixes (e.g., +91), ensure 10 digits.
  - Email: Lowercase, trim.
  - Name: Strip titles (Mr., Mrs., Dr.), expand initials if possible (or just trim).
  - Date: Standardize to ISO format.
  - City: Normalize aliases (e.g., Bombay -> Mumbai).
- **Ingestion Pipeline:** 
  - Endpoint for CSV/JSON upload.
  - Apply standardizer.
  - Generate embeddings.
  - Insert into `source_records`.

### 4. Vector Embeddings (REQ-INGEST-03)
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`.
- **Dimensionality:** 384.
- **Input text:** `<name> | <city> | <segment>`.
- **Strategy:** Computed synchronously during ingestion.
- **Dependencies:** `sentence-transformers`, `torch`.

### 5. Audit Logger (REQ-AUD-01)
- A utility or SQLAlchemy event listener that writes to `audit_logs` whenever a privileged action or configuration change occurs.

## Codebase Architecture
- `app/main.py`: FastAPI application entrypoint.
- `app/api/...`: Route handlers.
- `app/core/config.py`: Environment variables (Supabase URI, Upstash URI, JWT secret).
- `app/core/security.py`: Password hashing and JWT generation.
- `app/db/session.py`: SQLAlchemy engine and sessionmaker.
- `app/db/models/...`: SQLAlchemy models.
- `app/services/...`: Business logic (Ingestion, Standardization, Embeddings).
- `app/schemas/...`: Pydantic models for request/response validation.
- `alembic/`: Migration scripts.

## Potential Blockers & Risks
- **sentence-transformers load time:** Loading the ML model on startup or first request can be slow. It should be loaded globally once at application startup.
- **Synchronous embedding latency:** For ~600 records, synchronous generation might take a few seconds, which is acceptable for a hackathon demo but needs proper batching logic in the script.
- **Supabase pgvector:** Ensure the migration explicitly executes `CREATE EXTENSION IF NOT EXISTS vector;` before defining tables with `Vector` types.

## Validation Architecture
- Create `01-VALIDATION.md` outlining exactly how to test these requirements.
- We need tests to verify vector dimensionality, regex standardizations, JWT token issuance, and Alembic migration application.

## RESEARCH COMPLETE

---
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - app/main.py
  - app/core/config.py
  - app/db/session.py
  - app/db/models/base.py
  - app/db/models/user.py
  - app/db/models/audit.py
  - app/db/models/source_record.py
  - alembic.ini
  - alembic/env.py
autonomous: true
requirements: REQ-AUD-01
---

# Plan 1: Foundation & Database Schemas

## Objective
Establish the FastAPI foundation and configure SQLAlchemy with Alembic for database migrations. Define the base tables needed for Phase 1.

## Must Haves
- truths:
  - Database is Supabase PostgreSQL with `pgvector` extension.
  - Schema migrations are handled by Alembic.
  - Direct connection to remote Supabase via `DATABASE_URL` (no docker-compose overhead).

## Tasks

### 1. Initialize FastAPI Project & Config
- **`<read_first>`**: `app/main.py`, `app/core/config.py`
- **`<action>`**: Create a standard FastAPI application entry point in `app/main.py`. Define environment variables in `app/core/config.py` using `pydantic-settings` to load `DATABASE_URL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, and `JWT_SECRET`.
- **`<acceptance_criteria>`**: `uvicorn app.main:app` starts successfully and serves the `/docs` endpoint.

### 2. Configure SQLAlchemy and Alembic
- **`<read_first>`**: `app/db/session.py`, `alembic.ini`, `alembic/env.py`
- **`<action>`**: Set up SQLAlchemy engine and session maker in `app/db/session.py` using the `DATABASE_URL`. Initialize Alembic with `alembic init alembic`. Modify `alembic/env.py` to point to the SQLAlchemy Base and use the config from `app/core/config.py`.
- **`<acceptance_criteria>`**: `alembic revision --autogenerate` runs successfully without errors.

### 3. Define Base Database Models
- **`<read_first>`**: `app/db/models/user.py`, `app/db/models/audit.py`, `app/db/models/source_record.py`
- **`<action>`**: Create SQLAlchemy models:
  - `User`: id, email, password_hash, role.
  - `AuditLog`: id, actor_id, action_type, entity_type, entity_id, old_value (JSON), new_value (JSON), timestamp. (Satisfies REQ-AUD-01 schema requirement).
  - `SourceRecord`: id, source_system, source_id, pan, mobile, email, name, dob, city, segment, vector_embedding (`Vector(384)`).
- **`<acceptance_criteria>`**: Models are successfully imported into `alembic/env.py`.

### 4. [BLOCKING] Schema Push
- **`<read_first>`**: `alembic.ini`
- **`<action>`**: Generate the initial migration script and execute `alembic upgrade head` to push the schema to the database. Include `CREATE EXTENSION IF NOT EXISTS vector;` in the initial migration script before table creation.
- **`<acceptance_criteria>`**: Tables `users`, `audit_logs`, and `source_records` exist in the connected PostgreSQL database.

## Verification
- Run `alembic check` or equivalent to ensure migrations are in sync.
- Execute unit tests ensuring models can be instantiated.

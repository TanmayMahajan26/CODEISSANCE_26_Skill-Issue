---
wave: 3
depends_on: ["1-01"]
files_modified:
  - app/services/standardizer.py
  - app/services/embeddings.py
  - app/services/ingestion.py
  - app/api/ingest.py
  - app/schemas/ingest.py
  - app/main.py
autonomous: true
requirements: REQ-INGEST-01, REQ-INGEST-02, REQ-INGEST-03
---

# Plan 3: Ingestion Pipeline & Embeddings

## Objective
Build the data normalization and ingestion pipeline. Standardize source records and synchronously compute 384-dimensional embeddings before storing them in the `source_records` table.

## Must Haves
- truths:
  - Embeddings use `all-MiniLM-L6-v2`.
  - Embeddings are generated synchronously during ingestion.
  - A synthetic data generator endpoint `/api/ingest/seed` explicitly loads the data.

## Tasks

### 1. Data Standardization Service
- **`<read_first>`**: `app/services/standardizer.py`
- **`<action>`**: Create `StandardizerService` with methods:
  - `clean_pan(pan: str) -> str`: regex validation, uppercase.
  - `clean_mobile(mobile: str) -> str`: strip non-digits and prefixes (+91, 0), return 10-digit number.
  - `clean_email(email: str) -> str`: lowercase and strip whitespace.
  - `clean_name(name: str) -> str`: strip common titles (Mr., Mrs., Dr.) and extra spaces.
  - `clean_city(city: str) -> str`: normalize aliases (e.g., Bombay -> Mumbai).
- **`<acceptance_criteria>`**: `pytest` passes with various edge cases for PAN, mobile, email, and names.

### 2. Embeddings Service
- **`<read_first>`**: `app/services/embeddings.py`
- **`<action>`**: Create `EmbeddingService` using `sentence-transformers` with model `all-MiniLM-L6-v2`. Initialize the model globally to avoid reloading. Provide a method `generate_embedding(text: str) -> list[float]` which returns a 384-dimensional float array.
- **`<acceptance_criteria>`**: `generate_embedding("Test String")` returns a list of 384 floats.

### 3. Ingestion & Seeding Logic
- **`<read_first>`**: `app/schemas/ingest.py`, `app/services/ingestion.py`
- **`<action>`**: Create `IngestRecord` schema. In `IngestionService`, create a method to accept a list of records. For each record:
  - Standardize fields using `StandardizerService`.
  - Construct embedding input string: `<name> | <city> | <segment>`.
  - Generate embedding using `EmbeddingService`.
  - Insert into `source_records` database table.
  Create a `seed_synthetic_data` method that generates ~250 mock customers across 5 source systems and passes them to the ingestion logic.
- **`<acceptance_criteria>`**: `seed_synthetic_data` successfully inserts valid rows with 384-dim embeddings into the `source_records` table.

### 4. API Endpoints
- **`<read_first>`**: `app/api/ingest.py`, `app/main.py`
- **`<action>`**: Implement `POST /api/ingest/seed` (triggers synthetic generation and DB insert) and `POST /api/ingest/upload` (accepts JSON list of `IngestRecord`s). Register router in `main.py`.
- **`<acceptance_criteria>`**: Calling `POST /api/ingest/seed` returns a success message indicating records were inserted.

## Verification
- Invoke the seed endpoint.
- Connect to PostgreSQL directly and verify the vector dimensions and data standardization visually.

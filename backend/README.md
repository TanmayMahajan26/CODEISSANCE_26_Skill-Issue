# Nexus360

**AI-powered Customer Identity Resolution & Next-Best-Opportunity Platform**

Nexus360 resolves duplicate customer identities across five independent financial business systems: Equity, Mutual Funds, Insurance, Loans, and Wealth Management.

---

## Architecture

```
CSV Upload → Schema Validation → Record Storage → Normalization
    → Candidate Blocking → Deterministic Matching
    → Fuzzy Feature Extraction → Weighted Scoring → Decision Engine
        → MATCH    → Link to Golden Customer
        → REVIEW   → Manual Review Queue
        → NON_MATCH → New Golden Customer
```

## Tech Stack

| Layer        | Technology                          |
|-------------|-------------------------------------|
| API         | FastAPI (async)                     |
| Database    | PostgreSQL + SQLAlchemy (async)     |
| Migrations  | Alembic                             |
| Matching    | RapidFuzz + custom scoring engine   |
| Validation  | Pydantic v2                         |
| Data        | Pandas                              |

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+

### 2. Set Up PostgreSQL

```sql
-- Connect to PostgreSQL and run:
CREATE DATABASE nexus360;
```

### 3. Configure Environment

```bash
cd backend
copy .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 4. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Generate Seed Data

```bash
cd backend
python -m scripts.seed_data
```

This creates CSV files in `scripts/data/` with 100+ synthetic records.

### 6. Start the Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access Swagger Docs

Open: **http://localhost:8000/docs**

---

## API Endpoints

| Method | Endpoint                          | Description                   |
|--------|-----------------------------------|-------------------------------|
| GET    | `/api/v1/health`                 | Health check                  |
| POST   | `/api/v1/ingest`                 | Upload CSV records            |
| GET    | `/api/v1/source-records`         | List source records           |
| POST   | `/api/v1/matching/run`           | Run matching pipeline         |
| GET    | `/api/v1/matching/decisions`     | List match decisions          |
| GET    | `/api/v1/matching/decisions/{id}`| Get a match decision          |
| GET    | `/api/v1/customers`             | List golden customers         |
| GET    | `/api/v1/customers/{id}`        | Get customer with sources     |
| GET    | `/api/v1/reviews`               | List review cases             |
| POST   | `/api/v1/reviews/{id}/approve`  | Approve a review              |
| POST   | `/api/v1/reviews/{id}/reject`   | Reject a review               |

---

## Typical Workflow

```bash
# 1. Generate seed data
python -m scripts.seed_data

# 2. Start the server
uvicorn app.main:app --reload

# 3. Ingest data (one file per system)
curl -X POST http://localhost:8000/api/v1/ingest \
     -F "source_system=EQUITY" \
     -F "file=@scripts/data/equity_records.csv"

curl -X POST http://localhost:8000/api/v1/ingest \
     -F "source_system=MUTUAL_FUND" \
     -F "file=@scripts/data/mutual_fund_records.csv"

# ... repeat for INSURANCE, LOAN, WEALTH

# 4. Run matching
curl -X POST http://localhost:8000/api/v1/matching/run

# 5. View results
curl http://localhost:8000/api/v1/customers
curl http://localhost:8000/api/v1/matching/decisions
curl http://localhost:8000/api/v1/reviews
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── core/
│   │   ├── config.py            # Settings from environment
│   │   └── database.py          # Async SQLAlchemy engine & session
│   ├── models/
│   │   ├── source_record.py     # Source record ORM model
│   │   ├── golden_customer.py   # Golden customer ORM model
│   │   ├── identity_link.py     # Source ↔ Golden link model
│   │   ├── match_decision.py    # Pairwise match decision model
│   │   ├── review_case.py       # Manual review case model
│   │   └── attribute_history.py # Survivorship audit trail
│   ├── schemas/
│   │   ├── source_record.py     # Ingestion request/response schemas
│   │   ├── golden_customer.py   # Customer response schemas
│   │   ├── matching.py          # Feature vector & score schemas
│   │   └── review.py            # Review action schemas
│   ├── api/routes/
│   │   ├── health.py            # Health check endpoint
│   │   ├── ingestion.py         # CSV upload & record listing
│   │   ├── matching.py          # Matching pipeline trigger
│   │   ├── customers.py         # Golden customer CRUD
│   │   └── reviews.py           # Review approve/reject
│   ├── services/
│   │   ├── ingestion_service.py       # CSV parsing & validation
│   │   ├── normalization_service.py   # Record normalization
│   │   ├── matching_service.py        # Pipeline orchestration
│   │   ├── golden_record_service.py   # Golden customer CRUD
│   │   └── review_service.py          # Review resolution
│   ├── matching/
│   │   ├── deterministic.py     # High-confidence matching rules
│   │   ├── blocking.py          # Candidate pair generation
│   │   ├── fuzzy.py             # RapidFuzz feature extraction
│   │   ├── features.py          # Feature engineering
│   │   └── scoring.py           # Weighted scoring engine
│   └── utils/
│       └── normalization.py     # Name, mobile, email, PAN, city normalizers
├── scripts/
│   └── seed_data.py             # Synthetic data generator
├── tests/
│   ├── test_normalization.py    # Normalization unit tests
│   └── test_matching.py         # Matching engine unit tests
├── requirements.txt
├── .env.example
├── .env
├── alembic.ini
└── README.md
```

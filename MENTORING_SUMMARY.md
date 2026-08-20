# IdentityForge — Project Status & Mentoring Guide

## 1. High-Level Pitch (The "Elevator Pitch")
> **Problem:** Banks and financial institutions store customer information across isolated silos (Equity Trading, Mutual Funds, Insurance, Personal Loans, Wealth Management). A single customer often has different emails, outdated addresses, or missing PANs across systems. Because data is disconnected, banks miss cross-sell opportunities, risk compliance errors, and cannot get a unified Customer 360 view.
>
> **Our Solution (IdentityForge):** An AI-powered Financial Customer 360 & Next-Best-Opportunity Engine. We ingest siloed data, standardize it, run a 3-tier entity resolution engine (Deterministic, Probabilistic fuzzy matching, and pgvector Semantic AI matching) to build trusted "Golden Customer Records", and use an LLM RAG engine to explain why records match and recommend personalized financial products.

---

## 2. What We Have Built & Verified So Far

### A. Database & Enterprise Foundation
* **PostgreSQL + pgvector**: Set up on Supabase with vector extensions enabled for fast AI semantic similarity search.
* **Full Data Architecture**:
  * `source_records`: Ingests raw data from 5 financial divisions.
  * `golden_records`: Master customer profiles with full attribute-level JSONB provenance (tracking which bank system provided each data field).
  * `identity_edges`: Graph-based match relationships with confidence scores and breakdown.
  * `audit_logs`: Immutable audit logging for regulatory compliance and enterprise security.
  * `users` & RBAC: Role-based access control (Relationship Managers, Managers, Admins, Approvers) secured with JWT tokens & bcrypt password hashing.

### B. Ingestion & Data Standardization Pipeline
* **Normalizers**: Built automated data cleaning pipelines:
  * **PAN**: Regex verification & uppercase formatting.
  * **Mobile**: Indian 10-digit normalization (stripping `+91`, `0`, spaces).
  * **Email & Name**: Trimming, lowercase conversion, title removal.
  * **City Aliases**: Canonical mapping of city names.
* **AI Embeddings (384-dimensional)**:
  * Integrated `sentence-transformers` (`all-MiniLM-L6-v2`) locally to compute vector representations of normalized profiles (`name + city + segment`).
  * Embedded directly into the database for pgvector search.
* **Idempotent Data Seeder (`/api/ingest/seed`)**:
  * Generates realistic synthetic customer data across all 5 financial systems.
  * **Idempotent**: Running the seeder multiple times does not create duplicates; it skips existing records cleanly.
  * Generates an audit log and returns detailed metrics (`customers_created`, `embeddings_generated`, `duplicates_skipped`).
  * **Status:** Tested & 100% verified passing.

### C. AI Agent & LLM Orchestration
* **LangChain + Groq Integration**:
  * Set up `RagEngine` service communicating with high-speed LLMs on Groq.
  * Configured active LLM model (`openai/gpt-oss-20b`) for rapid reasoning.
  * Verified live connectivity via authenticated `/api/ai/health` endpoint.
* **Graph & Fuzzy Libraries**: Installed and configured `NetworkX` (for graph-based transitive closure clustering) and `RapidFuzz` (for Levenshtein string distance scoring).

---

## 3. Architecture of the 3-Tier Identity Resolution Engine
*(What we are executing right now in Phase 2)*

```
[ Siloed Source Records (Equity, MF, Insurance, Loans, Wealth) ]
                               │
                               ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 1. Deterministic Match: Exact PAN, Mobile, Email (Conf: 1.0)│
 └─────────────────────────────┬───────────────────────────────┘
                               │
 ┌─────────────────────────────▼───────────────────────────────┐
 │ 2. Probabilistic Match: Weighted multi-attribute scoring    │
 │    (Levenshtein Name, DOB, City, Segment)                   │
 └─────────────────────────────┬───────────────────────────────┘
                               │
 ┌─────────────────────────────▼───────────────────────────────┐
 │ 3. Semantic AI Discovery: pgvector cosine similarity search │
 │    (Catches typos & unkeyed records with >= 90% similarity) │
 └─────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
             [ NetworkX Graph Transitive Closure ]
             (Links A=B and B=C into unified Cluster)
                               │
                               ▼
        [ Golden Record Builder + Survivorship Rules ]
        (Picks latest/highest quality data + calculates
         Total Relationship Value & Product Portfolio)
```

---

## 4. Key Talking Points for Mentors

1. **Why is our solution unique?**
   * Most matching systems only do exact matches (deterministic) or basic fuzzy matching. We combine **Exact + Probabilistic + AI Vector Semantic (pgvector)** search.
   * We don't just merge data into a black box: we provide **Attribute-Level Provenance** (we can prove which source system each phone number or address came from).

2. **Enterprise Ready & Compliant:**
   * Immutable **Audit Logging** tracking every data ingestion and resolution event.
   * **Role-Based Access Control (RBAC)** ensuring Relationship Managers only see their assigned customers, with sensitive field masking.

3. **Performance & Scalability:**
   * Fast vector similarity using **pgvector** inside PostgreSQL instead of separate heavy vector DBs.
   * Sub-second LLM inference via **Groq** for real-time natural language explanations.

---

## 5. Current Progress & Immediate Next Steps
* **Completed:** Phase 1 (Database, Ingestion, Standardization, Embeddings, Auth, Seeding, Audit Logging) + LangChain AI Service setup.
* **In Progress:** Phase 2 (Completing the 3-phase matching runner & transitive closure graph compilation).
* **Next on Roadmap:** Phase 3 (Next-Best-Opportunity cross-sell engine & AI RAG explanations), Phase 4 (What-If simulator & field masking), Phase 5 (Next.js 14 Dark Fintech UI with D3.js Identity Graph).

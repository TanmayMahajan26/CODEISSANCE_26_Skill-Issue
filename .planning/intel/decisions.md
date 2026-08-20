# Architecture Decisions (Synthesized)

## DEC-01: Layered Multi-Service Architecture
- **Source**: `implementation_plan.md` & `PRD.md`
- **Status**: Accepted (Locked)
- **Scope**: Core Backend & Frontend Architecture
- **Decision**: Adopt a clean 4-tier layered architecture:
  - **API Layer**: FastAPI routers, JWT auth middleware, Upstash Redis rate-limiter.
  - **Service/Engine Layer**: Identity Resolver, Opportunity Engine, RAG/AI Engine, Embedding Service, Config/BRE Service, Audit Service, Conflict Resolver.
  - **Repository Layer**: Async SQLAlchemy ORM + raw SQL for pgvector queries.
  - **Data Layer**: Supabase PostgreSQL 15 + pgvector, Upstash Redis.
  - **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion, D3.js, Recharts, Zustand.

## DEC-02: 3-Phase Algorithmic & AI-Augmented Entity Resolution
- **Source**: `implementation_plan.md` & `PRD.md`
- **Status**: Accepted (Locked)
- **Scope**: Identity Resolution Engine
- **Decision**: Avoid brute-force $O(N^2)$ comparisons and simple LLM wrappers. Implement:
  - **Phase 1 (Deterministic)**: Blocking on normalized PAN (confidence 1.0), mobile, email.
  - **Phase 2 (Probabilistic)**: Weighted scoring across 8 attributes (PAN: 0.35, Mobile: 0.20, Email: 0.15, Name String Jaro-Winkler: 0.12, Name Semantic Embedding: 0.08, DOB: 0.05, City: 0.03, Segment: 0.02). Thresholds: $\ge 0.85$ AUTO_MERGE, $0.60 - 0.85$ PENDING_REVIEW, $<0.60$ NO_MATCH.
  - **Phase 3 (Semantic Discovery)**: pgvector ANN search on sentence-transformer embeddings (all-MiniLM-L6-v2) for unkeyed records with cosine similarity $\ge 0.90$.
  - **Graph Clustering**: Transitive closure across matched pairs to form single Golden Records with min spanning tree confidence.

## DEC-03: Purposeful Open-Weight AI & RAG Explainability
- **Source**: `implementation_plan.md` & `PRD.md`
- **Status**: Accepted (Locked)
- **Scope**: AI / LLM Integration
- **Decision**: Leverage Groq Cloud with Llama 3.1 70B and LangChain for four specific non-wrapper functions:
  1. RAG-based explanation of match confidence and waterfall contributions.
  2. RAG-based explanation of cross-sell opportunity rationale and customer eligibility.
  3. Natural language query translation to structured filter API parameters.
  4. Intelligent conflict resolution suggestion for human review in Review Queue.

## DEC-04: RBAC, Data Scoping, and Dynamic Masking
- **Source**: `PRD.md` & `implementation_plan.md`
- **Status**: Accepted (Locked)
- **Scope**: Security Architecture
- **Decision**: Enforce strict server-side RBAC across 4 roles:
  - `RM`: Scoped strictly to assigned customer IDs (403 for unassigned); PAN, Mobile, Email dynamically masked.
  - `MANAGER`: Scoped to team customers; full Mobile/Email visible, PAN partially masked; Review Queue approval access.
  - `ADMIN`: Unrestricted data access, unmasked fields, full BRE rule mutation, ingestion, manual merge/unmerge, audit inspection.
  - `CREDIT_APPROVER`: Read-only 360 view, masked fields, no config or merge mutation.

## DEC-05: Dynamic Business Rules Engine (BRE) & What-If Simulator
- **Source**: `PRD.md` & `implementation_plan.md`
- **Status**: Accepted (Locked)
- **Scope**: Rule Management & Judge Demonstrations
- **Decision**: Store all matching weights, thresholds, survivorship strategies, and opportunity eligibility rules in `config_rules` table. Provide What-If preview endpoint (`/api/config/rules/impact-preview`) to simulate impact before committing, with full audit trail logging (`audit_logs`).

# IdentityForge — Financial Customer 360 & Next-Best-Opportunity Engine

## What This Is

IdentityForge is a high-performance Customer 360 platform and Next-Best-Opportunity engine designed for multi-product financial institutions operating siloed systems (Equity, Mutual Funds, Insurance, Loans, and Wealth Management). It resolves customer identities across systems using a 3-phase resolution engine (deterministic, probabilistic, and AI-semantic matching), builds single Golden Records with attribute-level survivorship and provenance, generates explainable cross-sell opportunities using configurable business rules and RAG reasoning (Llama 3.1 70B via Groq), and delivers interactive role-adaptive dashboards featuring an interactive D3.js identity graph, confidence waterfall charts, and a real-time What-If rule simulator.

## Core Value

Accurately unify siloed financial customer identities into trusted golden records and deliver transparent, explainable next-best cross-sell recommendations with real-time rule configurability and strict enterprise security.

## Requirements

### Validated

(None yet — bootstrap from ingested documentation)

### Active

- [ ] **REQ-INGEST-01**: Ingest source customer records across 5 financial systems (Equity, Mutual Funds, Insurance, Loans, Wealth Management).
- [ ] **REQ-INGEST-02**: Standardize PAN, mobile, email, name, DOB, and city formats across all inputs.
- [ ] **REQ-INGEST-03**: Compute 384-dimensional dense vector embeddings for customer identities using `all-MiniLM-L6-v2` and store in pgvector.
- [ ] **REQ-MATCH-01**: Phase 1 deterministic blocking and matching on normalized PAN (confidence 1.0), mobile, and email.
- [ ] **REQ-MATCH-02**: Phase 2 probabilistic weighted multi-attribute scoring with configurable weights and decision thresholds (auto-merge >= 0.85, review 0.60-0.85).
- [ ] **REQ-MATCH-03**: Phase 3 semantic discovery using pgvector cosine distance search ($\ge 0.90$) for unkeyed records.
- [ ] **REQ-MATCH-04**: Graph clustering (transitive closure) to construct Golden Records and persist identity edges with confidence waterfall breakdown.
- [ ] **REQ-GOLD-01**: Configurable survivorship rules (Most Recent, Source Priority, Most Frequent, Highest Value Source) to resolve attribute conflicts.
- [ ] **REQ-GOLD-02**: Full attribute-level provenance tracking in JSONB on golden records.
- [ ] **REQ-GOLD-03**: Total relationship value aggregation and products held matrix across connected source systems.
- [ ] **REQ-OPP-01**: Automated product gap analysis comparing product universe against existing holdings.
- [ ] **REQ-OPP-02**: Business eligibility rule evaluation for cross-sell and upsell products.
- [ ] **REQ-OPP-03**: Multi-factor opportunity scoring based on relationship value, product affinity, recency, and engagement.
- [ ] **REQ-OPP-04**: Opportunity lifecycle management (NEW, VIEWED, ASSIGNED, IN_PROGRESS, CONVERTED, DISMISSED) with RM status update.
- [ ] **REQ-AI-01**: Context-rich RAG explanation for identity match decisions using Groq / Llama 3.1 70B and LangChain.
- [ ] **REQ-AI-02**: RAG-powered reasoning for cross-sell opportunities detailing relationship value and product gap rationale.
- [ ] **REQ-AI-03**: Natural Language Query interface translating plain English questions to structured API query parameters.
- [ ] **REQ-AI-04**: AI-powered conflict resolution suggestions for pending review items.
- [ ] **REQ-SEC-01**: JWT authentication (access & refresh tokens with rotation) and bcrypt password hashing.
- [ ] **REQ-SEC-02**: 4-role RBAC enforcement (RM, MANAGER, ADMIN, CREDIT_APPROVER).
- [ ] **REQ-SEC-03**: Data-level scoping (RM own customers, Manager team customers, Admin all).
- [ ] **REQ-SEC-04**: Dynamic role-based field masking on PAN, mobile, and email.
- [ ] **REQ-SEC-05**: Upstash Redis rate limiting on authentication and sensitive endpoints.
- [ ] **REQ-BRE-01**: Centralized Business Rules Engine storing all weights, thresholds, and rules in `config_rules` database table.
- [ ] **REQ-BRE-02**: What-If Simulator API endpoint (`/api/config/rules/impact-preview`) to preview rule change impact before applying.
- [ ] **REQ-BRE-03**: Admin "Apply & Re-run" trigger for instant live re-evaluation.
- [ ] **REQ-UI-01**: Responsive dark-mode enterprise fintech UI using Next.js 14 App Router, Tailwind CSS, shadcn/ui, and Framer Motion.
- [ ] **REQ-UI-02**: Role-adaptive dashboards for RM, Manager, and Admin.
- [ ] **REQ-UI-03**: Customer 360 profile with confidence waterfall chart, source lineage diff cards, and AI reasoning cards.
- [ ] **REQ-UI-04**: Interactive D3.js force-directed identity graph with zoom, pan, drag, and color-coded system nodes.
- [ ] **REQ-UI-05**: Config Console UI with sliders, split-screen preview, What-If simulator, and change timeline.
- [ ] **REQ-UI-06**: Review Queue UI with side-by-side record diff comparison and Manager approval actions.
- [ ] **REQ-UI-07**: Natural Language Query search interface with tabular results.
- [ ] **REQ-AUD-01**: Comprehensive, immutable audit logging for all privileged actions and configuration changes.
- [ ] **REQ-AUD-02**: Audit log viewer with search, filtering, and JSON diff inspector.
- [ ] **REQ-AUD-03**: Data Quality Scorecard displaying completeness and anomaly metrics per source system.

### Out of Scope

- Production Kafka streaming pipeline — REST and synthetic batch ingestion is sufficient for demo and test scale.
- Native mobile app store releases — Flutter mobile prototype considered optional bonus after web app completion.
- Generic third-party LLM wrappers without retrieval — All AI usage must be purposeful (embeddings, RAG explainability, NL query translation, conflict suggestions).

## Context

- **Problem Statement**: Codeissance PS-04 (Financial Customer 360 & Next-Best-Opportunity Engine).
- **Target Audience**: Financial Relationship Managers, Team Managers, System Administrators, and Credit Approvers.
- **Tech Stack**:
  - Backend: Python 3.11, FastAPI, Async SQLAlchemy, Pydantic v2, sentence-transformers, LangChain, Groq SDK.
  - Frontend: Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion, D3.js, Recharts, Zustand.
  - Data Stores: Supabase PostgreSQL 15 + pgvector extension, Upstash Redis.

## Constraints

- **Tech Stack**: Python FastAPI backend + Next.js 14 frontend.
- **Vector Search**: PostgreSQL `pgvector` extension with 384-dimensional cosine distance index.
- **LLM Rate Limits**: Groq Free Tier (30 RPM) requiring robust error handling and timeout fallbacks.
- **Security**: Strict server-side RBAC with data scoping; masked PII before serialization; bcrypt password hashing.
- **Latency SLO**: Customer 360 profile $< 500\text{ ms}$; matching $< 10\text{ s}$ for 600 records; AI explanation $< 3\text{ s}$.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 4-Tier Layered Architecture | Clean separation between Routers, Services/Engines, Repositories, and Data Stores | — Pending |
| 3-Phase Entity Resolution | Deterministic blocking + probabilistic weighted scoring + pgvector semantic discovery avoids $O(N^2)$ and simple wrappers | — Pending |
| Groq / Llama 3.1 70B for RAG | Open-weight high-speed inference for explainability, NL querying, and conflict resolution | — Pending |
| Centralized DB-Backed BRE | Enables judges to modify weights/thresholds live and see instant What-If diffs | — Pending |
| D3.js Force-Directed Graph | Delivers stunning visual demonstration of customer cluster graphs | — Pending |

---
*Last updated: 2026-08-20 after /gsd-ingest-docs bootstrap*

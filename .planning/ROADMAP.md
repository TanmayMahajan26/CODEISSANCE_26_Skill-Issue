# Roadmap: IdentityForge

## Overview

IdentityForge delivers a complete Financial Customer 360 and Next-Best-Opportunity platform across 5 phases. The build begins with the database foundations, pgvector vector store, async FastAPI architecture, and data standardization pipeline (Phase 1). It progresses through the 3-phase entity resolution engine and golden record builder (Phase 2), the Next-Best-Opportunity engine and Groq/Llama 3.1 RAG services (Phase 3), enterprise security scoping, RBAC, dynamic field masking, and dynamic BRE with What-If simulator (Phase 4), and culminates in a Next.js 14 frontend featuring role-adaptive dashboards, Customer 360 view with confidence waterfall, interactive D3.js force-directed identity graph, and live config console (Phase 5).

## Phases

- [ ] **Phase 1: Foundation, Data Models & Ingestion Pipeline** - PostgreSQL + pgvector schemas, FastAPI foundation, JWT auth, and data standardization pipeline with sentence-transformer embeddings.
- [ ] **Phase 2: Algorithmic & Semantic Identity Resolution Engine** - 3-phase entity resolution (Deterministic, Probabilistic, Semantic pgvector), graph clustering, survivorship rules, and Golden Record compilation.
- [ ] **Phase 3: Next-Best-Opportunity Engine & AI RAG Services** - Product gap analysis, eligibility rules, multi-factor opportunity scoring, Groq Llama 3.1 RAG explainability, NL queries, and review suggestions.
- [ ] **Phase 4: Security Scoping, RBAC, Masking & Business Rules Engine** - 4-role RBAC, data scoping, dynamic field masking, Redis rate limiting, centralized BRE with What-If simulator, and audit logging.
- [ ] **Phase 5: Next.js Frontend Dashboard, Customer 360 & D3 Graph** - Next.js 14 dark fintech UI, role-adaptive dashboards, Customer 360 view, D3.js force-directed graph, config console, review queue, and NL query interface.

## Phase Details

### Phase 1: Foundation, Data Models & Ingestion Pipeline
**Goal**: Establish the core backend infrastructure, database schemas with pgvector extension, JWT authentication, immutable audit logger, and data normalization pipeline with 384-dimensional vector embeddings.
**Depends on**: Nothing (first phase)
**Requirements**: REQ-INGEST-01, REQ-INGEST-02, REQ-INGEST-03, REQ-SEC-01, REQ-AUD-01
**Success Criteria** (what must be TRUE):
  1. PostgreSQL and pgvector database tables initialized with full schemas, JSONB columns, and vector index.
  2. JWT authentication endpoints (`/api/auth/login`, `/api/auth/me`, `/api/auth/refresh`) verify credentials and issue signed tokens with role claims.
  3. Ingestion pipeline standardizes PAN, mobile, email, names, DOB, and city aliases, and generates 384-dim embeddings via `all-MiniLM-L6-v2`.
**Plans**: TBD

### Phase 2: Algorithmic & Semantic Identity Resolution Engine
**Goal**: Build the 3-phase entity resolution pipeline, graph-based transitive closure clustering, attribute survivorship rules, and Golden Record builder with confidence waterfall breakdown.
**Depends on**: Phase 1
**Requirements**: REQ-MATCH-01, REQ-MATCH-02, REQ-MATCH-03, REQ-MATCH-04, REQ-GOLD-01, REQ-GOLD-02, REQ-GOLD-03
**Success Criteria** (what must be TRUE):
  1. Deterministic PAN matching links records with 1.0 confidence across systems.
  2. Probabilistic weighted scoring computes multi-attribute composite confidence and routes pairs to auto-merge ($\ge 0.85$), review ($0.60-0.85$), or no-match ($<0.60$).
  3. Semantic vector search catches unkeyed name/city variants using pgvector cosine similarity ($\ge 0.90$).
  4. Golden records built with survivorship rules, total relationship value, and complete attribute provenance in JSONB.
**Plans**: TBD

### Phase 3: Next-Best-Opportunity Engine & AI RAG Services
**Goal**: Implement the Next-Best-Opportunity recommendation engine with product gap analysis, eligibility checking, composite scoring, and Groq/Llama 3.1 RAG services for match explanations, opportunity reasoning, NL query translation, and review suggestions.
**Depends on**: Phase 2
**Requirements**: REQ-OPP-01, REQ-OPP-02, REQ-OPP-03, REQ-OPP-04, REQ-AI-01, REQ-AI-02, REQ-AI-03, REQ-AI-04
**Success Criteria** (what must be TRUE):
  1. Product gap analysis and eligibility rules evaluate customer holdings and generate scored cross-sell/upsell recommendations.
  2. RAG pipeline produces human-readable justifications for match decisions and opportunity recommendations citing exact data points.
  3. Natural language query endpoint converts English questions into structured API query parameters.
  4. AI conflict resolution suggestions generated for ambiguous records in the review queue.
**Plans**: TBD

### Phase 4: Security Scoping, RBAC, Masking & Business Rules Engine
**Goal**: Enforce strict server-side RBAC across 4 roles, customer data scoping, dynamic role-based field masking, Upstash Redis rate limiting, centralized BRE with real-time What-If simulator, and Data Quality Scorecard.
**Depends on**: Phase 3
**Requirements**: REQ-SEC-02, REQ-SEC-03, REQ-SEC-04, REQ-SEC-05, REQ-BRE-01, REQ-BRE-02, REQ-BRE-03, REQ-AUD-02, REQ-AUD-03
**Success Criteria** (what must be TRUE):
  1. API returns 403 Forbidden when RM attempts to access unassigned customer profiles.
  2. Sensitive fields (PAN, mobile, email) dynamically masked according to the user's role before JSON serialization.
  3. What-If simulator endpoint previews record merge and opportunity count shifts before committing rule updates.
  4. Audit trail captures all configuration updates, logins, and merge decisions with before/after state diffs.
**Plans**: TBD

### Phase 5: Next.js Frontend Dashboard, Customer 360 & D3 Graph
**Goal**: Build a responsive dark-mode fintech frontend with role-adaptive dashboards, Customer 360 profile with confidence waterfall, interactive D3.js force-directed identity graph, Admin Config Console with What-If simulator, Review Queue, and NL Query interface.
**Depends on**: Phase 4
**Requirements**: REQ-UI-01, REQ-UI-02, REQ-UI-03, REQ-UI-04, REQ-UI-05, REQ-UI-06, REQ-UI-07
**Success Criteria** (what must be TRUE):
  1. Authenticated users see role-adaptive dashboards with portfolio statistics, opportunity funnels, and data quality scorecards.
  2. Customer 360 view renders masked identifiers, source lineage with conflict flags, animated relationship totals, and AI reasoning cards.
  3. D3.js interactive force-directed graph visualizes identity clusters with color-coded system nodes and confidence edges.
  4. Admin Config Console provides interactive sliders, What-If impact preview, and "Apply & Re-run" trigger.
  5. Review queue enables side-by-side record diff comparison and Manager approve/reject actions.
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation, Data Models & Ingestion Pipeline | 0/TBD | Not started | - |
| 2. Algorithmic & Semantic Identity Resolution Engine | 0/TBD | Not started | - |
| 3. Next-Best-Opportunity Engine & AI RAG Services | 0/TBD | Not started | - |
| 4. Security Scoping, RBAC, Masking & Business Rules Engine | 0/TBD | Not started | - |
| 5. Next.js Frontend Dashboard, Customer 360 & D3 Graph | 0/TBD | Not started | - |

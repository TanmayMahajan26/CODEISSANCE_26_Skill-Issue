# Requirements: IdentityForge

**Defined:** 2026-08-20
**Core Value:** Accurately unify siloed financial customer identities into trusted golden records and deliver transparent, explainable next-best cross-sell recommendations with real-time rule configurability and strict enterprise security.

## v1 Requirements

### Ingestion & Standardization (INGEST)

- [ ] **REQ-INGEST-01**: Ingest source customer records across 5 financial systems (Equity, Mutual Funds, Insurance, Loans, Wealth Management) via CSV/JSON upload and synthetic generator.
- [ ] **REQ-INGEST-02**: Standardize PAN (regex check, uppercase), mobile (10-digit clean, strip prefix), email (lowercase/trim), names (strip titles/expand initials), and dates to ISO.
- [ ] **REQ-INGEST-03**: Compute 384-dimensional dense vector embeddings for normalized customer identity representations (`name + city + segment`) using `all-MiniLM-L6-v2` and store in pgvector.

### Identity Resolution & Graph (MATCH)

- [ ] **REQ-MATCH-01**: Execute Phase 1 deterministic blocking and matching on normalized PAN (confidence 1.0), mobile, and email.
- [ ] **REQ-MATCH-02**: Execute Phase 2 probabilistic weighted multi-attribute scoring combining PAN (0.35), Mobile (0.20), Email (0.15), Name String (0.12), Name Semantic (0.08), DOB (0.05), City (0.03), and Segment (0.02) with configurable auto-merge ($\ge 0.85$) and review ($0.60-0.85$) thresholds.
- [ ] **REQ-MATCH-03**: Execute Phase 3 semantic discovery using pgvector cosine distance search ($\ge 0.90$) for unkeyed records lacking PAN/Mobile/Email.
- [ ] **REQ-MATCH-04**: Build connected components / transitive closure across matched pairs into unified Golden Records and store `identity_edges` with attribution scores and confidence waterfall.

### Survivorship & Golden Records (GOLD)

- [ ] **REQ-GOLD-01**: Implement configurable survivorship rules (Most Recent, Source System Priority, Most Frequent, Highest Value Source) to resolve attribute conflicts.
- [ ] **REQ-GOLD-02**: Maintain complete attribute-level provenance in JSONB on golden records (value, source system, applied rule, confidence, timestamp).
- [ ] **REQ-GOLD-03**: Compute aggregated Total Relationship Value and compile `products_held` array across all connected source systems.

### Opportunity Engine & Cross-Sell (OPP)

- [ ] **REQ-OPP-01**: Perform automated Product Gap Analysis comparing universe of products against customer's existing holdings.
- [ ] **REQ-OPP-02**: Evaluate configurable business eligibility rules (minimum relationship value, tenure, existing products, age limits, segment exclusions).
- [ ] **REQ-OPP-03**: Calculate composite opportunity scores based on Relationship Value (0.35), Product Affinity (0.25), Recency (0.20), and Engagement (0.20).
- [ ] **REQ-OPP-04**: Track opportunity lifecycle states (NEW, VIEWED, ASSIGNED, IN_PROGRESS, CONVERTED, DISMISSED) with RM status mutation.

### AI & RAG Explainability (AI)

- [ ] **REQ-AI-01**: Generate context-rich, human-readable RAG explanations for identity match decisions using Groq / Llama 3.1 70B and LangChain.
- [ ] **REQ-AI-02**: Generate RAG-powered reasoning for cross-sell recommendations citing customer relationship value, product gaps, and business rule eligibility.
- [ ] **REQ-AI-03**: Provide Natural Language Query translation converting English questions into structured API filter parameters.
- [ ] **REQ-AI-04**: Generate AI suggestions and conflict analysis for items in the Review Queue.

### Security, RBAC & Data Masking (SEC)

- [ ] **REQ-SEC-01**: Implement JWT authentication (access & refresh tokens with rotation) and bcrypt password hashing (cost factor 12).
- [ ] **REQ-SEC-02**: Implement 4-role RBAC (RM, MANAGER, ADMIN, CREDIT_APPROVER) with strict endpoint permissions.
- [ ] **REQ-SEC-03**: Enforce data-level scoping: RM sees only assigned portfolio, Manager sees team portfolio, Admin sees organization.
- [ ] **REQ-SEC-04**: Dynamic role-based field masking on sensitive identifiers: PAN (`ABCDE****F` for RM/Manager/Approver, full for Admin), Mobile (`******3210` for RM/Approver, full for Manager/Admin), Email (`ra****@gmail.com` for RM/Approver).
- [ ] **REQ-SEC-05**: Upstash Redis sliding-window rate limiting on login (5 attempts / 15 minutes lockout) and sensitive endpoints.

### Business Rules Engine & What-If Simulator (BRE)

- [ ] **REQ-BRE-01**: Centralize all matching weights, thresholds, survivorship rules, and opportunity rules in `config_rules` database table.
- [ ] **REQ-BRE-02**: Provide What-If Simulator API endpoint (`/api/config/rules/impact-preview`) to calculate impact of rule changes before committing.
- [ ] **REQ-BRE-03**: Admin "Apply & Re-run" action to update config rules and trigger incremental/full re-evaluation in real-time.

### Frontend User Experience & Visualizations (UI)

- [ ] **REQ-UI-01**: Build responsive, dark-mode fintech UI using Next.js 14 App Router, Tailwind CSS, shadcn/ui, and Framer Motion.
- [ ] **REQ-UI-02**: Role-adaptive Dashboard: RM view (portfolio metrics, top opportunities, recent matches), Manager view (team pipeline funnel, review badges), Admin view (Data Quality Scorecard, system health).
- [ ] **REQ-UI-03**: Customer 360 View featuring profile summary, Confidence Waterfall breakdown chart, Source Lineage cards with conflict markers, Product holdings, and RAG opportunity cards.
- [ ] **REQ-UI-04**: Interactive D3.js Force-Directed Identity Graph displaying color-coded source nodes, central Golden Record node, weighted confidence edges, zoom/pan/drag, and cluster side-panel inspection.
- [ ] **REQ-UI-05**: Config Console UI with sliders for matching weights/thresholds, split-screen preview, What-If simulator trigger, and version change timeline.
- [ ] **REQ-UI-06**: Review Queue UI with side-by-side record diff comparison, conflict highlights, AI suggestion cards, and Approve/Reject/Manual-Merge actions.
- [ ] **REQ-UI-07**: Natural Language Query Search Interface with conversation history and structured table results.

### Audit & Review (AUD)

- [ ] **REQ-AUD-01**: Comprehensive audit logging capturing actor, role, action type, entity, timestamp, IP, old value JSON, and new value JSON.
- [ ] **REQ-AUD-02**: Audit Log Viewer with searching, filtering by action/actor, and expandable JSON diff inspector.
- [ ] **REQ-AUD-03**: Data Quality Scorecard displaying % completeness of PAN, Mobile, Email per source system, anomaly counts, and match rates.

## v2 Requirements

- **V2-01**: Real-time Kafka / CDC streaming ingestion pipeline for live enterprise scale.
- **V2-02**: Native Flutter RM mobile app for iOS/Android with offline cache and biometric auth.
- **V2-03**: Dedicated Neo4j graph database integration for enterprise-scale multi-million node traversals.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Kafka Streaming Cluster | Batch and REST synthetic ingestion is optimal for demo and development |
| Native App Store Publishing | Web-first responsive application prioritizes judge evaluation experience |
| Plain LLM Wrappers Without Data Grounding | Violates hackathon core engineering requirements; AI is strictly purposeful |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-INGEST-01 | Phase 1 | Pending |
| REQ-INGEST-02 | Phase 1 | Pending |
| REQ-INGEST-03 | Phase 1 | Pending |
| REQ-SEC-01 | Phase 1 | Pending |
| REQ-AUD-01 | Phase 1 | Pending |
| REQ-MATCH-01 | Phase 2 | Pending |
| REQ-MATCH-02 | Phase 2 | Pending |
| REQ-MATCH-03 | Phase 2 | Pending |
| REQ-MATCH-04 | Phase 2 | Pending |
| REQ-GOLD-01 | Phase 2 | Pending |
| REQ-GOLD-02 | Phase 2 | Pending |
| REQ-GOLD-03 | Phase 2 | Pending |
| REQ-OPP-01 | Phase 3 | Pending |
| REQ-OPP-02 | Phase 3 | Pending |
| REQ-OPP-03 | Phase 3 | Pending |
| REQ-OPP-04 | Phase 3 | Pending |
| REQ-AI-01 | Phase 3 | Pending |
| REQ-AI-02 | Phase 3 | Pending |
| REQ-AI-03 | Phase 3 | Pending |
| REQ-AI-04 | Phase 3 | Pending |
| REQ-SEC-02 | Phase 4 | Pending |
| REQ-SEC-03 | Phase 4 | Pending |
| REQ-SEC-04 | Phase 4 | Pending |
| REQ-SEC-05 | Phase 4 | Pending |
| REQ-BRE-01 | Phase 4 | Pending |
| REQ-BRE-02 | Phase 4 | Pending |
| REQ-BRE-03 | Phase 4 | Pending |
| REQ-AUD-02 | Phase 4 | Pending |
| REQ-AUD-03 | Phase 4 | Pending |
| REQ-UI-01 | Phase 5 | Pending |
| REQ-UI-02 | Phase 5 | Pending |
| REQ-UI-03 | Phase 5 | Pending |
| REQ-UI-04 | Phase 5 | Pending |
| REQ-UI-05 | Phase 5 | Pending |
| REQ-UI-06 | Phase 5 | Pending |
| REQ-UI-07 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 33
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-20*
*Last updated: 2026-08-20 after /gsd-ingest-docs bootstrap*

# Requirements (Synthesized)

## Category: Ingestion & Standardization (INGEST)
- **REQ-INGEST-01**: Ingest source customer records across 5 financial systems (Equity, Mutual Funds, Insurance, Loans, Wealth Management) via CSV/JSON upload and synthetic data generator.
  - *Source*: `PRD.md` (§5.1, §7.8), `implementation_plan.md` (§5, §9)
  - *Acceptance Criteria*: CSV validation, normalization, and trigger of matching pipeline.
- **REQ-INGEST-02**: Standardize PAN (regex check, uppercase), mobile (10-digit clean, strip prefix), email (lowercase/trim), names (strip titles/expand initials), and dates to ISO.
  - *Source*: `PRD.md` (§10.1), `implementation_plan.md` (§3)
  - *Acceptance Criteria*: Normalization cleans malformed inputs, aliases, and bad formats gracefully.
- **REQ-INGEST-03**: Compute 384-dimensional dense vector embeddings for normalized customer identity representations (`name + city + segment`) using `all-MiniLM-L6-v2` and store in pgvector.
  - *Source*: `PRD.md` (§11.1), `implementation_plan.md` (§5)
  - *Acceptance Criteria*: Embeddings generated and indexed for ANN search in Supabase PostgreSQL.

## Category: Identity Resolution & Graph (MATCH)
- **REQ-MATCH-01**: Execute Phase 1 deterministic blocking and matching on normalized PAN (confidence 1.0), mobile, and email.
  - *Source*: `PRD.md` (§5.2), `implementation_plan.md` (§3)
  - *Acceptance Criteria*: Exact PAN matches merge automatically with 1.0 confidence.
- **REQ-MATCH-02**: Execute Phase 2 probabilistic weighted multi-attribute scoring combining PAN (0.35), Mobile (0.20), Email (0.15), Name String (0.12), Name Semantic (0.08), DOB (0.05), City (0.03), and Segment (0.02).
  - *Source*: `PRD.md` (§5.2), `implementation_plan.md` (§3)
  - *Acceptance Criteria*: Weighted sum evaluated against configurable thresholds (auto-merge >= 0.85, review 0.60-0.85, no-match < 0.60).
- **REQ-MATCH-03**: Execute Phase 3 semantic discovery using pgvector cosine distance search ($\ge 0.90$) for unkeyed records lacking PAN/Mobile/Email.
  - *Source*: `PRD.md` (§5.1, §11.1), `implementation_plan.md` (§3)
  - *Acceptance Criteria*: Semantically similar names/locations discovered and scored even when string distance fails.
- **REQ-MATCH-04**: Build connected components / transitive closure across matched pairs into unified Golden Records and store `identity_edges` with attribution scores and confidence waterfall.
  - *Source*: `PRD.md` (§5.2, §6.1), `implementation_plan.md` (§2, §3)
  - *Acceptance Criteria*: Cluster confidence calculated as min edge confidence in spanning tree; full edge provenance persisted.

## Category: Survivorship & Golden Records (GOLD)
- **REQ-GOLD-01**: Implement configurable survivorship rules (Most Recent, Source System Priority, Most Frequent, Highest Value Source) to resolve attribute conflicts.
  - *Source*: `PRD.md` (§5.3, §10.1), `implementation_plan.md` (§3)
  - *Acceptance Criteria*: Golden record attributes selected deterministically per rule; fallback to review queue if unresolved.
- **REQ-GOLD-02**: Maintain complete attribute-level provenance in JSONB on golden records (value, source system, applied rule, confidence, timestamp).
  - *Source*: `PRD.md` (§6.1), `implementation_plan.md` (§2)
  - *Acceptance Criteria*: Every field on the Customer 360 profile tracks its originating source record and rule.
- **REQ-GOLD-03**: Compute aggregated Total Relationship Value and compile `products_held` array across all connected source systems.
  - *Source*: `PRD.md` (§6.1), `implementation_plan.md` (§2)
  - *Acceptance Criteria*: Sum of balance/AUM across all linked products accurately reflected in Golden Record.

## Category: Opportunity Engine & Cross-Sell (OPP)
- **REQ-OPP-01**: Perform automated Product Gap Analysis comparing universe of products against customer's existing holdings.
  - *Source*: `PRD.md` (§5.4), `implementation_plan.md` (§4)
  - *Acceptance Criteria*: Accurately identifies missing product lines (e.g., Insurance, Wealth, Loans).
- **REQ-OPP-02**: Evaluate configurable business eligibility rules (minimum relationship value, tenure, existing products, age limits, segment exclusions).
  - *Source*: `PRD.md` (§5.4, §10.1), `implementation_plan.md` (§4)
  - *Acceptance Criteria*: Unmet eligibility criteria immediately filtered out; passed checks recorded in `eligibility_met`.
- **REQ-OPP-03**: Calculate composite opportunity scores based on Relationship Value (0.35), Product Affinity (0.25), Recency (0.20), and Engagement (0.20).
  - *Source*: `PRD.md` (§5.4, §10.1), `implementation_plan.md` (§4)
  - *Acceptance Criteria*: Scored opportunities ranked and filtered by minimum score threshold.
- **REQ-OPP-04**: Track opportunity lifecycle states (NEW, VIEWED, ASSIGNED, IN_PROGRESS, CONVERTED, DISMISSED) with RM status mutation.
  - *Source*: `PRD.md` (§3 Persona 1, §7.5), `implementation_plan.md` (§2, §6)
  - *Acceptance Criteria*: RM status updates persist, update dashboard counts, and log audit events.

## Category: AI & RAG Explainability (AI)
- **REQ-AI-01**: Generate context-rich, human-readable RAG explanations for identity match decisions using Groq / Llama 3.1 70B and LangChain.
  - *Source*: `PRD.md` (§11.2), `implementation_plan.md` (§1, §5)
  - *Acceptance Criteria*: Explanations articulate exact matching attributes, confidence score, and discrepancies.
- **REQ-AI-02**: Generate RAG-powered reasoning for cross-sell recommendations citing customer relationship value, product gaps, and business rule eligibility.
  - *Source*: `PRD.md` (§5.4, §11.1), `implementation_plan.md` (§4, §5)
  - *Acceptance Criteria*: RM sees clear, actionable explanation of why product is recommended.
- **REQ-AI-03**: Provide Natural Language Query translation converting English questions into structured API filter parameters.
  - *Source*: `PRD.md` (§7.2, §11.1), `implementation_plan.md` (§1, §5)
  - *Acceptance Criteria*: Query like "Show HNI clients in Mumbai without insurance" returns correct filtered results.
- **REQ-AI-04**: Generate AI suggestions and conflict analysis for items in the Review Queue.
  - *Source*: `PRD.md` (§5.3, §11.1), `implementation_plan.md` (§1, §5)
  - *Acceptance Criteria*: Managers see intelligent reasoning regarding probable data entry errors or alternate identities.

## Category: Security, RBAC & Data Masking (SEC)
- **REQ-SEC-01**: Implement JWT authentication (access & refresh tokens with rotation) and bcrypt password hashing (cost factor 12).
  - *Source*: `PRD.md` (§7.1, §8.3), `implementation_plan.md` (§1, §7)
  - *Acceptance Criteria*: Secure auth endpoints, token validation middleware, and refresh lifecycle.
- **REQ-SEC-02**: Implement 4-role RBAC (RM, MANAGER, ADMIN, CREDIT_APPROVER) with strict endpoint permissions.
  - *Source*: `PRD.md` (§8.1), `implementation_plan.md` (§7)
  - *Acceptance Criteria*: Unauthorized actions return HTTP 403 Forbidden.
- **REQ-SEC-03**: Enforce data-level scoping: RM sees only assigned portfolio, Manager sees team portfolio, Admin sees organization.
  - *Source*: `PRD.md` (§5.5, §8.1), `implementation_plan.md` (§7)
  - *Acceptance Criteria*: Direct URL access to another RM's customer returns 403.
- **REQ-SEC-04**: Dynamic role-based field masking on sensitive identifiers: PAN (`ABCDE****F` for RM/Manager/Approver, full for Admin), Mobile (`******3210` for RM/Approver, full for Manager/Admin), Email (`ra****@gmail.com` for RM/Approver).
  - *Source*: `PRD.md` (§8.2), `implementation_plan.md` (§7)
  - *Acceptance Criteria*: Sensitive data masked on the backend before API serialization.
- **REQ-SEC-05**: Redis sliding-window rate limiting on login (5 attempts / 15 minutes lockout) and sensitive endpoints.
  - *Source*: `PRD.md` (§8.3, §12), `implementation_plan.md` (§6, §7)
  - *Acceptance Criteria*: Excessive attempts lock out the user with descriptive message.

## Category: Business Rules Engine & What-If Simulator (BRE)
- **REQ-BRE-01**: Centralize all matching weights, thresholds, survivorship rules, and opportunity rules in `config_rules` database table.
  - *Source*: `PRD.md` (§10.1), `implementation_plan.md` (§2, §6)
  - *Acceptance Criteria*: Zero hardcoded weights or thresholds in application code.
- **REQ-BRE-02**: Provide What-If Simulator API endpoint (`/api/config/rules/impact-preview`) to calculate impact of rule changes before committing.
  - *Source*: `PRD.md` (§5.6, §7.6), `implementation_plan.md` (§6)
  - *Acceptance Criteria*: Returns projected new auto-merges, pending reviews, or opportunity count shifts.
- **REQ-BRE-03**: Admin "Apply & Re-run" action to update config rules and trigger incremental/full re-evaluation in real-time.
  - *Source*: `PRD.md` (§5.6, §7.6), `implementation_plan.md` (§6)
  - *Acceptance Criteria*: Immediate live re-evaluation reflected across customer records and dashboards.

## Category: Frontend User Experience & Visualizations (UI)
- **REQ-UI-01**: Build responsive, dark-mode fintech UI using Next.js 14 App Router, Tailwind CSS, shadcn/ui, and Framer Motion.
  - *Source*: `PRD.md` (§9.1, §9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Polished dark theme, emerald accents, micro-animations, glassmorphism.
- **REQ-UI-02**: Role-adaptive Dashboard: RM view (portfolio metrics, top opportunities, recent matches), Manager view (team pipeline funnel, review badges), Admin view (Data Quality Scorecard, system health).
  - *Source*: `PRD.md` (§9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Dashboard dynamically configures widgets based on authenticated user's role.
- **REQ-UI-03**: Customer 360 View featuring profile summary, Confidence Waterfall breakdown chart, Source Lineage cards with conflict markers, Product holdings, and RAG opportunity cards.
  - *Source*: `PRD.md` (§9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Complete 360 profile with animated counters, lineage diffs, and AI insights.
- **REQ-UI-04**: Interactive D3.js Force-Directed Identity Graph displaying color-coded source nodes (Equity, MF, Insurance, Loans, Wealth), central Golden Record node, weighted confidence edges, zoom/pan/drag, and cluster side-panel inspection.
  - *Source*: `PRD.md` (§9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Fluid interactive graph rendering customer identity clusters.
- **REQ-UI-05**: Config Console UI with sliders for matching weights/thresholds, split-screen preview, What-If simulator trigger, and version change timeline.
  - *Source*: `PRD.md` (§9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Admin can adjust weights and see instant live impact diff.
- **REQ-UI-06**: Review Queue UI with side-by-side record diff comparison, conflict highlights, AI suggestion cards, and Approve/Reject/Manual-Merge actions.
  - *Source*: `PRD.md` (§9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Managers/Admins can inspect conflict details and resolve merge status.
- **REQ-UI-07**: Natural Language Query Search Interface with conversation history and structured table results.
  - *Source*: `PRD.md` (§9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Interactive search bar with instant query execution.

## Category: Audit & Review (AUD)
- **REQ-AUD-01**: Comprehensive audit logging capturing actor, role, action type, entity, timestamp, IP, old value JSON, and new value JSON.
  - *Source*: `PRD.md` (§8.4), `implementation_plan.md` (§2, §6)
  - *Acceptance Criteria*: All logins, config updates, merge actions, and status changes logged immutably.
- **REQ-AUD-02**: Audit Log Viewer with searching, filtering by action/actor, and expandable JSON diff inspector.
  - *Source*: `PRD.md` (§7.7, §9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Clean tabular view with CSV export capability.
- **REQ-AUD-03**: Data Quality Scorecard displaying % completeness of PAN, Mobile, Email per source system, anomaly counts, and match rates.
  - *Source*: `PRD.md` (§7.8, §9.2), `implementation_plan.md` (§8)
  - *Acceptance Criteria*: Visual scorecard providing immediate insight into data health across systems.

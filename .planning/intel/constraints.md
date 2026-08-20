# Technical Constraints (Synthesized)

## Database & Data Layer Constraints
- **Type**: `schema` / `database`
- **Source**: `PRD.md` (§6, §14), `implementation_plan.md` (§1, §2)
- **Constraint**: Supabase PostgreSQL 15+ with `pgvector` extension enabled.
- **Specification**:
  - `source_records.name_embedding` is `Vector(384)`.
  - Normalized fields: `normalized_name`, `normalized_mobile`, `normalized_email`.
  - Sensitive columns (`pan_id`, `canonical_pan`) stored with field-level encryption.
  - JSONB used for `raw_data`, `products_held`, `attribute_provenance`, `match_reasons`, `score_breakdown`, `eligibility_met`, `old_value`, `new_value`.

## AI / Inference Constraints & Rate Limits
- **Type**: `nfr` / `external-api`
- **Source**: `PRD.md` (§11, §14), `implementation_plan.md` (§1, §5)
- **Constraint**:
  - Groq Cloud API using `llama-3.1-70b-versatile` under Free Tier (30 RPM limit).
  - Sentence-transformers model `all-MiniLM-L6-v2` loaded in-process (80MB footprint, 384 dimensions).
  - RAG calls must include timeout and fallback handling if external API is unreachable or rate-limited.

## Security, Auth & RBAC Constraints
- **Type**: `security` / `protocol`
- **Source**: `PRD.md` (§7.1, §8.1, §8.2, §8.3), `implementation_plan.md` (§7)
- **Constraint**:
  - Password hashing via bcrypt (work factor $\ge 12$).
  - JWT Tokens: Access token expires in 30 minutes; Refresh token valid for 7 days with rotation.
  - Rate limiting on authentication: Upstash Redis sliding window (5 failed login attempts in 15 minutes locks account).
  - Strict data-level scoping applied before returning queries: RM cannot view unassigned customers (must return HTTP 403 Forbidden).
  - Field masking applied at API layer before response serialization.

## Performance & SLO Constraints
- **Type**: `nfr`
- **Source**: `PRD.md` (§14), `implementation_plan.md` (§14)
- **Constraint**:
  - Customer 360 profile load time $< 500\text{ ms}$ (leveraging Redis cache for active Golden Records).
  - Identity matching run for 600 records $< 10\text{ s}$ via blocking strategy $O(N \times B)$.
  - AI explanation generation $< 3\text{ s}$ per request.

## Frontend Framework & Design Constraints
- **Type**: `frontend-contract`
- **Source**: `PRD.md` (§9), `implementation_plan.md` (§8)
- **Constraint**:
  - Next.js 14 App Router with TypeScript.
  - Dark enterprise fintech visual theme with emerald (`#10B981`) accent and slate background (`#0F172A`).
  - Interactive D3.js force-directed graph with SVG canvas, zoom/pan/drag, and color-coded node taxonomy.
  - Recharts for dashboard analytics and funnel charts.

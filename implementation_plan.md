# PS-04: Financial Customer 360 & Next-Best-Opportunity Engine
## **IdentityForge** — v2 (Technically Rich Architecture)

---

## 🎯 Problem Interpretation

Build a **Customer 360 platform** that:
1. **Resolves identities** across 5 siloed financial systems (Equity, MF, Insurance, Loans, Wealth) using deterministic + probabilistic + **AI-semantic matching**
2. **Generates explainable cross-sell opportunities** using a configurable rules engine + **RAG-powered reasoning**
3. Handles ambiguity, confidence, conflicts — and lets judges **change rules live** and see instant impact

> [!IMPORTANT]
> The judges explicitly warn: "An LLM wrapper should not substitute for core engineering." Our AI usage is **purposeful** — it powers semantic matching, explainability, natural-language querying, and intelligent conflict resolution. The core identity resolution engine is algorithmic; AI augments it.

---

## Why We Win — Rubric Mapping

| Rubric (Weight) | Our Differentiator |
|---|---|
| **Approach & Design (12%)** | Graph-based entity resolution + RAG-powered explainability — industry MDM meets modern AI |
| **Architecture (13%)** | Event-driven pipeline: Ingestion → Standardization → Blocking → Matching (algo + semantic) → Golden Record → Opportunity Engine → RAG Explainer |
| **Programming (13%)** | Typed Python FastAPI, Next.js App Router, clean layered architecture, async everywhere, test coverage |
| **Configurability (12%)** | Centralized BRE — every weight/threshold/rule editable via Admin UI → instant re-run → before/after diff |
| **Backend & Data (10%)** | Supabase PostgreSQL + pgvector, identity graph model, audit tables, vector embeddings for semantic search |
| **UI/UX (8%)** | Premium dark fintech dashboard, D3.js identity graph, glassmorphism, micro-animations, responsive |
| **Robustness (8%)** | Missing PAN, duplicate mobiles, conflicting DOBs, malformed data, replay protection, graceful degradation |
| **Scalability (7%)** | Blocking-based resolution (not O(n²)), vector index for ANN search, async pipeline, Redis caching, deployed on cloud |
| **Innovation (7%)** | RAG for explainability, vector embeddings for semantic matching, NL querying, identity graph visualization |
| **Security (10%)** | Full RBAC (4 roles), data-level auth, PAN masking, JWT, audit trail, rate limiting, env-based secrets |

---

## Tech Stack (Technically Rich)

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT                                │
│   Vercel (Frontend)  •  Render (Backend)  •  Supabase (DB)      │
│   Upstash (Redis)    •  Groq (LLM API)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND — Next.js 14 (App Router) + TypeScript                │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │ shadcn/ui │ │ Framer    │ │ D3.js     │ │ Recharts      │   │
│  │ Components│ │ Motion    │ │ Graph Viz │ │ Charts        │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘   │
│  ┌───────────┐ ┌───────────┐ ┌───────────────────────────────┐ │
│  │ TanStack  │ │ Zustand   │ │ next-auth (JWT + RBAC)        │ │
│  │ Query     │ │ State     │ │                               │ │
│  └───────────┘ └───────────┘ └───────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API + WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│  BACKEND — Python FastAPI + Async                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  API Layer (Routers + Auth Middleware + Rate Limiter)    │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Service Layer                                          │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │    │
│  │  │  Identity     │ │  Opportunity │ │  RAG / AI      │  │    │
│  │  │  Resolution   │ │  Engine      │ │  Engine        │  │    │
│  │  │  Engine       │ │              │ │  (LangChain)   │  │    │
│  │  └──────────────┘ └──────────────┘ └────────────────┘  │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │    │
│  │  │  Embedding   │ │  Conflict    │ │  Config/BRE    │  │    │
│  │  │  Service     │ │  Resolver    │ │  Service       │  │    │
│  │  │  (sentence-  │ │  + Review    │ │                │  │    │
│  │  │  transformers)│ │              │ │                │  │    │
│  │  └──────────────┘ └──────────────┘ └────────────────┘  │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Repository Layer (SQLAlchemy Async + Raw SQL)          │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────┬───────────────┬──────────────────────────┘
                       │               │
┌──────────────────────▼───┐  ┌────────▼─────────────────────────┐
│  Supabase PostgreSQL     │  │  External Services               │
│  + pgvector extension    │  │  ┌─────────────────────────┐     │
│  ┌────────┐ ┌─────────┐ │  │  │ Groq API (Free Tier)    │     │
│  │ Tables │ │ Vector  │ │  │  │ Llama 3.1 70B / Mixtral │     │
│  │ (data) │ │ Index   │ │  │  │ Open-weight models      │     │
│  └────────┘ └─────────┘ │  │  └─────────────────────────┘     │
│  ┌────────┐ ┌─────────┐ │  │  ┌─────────────────────────┐     │
│  │ Audit  │ │ Config  │ │  │  │ Upstash Redis            │     │
│  │ Trail  │ │ Rules   │ │  │  │ (Cache + Rate Limiting)  │     │
│  └────────┘ └─────────┘ │  │  └─────────────────────────┘     │
└──────────────────────────┘  └──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MOBILE (Bonus) — Flutter                                        │
│  RM mobile app: Customer 360 view, opportunity notifications,   │
│  quick actions, offline-capable customer list                    │
└─────────────────────────────────────────────────────────────────┘
```

### Why Each Technology

| Technology | Why | Judge Impact |
|---|---|---|
| **Groq + Llama 3.1 70B** | Open-weight LLM, blazing fast inference (free tier), NOT a wrapper — powers explainability & semantic matching | "They trained/used open-weight models purposefully" |
| **pgvector** | Vector similarity search in PostgreSQL — no separate vector DB needed, enables semantic customer matching | "Smart use of embeddings for fuzzy matching" |
| **sentence-transformers** | Generate embeddings for customer name/address for semantic similarity (better than Jaro-Winkler alone) | "Beyond basic string matching" |
| **LangChain** | RAG pipeline: retrieves relevant customer data + rules context → LLM generates explanations | "Proper RAG implementation, not just prompting" |
| **Next.js 14 App Router** | Server components, API routes, middleware auth, deployed on Vercel edge | "Modern full-stack framework" |
| **shadcn/ui + Framer Motion** | Premium UI components + smooth animations | "Polished, professional interface" |
| **Supabase** | Managed PostgreSQL with pgvector, real-time subscriptions, auth helpers | "Production-ready infrastructure" |
| **Upstash Redis** | Serverless Redis for caching golden records, rate limiting, session management | "Proper caching layer" |
| **D3.js** | Interactive force-directed identity graph — the WOW factor | "Impressive data visualization" |

---

## AI/RAG Integration — Purposeful, Not a Wrapper

> [!CAUTION]
> The rubric says: "AI usage should be evaluated on necessity and implementation quality; an LLM wrapper should not substitute for core engineering." Our AI has **four distinct, necessary purposes**.

### AI Purpose 1: Semantic Customer Matching (Embedding-based)
Traditional fuzzy matching (Jaro-Winkler) fails on:
- "Rajesh Kumar Sharma" vs "R.K. Sharma" vs "Raj Sharma"
- "12, MG Road, Bangalore" vs "12 Mahatma Gandhi Rd, Bengaluru"

**Our approach:** Generate sentence-transformer embeddings for `name + address + city` → store in pgvector → cosine similarity search finds semantically similar records that string matching would miss.

```python
# Embedding-based matching (augments, doesn't replace, deterministic matching)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, fast

def compute_customer_embedding(record):
    text = f"{record.name} {record.city} {record.segment}"
    return model.encode(text)

# Store in pgvector, query with:
# SELECT * FROM source_records 
# ORDER BY embedding <=> query_embedding 
# LIMIT 10;
```

### AI Purpose 2: RAG-Powered Explainability
When showing WHY records matched or WHY an opportunity was generated, raw scores are not human-friendly. Our RAG pipeline:

1. **Retrieves** the match data (scores, reasons, source records)
2. **Retrieves** the relevant business rules from config
3. **Generates** a human-readable explanation via Llama 3.1

```python
# RAG Explainer
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.1)

def explain_match(match_data: dict, rules_context: str) -> str:
    prompt = ChatPromptTemplate.from_template("""
    You are a financial data analyst explaining identity resolution results.
    
    Match Data: {match_data}
    Business Rules Applied: {rules_context}
    
    Explain in 2-3 sentences why these records were identified as the 
    same customer. Mention specific matching criteria and confidence factors.
    Be precise and professional.
    """)
    chain = prompt | llm
    return chain.invoke({"match_data": match_data, "rules_context": rules_context})
```

### AI Purpose 3: Natural Language Querying
RMs and Managers can ask questions in plain English:
- *"Show me high-value customers in Mumbai without insurance"*
- *"Which customers have conflicting addresses across systems?"*
- *"What are the top 5 cross-sell opportunities for my team?"*

The LLM converts natural language → structured API query → results.

```python
def nl_to_query(question: str, schema_context: str) -> dict:
    """Convert natural language to structured filter parameters"""
    prompt = f"""Given this data schema: {schema_context}
    Convert this question to API filter params: {question}
    Return JSON with: filters, sort, limit"""
    return llm.invoke(prompt)
```

### AI Purpose 4: Intelligent Conflict Resolution Suggestions
When records conflict (e.g., two different DOBs), the LLM analyzes:
- Source system reliability
- Data recency
- Pattern consistency
- Suggests which value to keep and why

```python
def suggest_conflict_resolution(conflicts: list, source_metadata: dict) -> dict:
    """AI suggests which conflicting value to keep, with reasoning"""
    prompt = f"""Analyze these data conflicts for a customer identity merge:
    Conflicts: {conflicts}
    Source System Metadata: {source_metadata}
    
    For each conflict, recommend which value to keep and explain why,
    considering source reliability, data recency, and consistency."""
    return llm.invoke(prompt)
```

---

## Proposed Changes (Detailed)

### Component 1: Backend Core

#### [NEW] `backend/app/main.py`
FastAPI app with lifespan events, CORS for Vercel frontend, middleware registration, WebSocket endpoint for real-time matching progress.

#### [NEW] `backend/app/config.py`
Pydantic Settings reading from `.env`:
```python
class Settings(BaseSettings):
    DATABASE_URL: str           # Supabase connection string
    REDIS_URL: str              # Upstash Redis URL
    JWT_SECRET: str             # Generated, never hardcoded
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE: int = 30  # minutes
    REFRESH_TOKEN_EXPIRE: int = 7  # days
    GROQ_API_KEY: str           # For Llama 3.1
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
```

#### [NEW] `backend/app/database.py`
Async SQLAlchemy engine with Supabase PostgreSQL, connection pooling, pgvector extension initialization.

---

### Component 2: Data Models

#### [NEW] `backend/app/models/source_record.py`
```python
class SourceRecord(Base):
    __tablename__ = "source_records"
    id: UUID (PK)
    source_system: Enum[EQUITY, MUTUAL_FUNDS, INSURANCE, LOANS, WEALTH]
    source_customer_id: str
    pan_id: str (nullable, encrypted)
    mobile: str (nullable)
    email: str (nullable)
    name: str
    dob: date (nullable)
    city: str (nullable)
    segment: str (nullable)
    product_type: str
    balance_aum: Decimal
    relationship_value: Decimal
    last_activity_date: date
    rm_id: str (nullable)
    raw_data: JSONB
    # Vector embedding for semantic matching
    name_embedding: Vector(384)  # pgvector column
    normalized_name: str
    normalized_mobile: str
    normalized_email: str
    created_at: datetime
```

#### [NEW] `backend/app/models/golden_record.py`
```python
class GoldenRecord(Base):
    __tablename__ = "golden_records"
    golden_id: UUID (PK)
    canonical_name: str
    canonical_pan: str (encrypted)
    canonical_mobile: str
    canonical_email: str
    canonical_dob: date
    canonical_city: str
    canonical_segment: str
    total_relationship_value: Decimal
    products_held: JSONB  # [{system, product, balance, last_activity}]
    source_record_ids: ARRAY[UUID]
    attribute_provenance: JSONB  # {field: {value, source, rule, confidence}}
    match_confidence: float  # Overall cluster confidence
    version: int  # For version history
    status: Enum[ACTIVE, UNDER_REVIEW, MERGED_INTO]
    merged_into_id: UUID (nullable, FK)
    assigned_rm_id: str
    created_at, updated_at: datetime
```

#### [NEW] `backend/app/models/identity_edge.py`
```python
class IdentityEdge(Base):
    __tablename__ = "identity_edges"
    id: UUID (PK)
    source_a_id: UUID (FK → source_records)
    source_b_id: UUID (FK → source_records)
    golden_id: UUID (FK → golden_records, nullable)
    match_type: Enum[DETERMINISTIC, PROBABILISTIC, SEMANTIC, MANUAL]
    confidence_score: float
    match_reasons: JSONB  # {pan: 1.0, mobile: 0.9, name_semantic: 0.82, ...}
    ai_explanation: str (nullable)  # RAG-generated explanation
    status: Enum[AUTO_MERGED, PENDING_REVIEW, REJECTED, MANUAL_MERGED]
    created_at: datetime
```

#### [NEW] `backend/app/models/opportunity.py`
```python
class Opportunity(Base):
    __tablename__ = "opportunities"
    id: UUID (PK)
    golden_id: UUID (FK)
    opportunity_type: Enum[CROSS_SELL, UPSELL, RETENTION, PROTECTION]
    product_recommended: str
    score: float
    score_breakdown: JSONB  # {factor: weight × value for each}
    ai_reasoning: str  # RAG-generated human explanation
    potential_value: Decimal
    eligibility_met: JSONB  # Which rules passed/failed
    status: Enum[NEW, VIEWED, ASSIGNED, IN_PROGRESS, CONVERTED, DISMISSED]
    assigned_rm_id: str
    created_at, updated_at: datetime
```

#### [NEW] `backend/app/models/config_rule.py`
```python
class ConfigRule(Base):
    __tablename__ = "config_rules"
    id: UUID (PK)
    category: Enum[MATCHING_WEIGHTS, THRESHOLDS, OPPORTUNITY_RULES, 
                   NORMALIZATION, SOURCE_PRECEDENCE, SCORING_WEIGHTS]
    rule_key: str (unique)
    rule_value: JSONB
    description: str
    is_active: bool
    version: int
    updated_by: UUID (FK → users)
    updated_at: datetime
```

#### [NEW] `backend/app/models/audit_log.py`
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: UUID (PK)
    actor_id: UUID
    actor_username: str
    actor_role: str
    action: Enum[LOGIN, LOGOUT, CONFIG_CHANGE, MERGE_APPROVE, MERGE_REJECT,
                 MANUAL_MERGE, UNMERGE, OPPORTUNITY_UPDATE, DATA_INGEST,
                 MATCHING_RUN, RULE_CHANGE]
    entity_type: str
    entity_id: str
    old_value: JSONB (nullable)
    new_value: JSONB (nullable)
    ip_address: str
    user_agent: str
    timestamp: datetime (server_default=now())
```

#### [NEW] `backend/app/models/user.py`
```python
class User(Base):
    __tablename__ = "users"
    id: UUID (PK)
    username: str (unique)
    email: str
    password_hash: str  # bcrypt
    role: Enum[RM, MANAGER, ADMIN, CREDIT_APPROVER]
    rm_id: str (nullable)  # Links to RM assignments
    team_id: str (nullable)  # For manager → team scoping
    is_active: bool
    failed_login_attempts: int (default=0)
    locked_until: datetime (nullable)
    created_at: datetime
```

#### [NEW] `backend/app/models/review_queue.py`
```python
class ReviewItem(Base):
    __tablename__ = "review_queue"
    id: UUID (PK)
    review_type: Enum[LOW_CONFIDENCE_MATCH, ATTRIBUTE_CONFLICT, 
                      DUPLICATE_SUSPECT, AI_FLAGGED]
    golden_id: UUID (nullable)
    source_record_ids: ARRAY[UUID]
    details: JSONB  # Conflict details, match scores, AI suggestion
    ai_suggestion: str  # LLM-generated resolution suggestion
    priority: Enum[LOW, MEDIUM, HIGH, CRITICAL]
    assigned_to: UUID (nullable)
    status: Enum[PENDING, IN_REVIEW, APPROVED, REJECTED]
    resolved_by: UUID (nullable)
    resolution_notes: str (nullable)
    created_at, resolved_at: datetime
```

---

### Component 3: Identity Resolution Engine

#### [NEW] `backend/app/engines/data_standardizer.py`
Configurable normalization pipeline (rules from DB):
- PAN: uppercase, strip whitespace, validate `XXXXX0000X` regex
- Mobile: strip `+91`/`0`/spaces/dashes → 10-digit
- Email: lowercase, trim, validate format
- Name: uppercase, remove titles, expand initials, remove special chars
- DOB: parse `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-Mon-YY` → ISO
- City: alias mapping (Bombay→Mumbai, Bangalore→Bengaluru, Calcutta→Kolkata)
- **Generate embedding** for `name + city` using sentence-transformers → store in pgvector

#### [NEW] `backend/app/engines/identity_resolver.py`
**Three-phase identity resolution:**

**Phase 1 — Deterministic (Blocking + Exact Match):**
- Block on normalized PAN → exact match → confidence 1.0
- Block on normalized mobile → candidate pairs
- Block on normalized email → candidate pairs

**Phase 2 — Probabilistic (Weighted Multi-attribute Scoring):**
```
For each candidate pair from blocking:

score = Σ (weight_i × match_function_i(a, b))

Configurable weights (read from config_rules table):
┌──────────────┬────────┬──────────────────────────┐
│ Attribute    │ Weight │ Match Function            │
├──────────────┼────────┼──────────────────────────┤
│ PAN          │ 0.35   │ Exact match (1.0 / 0.0)  │
│ Mobile       │ 0.20   │ Exact match (1.0 / 0.0)  │
│ Email        │ 0.15   │ Exact match (1.0 / 0.0)  │
│ Name         │ 0.12   │ Jaro-Winkler (0.0–1.0)   │
│ Name Semantic│ 0.08   │ Cosine sim (pgvector)     │
│ DOB          │ 0.05   │ Exact match (1.0 / 0.0)  │
│ City         │ 0.03   │ Exact or alias (1.0/0.0)  │
│ Segment      │ 0.02   │ Exact match (1.0 / 0.0)  │
└──────────────┴────────┴──────────────────────────┘

Decision thresholds (configurable):
  score >= 0.85 → AUTO_MERGE (create/update golden record)
  0.60 <= score < 0.85 → PENDING_REVIEW (route to review queue)
  score < 0.60 → NO_MATCH
```

**Phase 3 — Semantic Discovery (Vector Similarity):**
For records with NO blocking key match (no PAN, no mobile, no email):
- Query pgvector for nearest neighbors by name+city embedding
- Cosine similarity > 0.90 → create candidate pair → run Phase 2 scoring
- This catches matches that blocking would miss entirely

**Explainability output per match:**
```json
{
  "match_type": "PROBABILISTIC",
  "confidence": 0.87,
  "match_reasons": {
    "pan_exact": {"weight": 0.35, "score": 1.0, "contribution": 0.35},
    "mobile_exact": {"weight": 0.20, "score": 0.0, "contribution": 0.0, "note": "mobile missing in source B"},
    "email_exact": {"weight": 0.15, "score": 1.0, "contribution": 0.15},
    "name_jaro_winkler": {"weight": 0.12, "score": 0.92, "contribution": 0.11},
    "name_semantic": {"weight": 0.08, "score": 0.95, "contribution": 0.076},
    "dob_exact": {"weight": 0.05, "score": 1.0, "contribution": 0.05},
    "city": {"weight": 0.03, "score": 1.0, "contribution": 0.03},
    "segment": {"weight": 0.02, "score": 1.0, "contribution": 0.02}
  },
  "ai_explanation": "These records represent the same customer with high confidence (87%). 
    PAN ABCDE1234F matches exactly across Equity and Insurance systems. Email addresses match. 
    Names ('Rajesh K Sharma' vs 'R.K. Sharma') show 92% string similarity and 95% semantic similarity. 
    Mobile is missing in the Insurance record but all other identifiers align strongly."
}
```

#### [NEW] `backend/app/engines/conflict_resolver.py`
Survivorship rules (configurable per attribute via BRE):
```json
{
  "name": {"strategy": "SOURCE_PRIORITY", "priority": ["WEALTH", "INSURANCE", "EQUITY", "MF", "LOANS"]},
  "mobile": {"strategy": "MOST_RECENT"},
  "email": {"strategy": "MOST_RECENT"},
  "dob": {"strategy": "MOST_FREQUENT"},
  "city": {"strategy": "SOURCE_PRIORITY", "priority": ["INSURANCE", "LOANS", "WEALTH"]},
  "segment": {"strategy": "HIGHEST_VALUE_SOURCE"}
}
```
When no clear winner → flag for review with AI suggestion.

#### [NEW] `backend/app/engines/golden_record_builder.py`
- Builds golden record from cluster of matched source records
- Applies survivorship rules → records provenance per attribute
- Computes total_relationship_value (sum across sources)
- Builds products_held array
- Assigns RM (configurable: by highest value, most recent, or source priority)
- Increments version on every update (version history)

---

### Component 4: Opportunity Engine

#### [NEW] `backend/app/engines/opportunity_engine.py`

**Pipeline: Gap Analysis → Eligibility → Scoring → Explainability**

**Step 1 — Product Gap Analysis:**
```
Universe: [Equity, MutualFunds, Insurance, Loans, WealthManagement]
Customer has: [Equity, MutualFunds]
Missing: [Insurance, Loans, WealthManagement]
```

**Step 2 — Eligibility Rules (from config_rules, fully configurable):**
```json
{
  "Insurance": {
    "min_relationship_value": 100000,
    "required_products_any": ["Equity", "MutualFunds"],
    "min_tenure_months": 6,
    "excluded_segments": ["DORMANT", "NRI"],
    "max_age": 65
  },
  "WealthManagement": {
    "min_relationship_value": 2500000,
    "required_products_all": ["Equity", "MutualFunds"],
    "min_tenure_months": 12,
    "preferred_segments": ["HNI", "ULTRA_HNI"]
  },
  "Loans": {
    "min_relationship_value": 200000,
    "required_products_any": ["Equity", "MutualFunds", "Insurance"],
    "excluded_products": ["Loans"],
    "min_tenure_months": 3
  }
}
```

**Step 3 — Opportunity Scoring (configurable weights):**
```
score = w1×relationship_value_norm + w2×product_affinity + w3×recency + w4×engagement

Defaults: w1=0.35, w2=0.25, w3=0.20, w4=0.20
All configurable via Admin UI.
```

**Step 4 — RAG Explainability:**
```json
{
  "opportunity": "Insurance Cross-Sell",
  "score": 0.78,
  "score_breakdown": {
    "relationship_value": {"weight": 0.35, "raw": 520000, "normalized": 0.72, "contribution": 0.252},
    "product_affinity": {"weight": 0.25, "value": 0.85, "contribution": 0.213},
    "recency": {"weight": 0.20, "last_activity": "2024-01-15", "value": 0.90, "contribution": 0.180},
    "engagement": {"weight": 0.20, "value": 0.60, "contribution": 0.120}
  },
  "ai_reasoning": "Rajesh Sharma is a strong candidate for Insurance cross-sell. With ₹5.2L in 
    combined Equity and Mutual Fund holdings and active trading in the last 30 days, he shows 
    high financial engagement. His profile matches the Insurance eligibility criteria (min ₹1L 
    relationship value, existing Equity/MF products, 18-month tenure). The protection gap — 
    significant investments without insurance coverage — represents both a customer need and 
    a ₹1.56L potential opportunity."
}
```

---

### Component 5: RAG Engine

#### [NEW] `backend/app/engines/rag_engine.py`
Central RAG service using LangChain + Groq:

```python
class RAGEngine:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.1)
    
    async def explain_match(self, match_data, rules_context) -> str:
        """Generate human-readable match explanation"""
    
    async def explain_opportunity(self, opportunity, customer_profile, rules) -> str:
        """Generate opportunity reasoning"""
    
    async def suggest_conflict_resolution(self, conflicts, source_metadata) -> dict:
        """AI-powered conflict resolution suggestion"""
    
    async def natural_language_query(self, question, schema, user_role) -> dict:
        """Convert NL question to structured API query"""
    
    async def generate_customer_summary(self, golden_record) -> str:
        """Generate executive summary of customer relationship"""
```

#### [NEW] `backend/app/engines/embedding_service.py`
```python
class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def compute_embedding(self, text: str) -> list[float]:
        """Generate 384-dim embedding for customer attributes"""
    
    async def find_similar_records(self, embedding, threshold=0.90, limit=10):
        """pgvector ANN search for semantically similar records"""
    
    async def batch_embed_records(self, records: list) -> None:
        """Batch compute and store embeddings for source records"""
```

---

### Component 6: API Routers

#### [NEW] `backend/app/routers/auth.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/login` | POST | Public | Login → JWT access + refresh tokens |
| `/api/auth/refresh` | POST | Public | Refresh token rotation |
| `/api/auth/me` | GET | Any | Current user profile |
| `/api/auth/logout` | POST | Any | Invalidate refresh token |

Rate limiting: 5 failed attempts → 15-min lockout (tracked in Redis).

#### [NEW] `backend/app/routers/customers.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/customers` | GET | RM+ | List golden records (scoped by role) |
| `/api/customers/{id}` | GET | RM+ | Full Customer 360 with source lineage |
| `/api/customers/{id}/graph` | GET | RM+ | Identity graph data for D3.js |
| `/api/customers/{id}/summary` | GET | RM+ | AI-generated customer summary |
| `/api/customers/search` | GET | RM+ | Search by name, masked PAN, mobile |
| `/api/customers/nl-query` | POST | Manager+ | Natural language query |

**Data-level auth:** RM sees only assigned customers. Manager sees team. Admin sees all.

#### [NEW] `backend/app/routers/matching.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/matching/run` | POST | Admin | Trigger full identity resolution |
| `/api/matching/run-incremental` | POST | Admin | Match single new record |
| `/api/matching/results` | GET | Manager+ | View match results with confidence |
| `/api/matching/results/{id}/explain` | GET | Manager+ | AI explanation for a match |
| `/api/matching/progress` | WebSocket | Admin | Real-time matching progress |

#### [NEW] `backend/app/routers/review.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/review/queue` | GET | Manager+ | Pending reviews |
| `/api/review/{id}` | GET | Manager+ | Review item details with AI suggestion |
| `/api/review/{id}/approve` | POST | Manager+ | Approve merge |
| `/api/review/{id}/reject` | POST | Manager+ | Reject merge |
| `/api/review/{id}/manual-merge` | POST | Admin | Manual merge with custom selections |
| `/api/review/unmerge/{golden_id}` | POST | Admin | Unmerge a golden record |

#### [NEW] `backend/app/routers/opportunities.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/opportunities` | GET | RM+ | List opportunities (role-scoped) |
| `/api/opportunities/dashboard` | GET | Manager+ | Aggregated dashboard data |
| `/api/opportunities/{id}` | GET | RM+ | Opportunity detail with AI reasoning |
| `/api/opportunities/{id}/status` | PATCH | RM+ | Update status |
| `/api/opportunities/generate` | POST | Admin | Re-generate opportunities |

#### [NEW] `backend/app/routers/config.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/config/rules` | GET | Admin | List all configurable rules |
| `/api/config/rules/{id}` | PUT | Admin | Update rule (creates audit entry) |
| `/api/config/rules/{id}/history` | GET | Admin | Version history for a rule |
| `/api/config/rules/impact-preview` | POST | Admin | Preview impact of rule change before applying |

#### [NEW] `backend/app/routers/audit.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/audit/logs` | GET | Admin/Manager | Filtered audit trail |
| `/api/audit/logs/export` | GET | Admin | Export as CSV |

#### [NEW] `backend/app/routers/data_ingestion.py`
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/ingest/upload` | POST | Admin | Upload CSV source data |
| `/api/ingest/seed` | POST | Admin | Seed synthetic demo data |
| `/api/ingest/status` | GET | Admin | Ingestion job status |

---

### Component 7: Security & Middleware

#### [NEW] `backend/app/middleware/auth.py`
- JWT validation with RS256 or HS256
- Role extraction → request state injection
- Data-level authorization decorator:
```python
@data_scope(role_field="assigned_rm_id")
async def get_customers(current_user: User):
    # Automatically filters: RM→own, Manager→team, Admin→all
```

#### [NEW] `backend/app/middleware/security.py`
- Rate limiting via Upstash Redis (sliding window)
- Input sanitization (SQL injection, XSS prevention)
- Idempotency key validation for sensitive operations
- Request ID tracking for correlation
- Safe error responses (no stack traces, no sensitive data)

#### [NEW] `backend/app/utils/masking.py`
```python
def mask_pan(pan: str, role: str) -> str:
    if role == "ADMIN": return pan  # Full access
    return f"{pan[:5]}{'*' * 4}{pan[-1]}" if pan else None  # ABCDE****F

def mask_mobile(mobile: str, role: str) -> str:
    if role in ["ADMIN", "MANAGER"]: return mobile
    return f"{'*' * 6}{mobile[-4:]}"  # ******1234

def mask_email(email: str, role: str) -> str:
    if role in ["ADMIN", "MANAGER"]: return email
    user, domain = email.split("@")
    return f"{user[:2]}{'*' * 4}@{domain}"  # ra****@gmail.com
```

---

### Component 8: Frontend (Next.js 14)

#### Design System
- **Theme:** Dark mode with teal/emerald (#10B981) accent, deep navy (#0F172A) background
- **Typography:** Inter (Google Fonts)
- **Components:** shadcn/ui (Radix primitives + Tailwind)
- **Animations:** Framer Motion for page transitions, micro-interactions
- **Charts:** Recharts for dashboards
- **Graph:** D3.js force-directed for identity visualization

#### Pages

##### [NEW] `frontend/src/app/login/page.tsx`
Premium login with animated gradient background, role selector, rate-limit error feedback.

##### [NEW] `frontend/src/app/dashboard/page.tsx`
**Role-adaptive dashboard:**
- **RM:** My customers (count), active opportunities (with scores), relationship value (animated counter), recent matches, quick actions
- **Manager:** Team overview, opportunity pipeline funnel (Recharts), team leaderboard, pending reviews badge
- **Admin:** System health metrics, match statistics (pie chart by type), recent config changes, audit summary, data ingestion status

##### [NEW] `frontend/src/app/customers/[id]/page.tsx`
**Customer 360 — The Hero Screen:**

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back    CUSTOMER 360                        Role: RM      │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────────┐ │
│ │ 👤 Rajesh Kumar Sharma      │ │ 🔗 Match Confidence     │ │
│ │ PAN: ABCDE****F             │ │ ████████░░ 87%          │ │
│ │ Mobile: ******5678          │ │ Type: PROBABILISTIC     │ │
│ │ Email: ra****@gmail.com     │ │ Matched across 3 systems│ │
│ │ City: Mumbai | Segment: HNI │ │ [View Match Details]    │ │
│ └─────────────────────────────┘ └─────────────────────────┘ │
│                                                             │
│ ┌─ SOURCE LINEAGE ──────────────────────────────────────┐   │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │
│ │ │ EQUITY   │ │ MF       │ │ INSURANCE│               │   │
│ │ │ ₹3.2L    │ │ ₹1.8L    │ │ ₹0.2L    │               │   │
│ │ │ Name ✓   │ │ Name ✓   │ │ Name ⚠️   │← conflict    │   │
│ │ │ DOB ✓    │ │ DOB ✓    │ │ DOB ✓    │               │   │
│ │ │ Email ✓  │ │ Email ⚠️  │ │ Email ✓  │               │   │
│ │ └──────────┘ └──────────┘ └──────────┘               │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ PRODUCTS & VALUE ────────────────────────────────────┐   │
│ │  Total Relationship Value: ₹5,20,000 (animated)       │   │
│ │  ┌────────┐ ┌────────┐ ┌────────┐                     │   │
│ │  │Equity  │ │ MF     │ │Insure  │ Loans ○  Wealth ○  │   │
│ │  │ ₹3.2L  │ │ ₹1.8L  │ │ ₹0.2L  │ (missing products) │   │
│ │  └────────┘ └────────┘ └────────┘                     │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ OPPORTUNITIES ───────────────────────────────────────┐   │
│ │  🎯 Insurance Cross-Sell  Score: 0.78  Value: ₹1.56L  │   │
│ │  💡 AI: "High Equity+MF engagement, protection gap"   │   │
│ │  🎯 Wealth Mgmt Upsell   Score: 0.65  Value: ₹2.10L  │   │
│ │  💡 AI: "HNI segment, sufficient AUM, 18mo tenure"    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─ AI CUSTOMER SUMMARY ────────────────────────────────┐   │
│ │  "Rajesh is a high-value HNI client with ₹5.2L across│   │
│ │   Equity and MF. Active trader with weekly engagement.│   │
│ │   Key gap: No insurance coverage despite significant  │   │
│ │   portfolio — strong cross-sell candidate."           │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

##### [NEW] `frontend/src/app/identity-graph/page.tsx`
**Interactive D3.js Force-Directed Graph — THE WOW FACTOR:**
- Nodes colored by source system (Equity=blue, MF=green, Insurance=red, Loans=amber, Wealth=purple)
- Central golden node (gold color, larger)
- Edge thickness = confidence score
- Edge labels = match type + confidence
- Click node → side panel with record details
- Hover → highlight connected cluster
- Zoom/pan/drag support
- Cluster view for multiple golden records

##### [NEW] `frontend/src/app/review/page.tsx`
Review queue with side-by-side record comparison, conflict highlighting, AI suggestion panel, approve/reject/merge actions.

##### [NEW] `frontend/src/app/opportunities/page.tsx`
Sortable/filterable opportunity table, funnel chart, RM aggregation (Manager view), explainability modal with AI reasoning.

##### [NEW] `frontend/src/app/config/page.tsx`
**The judge-impressing config console:**
- Tabs: Matching Weights | Thresholds | Opportunity Rules | Source Precedence | Scoring
- Inline editing with sliders for weights/thresholds
- **"Apply & Re-run"** button → triggers re-matching → shows before/after comparison
- **Impact Preview** → "Changing threshold from 0.85→0.70 would auto-merge 12 more records"
- Change history timeline with diff view

##### [NEW] `frontend/src/app/audit/page.tsx`
Searchable audit log with filters, expandable rows showing old/new values.

##### [NEW] `frontend/src/app/ask/page.tsx`
**Natural Language Query Interface:**
- Chat-style input: "Show me HNI customers in Mumbai without Insurance"
- LLM converts → API query → displays results in table
- Query history sidebar

---

### Component 9: Synthetic Data

#### [NEW] `backend/app/seed/data_generator.py`

**~250 customers across 5 source systems (~600+ source records):**

| Scenario | Count | Purpose |
|---|---|---|
| Exact PAN across 3+ systems, different emails | 20 customers | Demo scenario 1 — deterministic match with conflicts |
| No PAN, matching mobile+email+name | 15 customers | Demo scenario 2 — probabilistic match |
| Shared mobile, conflicting name/DOB | 10 pairs | Demo scenario 3 — review queue routing |
| Equity+MF heavy, no Insurance | 25 customers | Demo scenario 4 — cross-sell opportunities |
| High-value single-system | 30 customers | Baseline, no-match cases |
| Garbled names, missing DOB, bad emails | 20 records | Robustness/edge cases |
| Same system duplicates | 8 records | Intra-system dedup |
| Semantically similar but different people | 5 pairs | False positive testing |
| High-value wealth, missing multiple products | 15 customers | Upsell + multiple opportunities |

**Pre-seeded users:**
- `admin` / `admin123` — ADMIN role
- `rm_priya` / `pass123` — RM (assigned 40 customers)
- `rm_vikram` / `pass123` — RM (assigned 35 customers)
- `rm_anita` / `pass123` — RM (assigned 30 customers)
- `mgr_sanjay` / `pass123` — MANAGER (oversees all 3 RMs)
- `approver_neha` / `pass123` — CREDIT_APPROVER

---

### Component 10: Deployment

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   VERCEL        │     │   RENDER        │     │   SUPABASE      │
│   (Frontend)    │────▶│   (Backend)     │────▶│   (PostgreSQL   │
│   Next.js 14    │     │   FastAPI       │     │    + pgvector)  │
│   Edge Network  │     │   Docker        │     │   Free Tier     │
│   Free Tier     │     │   Free Tier     │     │                │
└────────────────┘     └───────┬─────────┘     └────────────────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
              ┌─────▼──┐ ┌────▼───┐ ┌────▼───────┐
              │ Groq   │ │Upstash │ │ sentence-  │
              │ API    │ │ Redis  │ │ transformers│
              │Free    │ │Free    │ │ (in-process)│
              └────────┘ └────────┘ └────────────┘
```

#### [NEW] `Dockerfile` (Backend)
Multi-stage build: Python 3.11 slim, install deps, download embedding model, run uvicorn.

#### [NEW] `docker-compose.yml`
Local dev: PostgreSQL + pgvector + Redis + Backend + Frontend.

#### [NEW] `render.yaml`
Render Blueprint for one-click backend deployment.

#### [NEW] `frontend/vercel.json`
Vercel config with API proxy rewrites to Render backend.

---

### Component 11: Flutter Mobile App (Bonus — Lower Priority)

#### [NEW] `mobile/lib/main.dart`
Minimal but functional RM mobile app:
- Login screen with JWT auth
- Customer list (assigned customers only)
- Customer 360 detail view
- Opportunity list with push notifications
- Pull-to-refresh, offline cached customer list

---

## 10-Minute Demo Script

### 2 min — Architecture & Problem Interpretation
1. Show architecture diagram (the one above)
2. "We built a **graph-based identity resolution engine** augmented with **AI semantic matching** and **RAG-powered explainability** — not a simple JOIN, not an LLM wrapper"
3. Explain data flow: Ingest → Standardize + Embed → Block → Match (deterministic + probabilistic + semantic) → Golden Record → Opportunity Engine → RAG Explainer
4. Mention tech stack highlights: pgvector, Groq/Llama 3.1, LangChain, Next.js 14

### 5 min — Live Demo

**Scenario 1 (1 min):** Login as RM → Customer 360 for customer matched via PAN across Equity/MF/Insurance. Show source lineage with conflict icons. Show masked PAN. Click "View Match Details" → see 87% confidence with breakdown. Click "AI Explanation" → see RAG-generated reasoning.

**Scenario 2 (1 min):** Show customer matched WITHOUT PAN — mobile+email+name matched probabilistically at 0.78. Show semantic name matching caught "R.K. Sharma" ↔ "Rajesh Kumar Sharma". Show identity graph visualization in D3.js.

**Scenario 3 (45s):** Show review queue — records sharing mobile but conflicting DOB. AI suggestion: "Likely same person — DOB differs by transposed digits (likely data entry error)." Manager approves. Show RM can't access review queue → 403.

**Scenario 4 (45s):** Opportunity dashboard → Customer with Equity+MF but no Insurance. Score 0.78. Click → AI reasoning explains the cross-sell logic. RM marks "Assigned".

**Scenario 5 (1.5 min):** **THE JUDGE-WOWER:**
- Admin opens Config Console
- Changes auto-merge threshold from 0.85 → 0.70
- Clicks "Impact Preview" → "This would auto-merge 12 additional records"
- Clicks "Apply & Re-run" → matching re-runs → dashboard updates live
- Changes opportunity minimum score from 0.60 → 0.40 → more opportunities appear
- Show audit log captured both changes with old/new values, actor, timestamp
- **Security demo:** RM tries accessing another RM's customer → 403. Show `.env` file — no hardcoded secrets.

### 2 min — Backend/Code Walkthrough
- Show identity_resolver.py — explain blocking + weighted scoring + semantic phase
- Show config_rules in database — fully configurable
- Show audit_log table — captures everything
- Show RAG engine — purposeful AI, not a wrapper
- Show embedding_service — pgvector for semantic matching

### 1 min — Scalability & Next Steps
- Blocking strategy: O(n×b) not O(n²) — scales to millions
- pgvector with HNSW index: ANN search in milliseconds at any scale
- Incremental matching: new records only compared against existing clusters
- Would add: Kafka for streaming ingestion, dedicated vector DB (Pinecone/Weaviate), Neo4j for complex graph queries, CDC for real-time sync
- Flutter mobile app for RM field access (show if built)

---

## Verification Plan

### Automated Tests
```bash
# Identity resolution tests
pytest backend/tests/test_identity_resolver.py -v
# - Test deterministic PAN matching
# - Test probabilistic scoring with known weights
# - Test semantic matching catches name variants
# - Test threshold changes affect merge decisions

# Opportunity engine tests
pytest backend/tests/test_opportunity_engine.py -v
# - Test product gap detection
# - Test eligibility rule evaluation
# - Test scoring calculation

# Auth & security tests
pytest backend/tests/test_auth.py -v
# - Test RM can't access other RM's customers
# - Test Manager sees team, Admin sees all
# - Test rate limiting after 5 failed logins
# - Test PAN masking in API responses

# Data standardization tests
pytest backend/tests/test_standardizer.py -v
# - Test PAN normalization
# - Test mobile format variations
# - Test name cleaning edge cases
```

### Manual Verification
- [ ] All 5 demo scenarios work end-to-end
- [ ] Unauthorized access returns 403 from backend (not just hidden UI)
- [ ] PAN/mobile/email masked in API responses for RM role
- [ ] Config change creates audit log entry
- [ ] Changing threshold re-runs matching, results change
- [ ] Missing/malformed data doesn't crash (graceful error)
- [ ] Duplicate record upload is handled (idempotency)
- [ ] AI explanations are relevant and accurate
- [ ] Identity graph renders correctly in D3.js
- [ ] Frontend deployed on Vercel, backend on Render, both accessible

---

## File Structure

```
Codeissance26_Skill-Issue/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app + lifespan
│   │   ├── config.py                  # Pydantic Settings (.env)
│   │   ├── database.py                # Async SQLAlchemy + pgvector
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── source_record.py
│   │   │   ├── golden_record.py
│   │   │   ├── identity_edge.py
│   │   │   ├── opportunity.py
│   │   │   ├── config_rule.py
│   │   │   ├── audit_log.py
│   │   │   └── review_queue.py
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── customer.py
│   │   │   ├── matching.py
│   │   │   ├── opportunity.py
│   │   │   ├── config.py
│   │   │   └── audit.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── customers.py
│   │   │   ├── matching.py
│   │   │   ├── review.py
│   │   │   ├── opportunities.py
│   │   │   ├── config.py
│   │   │   ├── audit.py
│   │   │   └── data_ingestion.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── data_standardizer.py   # Normalization pipeline
│   │   │   ├── identity_resolver.py   # 3-phase matching engine
│   │   │   ├── conflict_resolver.py   # Survivorship rules
│   │   │   ├── golden_record_builder.py
│   │   │   ├── opportunity_engine.py  # Gap → Eligibility → Score
│   │   │   ├── rag_engine.py          # LangChain + Groq RAG
│   │   │   └── embedding_service.py   # sentence-transformers + pgvector
│   │   ├── middleware/
│   │   │   ├── auth.py                # JWT + RBAC + data scoping
│   │   │   └── security.py            # Rate limit, sanitize, idempotency
│   │   ├── utils/
│   │   │   ├── masking.py             # PAN/mobile/email masking
│   │   │   └── validators.py          # Input validation helpers
│   │   └── seed/
│   │       ├── data_generator.py      # Synthetic data for all scenarios
│   │       └── seed_config.py         # Default BRE rules
│   ├── tests/
│   │   ├── test_identity_resolver.py
│   │   ├── test_opportunity_engine.py
│   │   ├── test_auth.py
│   │   ├── test_standardizer.py
│   │   └── test_masking.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout + providers
│   │   │   ├── page.tsx               # Landing → redirect to dashboard
│   │   │   ├── globals.css            # Design system
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx           # Role-adaptive dashboard
│   │   │   ├── customers/
│   │   │   │   ├── page.tsx           # Customer list
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Customer 360
│   │   │   ├── identity-graph/
│   │   │   │   └── page.tsx           # D3.js graph visualization
│   │   │   ├── review/
│   │   │   │   └── page.tsx           # Review queue
│   │   │   ├── opportunities/
│   │   │   │   └── page.tsx           # Opportunity dashboard
│   │   │   ├── config/
│   │   │   │   └── page.tsx           # Admin config console
│   │   │   ├── audit/
│   │   │   │   └── page.tsx           # Audit log
│   │   │   └── ask/
│   │   │       └── page.tsx           # NL query interface
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── Navbar.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── MaskedField.tsx
│   │   │   ├── ConfidenceBadge.tsx
│   │   │   ├── ExplainCard.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── IdentityGraph.tsx      # D3.js component
│   │   │   ├── SourceSystemBadge.tsx
│   │   │   └── OpportunityCard.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                 # Axios client with JWT interceptor
│   │   │   ├── auth.ts                # Auth context + hooks
│   │   │   └── utils.ts
│   │   └── stores/
│   │       └── useStore.ts            # Zustand global state
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── vercel.json
├── mobile/                            # (Bonus — Flutter)
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   ├── services/
│   │   └── models/
│   └── pubspec.yaml
├── docker-compose.yml
├── render.yaml
├── .env.example
└── README.md
```

---

## Open Questions

> [!IMPORTANT]
> **Groq API Key:** Do you have a Groq account for free Llama 3.1 access? If not, we can sign up at groq.com (free tier = 30 RPM, sufficient for demo). Alternative: Together AI, or Ollama locally as fallback.

> [!IMPORTANT]
> **Supabase:** Shall I use Supabase (managed PostgreSQL + pgvector, free tier) or do you prefer self-hosted PostgreSQL on Render? Supabase is faster to set up and has pgvector built-in.

> [!IMPORTANT]
> **shadcn/ui + Tailwind:** The plan uses shadcn/ui (built on Tailwind) for Next.js. This gives us premium components fast. OK to proceed with Tailwind for this project?

> [!IMPORTANT]  
> **Priority call:** With 24 hours, should I prioritize (a) getting ALL features working end-to-end with solid demo, or (b) building the Flutter app too? I recommend (a) first, Flutter only if time permits.

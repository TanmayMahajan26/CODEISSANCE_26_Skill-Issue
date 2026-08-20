# Nexus360 Backend — Integration Guide & Service Boundaries

This document defines the clear architecture boundaries, service protocols, database schemas, and REST API contracts for seamless integration with the **ML/AI Intelligence Layer** and **Frontend UI**.

---

## 1. Architecture Overview & Component Responsibilities

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             CLIENT / FRONTEND                            │
│                     (Next.js 14 / Enterprise Dark UI)                    │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ REST APIs (JSON)
┌────────────────────────────────────▼─────────────────────────────────────┐
│                            CORE BACKEND (FastAPI)                        │
│  ┌───────────────────────┐ ┌──────────────────────┐ ┌──────────────────┐ │
│  │ Ingestion & Standard. │ │ Identity Resolution  │ │ Golden Customer  │ │
│  │ (CSV, Normalization)  │ │ (Blocking, Scoring)  │ │ (360, Lineage)   │ │
│  └───────────────────────┘ └──────────────────────┘ └──────────────────┘ │
│  ┌───────────────────────┐ ┌──────────────────────┐ ┌──────────────────┐ │
│  │ Config & BRE Engine   │ │ Review Queue & Audit │ │ Opportunity Stub │ │
│  │ (What-If Simulator)   │ │ (Approve, Unmerge)   │ │ (Product Gaps)   │ │
│  └───────────────────────┘ └──────────────────────┘ └──────────────────┘ │
└───────────────────┬──────────────────────────────────┬───────────────────┘
                    │ Protocol / Hook                  │ PostgreSQL + pgvector
┌───────────────────▼──────────────────┐   ┌───────────▼───────────────────┐
│     ML/AI INTELLIGENCE LAYER         │   │       SUPABASE POSTGRESQL     │
│  (Sentence Transformers / Groq RAG)  │   │  • source_records             │
│  • Vector Embeddings (384-dim)       │   │  • golden_customers           │
│  • Semantic Similarity Engine        │   │  • identity_links             │
│  • RAG Explainer (Llama 3.1 70B)     │   │  • match_decisions            │
│  • Natural Language Query Converter  │   │  • review_cases               │
│  • Next-Best-Opportunity AI Engine   │   │  • config_rules               │
└──────────────────────────────────────┘   │  • audit_logs                 │
                                           │  • opportunities              │
                                           └───────────────────────────────┘
```

---

## 2. ML/AI Developer Integration Interfaces

### Interface A: Semantic Embedding Service (`app/services/embedding_service.py`)

The identity resolution engine calls `EmbeddingService` during feature extraction. To plug in a custom embedding model (e.g. `sentence-transformers/all-MiniLM-L6-v2`):

```python
from app.services.embedding_service import set_embedding_service, EmbeddingService

class SentenceTransformerEmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    async def get_embedding(self, text: str) -> list[float]:
        if not text:
            return []
        embedding = self.model.encode(text)
        return embedding.tolist()

    async def compute_similarity(self, text_a: str, text_b: str) -> float:
        if not text_a or not text_b:
            return 0.0
        emb_a = self.model.encode(text_a)
        emb_b = self.model.encode(text_b)
        from sentence_transformers.util import cos_sim
        return float(cos_sim(emb_a, emb_b)[0][0])

# Register your implementation on app startup:
set_embedding_service(SentenceTransformerEmbeddingService())
```

### Interface B: RAG Explanation Engine (`MatchDecision.ai_explanation` & `IdentityLink.ai_explanation`)

When a match or review is produced, populate the `ai_explanation` text field using your Groq / LLM pipeline.

- **Schema Field**: `MatchDecision.ai_explanation` (String)
- **Schema Field**: `IdentityLink.ai_explanation` (String)
- **Schema Field**: `ReviewCase.ai_suggestion` (Text)

### Interface C: Next-Best-Opportunity Engine (`app/services/opportunity_service.py`)

The baseline opportunity engine identifies product gaps across the universe `[Equity, MutualFunds, Insurance, Loans, Wealth]`. You can extend or replace `generate_opportunities_for_golden` to inject advanced ML recommendation scores.

- **Target Table**: `opportunities`
- **Fields**: `opportunity_type`, `product_recommended`, `score` (0.0 to 1.0), `score_breakdown` (JSONB), `ai_reasoning` (Text), `potential_value` (Decimal), `eligibility_met` (JSONB).

---

## 3. Database Schema Overview

| Table | Purpose | Key Columns |
|---|---|---|
| `source_records` | Raw + normalized incoming records | `id`, `source_system`, `source_record_id`, `normalized_*`, `balance_aum`, `relationship_value`, `name_embedding` |
| `golden_customers` | De-duplicated 360 view | `golden_customer_id` (GOLD-NNNNNN), `canonical_*`, `total_relationship_value`, `products_held` (JSONB), `attribute_provenance` (JSONB) |
| `identity_links` | Source ↔ Golden mappings | `source_record_id`, `golden_customer_id`, `match_confidence`, `match_method`, `ai_explanation` |
| `match_decisions` | Pairwise match evaluations | `record_a_id`, `record_b_id`, `pan_match`, `name_similarity`, `name_semantic_similarity`, `final_score`, `decision`, `reasoning` |
| `review_cases` | Human review queue | `match_decision_id`, `priority`, `status`, `review_type`, `ai_suggestion`, `details` |
| `config_rules` | Dynamic BRE rules | `category`, `rule_key`, `rule_value` (JSONB), `version`, `is_active` |
| `audit_logs` | Audit trail | `actor_username`, `actor_role`, `action`, `entity_type`, `entity_id`, `old_value`, `new_value`, `timestamp` |
| `opportunities` | Next-Best-Action recommendations | `golden_customer_id`, `opportunity_type`, `product_recommended`, `score`, `ai_reasoning`, `potential_value`, `status` |

---

## 4. Key REST API Endpoints for Frontend

### Identity Resolution & Customers
- `GET /api/v1/customers` — List golden customers with search & pagination
- `GET /api/v1/customers/search?q=...` — Dedicated customer search
- `GET /api/v1/customers/{id}` — Full Customer 360 with product holdings & lineage
- `GET /api/v1/customers/{id}/graph` — D3.js force-directed graph nodes & edges
- `GET /api/v1/customers/{id}/waterfall` — Step-by-step confidence score breakdown

### Configuration & What-If Simulator
- `GET /api/v1/config/rules` — List all BRE rules
- `PUT /api/v1/config/rules/{key}` — Update BRE rules (e.g. weights/thresholds)
- `POST /api/v1/config/rules/impact-preview` — What-If simulator split-screen preview

### Review Queue & Conflict Resolution
- `GET /api/v1/reviews?status=PENDING` — Pending manual review cases
- `POST /api/v1/reviews/{id}/approve` — Confirm match
- `POST /api/v1/reviews/{id}/reject` — Confirm non-match
- `POST /api/v1/reviews/{id}/manual-merge` — Manual merge with custom field picks
- `POST /api/v1/reviews/unmerge/{golden_id}` — Split golden customer record

### Next-Best-Opportunity Engine
- `GET /api/v1/opportunities` — List recommendations (filterable by status/RM)
- `GET /api/v1/opportunities/dashboard` — Aggregated sales funnel and relationship value
- `PATCH /api/v1/opportunities/{id}/status` — Update opportunity state (ASSIGNED, CONVERTED, DISMISSED)
- `POST /api/v1/opportunities/generate` — Trigger batch recommendation pipeline

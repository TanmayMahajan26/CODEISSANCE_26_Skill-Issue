# Phase 3: Next-Best-Opportunity Engine & AI RAG Services - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-20
**Phase:** 03-next-best-opportunity-engine-ai-rag-services
**Areas discussed:** Opportunity Generation Timing, AI RAG Explainability Trigger, NL Query Translation Approach

---

## Opportunity Generation Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-compute and store in DB via a batch job | (Recommended) Offers instant 0-latency UI, fits the 'opportunities' table in schema | ✓ |
| Generate on-the-fly via API | Always real-time, but UI latency might be high | |

**User's choice:** (Recommended) Pre-compute and store in DB via a batch job
**Notes:** 

| Option | Description | Selected |
|--------|-------------|----------|
| Automatically as the final step of the identity resolution pipeline | (Recommended) Ensures recommendations are always in sync with new Golden Records | ✓ |
| On a separate cron schedule (e.g., nightly) | | |

**User's choice:** (Recommended) Automatically as the final step of the identity resolution pipeline
**Notes:** 

---

## AI RAG Explainability Trigger

| Option | Description | Selected |
|--------|-------------|----------|
| Eagerly: Generate explanations in the batch job alongside opportunities | (Recommended) Zero latency in UI, but consumes more Groq tokens | ✓ |
| Lazily: Generate explanation only when the RM clicks "Explain why" in the UI | Saves tokens, but introduces a 1-3s delay in the UI | |

**User's choice:** (Recommended) Eagerly: Generate explanations in the batch job alongside opportunities
**Notes:** 

---

## NL Query Translation Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Tool Calling / JSON Output | (Recommended) The LLM generates a structured JSON object representing API parameters (filters, sorts, limits), and the backend queries the database using SQLAlchemy. (Safer, integrates easily with RBAC) | ✓ |
| Text-to-SQL | The LLM generates raw SQL queries to execute directly against the database. (More flexible, but high security risk and harder to scope RBAC) | |

**User's choice:** (Recommended) Tool Calling / JSON Output
**Notes:** 

---

## the agent's Discretion

None

## Deferred Ideas

None

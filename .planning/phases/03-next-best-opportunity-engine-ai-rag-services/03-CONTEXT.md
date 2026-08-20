# Phase 3: Next-Best-Opportunity Engine & AI RAG Services - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the Next-Best-Opportunity recommendation engine with product gap analysis, eligibility checking, composite scoring, and Groq/Llama 3.1 RAG services for match explanations, opportunity reasoning, NL query translation, and review suggestions.

</domain>

<decisions>
## Implementation Decisions

### Opportunity Generation Timing
- **D-01:** Pre-compute and store opportunities in DB via a batch job (fits the 'opportunities' table in schema).
- **D-02:** Run the pre-compute batch job automatically as the final step of the identity resolution pipeline.

### AI RAG Explainability Trigger
- **D-03:** Generate explanations eagerly in the batch job alongside opportunities.

### NL Query Translation Approach
- **D-04:** Use Tool Calling / JSON Output: The LLM generates a structured JSON object representing API parameters, and backend queries using SQLAlchemy.

### the agent's Discretion
None.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Foundational Docs
- `.planning/REQUIREMENTS.md` — Core requirements mapping
- `.planning/ROADMAP.md` — Overall architecture roadmap
- `PRD.md` — Feature specs

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app.services.golden_record_builder` — Pipeline engine hook for triggering batch generation.
- `app.db.models.opportunity` — Pre-existing schema for opportunities.
- `app.db.models.golden_record` — Source for identity graph.

### Established Patterns
- SQLAlchemy AsyncSession for DB operations.
- Dependency Injection (`get_db`) for sessions.
- LangChain / Groq setup for AI.

### Integration Points
- Add batch job trigger at the end of `run_resolution` in `app/api/resolution.py`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-next-best-opportunity-engine-ai-rag-services*
*Context gathered: 2026-08-20*

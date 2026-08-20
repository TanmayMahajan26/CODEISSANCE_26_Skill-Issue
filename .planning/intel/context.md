# Context & Background (Synthesized)

## Problem Overview
- **Domain**: Financial Services Multi-Product Customer Unification (PS-04).
- **Siloed Systems**: Equity, Mutual Funds, Insurance, Loans, Wealth Management.
- **Key Pain Point**: Fragmented customer identities prevent unified relationship valuation, result in duplicated outreach by multiple RMs, and cause missed high-value cross-sell opportunities (e.g. investment client without protection/insurance).

## Core Personas & Value Delivery
- **RM (Priya)**: Needs unified 360 profile, confidence waterfall explaining matches, and prioritized opportunity cards to drive conversations. Scoped to 40 assigned customers with masked PII.
- **Manager (Sanjay)**: Needs cross-team visibility, opportunity pipeline metrics, and a review queue to resolve ambiguous matches with AI assist.
- **Admin (Amit)**: Needs live configuration sliders, What-If simulator to test threshold impacts before applying, data quality scorecards, and full audit logs.
- **Credit Approver (Neha)**: Needs read-only Customer 360 overview for risk appraisal.

## Synthetic Dataset & Demo Scenarios
1. **Scenario 1 (Deterministic Match with Lineage)**: Exact PAN match across 3 systems with minor email variations.
2. **Scenario 2 (Probabilistic Match & Semantic Discovery)**: No PAN; matching Mobile + Email + Name caught by Jaro-Winkler & pgvector embedding ("R.K. Sharma" ↔ "Rajesh Kumar Sharma"). D3.js identity graph visualization.
3. **Scenario 3 (Review Queue & Discrepancy Resolution)**: Shared mobile with conflicting DOB; routed to review queue with AI suggestion.
4. **Scenario 4 (Opportunity Generation & RAG Explanation)**: Equity + MF customer without Insurance; scored at 0.78 with natural language RAG explanation.
5. **Scenario 5 (Live Config Mutation & What-If Simulator)**: Admin drags auto-merge threshold from 0.85 to 0.70; What-If simulator previews +12 auto-merges; "Apply & Re-run" triggers live re-evaluation and updates audit trail.

## Rubric Weightings & Focus
- Approach & System Design: 12%
- Architecture & Code Quality: 13%
- Programming & Code Quality: 13%
- Configurability & BRE: 12%
- Backend & Data Design (pgvector): 10%
- UI/UX (D3 Graph, Dark Fintech Theme): 8%
- Robustness & Edge Cases: 8%
- Scalability: 7%
- Innovation (RAG & Semantic Matching): 7%
- Security & RBAC: 10%

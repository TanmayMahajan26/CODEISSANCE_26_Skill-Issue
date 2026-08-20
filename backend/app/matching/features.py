"""
Nexus360 — Feature Extraction Orchestrator.

Re-exports the core extract_features function and provides any
additional feature-engineering helpers needed by the pipeline.
"""

from app.matching.fuzzy import extract_features  # noqa: F401

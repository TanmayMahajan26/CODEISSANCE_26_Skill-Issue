"""
Nexus360 — Embedding Service Module.

Provides clean abstraction and local ML implementation for semantic embedding generation
and similarity computation using sentence-transformers (all-MiniLM-L6-v2, 384 dimensions).
Includes a graceful fallback implementation (DefaultEmbeddingService) if the ML model is
unavailable or fails to load.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Protocol

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EmbeddingService(Protocol):
    """Protocol for semantic embedding services."""

    async def get_embedding(self, text: str) -> List[float]:
        """Generate 384-dimensional vector embedding for input text."""
        ...

    async def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine/semantic similarity (0.0 to 1.0) between two text strings."""
        ...

    def compute_similarity_sync(self, text_a: str, text_b: str) -> float:
        """Synchronous similarity calculation for feature extraction engine."""
        ...


class DefaultEmbeddingService:
    """
    Default fallback implementation when ML sentence-transformers service is not yet loaded.
    Uses fallback token-based string similarity.
    """

    async def get_embedding(self, text: str) -> List[float]:
        """Return dummy zero-vector placeholder for 384 dimensions."""
        if not text:
            return []
        return [0.0] * 384

    async def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Fallback semantic similarity calculation using RapidFuzz ratio."""
        return self.compute_similarity_sync(text_a, text_b)

    def compute_similarity_sync(self, text_a: str, text_b: str) -> float:
        """Synchronous fallback semantic similarity calculation using RapidFuzz ratio."""
        if not text_a or not text_b:
            return 0.0
        return round(fuzz.token_sort_ratio(text_a, text_b) / 100.0, 4)


class SentenceTransformerEmbeddingService:
    """
    Local ML embedding service using sentence-transformers/all-MiniLM-L6-v2.
    Produces 384-dimensional L2-normalized vector embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None
        self._load_failed = False

    def _load_model(self):
        """Lazily load sentence-transformer model once."""
        if self._model is not None:
            return self._model
        if self._load_failed:
            return None

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model '%s'...", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model '%s' loaded successfully!", self.model_name)
            return self._model
        except Exception as exc:
            logger.error("Failed to load SentenceTransformer model '%s': %s", self.model_name, exc)
            self._load_failed = True
            return None

    def compute_similarity_sync(self, text_a: str, text_b: str) -> float:
        """Synchronous CPU-bound cosine similarity computation."""
        if not text_a or not text_b or not text_a.strip() or not text_b.strip():
            return 0.0

        model = self._load_model()
        if model is None:
            return round(fuzz.token_sort_ratio(text_a, text_b) / 100.0, 4)

        try:
            from sentence_transformers import util
            embeddings = model.encode([text_a.strip(), text_b.strip()], normalize_embeddings=True)
            sim = float(util.cos_sim(embeddings[0], embeddings[1])[0][0])
            return max(0.0, min(1.0, round(sim, 4)))
        except Exception as exc:
            logger.warning("Error computing similarity between '%s' and '%s': %s", text_a, text_b, exc)
            return round(fuzz.token_sort_ratio(text_a, text_b) / 100.0, 4)

    def _sync_get_embedding(self, text: str) -> List[float]:
        """Synchronous CPU-bound embedding generation."""
        if not text or not text.strip():
            return []
        model = self._load_model()
        if model is None:
            return [0.0] * 384

        try:
            embedding = model.encode(text.strip(), normalize_embeddings=True)
            return [float(x) for x in embedding]
        except Exception as exc:
            logger.warning("Error generating embedding for '%s': %s", text, exc)
            return [0.0] * 384

    async def get_embedding(self, text: str) -> List[float]:
        """Generate 384-dimensional vector embedding asynchronously (offloaded to thread)."""
        return await asyncio.to_thread(self._sync_get_embedding, text)

    async def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity asynchronously (offloaded to thread)."""
        return await asyncio.to_thread(self.compute_similarity_sync, text_a, text_b)


# Global singleton instance
_embedding_service: EmbeddingService = DefaultEmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Get active embedding service instance."""
    return _embedding_service


def set_embedding_service(service: EmbeddingService) -> None:
    """Register custom ML embedding service instance."""
    global _embedding_service
    _embedding_service = service
    logger.info("Registered custom ML EmbeddingService: %s", service.__class__.__name__)


def init_embedding_service() -> EmbeddingService:
    """
    Attempt to initialize and register SentenceTransformerEmbeddingService.
    Falls back to DefaultEmbeddingService if loading fails.
    """
    try:
        service = SentenceTransformerEmbeddingService()
        set_embedding_service(service)
        return service
    except Exception as exc:
        logger.warning("Could not initialize SentenceTransformerEmbeddingService, using fallback: %s", exc)
        return get_embedding_service()


async def backfill_name_embeddings(session: AsyncSession) -> int:
    """
    Safely backfill 384-dimensional name embeddings for existing SourceRecord rows
    where normalized_name is present but name_embedding is NULL.
    Does not duplicate records or alter any other fields.
    """
    from sqlalchemy import select
    from app.models.source_record import SourceRecord

    res = await session.execute(
        select(SourceRecord).where(
            SourceRecord.name_embedding.is_(None),
            SourceRecord.normalized_name.isnot(None),
        )
    )
    records = res.scalars().all()
    if not records:
        logger.info("No records requiring name embedding backfill.")
        return 0

    logger.info("Backfilling name embeddings for %d records in database...", len(records))
    service = get_embedding_service()
    updated = 0
    for record in records:
        name = record.normalized_name or record.original_name
        if name:
            emb = await service.get_embedding(name)
            if emb:
                record.name_embedding = emb
                updated += 1

    await session.commit()
    logger.info("Successfully backfilled name embeddings for %d records.", updated)
    return updated

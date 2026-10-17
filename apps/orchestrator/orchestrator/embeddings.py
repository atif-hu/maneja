from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod

from orchestrator.config import get_settings

EMBEDDING_DIM = 512


class EmbeddingProvider(ABC):
    """Cross-modal embedding provider: reference images embedded once at
    upload time, concept-brief text embedded at generation time, both
    compared via cosine distance (pgvector's `<=>` operator) so text can be
    ranked against images in the same vector space."""

    name: str = "unknown"

    @abstractmethod
    async def embed_image(self, image_bytes: bytes) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError


def _deterministic_embedding(seed_bytes: bytes) -> list[float]:
    """Seed a PRNG from a sha256 digest of the input so the same input
    always produces the same vector, then L2-normalize (cosine distance is
    scale-invariant but normalizing keeps distances in the expected [0, 2]
    range and matches what a real embedding model would return)."""
    digest = hashlib.sha256(seed_bytes).digest()
    rng = random.Random(digest)
    vector = [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIM)]
    norm = sum(v * v for v in vector) ** 0.5
    if norm == 0:
        return vector
    return [v / norm for v in vector]


class StubEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free embedding for local/dev use — the
    default, mirroring how `image_provider` defaults to "stub".

    IMPORTANT: this is NOT a semantically meaningful embedding. Cosine
    similarity between two stub vectors reflects nothing about visual or
    textual similarity between the inputs; it only guarantees the same
    input always maps to the same vector. It exists purely so the
    embedding plumbing (upsert into image_embeddings, cosine ordering,
    ivfflat index, reference-image ranking) can be exercised end-to-end
    without external dependencies or API keys. A real provider (e.g. a
    hosted CLIP model) is an explicit Phase 2 follow-up once one is
    chosen — do not treat this as "real" ranking quality.
    """

    name = "stub-hash-512"

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        return _deterministic_embedding(b"image:" + image_bytes)

    async def embed_text(self, text: str) -> list[float]:
        return _deterministic_embedding(b"text:" + text.encode("utf-8"))


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "stub":
        return StubEmbeddingProvider()
    raise RuntimeError(
        f"Unknown or unimplemented embedding_provider={settings.embedding_provider!r}; "
        "only 'stub' is implemented in Phase 1 (see orchestrator/embeddings.py)"
    )


def to_vector_literal(vector: list[float]) -> str:
    """Render a Python float list as a pgvector text literal, e.g.
    '[0.1,0.2,...]', for use with a `CAST(:param AS vector)` bind param."""
    return "[" + ",".join(repr(float(v)) for v in vector) + "]"

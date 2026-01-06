"""ChromaDB embedding service implementation."""

from __future__ import annotations

from typing import Any

from memorycore.embedding.base import EmbeddingService
from memorycore.exceptions.embedding import EmbeddingModelError


class ChromaDBEmbeddingService(EmbeddingService):
    """ChromaDB embedding service using default model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._dimension: int | None = None

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        try:
            # ChromaDB handles embeddings internally, but for standalone use
            # we'd use sentence-transformers directly
            # This is a simplified version - in practice, ChromaDB generates embeddings
            # when you add documents, so this service is mainly for query embeddings
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingModelError(f"Failed to generate embedding: {e}", model_name=self.model_name) from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            embeddings = model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingModelError(f"Failed to generate batch embeddings: {e}", model_name=self.model_name) from e

    def get_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self._dimension is None:
            # Default dimension for all-MiniLM-L6-v2
            self._dimension = 384
        return self._dimension

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check."""
        try:
            # Test embedding generation
            test_embedding = await self.embed("test")
            return {
                "status": "healthy",
                "model": self.model_name,
                "dimension": self.get_dimension(),
                "test_embedding_length": len(test_embedding),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


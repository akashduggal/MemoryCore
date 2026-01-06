"""Base embedding service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform a health check."""
        pass


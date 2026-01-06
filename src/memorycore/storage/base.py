"""Base storage backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from memorycore.core.memory import Memory


class SearchResult:
    """Result from a memory search."""

    def __init__(self, memory: Memory, score: float, metadata: dict[str, Any] | None = None):
        self.memory = memory
        self.score = score
        self.metadata = metadata or {}


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass

    @abstractmethod
    async def save(self, memory: Memory) -> None:
        """Save a memory."""
        pass

    @abstractmethod
    async def get(self, memory_id: UUID, tenant_id: str) -> Memory | None:
        """Get a memory by ID."""
        pass

    @abstractmethod
    async def delete(self, memory_id: UUID, tenant_id: str) -> None:
        """Delete a memory."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        tenant_id: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search memories by embedding similarity."""
        pass

    @abstractmethod
    async def list(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[Memory]:
        """List memories with optional filters."""
        pass

    @abstractmethod
    async def count(self, tenant_id: str, filters: dict[str, Any] | None = None) -> int:
        """Count memories matching filters."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform a health check."""
        pass


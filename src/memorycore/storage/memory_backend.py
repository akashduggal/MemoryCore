"""In-memory storage backend for testing."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from memorycore.core.memory import Memory
from memorycore.storage.base import SearchResult, StorageBackend


class InMemoryBackend(StorageBackend):
    """In-memory storage backend (for testing)."""

    def __init__(self):
        self._memories: dict[tuple[UUID, str], Memory] = {}
        self._embeddings: dict[tuple[UUID, str], list[float]] = {}

    async def initialize(self) -> None:
        """Initialize the storage backend."""
        pass

    async def save(self, memory: Memory) -> None:
        """Save a memory."""
        key = (memory.id, memory.tenant_id)
        self._memories[key] = memory
        if memory.embedding:
            self._embeddings[key] = memory.embedding

    async def get(self, memory_id: UUID, tenant_id: str) -> Memory | None:
        """Get a memory by ID."""
        return self._memories.get((memory_id, tenant_id))

    async def delete(self, memory_id: UUID, tenant_id: str) -> None:
        """Delete a memory."""
        key = (memory_id, tenant_id)
        self._memories.pop(key, None)
        self._embeddings.pop(key, None)

    async def search(
        self,
        query_embedding: list[float],
        tenant_id: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search memories by embedding similarity."""
        # Simple cosine similarity
        results = []
        for (mem_id, tenant), memory in self._memories.items():
            if tenant != tenant_id:
                continue
            if memory.embedding:
                score = self._cosine_similarity(query_embedding, memory.embedding)
                results.append(SearchResult(memory, score))

        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)

        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def list(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[Memory]:
        """List memories with optional filters."""
        memories = [m for (_, tenant), m in self._memories.items() if tenant == tenant_id]
        if filters:
            memories = self._apply_filters_to_memories(memories, filters)
        return memories[offset : offset + limit]

    async def count(self, tenant_id: str, filters: dict[str, Any] | None = None) -> int:
        """Count memories matching filters."""
        memories = [m for (_, tenant), m in self._memories.items() if tenant == tenant_id]
        if filters:
            memories = self._apply_filters_to_memories(memories, filters)
        return len(memories)

    async def close(self) -> None:
        """Close the storage backend."""
        self._memories.clear()
        self._embeddings.clear()

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check."""
        return {"status": "healthy", "memory_count": len(self._memories)}

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def _apply_filters(self, results: list[SearchResult], filters: dict[str, Any]) -> list[SearchResult]:
        """Apply filters to search results."""
        filtered = []
        for result in results:
            memory = result.memory
            if "category" in filters and memory.metadata.category != filters["category"]:
                continue
            if "tags" in filters:
                required_tags = set(filters["tags"])
                if not required_tags.issubset(set(memory.metadata.tags)):
                    continue
            filtered.append(result)
        return filtered

    def _apply_filters_to_memories(self, memories: list[Memory], filters: dict[str, Any]) -> list[Memory]:
        """Apply filters to memory list."""
        filtered = []
        for memory in memories:
            if "category" in filters and memory.metadata.category != filters["category"]:
                continue
            if "tags" in filters:
                required_tags = set(filters["tags"])
                if not required_tags.issubset(set(memory.metadata.tags)):
                    continue
            filtered.append(memory)
        return filtered


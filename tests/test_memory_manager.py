"""Tests for MemoryManager."""

import pytest
from uuid import UUID

from memorycore.config.settings import Settings
from memorycore.core.memory import Memory, MemoryMetadata
from memorycore.core.memory_manager import MemoryManager
from memorycore.embedding.base import EmbeddingService
from memorycore.events.base import EventBus, Event
from memorycore.observability.metrics import MetricsCollector
from memorycore.storage.base import StorageBackend, SearchResult


class MockStorageBackend(StorageBackend):
    """Mock storage backend for testing."""

    def __init__(self):
        self.memories: dict[tuple[UUID, str], Memory] = {}
        self.initialized = False

    async def initialize(self) -> None:
        self.initialized = True

    async def save(self, memory: Memory) -> None:
        self.memories[(memory.id, memory.tenant_id)] = memory

    async def get(self, memory_id: UUID, tenant_id: str) -> Memory | None:
        return self.memories.get((memory_id, tenant_id))

    async def delete(self, memory_id: UUID, tenant_id: str) -> None:
        self.memories.pop((memory_id, tenant_id), None)

    async def search(self, query_embedding, tenant_id, limit=10, filters=None):
        results = []
        for memory in self.memories.values():
            if memory.tenant_id == tenant_id:
                results.append(SearchResult(memory, 0.9))
        return results[:limit]

    async def list(self, tenant_id, limit=100, offset=0, filters=None):
        memories = [m for m in self.memories.values() if m.tenant_id == tenant_id]
        return memories[offset:offset + limit]

    async def count(self, tenant_id, filters=None) -> int:
        return len([m for m in self.memories.values() if m.tenant_id == tenant_id])

    async def close(self) -> None:
        pass

    async def health_check(self):
        return {"status": "healthy"}


class MockEmbeddingService(EmbeddingService):
    """Mock embedding service for testing."""

    def __init__(self):
        self.dimension = 384

    async def embed(self, text: str) -> list[float]:
        return [0.1] * self.dimension

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self.dimension for _ in texts]

    def get_dimension(self) -> int:
        return self.dimension

    async def health_check(self):
        return {"status": "healthy"}


class MockEventBus(EventBus):
    """Mock event bus for testing."""

    def __init__(self):
        self.events: list[Event] = []

    def subscribe(self, event_type: str, handler) -> None:
        pass

    def publish(self, event: Event) -> None:
        self.events.append(event)

    def unsubscribe(self, event_type: str, handler) -> None:
        pass


@pytest.fixture
async def memory_manager():
    """Create a MemoryManager instance for testing."""
    storage = MockStorageBackend()
    embedding = MockEmbeddingService()
    settings = Settings(tenant_id="test")
    event_bus = MockEventBus()
    metrics = MetricsCollector(enabled=False)

    manager = MemoryManager(storage, embedding, settings, event_bus, metrics)
    await manager.initialize()
    return manager


@pytest.mark.asyncio
async def test_save_memory(memory_manager):
    """Test saving a memory."""
    memory = await memory_manager.save(
        content="Test memory content",
        metadata=MemoryMetadata(category="test", tags=["test"]),
    )

    assert memory.id is not None
    assert memory.content == "Test memory content"
    assert memory.metadata.category == "test"
    assert memory.embedding is not None


@pytest.mark.asyncio
async def test_get_memory(memory_manager):
    """Test retrieving a memory."""
    memory = await memory_manager.save(content="Test content")
    retrieved = await memory_manager.get(memory.id)

    assert retrieved is not None
    assert retrieved.id == memory.id
    assert retrieved.content == "Test content"


@pytest.mark.asyncio
async def test_search_memory(memory_manager):
    """Test searching memories."""
    await memory_manager.save(content="Python is great")
    await memory_manager.save(content="ChromaDB uses embeddings")

    results = await memory_manager.search("Python programming", limit=5)

    assert len(results) > 0
    assert any("Python" in r.memory.content for r in results)


@pytest.mark.asyncio
async def test_update_memory(memory_manager):
    """Test updating a memory."""
    memory = await memory_manager.save(content="Original content")
    original_version = memory.version

    updated = await memory_manager.update(memory.id, content="Updated content")

    assert updated.content == "Updated content"
    assert updated.version > original_version


@pytest.mark.asyncio
async def test_delete_memory(memory_manager):
    """Test deleting a memory."""
    memory = await memory_manager.save(content="To be deleted")
    await memory_manager.delete(memory.id)

    retrieved = await memory_manager.get(memory.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_invalid_content(memory_manager):
    """Test validation of empty content."""
    with pytest.raises(Exception):  # Should raise InvalidMemoryError
        await memory_manager.save(content="")


@pytest.mark.asyncio
async def test_ttl(memory_manager):
    """Test TTL functionality."""
    memory = await memory_manager.save(content="TTL test", ttl_days=7)

    assert memory.expires_at is not None
    assert not memory.is_expired()


"""Core memory manager - main orchestrator."""

from __future__ import annotations

from time import time
from typing import Any
from uuid import UUID

from tenacity import retry, stop_after_attempt, wait_exponential

from memorycore.config.settings import Settings
from memorycore.core.memory import Memory, MemoryMetadata
from memorycore.embedding.base import EmbeddingService
from memorycore.events.base import EventBus, SimpleEventBus
from memorycore.events.memory_events import (
    MemoryCreatedEvent,
    MemoryDeletedEvent,
    MemorySearchedEvent,
    MemoryUpdatedEvent,
)
from memorycore.exceptions.validation import InvalidMemoryError, InvalidQueryError
from memorycore.observability.logging import get_logger
from memorycore.observability.metrics import MetricsCollector
from memorycore.storage.base import SearchResult, StorageBackend

logger = get_logger(__name__)


class MemoryManager:
    """Main memory manager orchestrating storage, embedding, and events."""

    def __init__(
        self,
        storage: StorageBackend,
        embedding: EmbeddingService,
        settings: Settings,
        event_bus: EventBus | None = None,
        metrics: MetricsCollector | None = None,
    ):
        self.storage = storage
        self.embedding = embedding
        self.settings = settings
        self.event_bus = event_bus or SimpleEventBus()
        self.metrics = metrics

    async def initialize(self) -> None:
        """Initialize the memory manager."""
        logger.info("Initializing MemoryManager")
        await self.storage.initialize()
        logger.info("MemoryManager initialized")

    async def save(
        self,
        content: str,
        metadata: MemoryMetadata | None = None,
        tenant_id: str | None = None,
        generate_embedding: bool = True,
        ttl_days: int | None = None,
    ) -> Memory:
        """Save a memory."""
        start_time = time()
        tenant_id = tenant_id or self.settings.tenant_id

        # Validate input
        if not content or not content.strip():
            raise InvalidMemoryError("Memory content cannot be empty", field="content")

        # Create memory object
        memory = Memory(
            content=content.strip(),
            metadata=metadata or MemoryMetadata(),
            tenant_id=tenant_id,
        )

        # Set TTL if provided
        if ttl_days:
            memory.set_ttl(ttl_days)
        elif self.settings.default_ttl_days:
            memory.set_ttl(self.settings.default_ttl_days)

        # Generate embedding if needed
        if generate_embedding:
            try:
                memory.embedding = await self._generate_embedding_with_retry(content)
            except Exception as e:
                logger.error("Failed to generate embedding", error=str(e))
                if self.metrics:
                    self.metrics.record_embedding(status="error")
                # Continue without embedding - can be generated later

        # Save to storage with retry
        try:
            await self._save_with_retry(memory)
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("save", tenant_id, "success", duration)
            logger.info("Memory saved", memory_id=str(memory.id), tenant_id=tenant_id)
        except Exception as e:
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("save", tenant_id, "error", duration)
            logger.error("Failed to save memory", error=str(e), memory_id=str(memory.id))
            raise

        # Publish event
        self.event_bus.publish(MemoryCreatedEvent(memory))

        return memory

    async def get(self, memory_id: UUID, tenant_id: str | None = None) -> Memory | None:
        """Get a memory by ID."""
        tenant_id = tenant_id or self.settings.tenant_id
        start_time = time()

        try:
            memory = await self.storage.get(memory_id, tenant_id)
            if memory:
                if self.metrics:
                    duration = time() - start_time
                    self.metrics.record_operation("get", tenant_id, "success", duration)
                logger.debug("Memory retrieved", memory_id=str(memory_id), tenant_id=tenant_id)
            else:
                if self.metrics:
                    duration = time() - start_time
                    self.metrics.record_operation("get", tenant_id, "not_found", duration)
            return memory
        except Exception as e:
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("get", tenant_id, "error", duration)
            logger.error("Failed to get memory", error=str(e), memory_id=str(memory_id))
            raise

    async def update(
        self,
        memory_id: UUID,
        content: str | None = None,
        metadata: MemoryMetadata | None = None,
        tenant_id: str | None = None,
    ) -> Memory:
        """Update a memory."""
        tenant_id = tenant_id or self.settings.tenant_id
        start_time = time()

        # Get existing memory
        memory = await self.get(memory_id, tenant_id)
        if not memory:
            raise InvalidMemoryError(f"Memory {memory_id} not found", field="id")

        previous_version = memory.version

        # Update fields
        if content:
            if not content.strip():
                raise InvalidMemoryError("Memory content cannot be empty", field="content")
            memory.content = content.strip()
            # Regenerate embedding for new content
            try:
                memory.embedding = await self._generate_embedding_with_retry(content)
            except Exception as e:
                logger.warning("Failed to regenerate embedding", error=str(e))

        if metadata:
            memory.metadata = metadata

        # Create version if enabled
        if self.settings.enable_versioning:
            changed_fields = []
            if content:
                changed_fields.append("content")
            if metadata:
                changed_fields.append("metadata")
            memory.create_version(changed_fields)

        # Save updated memory
        try:
            await self._save_with_retry(memory)
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("update", tenant_id, "success", duration)
            logger.info("Memory updated", memory_id=str(memory_id), tenant_id=tenant_id)
        except Exception as e:
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("update", tenant_id, "error", duration)
            logger.error("Failed to update memory", error=str(e), memory_id=str(memory_id))
            raise

        # Publish event
        self.event_bus.publish(MemoryUpdatedEvent(memory, previous_version))

        return memory

    async def delete(self, memory_id: UUID, tenant_id: str | None = None) -> None:
        """Delete a memory."""
        tenant_id = tenant_id or self.settings.tenant_id
        start_time = time()

        try:
            await self.storage.delete(memory_id, tenant_id)
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("delete", tenant_id, "success", duration)
            logger.info("Memory deleted", memory_id=str(memory_id), tenant_id=tenant_id)
        except Exception as e:
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("delete", tenant_id, "error", duration)
            logger.error("Failed to delete memory", error=str(e), memory_id=str(memory_id))
            raise

        # Publish event
        self.event_bus.publish(MemoryDeletedEvent(memory_id, tenant_id))

    async def search(
        self,
        query: str,
        tenant_id: str | None = None,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search memories by semantic similarity."""
        tenant_id = tenant_id or self.settings.tenant_id
        start_time = time()

        # Validate query
        if not query or not query.strip():
            raise InvalidQueryError("Query cannot be empty", query=query)

        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding_with_retry(query)

            # Search storage
            results = await self.storage.search(query_embedding, tenant_id, limit, filters)

            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("search", tenant_id, "success", duration)
                self.metrics.record_search(tenant_id)

            logger.info(
                "Memory search completed",
                query=query,
                result_count=len(results),
                tenant_id=tenant_id,
            )

            # Publish event
            self.event_bus.publish(MemorySearchedEvent(query, len(results), tenant_id))

            return results
        except Exception as e:
            if self.metrics:
                duration = time() - start_time
                self.metrics.record_operation("search", tenant_id, "error", duration)
            logger.error("Failed to search memories", error=str(e), query=query)
            raise

    async def list(
        self,
        tenant_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[Memory]:
        """List memories."""
        tenant_id = tenant_id or self.settings.tenant_id
        return await self.storage.list(tenant_id, limit, offset, filters)

    async def count(self, tenant_id: str | None = None, filters: dict[str, Any] | None = None) -> int:
        """Count memories."""
        tenant_id = tenant_id or self.settings.tenant_id
        return await self.storage.count(tenant_id, filters)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _generate_embedding_with_retry(self, text: str) -> list[float]:
        """Generate embedding with retry logic."""
        embedding = await self.embedding.embed(text)
        if self.metrics:
            self.metrics.record_embedding(status="success")
        return embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _save_with_retry(self, memory: Memory) -> None:
        """Save memory with retry logic."""
        await self.storage.save(memory)

    async def close(self) -> None:
        """Close the memory manager."""
        await self.storage.close()
        logger.info("MemoryManager closed")


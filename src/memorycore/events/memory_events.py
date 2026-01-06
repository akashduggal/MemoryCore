"""Memory-related events."""

from dataclasses import dataclass
from uuid import UUID

from memorycore.core.memory import Memory
from memorycore.events.base import Event


@dataclass
class MemoryCreatedEvent(Event):
    """Event fired when a memory is created."""

    memory: Memory

    def __init__(self, memory: Memory, **kwargs):
        super().__init__(
            event_id=kwargs.get("event_id"),
            event_type="memory.created",
            timestamp=kwargs.get("timestamp"),
            tenant_id=memory.tenant_id,
            metadata=kwargs.get("metadata", {}),
        )
        self.memory = memory


@dataclass
class MemoryUpdatedEvent(Event):
    """Event fired when a memory is updated."""

    memory: Memory
    previous_version: int

    def __init__(self, memory: Memory, previous_version: int, **kwargs):
        super().__init__(
            event_id=kwargs.get("event_id"),
            event_type="memory.updated",
            timestamp=kwargs.get("timestamp"),
            tenant_id=memory.tenant_id,
            metadata=kwargs.get("metadata", {}),
        )
        self.memory = memory
        self.previous_version = previous_version


@dataclass
class MemoryDeletedEvent(Event):
    """Event fired when a memory is deleted."""

    memory_id: UUID

    def __init__(self, memory_id: UUID, tenant_id: str, **kwargs):
        super().__init__(
            event_id=kwargs.get("event_id"),
            event_type="memory.deleted",
            timestamp=kwargs.get("timestamp"),
            tenant_id=tenant_id,
            metadata=kwargs.get("metadata", {}),
        )
        self.memory_id = memory_id


@dataclass
class MemorySearchedEvent(Event):
    """Event fired when a memory search is performed."""

    query: str
    result_count: int

    def __init__(self, query: str, result_count: int, tenant_id: str, **kwargs):
        super().__init__(
            event_id=kwargs.get("event_id"),
            event_type="memory.searched",
            timestamp=kwargs.get("timestamp"),
            tenant_id=tenant_id,
            metadata=kwargs.get("metadata", {}),
        )
        self.query = query
        self.result_count = result_count


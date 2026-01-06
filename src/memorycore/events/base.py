"""Base event system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID, uuid4


@dataclass
class Event:
    """Base event class."""

    event_id: UUID
    event_type: str
    timestamp: datetime
    tenant_id: str
    metadata: dict[str, Any]

    def __post_init__(self):
        """Initialize event."""
        if self.event_id is None:
            self.event_id = uuid4()
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


EventHandler = Callable[[Event], None]


class EventBus(ABC):
    """Abstract event bus."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        pass

    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish an event."""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        pass


class SimpleEventBus(EventBus):
    """Simple in-memory event bus implementation."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        """Publish an event."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't fail event publishing
                print(f"Error in event handler for {event.event_type}: {e}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)


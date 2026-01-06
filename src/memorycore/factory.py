"""Factory functions for creating MemoryCore components."""

from memorycore.config.settings import Settings, get_settings
from memorycore.core.memory_manager import MemoryManager
from memorycore.embedding.base import EmbeddingService
from memorycore.embedding.chromadb_embedding import ChromaDBEmbeddingService
from memorycore.events.base import SimpleEventBus
from memorycore.observability.logging import setup_logging, get_logger
from memorycore.observability.metrics import get_metrics_collector
from memorycore.storage.base import StorageBackend
from memorycore.storage.chromadb_backend import ChromaDBBackend
from memorycore.storage.memory_backend import InMemoryBackend

logger = get_logger(__name__)


def create_storage_backend(settings: Settings) -> StorageBackend:
    """Create a storage backend based on settings."""
    if settings.storage.backend == "chromadb":
        return ChromaDBBackend(
            path=settings.storage.path,
            collection_name=settings.storage.collection_name,
            persist=settings.storage.persist,
        )
    elif settings.storage.backend == "memory":
        return InMemoryBackend()
    else:
        raise ValueError(f"Unknown storage backend: {settings.storage.backend}")


def create_embedding_service(settings: Settings) -> EmbeddingService:
    """Create an embedding service based on settings."""
    if settings.embedding.provider == "chromadb":
        return ChromaDBEmbeddingService(model_name=settings.embedding.model_name)
    else:
        raise ValueError(f"Unknown embedding provider: {settings.embedding.provider}")


async def create_memory_manager(settings_path: str | None = None) -> MemoryManager:
    """Create a fully configured MemoryManager."""
    # Load settings
    settings = get_settings()

    # Setup logging
    setup_logging(
        log_level=settings.observability.log_level,
        log_format=settings.observability.log_format,
    )

    # Create components
    storage = create_storage_backend(settings)
    embedding = create_embedding_service(settings)
    event_bus = SimpleEventBus()
    metrics = get_metrics_collector(enabled=settings.observability.enable_metrics)

    # Start metrics server if enabled
    if settings.observability.enable_metrics:
        metrics.start_metrics_server(port=settings.observability.metrics_port)

    # Create manager
    manager = MemoryManager(
        storage=storage,
        embedding=embedding,
        settings=settings,
        event_bus=event_bus,
        metrics=metrics,
    )

    # Initialize
    await manager.initialize()

    logger.info("MemoryManager created and initialized", tenant_id=settings.tenant_id)

    return manager


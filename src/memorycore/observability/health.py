"""Health check system."""

from datetime import datetime, timezone
from typing import Any

from memorycore.storage.base import StorageBackend
from memorycore.embedding.base import EmbeddingService


class HealthChecker:
    """Health checker for MemoryCore components."""

    def __init__(self, storage: StorageBackend, embedding: EmbeddingService):
        self.storage = storage
        self.embedding = embedding

    async def check_health(self) -> dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": None,
        }

        # Check storage
        try:
            storage_health = await self.storage.health_check()
            health["components"]["storage"] = storage_health
            if storage_health.get("status") != "healthy":
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["storage"] = {"status": "unhealthy", "error": str(e)}
            health["status"] = "unhealthy"

        # Check embedding
        try:
            embedding_health = await self.embedding.health_check()
            health["components"]["embedding"] = embedding_health
            if embedding_health.get("status") != "healthy" and health["status"] == "healthy":
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["embedding"] = {"status": "unhealthy", "error": str(e)}
            if health["status"] == "healthy":
                health["status"] = "unhealthy"

        health["timestamp"] = datetime.now(timezone.utc).isoformat()
        return health


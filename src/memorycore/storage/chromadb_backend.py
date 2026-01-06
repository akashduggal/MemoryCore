"""ChromaDB storage backend implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None

from memorycore.core.memory import Memory
from memorycore.exceptions.storage import StorageConnectionError, StorageOperationError
from memorycore.storage.base import SearchResult, StorageBackend


class ChromaDBBackend(StorageBackend):
    """ChromaDB storage backend."""

    def __init__(self, path: Path, collection_name: str = "memories", persist: bool = True):
        if chromadb is None:
            raise ImportError("chromadb is not installed. Install with: pip install chromadb")
        self.path = path
        self.collection_name = collection_name
        self.persist = persist
        self.client: chromadb.ClientAPI | None = None
        self.collection: chromadb.Collection | None = None

    async def initialize(self) -> None:
        """Initialize the storage backend."""
        try:
            if self.persist:
                self.path.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=str(self.path), settings=ChromaSettings(anonymized_telemetry=False)
                )
            else:
                self.client = chromadb.Client(settings=ChromaSettings(anonymized_telemetry=False))

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "MemoryCore memory storage"},
            )
        except Exception as e:
            raise StorageConnectionError(f"Failed to initialize ChromaDB: {e}", {"path": str(self.path)}) from e

    async def save(self, memory: Memory) -> None:
        """Save a memory."""
        if not self.collection:
            raise StorageOperationError("Storage not initialized", operation="save")

        try:
            metadata = {
                "tenant_id": memory.tenant_id,
                "category": memory.metadata.category,
                "tags": ",".join(memory.metadata.tags),
                "importance": memory.metadata.importance,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat(),
                "version": str(memory.version),
            }
            if memory.expires_at:
                metadata["expires_at"] = memory.expires_at.isoformat()

            # Store embedding if available
            if memory.embedding:
                self.collection.add(
                    ids=[str(memory.id)],
                    embeddings=[memory.embedding],
                    documents=[memory.content],
                    metadatas=[metadata],
                )
            else:
                # Store without embedding (will need to be generated later)
                self.collection.add(
                    ids=[str(memory.id)],
                    documents=[memory.content],
                    metadatas=[metadata],
                )
        except Exception as e:
            raise StorageOperationError(f"Failed to save memory: {e}", operation="save") from e

    async def get(self, memory_id: UUID, tenant_id: str) -> Memory | None:
        """Get a memory by ID."""
        if not self.collection:
            raise StorageOperationError("Storage not initialized", operation="get")

        try:
            results = self.collection.get(ids=[str(memory_id)], include=["documents", "metadatas", "embeddings"])
            if not results["ids"]:
                return None

            metadata = results["metadatas"][0]
            if metadata.get("tenant_id") != tenant_id:
                return None

            # Reconstruct Memory object
            # Note: This is simplified - full reconstruction would need relationships, versions, etc.
            from memorycore.core.memory import MemoryMetadata

            mem_metadata = MemoryMetadata(
                category=metadata.get("category", "general"),
                tags=metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                importance=metadata.get("importance", "medium"),
            )

            memory = Memory(
                id=memory_id,
                content=results["documents"][0],
                metadata=mem_metadata,
                embedding=results["embeddings"][0] if results["embeddings"] else None,
                tenant_id=tenant_id,
            )
            return memory
        except Exception as e:
            raise StorageOperationError(f"Failed to get memory: {e}", operation="get") from e

    async def delete(self, memory_id: UUID, tenant_id: str) -> None:
        """Delete a memory."""
        if not self.collection:
            raise StorageOperationError("Storage not initialized", operation="delete")

        try:
            self.collection.delete(ids=[str(memory_id)])
        except Exception as e:
            raise StorageOperationError(f"Failed to delete memory: {e}", operation="delete") from e

    async def search(
        self,
        query_embedding: list[float],
        tenant_id: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search memories by embedding similarity."""
        if not self.collection:
            raise StorageOperationError("Storage not initialized", operation="search")

        try:
            where = {"tenant_id": tenant_id}
            if filters:
                if "category" in filters:
                    where["category"] = filters["category"]
                if "tags" in filters:
                    # ChromaDB doesn't support array contains, so we filter post-query
                    pass

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
                include=["documents", "metadatas", "embeddings", "distances"],
            )

            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, mem_id in enumerate(results["ids"][0]):
                    # Filter by tags if needed
                    if filters and "tags" in filters:
                        tags = results["metadatas"][0][i].get("tags", "").split(",")
                        if not set(filters["tags"]).issubset(set(tags)):
                            continue

                    memory = await self.get(UUID(mem_id), tenant_id)
                    if memory:
                        distance = results["distances"][0][i] if results["distances"] else 0.0
                        score = 1.0 - distance  # Convert distance to similarity
                        search_results.append(SearchResult(memory, score))

            return search_results
        except Exception as e:
            raise StorageOperationError(f"Failed to search memories: {e}", operation="search") from e

    async def list(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[Memory]:
        """List memories with optional filters."""
        if not self.collection:
            raise StorageOperationError("Storage not initialized", operation="list")

        try:
            where = {"tenant_id": tenant_id}
            if filters and "category" in filters:
                where["category"] = filters["category"]

            results = self.collection.get(
                where=where,
                limit=limit + offset,
                include=["documents", "metadatas", "embeddings"],
            )

            memories = []
            if results["ids"]:
                for i, mem_id in enumerate(results["ids"][offset:]):
                    memory = await self.get(UUID(mem_id), tenant_id)
                    if memory:
                        memories.append(memory)

            return memories
        except Exception as e:
            raise StorageOperationError(f"Failed to list memories: {e}", operation="list") from e

    async def count(self, tenant_id: str, filters: dict[str, Any] | None = None) -> int:
        """Count memories matching filters."""
        if not self.collection:
            raise StorageOperationError("Storage not initialized", operation="count")

        try:
            where = {"tenant_id": tenant_id}
            if filters and "category" in filters:
                where["category"] = filters["category"]

            results = self.collection.get(where=where, limit=1)
            # ChromaDB doesn't have a direct count, so we get all IDs
            all_results = self.collection.get(where=where)
            return len(all_results["ids"]) if all_results["ids"] else 0
        except Exception as e:
            raise StorageOperationError(f"Failed to count memories: {e}", operation="count") from e

    async def close(self) -> None:
        """Close the storage backend."""
        # ChromaDB doesn't require explicit closing for persistent client
        pass

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check."""
        try:
            if not self.collection:
                return {"status": "unhealthy", "error": "Not initialized"}
            # Try a simple operation
            self.collection.count()
            return {"status": "healthy", "backend": "chromadb", "path": str(self.path)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


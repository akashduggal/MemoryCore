"""MCP server integration for MemoryCore."""

from __future__ import annotations

import asyncio
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

from memorycore.core.memory_manager import MemoryManager
from memorycore.core.memory import MemoryMetadata
from memorycore.observability.logging import get_logger

logger = get_logger(__name__)


class MemoryCoreServer:
    """MCP server wrapper for MemoryCore."""

    def __init__(self, memory_manager: MemoryManager):
        if FastMCP is None:
            raise ImportError("mcp package is required. Install with: pip install mcp")
        self.memory_manager = memory_manager
        self.mcp = FastMCP("memorycore")

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools."""

        @self.mcp.tool()
        async def save_memory(
            content: str,
            category: str = "general",
            tags: list[str] | None = None,
            importance: str = "medium",
            tenant_id: str | None = None,
            ttl_days: int | None = None,
        ) -> dict[str, Any]:
            """Save a memory to persistent storage."""
            metadata = MemoryMetadata(
                category=category,
                tags=tags or [],
                importance=importance,
            )
            memory = await self.memory_manager.save(
                content=content,
                metadata=metadata,
                tenant_id=tenant_id,
                ttl_days=ttl_days,
            )
            return {
                "success": True,
                "memory_id": str(memory.id),
                "message": f"Memory saved with ID {memory.id}",
            }

        @self.mcp.tool()
        async def recall_memory(
            query: str,
            limit: int = 10,
            category: str | None = None,
            tags: list[str] | None = None,
            tenant_id: str | None = None,
        ) -> dict[str, Any]:
            """Search and recall memories by semantic similarity."""
            filters = {}
            if category:
                filters["category"] = category
            if tags:
                filters["tags"] = tags

            results = await self.memory_manager.search(
                query=query,
                tenant_id=tenant_id,
                limit=limit,
                filters=filters if filters else None,
            )

            memories = []
            for result in results:
                memories.append(
                    {
                        "id": str(result.memory.id),
                        "content": result.memory.content,
                        "category": result.memory.metadata.category,
                        "tags": result.memory.metadata.tags,
                        "score": result.score,
                        "created_at": result.memory.created_at.isoformat(),
                    }
                )

            return {
                "success": True,
                "count": len(memories),
                "memories": memories,
            }

        @self.mcp.tool()
        async def get_memory(memory_id: str, tenant_id: str | None = None) -> dict[str, Any]:
            """Get a specific memory by ID."""
            from uuid import UUID

            memory = await self.memory_manager.get(UUID(memory_id), tenant_id)
            if not memory:
                return {"success": False, "error": "Memory not found"}

            return {
                "success": True,
                "memory": {
                    "id": str(memory.id),
                    "content": memory.content,
                    "category": memory.metadata.category,
                    "tags": memory.metadata.tags,
                    "created_at": memory.created_at.isoformat(),
                    "updated_at": memory.updated_at.isoformat(),
                },
            }

        @self.mcp.tool()
        async def delete_memory(memory_id: str, tenant_id: str | None = None) -> dict[str, Any]:
            """Delete a memory by ID."""
            from uuid import UUID

            await self.memory_manager.delete(UUID(memory_id), tenant_id)
            return {"success": True, "message": f"Memory {memory_id} deleted"}

    def run(self):
        """Run the MCP server."""
        logger.info("Starting MemoryCore MCP server")
        self.mcp.run()


async def create_server(settings_path: str | None = None) -> MemoryCoreServer:
    """Factory function to create a configured server."""
    from memorycore.factory import create_memory_manager

    manager = await create_memory_manager(settings_path)
    return MemoryCoreServer(manager)


if __name__ == "__main__":
    server = asyncio.run(create_server())
    server.run()


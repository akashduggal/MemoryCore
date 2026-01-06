"""Basic usage example for MemoryCore.

This example demonstrates core MemoryCore functionality:
- Saving memories with metadata
- Semantic search
- Memory retrieval and updates
- Memory counting and listing
"""

import asyncio
import os

# Configure for example (in-memory backend for simplicity)
os.environ["STORAGE_BACKEND"] = "memory"
os.environ["EMBEDDING_PROVIDER"] = "chromadb"
os.environ["OBSERVABILITY_LOG_LEVEL"] = "INFO"

from memorycore.factory import create_memory_manager
from memorycore.core.memory import MemoryMetadata


async def main():
    """Demonstrate MemoryCore capabilities."""
    print("Initializing MemoryCore...")
    manager = await create_memory_manager()

    print("\n1. Saving memories...")
    memory1 = await manager.save(
        content="Production database is at 10.0.0.5:5432",
        metadata=MemoryMetadata(
            category="infrastructure",
            tags=["database", "production"],
            importance="high",
        ),
        ttl_days=90,
    )
    print(f"   Saved memory ID: {memory1.id}")

    memory2 = await manager.save(
        content="API uses FastAPI framework with async support",
        metadata=MemoryMetadata(
            category="architecture",
            tags=["api", "fastapi"],
            importance="medium",
        ),
    )
    print(f"   Saved memory ID: {memory2.id}")

    print("\n2. Searching memories...")
    results = await manager.search(
        query="production database connection",
        limit=5,
    )

    print(f"   Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Score: {result.score:.3f} - {result.memory.content[:60]}...")

    print("\n3. Retrieving specific memory...")
    retrieved = await manager.get(memory1.id)
    if retrieved:
        print(f"   Memory: {retrieved.content}")
        print(f"   Category: {retrieved.metadata.category}")
        print(f"   Tags: {retrieved.metadata.tags}")

    print("\n4. Updating memory...")
    updated = await manager.update(
        memory_id=memory1.id,
        content="Production database is at 10.0.0.6:5432 (updated)",
    )
    print(f"   Updated memory version: {updated.version}")

    print("\n5. Counting memories...")
    count = await manager.count()
    print(f"   Total memories: {count}")

    print("\n6. Listing memories...")
    memories = await manager.list(limit=10)
    print(f"   Listed {len(memories)} memories")

    print("\n7. Cleaning up...")
    await manager.close()
    print("   Done!")


if __name__ == "__main__":
    asyncio.run(main())


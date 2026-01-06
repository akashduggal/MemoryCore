# 📖 MemoryCore Usage Guide

Complete guide to using MemoryCore in your applications.

## 🔧 Basic Operations

### Creating a Memory Manager

```python
import asyncio
from memorycore.factory import create_memory_manager
from memorycore.core.memory import MemoryMetadata

async def main():
    # Create manager (auto-configures from environment)
    manager = await create_memory_manager()
    
    # Your code here

asyncio.run(main())
```

### Saving a Memory

```python
async def main():
    manager = await create_memory_manager()
    
    # Save a memory
    memory = await manager.save(
        content="Production database is at 10.0.0.5:5432",
        metadata=MemoryMetadata(
            category="infrastructure",
            tags=["database", "production"],
            importance="high"
        ),
        ttl_days=90
    )
    
    print(f"Saved memory with ID: {memory.id}")

asyncio.run(main())
```

### Searching Memories

```python
async def main():
    manager = await create_memory_manager()
    
    # Search memories
    results = await manager.search(
        query="production database connection",
        limit=5
    )
    
    for result in results:
        print(f"{result.score:.3f}: {result.memory.content}")

asyncio.run(main())
```

### Retrieving a Memory by ID

```python
async def main():
    manager = await create_memory_manager()
    
    # Get a specific memory
    memory = await manager.get(memory_id="your-memory-id")
    print(f"Content: {memory.content}")
    print(f"Category: {memory.metadata.category}")

asyncio.run(main())
```

### Updating a Memory

```python
async def main():
    manager = await create_memory_manager()
    
    # Update existing memory
    updated = await manager.update(
        memory_id=memory.id,
        content="Updated database IP: 10.0.0.6:5432"
    )
    
    print(f"Updated to version: {updated.version}")

asyncio.run(main())
```

### Deleting a Memory

```python
async def main():
    manager = await create_memory_manager()
    
    # Delete a memory
    await manager.delete(memory_id="your-memory-id")
    print("Memory deleted")

asyncio.run(main())
```

## 🔌 MCP Server Integration

MemoryCore includes an MCP (Model Context Protocol) server for integration with AI agents.

### Running the MCP Server

```bash
# Run MCP server
python -m memorycore.server
```

### Configuring Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memorycore": {
      "command": "python",
      "args": ["-m", "memorycore.server"]
    }
  }
}
```

### MCP Tools Available

- `save_memory` - Save a new memory
- `search_memories` - Search existing memories
- `get_memory` - Retrieve a memory by ID
- `update_memory` - Update an existing memory
- `delete_memory` - Delete a memory
- `list_memories` - List memories with filters

## 🚀 Advanced Features

### 📚 Memory Versioning

MemoryCore automatically tracks versions when you update memories:

```python
# Save initial memory
memory = await manager.save(
    content="Database schema v1",
    metadata=MemoryMetadata(category="database")
)

# Update creates a new version
updated = await manager.update(
    memory_id=memory.id,
    content="Database schema v2"
)

print(f"Current version: {updated.version}")
print(f"Version history: {len(updated.versions)} versions")

# Access previous versions
for version in updated.versions:
    print(f"Version {version.version}: {version.content}")
```

### 🔗 Memory Relationships

Link related memories together:

```python
# Create related memories
schema_v1 = await manager.save(
    content="Database schema v1",
    metadata=MemoryMetadata(category="database")
)

schema_v2 = await manager.save(
    content="Database schema v2",
    metadata=MemoryMetadata(category="database")
)

# Link memories
schema_v2.add_relationship(
    target_id=schema_v1.id,
    relationship_type="supersedes",
    strength=1.0
)

# Save the relationship
await manager.update(memory_id=schema_v2.id, memory=schema_v2)

# Query related memories
related = await manager.get_related(memory_id=schema_v2.id)
for rel in related:
    print(f"Related: {rel.relationship_type} - {rel.target_id}")
```

### 📡 Event Subscriptions

Subscribe to events for extensibility:

```python
from memorycore.events.memory_events import MemoryCreatedEvent, MemorySearchedEvent

def on_memory_created(event: MemoryCreatedEvent):
    # Custom logic: analytics, replication, etc.
    print(f"Memory created: {event.memory.id}")
    # Log to audit system, send webhook, etc.

def on_memory_searched(event: MemorySearchedEvent):
    # Track search patterns
    print(f"Searched for: {event.query}, found {len(event.results)} results")

# Subscribe to events
manager.event_bus.subscribe("memory.created", on_memory_created)
manager.event_bus.subscribe("memory.searched", on_memory_searched)
```

### 🔍 Advanced Filtering

Filter memories by metadata:

```python
# Search with filters
results = await manager.search(
    query="database",
    limit=10,
    filters={
        "category": "infrastructure",
        "tags": ["production"],
        "importance": "high"
    }
)

# List memories with filters
memories = await manager.list(
    limit=20,
    filters={
        "category": "database",
        "tags": ["schema"]
    }
)
```

### 📊 Batch Operations

Process multiple memories efficiently:

```python
# Save multiple memories
memories = [
    {"content": "Memory 1", "metadata": MemoryMetadata(category="test")},
    {"content": "Memory 2", "metadata": MemoryMetadata(category="test")},
    {"content": "Memory 3", "metadata": MemoryMetadata(category="test")},
]

saved = []
for mem in memories:
    memory = await manager.save(**mem)
    saved.append(memory)

print(f"Saved {len(saved)} memories")
```

### ⏰ TTL (Time To Live)

Set expiration for memories:

```python
# Memory expires in 30 days
memory = await manager.save(
    content="Temporary configuration",
    metadata=MemoryMetadata(category="config"),
    ttl_days=30
)

# Check if expired
if memory.is_expired():
    print("Memory has expired")
```

### 🏷️ Custom Metadata

Add custom fields to metadata:

```python
memory = await manager.save(
    content="Custom memory",
    metadata=MemoryMetadata(
        category="custom",
        tags=["important"],
        custom_fields={
            "project": "my-project",
            "author": "john@example.com",
            "priority": 1
        }
    )
)

# Access custom fields
print(memory.metadata.custom_fields["project"])
```

## 🔄 Best Practices

### 1. Use Appropriate Categories
Organize memories with consistent categories:
- `infrastructure` - Server configs, databases, etc.
- `decisions` - Architectural decisions
- `credentials` - API keys, passwords (be careful!)
- `documentation` - Code docs, guides

### 2. Tag Strategically
Use tags for fine-grained filtering:
- Multiple tags per memory
- Consistent tag naming
- Avoid too many tags (3-5 is ideal)

### 3. Set TTL for Temporary Data
Use TTL for data that becomes stale:
- Configuration that changes frequently
- Temporary credentials
- Cache entries

### 4. Leverage Relationships
Link related memories:
- `supersedes` - New version replaces old
- `extends` - Builds upon another memory
- `contradicts` - Conflicts with another memory

### 5. Monitor Events
Subscribe to events for:
- Audit logging
- Analytics
- Replication
- Notifications

## 🐛 Error Handling

```python
from memorycore.exceptions.storage import StorageError
from memorycore.exceptions.validation import InvalidMemoryError

try:
    memory = await manager.save(
        content="",  # Empty content will raise error
        metadata=MemoryMetadata(category="test")
    )
except InvalidMemoryError as e:
    print(f"Validation error: {e}")
except StorageError as e:
    print(f"Storage error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 📚 Additional Resources

- [Architecture Documentation](../ARCHITECTURE.md) - Deep dive into how MemoryCore works
- [Design Decisions](../DESIGN_DECISIONS.md) - Architectural rationale
- [Getting Started Guide](GETTING_STARTED.md) - Installation and setup


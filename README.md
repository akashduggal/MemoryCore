# MemoryCore

**A production-grade memory framework for AI agents**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Status:** Early Development | **Version:** 0.1.0

## The Problem

While building AI agent systems, I encountered a fundamental limitation: agents have no persistent memory across sessions. Every conversation starts from scratch, requiring expensive re-indexing of context and preventing agents from building on prior knowledge.

The specific pain points:

1. **Session Volatility:** Closing a development session erases all accumulated context. An agent that spent hours understanding a codebase must start over.

2. **Costly Re-indexing:** Re-sending 50k+ tokens of context to an LLM costs $1-3 per interaction. For agents that interact frequently, this becomes prohibitively expensive.

3. **No Semantic Recall:** Agents cannot answer questions like "What database decision did we make last week?" without re-reading entire conversation histories. There's no way to query past knowledge semantically.

4. **Limited Extensibility:** Existing solutions tie you to a single storage backend. If your needs change—say, you need faster search or cloud storage—you're locked in.

5. **Production Blindness:** In production, when memory operations fail or perform poorly, there's no visibility into what's happening. Debugging becomes guesswork.

This isn't just a technical limitation—it prevents agents from becoming true long-term collaborators.

## Design Goals

MemoryCore was designed to solve these problems with the following goals:

### Must Have

- **Persistent Semantic Memory:** Store and retrieve information by meaning, not keywords
- **Production-Ready:** Built-in observability, error handling, and resilience patterns
- **Extensible:** Plugin architecture allowing different storage backends and embedding providers
- **Type-Safe:** Strong typing and validation prevent entire classes of runtime errors
- **Configuration-Driven:** No hardcoded values; everything configurable via environment variables

### Non-Goals

- **Not a Vector Database:** MemoryCore orchestrates vector databases; it doesn't implement one
- **Not a Chat History System:** This is for structured knowledge, not conversation transcripts
- **Not Multi-Agent Coordination:** Focused on memory persistence, not agent orchestration
- **Not a Knowledge Graph:** Relationships exist but aren't the primary query mechanism

## Tech Stack

### Core
- **Python 3.10+** - Modern Python with async/await support
- **Pydantic** - Type-safe data validation and settings management
- **asyncio** - Asynchronous operations for scalability

### Storage & Embeddings
- **ChromaDB** - Vector database for semantic search
- **sentence-transformers** - Local embedding generation
- **FAISS** - High-performance vector search (planned)

### Observability
- **structlog** - Structured JSON logging
- **Prometheus** - Metrics collection and monitoring
- **Correlation IDs** - Request tracking across components

### Architecture Patterns
- **Plugin Architecture** - Extensible storage and embedding backends
- **Event-Driven** - Publish-subscribe event bus
- **Retry Logic** - Exponential backoff with tenacity

### Development & Testing
- **pytest** - Testing framework
- **mypy** - Static type checking
- **ruff** - Fast Python linter
- **pytest-asyncio** - Async test support

### Protocols
- **MCP (Model Context Protocol)** - Agent integration protocol

## Architecture

### Core Concept

MemoryCore operates on a simple principle: **memories are structured data with semantic embeddings, stored in pluggable backends, orchestrated by a manager that handles resilience and observability**.

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Interface                           │
│              (MCP Protocol, Direct API)                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    MemoryManager                            │
│  • Validates inputs                                         │
│  • Generates embeddings                                     │
│  • Coordinates storage operations                            │
│  • Publishes events                                         │
│  • Records metrics                                          │
└──────┬───────────────────────┬───────────────────┬──────────┘
       │                       │                   │
┌──────▼──────┐      ┌─────────▼────────┐  ┌──────▼──────────┐
│   Storage   │      │    Embedding     │  │    Events       │
│   Backend   │      │     Service      │  │     Bus         │
│  (Pluggable)│      │   (Pluggable)   │  │                 │
└──────┬──────┘      └─────────────────┘  └─────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────┐
│  ChromaDB │ FAISS │ InMemory │ Custom Implementations       │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**MemoryManager:** The orchestrator. It doesn't store data or generate embeddings—it coordinates between components, handles retries, validates inputs, and publishes events. Think of it as the conductor of an orchestra.

**StorageBackend:** Abstract interface for persistence. Implementations handle the specifics of their storage technology. The interface ensures they're swappable without changing MemoryManager code.

**EmbeddingService:** Abstract interface for generating vector embeddings. Different providers (local models, API services) implement the same interface.

**EventBus:** Publish-subscribe system for extensibility. When a memory is saved, an event is published. Handlers can subscribe to add audit logging, analytics, replication, or other cross-cutting concerns.

**Observability Layer:** Structured logging, metrics collection, and health checks. These are integrated throughout, not bolted on.

### Data Model

A **Memory** consists of:
- **Content:** The actual information (text)
- **Metadata:** Category, tags, importance level, custom fields
- **Embedding:** Vector representation for semantic search
- **Relationships:** Links to other memories (supersedes, contradicts, extends)
- **Versions:** History of changes (if versioning enabled)
- **TTL:** Optional expiration timestamp

This model emerged from real use cases: categorizing infrastructure decisions, tracking architectural choices, remembering credentials, and linking related concepts.

## How It Works

### Saving a Memory

1. **Validation:** MemoryManager validates the content isn't empty, metadata is well-formed
2. **Embedding Generation:** EmbeddingService generates a vector representation (with retry on failure)
3. **Storage:** StorageBackend persists the memory (with retry on transient failures)
4. **Event Publishing:** EventBus publishes `MemoryCreatedEvent` (non-blocking)
5. **Metrics:** Operation duration, success/failure recorded
6. **Logging:** Structured log entry with correlation ID

The retry logic uses exponential backoff—critical because embedding APIs and databases can have transient failures, but we don't want to fail the entire operation.

### Searching Memories

1. **Query Validation:** Ensure query isn't empty
2. **Query Embedding:** Generate embedding for the search query
3. **Semantic Search:** StorageBackend performs similarity search
4. **Ranking:** Results sorted by similarity score
5. **Filtering:** Optional filters applied (category, tags)
6. **Event Publishing:** `MemorySearchedEvent` published
7. **Metrics & Logging:** Search metrics recorded

The search is semantic—"database connection" matches "PostgreSQL is at 10.0.0.5" even without keyword overlap.

### Event-Driven Extensibility

When a memory is saved, the EventBus publishes an event. Handlers can subscribe:

```python
def audit_logger(event: MemoryCreatedEvent):
    # Log to audit system
    pass

manager.event_bus.subscribe("memory.created", audit_logger)
```

This pattern allows adding features without modifying core code: analytics, replication, caching, webhooks—all through event handlers.

## Getting Started

### Prerequisites

- **Python 3.10 or higher** (check with `python3 --version`)
- **pip** (Python package manager) or **uv** (faster alternative)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd memorycore

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# Install with ChromaDB backend and dev tools
pip install -e ".[chromadb,dev]"

# Or with uv (faster)
uv pip install -e ".[chromadb,dev]"
```

### Quick Test

```bash
# Run basic example
python examples/basic_usage.py

# Run tests
pytest tests/ -v

# Type checking
mypy src/

# Linting
ruff check src/
```

### Troubleshooting

**ImportError for chromadb:**
```bash
pip install chromadb>=0.4.0 sentence-transformers>=2.2.0
```

**pytest not found:**
```bash
pip install pytest pytest-asyncio pytest-cov
```

**Tests fail with async errors:**
```bash
pip install pytest-asyncio>=0.21.0
```

## Configuration

MemoryCore is configuration-driven. Set environment variables:

```bash
# Storage backend
STORAGE_BACKEND=chromadb
STORAGE_PATH=./memorycore_db
STORAGE_COLLECTION_NAME=memories

# Embedding provider
EMBEDDING_PROVIDER=chromadb
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Observability
OBSERVABILITY_LOG_LEVEL=INFO
OBSERVABILITY_LOG_FORMAT=json
OBSERVABILITY_ENABLE_METRICS=true
OBSERVABILITY_METRICS_PORT=9090

# Memory settings
TENANT_ID=default
DEFAULT_TTL_DAYS=30
ENABLE_VERSIONING=true
```

Or use a `.env` file. Configuration is validated at startup—invalid configs fail fast with clear error messages.

## Usage

### Basic Operations

```python
import asyncio
from memorycore.factory import create_memory_manager
from memorycore.core.memory import MemoryMetadata

async def main():
    # Create manager (auto-configures from environment)
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
    
    # Search memories
    results = await manager.search(
        query="production database connection",
        limit=5
    )
    
    for result in results:
        print(f"{result.score:.3f}: {result.memory.content}")

asyncio.run(main())
```

### MCP Server Integration

```bash
# Run MCP server
python -m memorycore.server

# Configure in Claude Desktop (claude_desktop_config.json)
{
  "mcpServers": {
    "memorycore": {
      "command": "python",
      "args": ["-m", "memorycore.server"]
    }
  }
}
```

### Advanced Features

**Memory Versioning:**
```python
# Updates automatically create versions
updated = await manager.update(
    memory_id=memory.id,
    content="Updated database IP: 10.0.0.6:5432"
)
print(f"Current version: {updated.version}")
print(f"Version history: {len(updated.versions)} versions")
```

**Memory Relationships:**
```python
schema_v1 = await manager.save(content="Database schema v1")
schema_v2 = await manager.save(content="Database schema v2")

# Link memories
schema_v2.add_relationship(
    target_id=schema_v1.id,
    relationship_type="supersedes",
    strength=1.0
)
```

**Event Subscriptions:**
```python
from memorycore.events.memory_events import MemoryCreatedEvent

def on_memory_created(event: MemoryCreatedEvent):
    # Custom logic: analytics, replication, etc.
    pass

manager.event_bus.subscribe("memory.created", on_memory_created)
```

## Design Decisions

MemoryCore makes several key architectural decisions to balance extensibility, production-readiness, and maintainability:

- **Plugin Architecture:** Abstract interfaces for storage backends and embedding services enable swapping implementations without changing core code
- **Event-Driven Architecture:** Publish-subscribe event bus allows adding features (audit logging, analytics, replication) without modifying core operations
- **Configuration-Driven:** Pydantic Settings with environment variables provide type-safe, validated configuration for different environments
- **Structured Logging:** JSON logs with correlation IDs enable production debugging and log aggregation
- **Retry Logic:** Exponential backoff handles transient failures while failing fast on persistent errors

For detailed rationale, alternatives considered, and implementation details, see [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md).

## Limitations & Tradeoffs

### Current Limitations

1. **Single Active Backend:** Only one storage backend active at a time (no replication)
2. **No Distributed Locking:** Multi-instance deployments may have race conditions
3. **Semantic Search Only:** No complex query language (SQL-like queries)
4. **No Built-in Auth:** Assumes single-user or external authentication
5. **Memory Size Limits:** Very large memories (>1MB) may impact performance
6. **Manual Backup:** No built-in backup/restore (users backup database files)

### Explicit Tradeoffs

1. **Extensibility vs. Simplicity:** Chose plugin architecture over simplicity. More complex initially, but enables long-term flexibility.

2. **Safety vs. Performance:** Retries add latency but improve reliability. For production systems, reliability is more important than microsecond latency.

3. **Storage vs. Features:** Versioning uses more storage but provides audit trail. Optional feature, but enabled by default because audit trails are valuable.

4. **Local-First vs. Cloud-Native:** Designed for local-first (data stays on user's machine) but architecture supports cloud deployments.

## Future Scope

- FAISS backend for high-performance vector search
- OpenAI and other embedding provider integrations
- Multi-backend replication and distributed locking
- REST API for non-MCP clients
- Web UI for memory management
- Export/import functionality
- Advanced filtering (date ranges, custom fields)
- Memory compression and optimization
- Authentication and rate limiting
- Graph visualization of memory relationships

## Contributing

Contributions welcome! 

### Development Setup

```bash
git clone <repository-url>
cd memorycore
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev,chromadb]"

# Run tests
pytest tests/ -v --cov=memorycore

# Type checking
mypy src/

# Linting
ruff check src/ --fix
```

---

**MemoryCore** - Persistent memory for AI agents, built for production.

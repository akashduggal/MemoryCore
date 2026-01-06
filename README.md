# 🧠 MemoryCore

**A production-grade memory framework for AI agents**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Status:** 🚧 Early Development | **Version:** 0.1.0

## ❓ The Problem

While building AI agent systems, I encountered a fundamental limitation: agents have no persistent memory across sessions. Every conversation starts from scratch, requiring expensive re-indexing of context and preventing agents from building on prior knowledge.

**Key pain points:**
- 💥 **Session Volatility** - Context lost when sessions end
- 💰 **Costly Re-indexing** - $1-3 per interaction for large contexts
- 🔍 **No Semantic Recall** - Can't query past knowledge by meaning
- 🔒 **Limited Extensibility** - Locked into single storage backends
- 👻 **Production Blindness** - No visibility into memory operations

## 🎯 Design Goals

MemoryCore solves these problems with:

- **🧠 Persistent Semantic Memory** - Store and retrieve by meaning, not keywords
- **🏭 Production-Ready** - Built-in observability, error handling, and resilience
- **🔌 Extensible** - Plugin architecture for storage backends and embedding providers
- **🛡️ Type-Safe** - Strong typing prevents runtime errors
- **⚙️ Configuration-Driven** - Everything configurable via environment variables

## 🏛️ Architecture Overview

MemoryCore uses a plugin architecture with clear separation of concerns:

```
Agent Interface (MCP/Direct API)
         ↓
   MemoryManager (Orchestrator)
    ↙    ↓    ↘
Storage  Embedding  Events
Backend  Service    Bus
```

**Key Components:**
- **🎯 MemoryManager** - Orchestrates operations, handles retries, publishes events
- **💾 StorageBackend** - Pluggable persistence (ChromaDB, FAISS, custom)
- **🔢 EmbeddingService** - Pluggable embeddings (local models, APIs)
- **📡 EventBus** - Extensibility through events
- **👁️ Observability** - Structured logging, metrics, health checks

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🚀 Quick Start

### Installation

```bash
# Clone and install
git clone <repository-url>
cd memorycore
python3 -m venv venv
source venv/bin/activate
pip install -e ".[chromadb,dev]"
```

### Basic Usage

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
        )
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

**📚 For detailed guides, see:**
- [Getting Started Guide](docs/GETTING_STARTED.md) - Installation, configuration, troubleshooting
- [Usage Guide](docs/USAGE.md) - Complete usage examples and advanced features
- [Architecture Documentation](ARCHITECTURE.md) - Deep dive into system design

## 🛠️ Tech Stack

- **🐍 Python 3.10+** with asyncio
- **📋 Pydantic** for type-safe validation
- **🗄️ ChromaDB** for vector storage
- **🤖 sentence-transformers** for embeddings
- **📝 structlog** for structured logging
- **📈 Prometheus** for metrics
- **🔌 MCP Protocol** for agent integration

## 📖 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - Installation, configuration, troubleshooting
- **[Usage Guide](docs/USAGE.md)** - Complete API reference and examples
- **[Architecture](ARCHITECTURE.md)** - System design and component details
- **[Design Decisions](DESIGN_DECISIONS.md)** - Architectural rationale

## ⚠️ Current Limitations

- 🔒 Single active backend (no replication)
- 🔐 No distributed locking
- 🔍 Semantic search only (no SQL-like queries)
- 🔑 No built-in authentication
- 📏 Memory size limits (>1MB may impact performance)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed limitations and tradeoffs.

## 🔮 Roadmap

- 🚀 FAISS backend for high-performance search
- 🤖 OpenAI and other embedding providers
- 🔄 Multi-backend replication
- 🌐 REST API
- 🖥️ Web UI
- 📤 Export/import functionality

## 🤝 Contributing

Contributions welcome! See [Getting Started](docs/GETTING_STARTED.md) for development setup.

```bash
# Development setup
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

**🧠 MemoryCore** - Persistent memory for AI agents, built for production.

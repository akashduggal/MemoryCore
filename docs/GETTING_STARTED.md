# 🚀 Getting Started with MemoryCore

This guide will help you get MemoryCore up and running quickly.

## 📋 Prerequisites

- **🐍 Python 3.10 or higher** (check with `python3 --version`)
- **📦 pip** (Python package manager) or **⚡ uv** (faster alternative)

## 📥 Installation

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

## ✅ Quick Test

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

## ⚙️ Configuration

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

## 🔧 Troubleshooting

### ImportError for chromadb
```bash
pip install chromadb>=0.4.0 sentence-transformers>=2.2.0
```

### pytest not found
```bash
pip install pytest pytest-asyncio pytest-cov
```

### Tests fail with async errors
```bash
pip install pytest-asyncio>=0.21.0
```

### Storage path issues
Make sure the directory specified in `STORAGE_PATH` exists and is writable:
```bash
mkdir -p ./memorycore_db
chmod 755 ./memorycore_db
```

### Embedding model download
The first time you use an embedding model, it will be downloaded. This can take a few minutes. Ensure you have internet connectivity.

## 🎯 Next Steps

- Read the [Usage Guide](USAGE.md) for detailed examples
- Check out the [Architecture Documentation](../ARCHITECTURE.md) to understand how it works
- Review [Design Decisions](../DESIGN_DECISIONS.md) for architectural rationale


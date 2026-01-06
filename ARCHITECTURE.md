# MemoryCore Architecture

## Design Philosophy

MemoryCore was designed from first principles to solve the persistent memory problem for AI agents. The architecture emerged from these constraints:

1. **Must work in production:** Observability, error handling, and resilience are not optional
2. **Must be extensible:** Different use cases need different storage backends and embedding providers
3. **Must be type-safe:** Runtime errors from invalid data should be caught at development time
4. **Must be configurable:** No hardcoded values; everything configurable for different environments
5. **Must be testable:** Unit tests shouldn't require external services

## System Architecture

### High-Level View

MemoryCore follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         Agent Interface Layer           │
│  (MCP Protocol, Direct Python API)     │
└──────────────────┬──────────────────────┘
                    │
┌──────────────────▼──────────────────────┐
│         Orchestration Layer              │
│         (MemoryManager)                  │
│  • Input validation                      │
│  • Retry coordination                   │
│  • Event publishing                      │
│  • Metrics recording                    │
└───┬──────────┬──────────┬───────────────┘
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼────────┐
│Storage│ │Embed  │ │  Events    │
│Plugin │ │Plugin │ │   Bus      │
└───┬───┘ └───┬───┘ └────────────┘
    │        │
┌───▼────────▼───────────────────────────┐
│      Implementation Layer               │
│  ChromaDB │ FAISS │ InMemory │ Custom   │
└─────────────────────────────────────────┘
```

### Component Responsibilities

#### MemoryManager

**Purpose:** Orchestrates all memory operations. It doesn't store data or generate embeddings—it coordinates between components.

**Responsibilities:**
- Validate inputs (content, metadata)
- Coordinate embedding generation
- Coordinate storage operations
- Handle retries with exponential backoff
- Publish events for extensibility
- Record metrics for observability
- Handle errors gracefully

**Design Rationale:** Centralizing orchestration in one place makes the system easier to reason about. The manager doesn't know about ChromaDB or FAISS—it only knows about the `StorageBackend` interface.

#### StorageBackend Interface

**Purpose:** Abstract interface for persistence. Implementations handle storage-specific details.

**Interface Methods:**
- `save(memory)`: Persist a memory
- `get(memory_id, tenant_id)`: Retrieve by ID
- `delete(memory_id, tenant_id)`: Delete a memory
- `search(query_embedding, tenant_id, limit, filters)`: Semantic search
- `list(tenant_id, limit, offset, filters)`: List memories
- `count(tenant_id, filters)`: Count memories
- `health_check()`: Component health status

**Design Rationale:** The interface ensures implementations are swappable. A ChromaDB backend and a FAISS backend implement the same interface, so MemoryManager doesn't need to change.

**Current Implementations:**
- `ChromaDBBackend`: Uses ChromaDB's persistent client
- `InMemoryBackend`: In-memory storage for testing

**Future Implementations:**
- `FAISSBackend`: High-performance vector search
- `PineconeBackend`: Cloud vector database
- `PostgresBackend`: Using pgvector extension

#### EmbeddingService Interface

**Purpose:** Abstract interface for generating vector embeddings.

**Interface Methods:**
- `embed(text)`: Generate embedding for single text
- `embed_batch(texts)`: Generate embeddings for multiple texts
- `get_dimension()`: Return embedding dimension
- `health_check()`: Component health status

**Design Rationale:** Different embedding providers (local models, API services) can be swapped without changing core code.

**Current Implementations:**
- `ChromaDBEmbeddingService`: Uses sentence-transformers locally

**Future Implementations:**
- `OpenAIEmbeddingService`: Uses OpenAI API
- `CohereEmbeddingService`: Uses Cohere API
- `CustomEmbeddingService`: User-provided models

#### EventBus

**Purpose:** Publish-subscribe system for extensibility.

**Events:**
- `MemoryCreatedEvent`: Fired when memory is saved
- `MemoryUpdatedEvent`: Fired when memory is updated
- `MemoryDeletedEvent`: Fired when memory is deleted
- `MemorySearchedEvent`: Fired when search is performed

**Design Rationale:** Events enable adding features without modifying core code. Handlers can subscribe to add audit logging, analytics, replication, caching, or webhooks.

**Implementation:** Simple in-memory event bus. Events are published non-blocking—handlers don't slow down main operations.

#### Observability Layer

**Purpose:** Provide visibility into system behavior.

**Components:**

1. **Structured Logging** (`observability/logging.py`)
   - JSON format for log aggregation systems
   - Correlation IDs for request tracking
   - Configurable log levels

2. **Metrics** (`observability/metrics.py`)
   - Prometheus metrics (counters, gauges, histograms)
   - Operation counts, durations, error rates
   - Memory counts per tenant

3. **Health Checks** (`observability/health.py`)
   - Component health status
   - Storage and embedding service checks
   - Aggregate health status

**Design Rationale:** Production systems need observability. Structured logs enable querying, metrics enable alerting, health checks enable monitoring.

## Data Flow

### Save Operation

```
1. Client calls MemoryManager.save()
   │
2. MemoryManager validates input
   │  ├─ Content not empty? → InvalidMemoryError if not
   │  └─ Metadata well-formed? → ValidationError if not
   │
3. MemoryManager calls EmbeddingService.embed()
   │  ├─ Success → Continue
   │  └─ Failure → Retry with exponential backoff (max 3 attempts)
   │     └─ Still fails → Log error, continue without embedding
   │
4. MemoryManager calls StorageBackend.save()
   │  ├─ Success → Continue
   │  └─ Failure → Retry with exponential backoff (max 3 attempts)
   │     └─ Still fails → Propagate error
   │
5. MemoryManager publishes MemoryCreatedEvent
   │  └─ Non-blocking, handlers execute asynchronously
   │
6. MemoryManager records metrics
   │  ├─ Operation count (save, success)
   │  └─ Operation duration
   │
7. MemoryManager logs structured entry
   │  └─ JSON log with correlation ID, memory ID, tenant ID
   │
8. Return Memory object to client
```

**Key Design Points:**
- Validation happens early (fail fast)
- Retries handle transient failures
- Events don't block main operation
- Metrics and logs provide observability

### Search Operation

```
1. Client calls MemoryManager.search()
   │
2. MemoryManager validates query
   │  └─ Query not empty? → InvalidQueryError if not
   │
3. MemoryManager calls EmbeddingService.embed(query)
   │  └─ Retry on failure (max 3 attempts)
   │
4. MemoryManager calls StorageBackend.search()
   │  ├─ Query embedding
   │  ├─ Tenant ID (for isolation)
   │  ├─ Limit (max results)
   │  └─ Filters (category, tags)
   │
5. StorageBackend performs semantic search
   │  ├─ ChromaDB: Cosine similarity search
   │  └─ Returns results sorted by similarity
   │
6. MemoryManager publishes MemorySearchedEvent
   │  └─ Includes query, result count
   │
7. MemoryManager records metrics
   │  ├─ Search count
   │  └─ Search duration
   │
8. MemoryManager logs structured entry
   │  └─ Query, result count, tenant ID
   │
9. Return SearchResult list to client
```

**Key Design Points:**
- Semantic search (meaning-based, not keyword-based)
- Tenant isolation (all queries scoped by tenant)
- Filtering support (category, tags)
- Observability (events, metrics, logs)

## Data Model

### Memory Structure

```python
Memory:
  id: UUID                    # Unique identifier
  content: str                # The actual information
  metadata: MemoryMetadata    # Category, tags, importance
  embedding: list[float]     # Vector representation
  tenant_id: str              # Tenant isolation
  created_at: datetime        # Creation timestamp
  updated_at: datetime        # Last update timestamp
  expires_at: datetime | None # Optional expiration
  relationships: list[...]     # Links to other memories
  versions: list[...]         # Version history
  version: int                # Current version number
```

**Design Rationale:**
- **ID:** UUID ensures uniqueness across distributed systems
- **Content:** The core information being stored
- **Metadata:** Structured categorization for filtering
- **Embedding:** Enables semantic search
- **Tenant ID:** Multi-tenant support from the start
- **Timestamps:** Audit trail and TTL support
- **Relationships:** Link related memories (supersedes, contradicts, extends)
- **Versions:** Track changes over time (optional but valuable)

### MemoryMetadata Structure

```python
MemoryMetadata:
  category: str                    # Classification (e.g., "infrastructure")
  tags: list[str]                  # Searchable tags
  importance: "low" | "medium" | "high"  # Priority level
  custom_fields: dict[str, Any]    # Extensible custom data
```

**Design Rationale:**
- **Category:** Coarse-grained classification for filtering
- **Tags:** Fine-grained, multiple tags per memory
- **Importance:** Affects retrieval priority (future feature)
- **Custom Fields:** Extensible for user-specific needs

## Error Handling Strategy

### Error Hierarchy

```
MemoryCoreError (base)
├── StorageError
│   ├── StorageConnectionError
│   ├── StorageOperationError
│   └── StorageNotFoundError
├── EmbeddingError
│   ├── EmbeddingModelError
│   └── EmbeddingDimensionError
└── ValidationError
    ├── InvalidMemoryError
    └── InvalidQueryError
```

**Design Rationale:**
- Hierarchical exceptions enable catching specific error types
- Error codes enable programmatic error handling
- Details dictionary provides context for debugging

### Retry Strategy

**When to Retry:**
- Embedding generation (transient API failures)
- Storage operations (transient database locks)

**When NOT to Retry:**
- Validation errors (invalid input won't become valid)
- Not found errors (missing resource won't appear)

**Retry Configuration:**
- Max attempts: 3 (configurable)
- Initial delay: 1 second
- Max delay: 60 seconds
- Exponential base: 2.0

**Design Rationale:**
- Retries handle transient failures automatically
- Exponential backoff reduces load on failing systems
- Limits prevent infinite retry loops

## Extension Points

### Adding a Storage Backend

1. Implement `StorageBackend` interface
2. Add factory method in `factory.py`
3. Add configuration option in `Settings`
4. Write tests with mock data

**Example:**
```python
class FAISSBackend(StorageBackend):
    async def save(self, memory: Memory) -> None:
        # FAISS-specific implementation
        pass
    # ... implement other methods
```

### Adding an Embedding Service

1. Implement `EmbeddingService` interface
2. Add factory method in `factory.py`
3. Add configuration option in `Settings`
4. Write tests

**Example:**
```python
class OpenAIEmbeddingService(EmbeddingService):
    async def embed(self, text: str) -> list[float]:
        # OpenAI API call
        pass
    # ... implement other methods
```

### Adding Event Handlers

1. Subscribe to event types
2. Implement handler function
3. Handle errors gracefully (don't block main operations)

**Example:**
```python
def audit_logger(event: MemoryCreatedEvent):
    # Log to audit system
    audit_system.log(event.memory)

manager.event_bus.subscribe("memory.created", audit_logger)
```

## Performance Considerations

### Embedding Generation
- **Caching:** Embeddings cached when memory is retrieved
- **Batching:** `embed_batch()` for multiple texts (more efficient)
- **Async:** Non-blocking operations don't slow down main flow

### Storage Queries
- **Indexing:** Storage backends index by tenant_id, category
- **Limits:** Search and list operations have configurable limits
- **Filtering:** Filters applied at storage level (not in memory)

### Event Publishing
- **Non-blocking:** Events published asynchronously
- **Error Handling:** Handler errors don't fail main operation
- **Lightweight:** Events are simple data structures

### Metrics Collection
- **Asynchronous:** Metrics recorded without blocking
- **Minimal Overhead:** Prometheus client is lightweight
- **Configurable:** Can be disabled for maximum performance

## Security Considerations

### Tenant Isolation
- All operations scoped by `tenant_id`
- Storage backends enforce tenant boundaries
- No cross-tenant data leakage

### Input Validation
- Pydantic validates all inputs at boundaries
- Prevents injection attacks (SQL, etc.)
- Type safety prevents entire classes of errors

### Local-First Design
- Data stays on user's machine by default
- No external API calls unless configured
- User controls their data

### Future Security Features
- Authentication (API keys, OAuth)
- Rate limiting (per tenant)
- Encryption at rest
- Audit logging

## Future Enhancements

### Distributed Locking
- For multi-instance deployments
- Prevent race conditions
- Use Redis or similar

### Replication
- Write to multiple backends
- Redundancy and failover
- Event-driven replication

### Caching
- Redis/Memcached for frequently accessed memories
- Reduce storage load
- Improve latency

### Compression
- Compress old memories to save space
- Transparent decompression on access
- Configurable compression threshold

### Graph Database
- For complex relationship queries
- Visualize memory relationships
- Traverse relationship graphs

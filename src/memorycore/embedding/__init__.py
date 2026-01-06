"""Embedding services for MemoryCore."""

from memorycore.embedding.base import EmbeddingService
from memorycore.embedding.chromadb_embedding import ChromaDBEmbeddingService

__all__ = ["EmbeddingService", "ChromaDBEmbeddingService"]


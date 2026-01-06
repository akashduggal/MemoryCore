"""Exception hierarchy for MemoryCore."""

from memorycore.exceptions.base import MemoryCoreError
from memorycore.exceptions.storage import (
    StorageError,
    StorageConnectionError,
    StorageOperationError,
    StorageNotFoundError,
)
from memorycore.exceptions.embedding import (
    EmbeddingError,
    EmbeddingModelError,
    EmbeddingDimensionError,
)
from memorycore.exceptions.validation import (
    ValidationError,
    InvalidMemoryError,
    InvalidQueryError,
)

__all__ = [
    "MemoryCoreError",
    "StorageError",
    "StorageConnectionError",
    "StorageOperationError",
    "StorageNotFoundError",
    "EmbeddingError",
    "EmbeddingModelError",
    "EmbeddingDimensionError",
    "ValidationError",
    "InvalidMemoryError",
    "InvalidQueryError",
]


"""Embedding-related exceptions."""

from memorycore.exceptions.base import MemoryCoreError


class EmbeddingError(MemoryCoreError):
    """Base exception for embedding operations."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, error_code="EMBEDDING_ERROR", details=details)


class EmbeddingModelError(EmbeddingError):
    """Raised when embedding model fails."""

    def __init__(self, message: str, model_name: str | None = None, details: dict | None = None):
        super().__init__(message, details)
        self.error_code = "EMBEDDING_MODEL_ERROR"
        self.model_name = model_name


class EmbeddingDimensionError(EmbeddingError):
    """Raised when embedding dimensions don't match."""

    def __init__(
        self, message: str, expected: int | None = None, actual: int | None = None, details: dict | None = None
    ):
        super().__init__(message, details)
        self.error_code = "EMBEDDING_DIMENSION_ERROR"
        self.expected = expected
        self.actual = actual


"""Validation-related exceptions."""

from memorycore.exceptions.base import MemoryCoreError


class ValidationError(MemoryCoreError):
    """Base exception for validation errors."""

    def __init__(self, message: str, field: str | None = None, details: dict | None = None):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)
        self.field = field


class InvalidMemoryError(ValidationError):
    """Raised when memory data is invalid."""

    def __init__(self, message: str, field: str | None = None, details: dict | None = None):
        super().__init__(message, field, details)
        self.error_code = "INVALID_MEMORY"


class InvalidQueryError(ValidationError):
    """Raised when query is invalid."""

    def __init__(self, message: str, query: str | None = None, details: dict | None = None):
        super().__init__(message, field="query", details=details)
        self.error_code = "INVALID_QUERY"
        self.query = query


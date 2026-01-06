"""Storage-related exceptions."""

from memorycore.exceptions.base import MemoryCoreError


class StorageError(MemoryCoreError):
    """Base exception for storage operations."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, error_code="STORAGE_ERROR", details=details)


class StorageConnectionError(StorageError):
    """Raised when storage connection fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, details)
        self.error_code = "STORAGE_CONNECTION_ERROR"


class StorageOperationError(StorageError):
    """Raised when a storage operation fails."""

    def __init__(self, message: str, operation: str | None = None, details: dict | None = None):
        super().__init__(message, details)
        self.error_code = "STORAGE_OPERATION_ERROR"
        self.operation = operation


class StorageNotFoundError(StorageError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, resource_id: str | None = None, details: dict | None = None):
        super().__init__(message, details)
        self.error_code = "STORAGE_NOT_FOUND"
        self.resource_id = resource_id


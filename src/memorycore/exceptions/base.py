"""Base exception classes."""


class MemoryCoreError(Exception):
    """Base exception for all MemoryCore errors."""

    def __init__(self, message: str, error_code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "MEMORY_CORE_ERROR"
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.error_code}): {self.message}"


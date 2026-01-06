"""Application settings and configuration."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageConfig(BaseSettings):
    """Storage backend configuration."""

    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    backend: Literal["chromadb", "faiss", "memory"] = Field(
        default="chromadb", description="Storage backend to use"
    )
    path: Path = Field(default=Path("./memorycore_db"), description="Storage path")
    collection_name: str = Field(default="memories", description="Collection name")
    persist: bool = Field(default=True, description="Whether to persist data")


class EmbeddingConfig(BaseSettings):
    """Embedding service configuration."""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    provider: Literal["chromadb", "openai", "sentence-transformers"] = Field(
        default="chromadb", description="Embedding provider"
    )
    model_name: str = Field(
        default="all-MiniLM-L6-v2", description="Model name for sentence-transformers"
    )
    dimension: int | None = Field(default=None, description="Embedding dimension (auto-detected)")
    api_key: str | None = Field(default=None, description="API key for external providers")


class ObservabilityConfig(BaseSettings):
    """Observability configuration."""

    model_config = SettingsConfigDict(env_prefix="OBSERVABILITY_")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(default="json", description="Log format")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    enable_health: bool = Field(default=True, description="Enable health check endpoint")
    health_port: int = Field(default=8080, description="Health check server port")


class RetryConfig(BaseSettings):
    """Retry configuration."""

    model_config = SettingsConfigDict(env_prefix="RETRY_")

    max_attempts: int = Field(default=3, ge=1, description="Maximum retry attempts")
    initial_delay: float = Field(default=1.0, ge=0, description="Initial delay in seconds")
    max_delay: float = Field(default=60.0, ge=0, description="Maximum delay in seconds")
    exponential_base: float = Field(default=2.0, ge=1, description="Exponential backoff base")


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    tenant_id: str = Field(default="default", description="Tenant ID for multi-tenant support")
    storage: StorageConfig = Field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)

    # Memory-specific settings
    default_ttl_days: int | None = Field(default=None, description="Default TTL in days")
    enable_versioning: bool = Field(default=True, description="Enable memory versioning")
    max_memory_size: int = Field(default=1_000_000, ge=0, description="Maximum memory size in bytes")

    @field_validator("storage", mode="before")
    @classmethod
    def validate_storage_path(cls, v):
        """Ensure storage path is absolute."""
        if isinstance(v, dict) and "path" in v:
            path = Path(v["path"])
            if not path.is_absolute():
                v["path"] = Path.cwd() / path
        return v

    def model_post_init(self, __context):
        """Post-initialization validation."""
        # Ensure storage directory exists
        if self.storage.persist:
            self.storage.path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


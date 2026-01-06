"""Core memory data models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class MemoryMetadata(BaseModel):
    """Metadata for a memory."""

    category: str = Field(default="general", description="Memory category")
    tags: list[str] = Field(default_factory=list, description="Memory tags")
    importance: Literal["low", "medium", "high"] = Field(
        default="medium", description="Importance level"
    )
    custom_fields: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags."""
        return [tag.lower().strip() for tag in v if tag.strip()]


class MemoryRelationship(BaseModel):
    """Relationship between memories."""

    target_id: UUID = Field(description="Target memory ID")
    relationship_type: Literal["related", "supersedes", "contradicts", "extends"] = Field(
        default="related", description="Type of relationship"
    )
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Relationship strength")


class MemoryVersion(BaseModel):
    """Version information for a memory."""

    version: int = Field(ge=1, description="Version number")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Version timestamp"
    )
    content: str = Field(description="Content at this version")
    changed_fields: list[str] = Field(default_factory=list, description="Fields that changed")

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat()

    model_config = ConfigDict()


class Memory(BaseModel):
    """Core memory model."""

    id: UUID = Field(default_factory=uuid4, description="Unique memory ID")
    content: str = Field(min_length=1, description="Memory content")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata, description="Memory metadata")
    embedding: list[float] | None = Field(default=None, description="Embedding vector")
    tenant_id: str = Field(default="default", description="Tenant ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp"
    )
    expires_at: datetime | None = Field(default=None, description="Expiration timestamp")
    relationships: list[MemoryRelationship] = Field(
        default_factory=list, description="Relationships to other memories"
    )
    versions: list[MemoryVersion] = Field(default_factory=list, description="Version history")
    version: int = Field(default=1, ge=1, description="Current version number")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v or not v.strip():
            raise ValueError("Memory content cannot be empty")
        return v.strip()

    def is_expired(self) -> bool:
        """Check if memory has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def add_relationship(self, target_id: UUID, relationship_type: str, strength: float = 1.0):
        """Add a relationship to another memory."""
        relationship = MemoryRelationship(
            target_id=target_id, relationship_type=relationship_type, strength=strength
        )
        # Remove existing relationship to same target
        self.relationships = [r for r in self.relationships if r.target_id != target_id]
        self.relationships.append(relationship)

    def create_version(self, changed_fields: list[str] | None = None):
        """Create a new version snapshot."""
        if changed_fields is None:
            changed_fields = ["content"]
        version = MemoryVersion(
            version=self.version,
            created_at=self.updated_at,
            content=self.content,
            changed_fields=changed_fields,
        )
        self.versions.append(version)
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def set_ttl(self, days: int):
        """Set time-to-live in days."""
        self.expires_at = datetime.now(timezone.utc) + timedelta(days=days)

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Serialize UUID to string."""
        return str(value)

    @field_serializer("created_at", "updated_at", "expires_at")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """Serialize datetime to ISO format."""
        if value is None:
            return None
        return value.isoformat()

    model_config = ConfigDict()


"""MemoryCore - Production-ready memory framework for AI agents."""

from memorycore.core.memory_manager import MemoryManager
from memorycore.core.memory import Memory, MemoryMetadata, MemoryRelationship
from memorycore.config.settings import Settings, get_settings

__version__ = "0.1.0"
__all__ = [
    "MemoryManager",
    "Memory",
    "MemoryMetadata",
    "MemoryRelationship",
    "Settings",
    "get_settings",
]


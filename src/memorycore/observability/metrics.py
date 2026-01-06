"""Metrics collection for MemoryCore."""

from functools import lru_cache
from time import time
from typing import Any

try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
except ImportError:
    # Fallback if prometheus_client not available
    Counter = Gauge = Histogram = None
    start_http_server = None


class MetricsCollector:
    """Metrics collector using Prometheus."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        if enabled and Counter is not None:
            self._init_metrics()
        else:
            self._init_noop_metrics()

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        self.memory_operations = Counter(
            "memorycore_memory_operations_total",
            "Total memory operations",
            ["operation", "tenant_id", "status"],
        )
        self.memory_count = Gauge("memorycore_memory_count", "Current memory count", ["tenant_id"])
        self.operation_duration = Histogram(
            "memorycore_operation_duration_seconds",
            "Operation duration in seconds",
            ["operation"],
        )
        self.embedding_operations = Counter(
            "memorycore_embedding_operations_total",
            "Total embedding operations",
            ["status"],
        )
        self.search_operations = Counter(
            "memorycore_search_operations_total",
            "Total search operations",
            ["tenant_id"],
        )

    def _init_noop_metrics(self):
        """Initialize no-op metrics."""
        self.memory_operations = self._noop_counter()
        self.memory_count = self._noop_gauge()
        self.operation_duration = self._noop_histogram()
        self.embedding_operations = self._noop_counter()
        self.search_operations = self._noop_counter()

    def record_operation(self, operation: str, tenant_id: str, status: str, duration: float | None = None):
        """Record a memory operation."""
        if self.enabled:
            self.memory_operations.labels(operation=operation, tenant_id=tenant_id, status=status).inc()
            if duration is not None:
                self.operation_duration.labels(operation=operation).observe(duration)

    def record_embedding(self, status: str):
        """Record an embedding operation."""
        if self.enabled:
            self.embedding_operations.labels(status=status).inc()

    def record_search(self, tenant_id: str):
        """Record a search operation."""
        if self.enabled:
            self.search_operations.labels(tenant_id=tenant_id).inc()

    def set_memory_count(self, tenant_id: str, count: int):
        """Set memory count gauge."""
        if self.enabled:
            self.memory_count.labels(tenant_id=tenant_id).set(count)

    def start_metrics_server(self, port: int = 9090):
        """Start Prometheus metrics server."""
        if start_http_server and self.enabled:
            start_http_server(port)
            return True
        return False

    @staticmethod
    def _noop_counter():
        """Create a no-op counter."""
        return type("NoOpCounter", (), {"labels": lambda **kwargs: type("", (), {"inc": lambda: None})()})()

    @staticmethod
    def _noop_gauge():
        """Create a no-op gauge."""
        return type("NoOpGauge", (), {"labels": lambda **kwargs: type("", (), {"set": lambda x: None})()})()

    @staticmethod
    def _noop_histogram():
        """Create a no-op histogram."""
        return type("NoOpHistogram", (), {"labels": lambda **kwargs: type("", (), {"observe": lambda x: None})()})()


@lru_cache()
def get_metrics_collector(enabled: bool = True) -> MetricsCollector:
    """Get cached metrics collector."""
    return MetricsCollector(enabled=enabled)


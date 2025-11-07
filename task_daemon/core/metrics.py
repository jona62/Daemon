"""Unified metrics interface for Task Daemon."""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CollectorRegistry,
)
from typing import Dict, Any


class MetricsCollector:
    """Unified metrics collection and access."""

    def __init__(self, registry=None):
        self.registry = registry or CollectorRegistry()
        self.tasks_received = Counter(
            "tasks_received_total", "Total tasks received", registry=self.registry
        )
        self.tasks_processed = Counter(
            "tasks_processed_total",
            "Total tasks processed",
            ["status"],
            registry=self.registry,
        )
        self.queue_size = Gauge(
            "queue_size", "Current queue size", registry=self.registry
        )
        self.processing_time = Histogram(
            "task_processing_seconds", "Task processing time", registry=self.registry
        )
        self.daemon_health = Gauge(
            "daemon_health",
            "Daemon health status (1=healthy, 0=unhealthy)",
            registry=self.registry,
        )

    def task_received(self):
        """Record a task being received."""
        self.tasks_received.inc()

    def task_processed(self, status: str, duration: float = None):
        """Record a task being processed."""
        self.tasks_processed.labels(status=status).inc()
        if duration is not None:
            self.processing_time.observe(duration)

    def update_queue_size(self, size: int):
        """Update current queue size."""
        self.queue_size.set(size)

    def set_health(self, healthy: bool):
        """Set daemon health status."""
        self.daemon_health.set(1 if healthy else 0)

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus formatted metrics."""
        return generate_latest(self.registry)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary as dict."""
        return {
            "tasks_received": self.tasks_received._value._value,
            "tasks_processed_success": self.tasks_processed.labels(
                status="success"
            )._value._value,
            "tasks_processed_failed": self.tasks_processed.labels(
                status="failed"
            )._value._value,
            "queue_size": self.queue_size._value._value,
            "daemon_healthy": bool(self.daemon_health._value._value),
        }

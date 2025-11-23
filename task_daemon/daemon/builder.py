"""Builder pattern for TaskDaemon configuration."""

from queue import Queue
from typing import Callable

from task_daemon.core.persistent_queue import PersistentQueue
from .daemon import TaskDaemon
from ..config import DaemonConfig


class DaemonBuilder:
    """Builder for TaskDaemon with fluent interface."""

    def __init__(self):
        self._config = DaemonConfig()
        self._queue = None
        self._metrics_registry = None
        self._handlers = []

    def with_config(self, **kwargs):
        """Configure daemon settings."""
        self._config = DaemonConfig(**kwargs)
        return self

    def with_queue(self, queue: Queue):
        """Set default queue to use."""
        self._queue = queue
        return self

    def with_metrics_registry(self, metrics_registry):
        """Set metrics registry."""
        self._metrics_registry = metrics_registry
        return self

    def add_handler(self, handler_func: Callable):
        """Add a task handler using function name as task type."""
        self._handlers.append(handler_func)
        return self

    def build(self) -> TaskDaemon:
        """Build and configure the TaskDaemon."""
        queue = self._queue or PersistentQueue(self._config.db_path)
        daemon = TaskDaemon(
            config=self._config, metrics_registry=self._metrics_registry, queue=queue
        )

        for handler in self._handlers:
            daemon.register_handler(handler)

        return daemon

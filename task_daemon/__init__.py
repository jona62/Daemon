"""Task Daemon - A configurable task processing system with monitoring."""

from .daemon import TaskDaemon
from .daemon.builder import DaemonBuilder
from .client import DaemonClient
from .config import DaemonConfig
from .core import task_handler, get_all_handlers, Queue, PersistentQueue, MemoryQueue

__version__ = "0.1.0"
__all__ = [
    "TaskDaemon",
    "DaemonBuilder",
    "DaemonClient",
    "DaemonConfig",
    "task_handler",
    "get_all_handlers",
    "Queue",
    "PersistentQueue",
    "MemoryQueue",
]

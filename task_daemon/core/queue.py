"""Queue interface for TaskDaemon."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any, Dict, List


class Queue(ABC):
    """Abstract interface for task queues."""

    @abstractmethod
    def enqueue(self, task_type: str, task_data: Any) -> int:
        """Add task to queue. Returns task ID."""
        pass

    @abstractmethod
    def dequeue(self) -> Optional[Tuple[int, str, Any]]:
        """Get next pending task. Returns (id, task_type, task_data) or None."""
        pass

    @abstractmethod
    def mark_complete(self, task_id: int, result: Any = None):
        """Mark task as completed (terminal state)."""
        pass

    @abstractmethod
    def mark_failed(self, task_id: int, error: str, max_retries: int = 3):
        """Mark task as failed, retry if under max attempts."""
        pass

    @abstractmethod
    def size(self) -> int:
        """Get number of pending tasks."""
        pass

    @abstractmethod
    def get_recent_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent tasks for monitoring."""
        pass

    @abstractmethod
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID with all metadata."""
        pass

    @abstractmethod
    def delete_task(self, task_id: int) -> bool:
        """Delete task from queue. Returns True if task existed."""
        pass

    @abstractmethod
    def redrive_task(self, task_id: int) -> bool:
        """Redrive a failed task by resetting it to pending. Returns True if successful."""
        pass

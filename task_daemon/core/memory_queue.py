"""In-memory task queue implementation."""

import threading
import time
from typing import Optional, Tuple, Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

from .queue import Queue


@dataclass
class Task:
    """Task data structure."""

    id: int
    task_type: str
    task_data: Any
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    attempts: int = 0
    last_error: Optional[str] = None
    result: Any = None


class MemoryQueue(Queue):
    """Thread-safe in-memory task queue."""

    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1

    def enqueue(self, task_type: str, task_data: Any) -> int:
        """Add task to queue. Returns task ID."""
        with self._lock:
            task_id = self._next_id
            self._next_id += 1
            self._tasks[task_id] = Task(
                id=task_id, task_type=task_type, task_data=task_data
            )
            return task_id

    def dequeue(self) -> Optional[Tuple[int, str, Any]]:
        """Get next pending task. Returns (id, task_type, task_data) or None."""
        with self._lock:
            for task in self._tasks.values():
                if task.status == "pending":
                    task.status = "processing"
                    return task.id, task.task_type, task.task_data
            return None

    def mark_complete(self, task_id: int, result: Any = None):
        """Mark task as completed (terminal state)."""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.result = result

    def mark_failed(self, task_id: int, error: str, max_retries: int = 3):
        """Mark task as failed, retry if under max attempts."""
        with self._lock:
            if task_id not in self._tasks:
                return

            task = self._tasks[task_id]
            task.attempts += 1
            task.last_error = error

            if task.attempts >= max_retries:
                task.status = "failed"
            else:
                task.status = "pending"

    def size(self) -> int:
        """Get number of pending tasks."""
        with self._lock:
            return sum(1 for task in self._tasks.values() if task.status == "pending")

    def get_recent_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent tasks for monitoring."""
        with self._lock:
            tasks = sorted(self._tasks.values(), key=lambda t: t.id, reverse=True)[
                :limit
            ]
            return [self._task_to_dict(task) for task in tasks]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID with all metadata."""
        with self._lock:
            task = self._tasks.get(task_id)
            return self._task_to_dict(task) if task else None

    def delete_task(self, task_id: int) -> bool:
        """Delete task from queue. Returns True if task existed."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    def redrive_task(self, task_id: int) -> bool:
        """Redrive a failed task by resetting it to pending. Returns True if successful."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == "failed":
                task.status = "pending"
                task.last_error = None
                return True
            return False

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": task.id,
            "task_type": task.task_type,
            "task_data": task.task_data,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "attempts": task.attempts,
            "last_error": task.last_error,
            "result": task.result,
        }

"""Client for interacting with TaskDaemon."""

import requests
import logging
from typing import Optional, List, Dict, Any, TypeVar, overload
from pydantic import BaseModel

from .models import HealthStatus, TaskInfo, MetricsSummary
from ..protocols import get_protocol, Protocol

T = TypeVar("T", bound=BaseModel)


class DaemonClient:
    """Client for interacting with TaskDaemon service."""

    def __init__(
        self,
        daemon_url: str = "http://localhost:8080",
        timeout: float = 0.1,
        protocol: str = "json",
    ):
        self.daemon_url = daemon_url.rstrip("/")
        self.timeout = timeout
        self.protocol: Protocol = get_protocol(f"application/{protocol}")
        self.logger = logging.getLogger(__name__)

    @overload
    def queue_task(
        self, task_type: str, task_data: T, *, critical: bool = True
    ) -> Optional[int]: ...

    @overload
    def queue_task(
        self, task_type: str, task_data: Dict[str, Any], *, critical: bool = True
    ) -> Optional[int]: ...

    @overload
    def queue_task(
        self, task_type: str, *args: Any, critical: bool = True, **kwargs: Any
    ) -> Optional[int]: ...

    def queue_task(
        self, task_type: str, *args: Any, critical: bool = True, **kwargs: Any
    ) -> Optional[int]:
        """Queue a task for processing.

        Args:
            task_type: Type of task to process
            *args: Positional arguments for the task handler
            critical: If True, raises exception on failure
            **kwargs: Keyword arguments for the task handler

        Returns:
            Task ID if successful, None if failed (unless critical=True)

        Examples:
            queue_task("add", MyClass(...))  # If defined with Pydantic like this MyClass(BaseModel)
            queue_task("add", {"a": 1, "b": 2})  # Dict
            queue_task("add", a=1, b=2)  # Kwargs
            queue_task("add", 1, 2)  # Positional (converted to dict with param names)
        """
        try:
            # Determine task_data format
            if args and len(args) == 1 and isinstance(args[0], (dict, BaseModel)):
                # Single dict or Pydantic model argument
                task_data = args[0]
            elif args:
                # Multiple positional args - convert to dict
                # Note: This requires the handler to accept **kwargs
                task_data = {"args": args}
            elif kwargs:
                # Keyword arguments
                task_data = kwargs
            else:
                task_data = None

            # Auto-serialize Pydantic models
            data = (
                task_data.model_dump()
                if isinstance(task_data, BaseModel)
                else task_data
            )
            payload = {"type": task_type, "data": data}

            # Serialize with protocol
            body = self.protocol.serialize(payload)
            headers = {"Content-Type": self.protocol.content_type}

            response = requests.post(
                f"{self.daemon_url}/queue",
                data=body,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                # Deserialize response with same protocol
                result = self.protocol.deserialize(response.content)
                return result.get("task_id")
            else:
                self.logger.warning(f"Failed to queue task: {response.status_code}")
                if response.status_code == 422:
                    self.logger.warning(f"Validation error: {response.text}")

        except Exception as e:
            self.logger.warning(f"Failed to queue task: {e}")
            if critical:
                raise
        return None

    def health_check(self) -> HealthStatus:
        """Check daemon health status."""
        try:
            response = requests.get(f"{self.daemon_url}/health", timeout=self.timeout)
            return HealthStatus.model_validate(response.json())
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return HealthStatus(
                status="unhealthy", queue_size=0, timestamp="", workers=0
            )

    def get_metrics(self) -> MetricsSummary:
        """Get daemon metrics."""
        try:
            response = requests.get(
                f"{self.daemon_url}/api/metrics", timeout=self.timeout
            )
            return MetricsSummary.model_validate(response.json())
        except Exception as e:
            self.logger.debug(f"Metrics request failed: {e}")
            return MetricsSummary(
                tasks_received=0,
                tasks_processed=0,
                tasks_failed=0,
                queue_size=0,
                workers=0,
            )

    def get_tasks(self, limit: int = 20) -> List[TaskInfo]:
        """Get recent tasks."""
        try:
            response = requests.get(
                f"{self.daemon_url}/api/tasks",
                params={"limit": limit},
                timeout=self.timeout,
            )
            tasks = response.json()
            # Parse JSON strings in task_data and result fields
            for task in tasks:
                if task.get("task_data") and isinstance(task["task_data"], str):
                    import json

                    task["task_data"] = json.loads(task["task_data"])
                if task.get("result") and isinstance(task["result"], str):
                    import json

                    task["result"] = json.loads(task["result"])
            return [TaskInfo.model_validate(task) for task in tasks]
        except Exception as e:
            self.logger.debug(f"Tasks request failed: {e}")
            return []

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus formatted metrics."""
        try:
            response = requests.get(f"{self.daemon_url}/metrics", timeout=self.timeout)
            return response.text
        except Exception as e:
            self.logger.debug(f"Prometheus metrics request failed: {e}")
            return ""

    def get_task(self, task_id: int) -> Optional[TaskInfo]:
        """Get task by ID with all metadata."""
        try:
            response = requests.get(
                f"{self.daemon_url}/api/tasks/{task_id}", timeout=self.timeout
            )
            if response.status_code == 200:
                raw_data = response.json()
                # Parse JSON strings in task_data and result fields
                if raw_data.get("task_data") and isinstance(raw_data["task_data"], str):
                    import json

                    raw_data["task_data"] = json.loads(raw_data["task_data"])
                if raw_data.get("result") and isinstance(raw_data["result"], str):
                    import json

                    raw_data["result"] = json.loads(raw_data["result"])
                return TaskInfo.model_validate(raw_data)
            return None
        except Exception as e:
            self.logger.debug(f"Get task request failed: {e}")
            return None

    def delete_task(self, task_id: int) -> bool:
        """Delete task from queue. Returns True if successful."""
        try:
            response = requests.delete(
                f"{self.daemon_url}/api/tasks/{task_id}", timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Delete task request failed: {e}")
            return False

    def redrive_task(self, task_id: int) -> bool:
        """Redrive a failed task. Returns True if successful."""
        try:
            response = requests.post(
                f"{self.daemon_url}/api/tasks/{task_id}/redrive", timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Redrive task request failed: {e}")
            return False

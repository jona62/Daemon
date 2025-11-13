"""Client for interacting with TaskDaemon."""

import requests
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel


class DaemonClient:
    """Client for interacting with TaskDaemon service."""

    def __init__(self, daemon_url: str = "http://localhost:8080", timeout: float = 0.1):
        self.daemon_url = daemon_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def queue_task(
        self, task_type: str, task_data: Optional[BaseModel] = None, critical: bool = True
    ) -> Optional[int]:
        """Queue a task for processing.

        Args:
            task_type: Type of task to process
            task_data: Task data (any format)
            critical: If True, raises exception on failure

        Returns:
            Task ID if successful, None if failed (unless critical=True)
        """
        try:
            # Auto-serialize Pydantic models
            data = task_data.model_dump() if isinstance(task_data, BaseModel) else task_data
            payload = {"type": task_type, "data": data}
            response = requests.post(
                f"{self.daemon_url}/queue", json=payload, timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json().get("task_id")
            else:
                self.logger.warning(f"Failed to queue task: {response.status_code}")
                if response.status_code == 422:
                    self.logger.warning(f"Validation error: {response.text}")

        except Exception as e:
            self.logger.warning(f"Failed to queue task: {e}")
            if critical:
                raise
        return None

    def health_check(self) -> Dict[str, Any]:
        """Check daemon health status."""
        try:
            response = requests.get(f"{self.daemon_url}/health", timeout=self.timeout)
            return response.json()
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Get daemon metrics."""
        try:
            response = requests.get(
                f"{self.daemon_url}/api/metrics", timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            self.logger.debug(f"Metrics request failed: {e}")
            return {}

    def get_tasks(self, limit: int = 20) -> list:
        """Get recent tasks."""
        try:
            response = requests.get(
                f"{self.daemon_url}/api/tasks",
                params={"limit": limit},
                timeout=self.timeout,
            )
            return response.json()
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

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID with all metadata."""
        try:
            response = requests.get(
                f"{self.daemon_url}/api/tasks/{task_id}", timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
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

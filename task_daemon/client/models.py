"""Client response models."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Health check response."""

    status: str
    queue_size: int
    timestamp: str
    workers: int


class TaskInfo(BaseModel):
    """Task information."""

    id: int
    task_type: str
    task_data: Optional[Dict[str, Any]]
    status: str
    created_at: str
    completed_at: Optional[str] = None
    attempts: int = 0
    last_error: Optional[str] = None
    result: Optional[Any] = None


class MetricsSummary(BaseModel):
    """Metrics summary."""

    tasks_received: int
    tasks_processed: int
    tasks_failed: int
    queue_size: int
    workers: int

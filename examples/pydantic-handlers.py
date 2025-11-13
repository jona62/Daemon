#!/usr/bin/env python3
"""Example showing Pydantic input/output models for task handlers."""

from task_daemon import TaskDaemon, DaemonConfig, task_handler
from pydantic import BaseModel, EmailStr
from typing import List
import time


class EmailInput(BaseModel):
    """Input model for email tasks."""

    recipient: EmailStr
    subject: str
    body: str


class EmailOutput(BaseModel):
    """Output model for email tasks."""

    status: str
    message_id: str
    timestamp: str
    recipient: str


class DataProcessingInput(BaseModel):
    """Input model for data processing tasks."""

    data: List[dict]
    operation: str


class DataProcessingOutput(BaseModel):
    """Output model for data processing tasks."""

    status: str
    items_processed: int
    operation: str
    summary: dict


@task_handler
def send_email(task_data: EmailInput) -> EmailOutput:
    """Handle email sending with Pydantic models."""
    print(f"Sending email to {task_data.recipient}")
    print(f"Subject: {task_data.subject}")
    time.sleep(1)  # Simulate work

    return EmailOutput(
        status="sent",
        message_id=f"msg-{int(time.time())}",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        recipient=str(task_data.recipient),
    )


@task_handler
def process_data(task_data: DataProcessingInput) -> DataProcessingOutput:
    """Handle data processing with Pydantic models."""
    print(
        f"Processing {len(task_data.data)} items with operation: {task_data.operation}"
    )
    time.sleep(1)  # Simulate work

    return DataProcessingOutput(
        status="completed",
        items_processed=len(task_data.data),
        operation=task_data.operation,
        summary={"total_items": len(task_data.data), "operation": task_data.operation},
    )


if __name__ == "__main__":
    """Run the daemon with Pydantic-enabled handlers."""
    config = DaemonConfig(
        worker_threads=2, port=8080, log_level="INFO", db_path="/tmp/pydantic_tasks.db"
    )

    daemon = TaskDaemon(config)
    print("Starting TaskDaemon with Pydantic handlers on port 8080...")
    print(
        "Handlers support typed input/output models for better validation and serialization"
    )
    daemon.run()

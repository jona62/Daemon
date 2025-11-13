#!/usr/bin/env python3
"""Basic usage example for TaskDaemon."""

from datetime import datetime
import time
from task_daemon import TaskDaemon, DaemonConfig, task_handler
from examples.inputs import LogAnalytics, SendEmailInput, SendEmailOutput


# Define task handlers using decorators
@task_handler
def send_email(task_data: SendEmailInput) -> SendEmailOutput:
    """Handle email sending tasks."""
    print(f"Sending email to {task_data.recipient}")
    time.sleep(1)  # Simulate work
    print("Email sent")
    return SendEmailOutput(sent_at=datetime.now())


@task_handler
def log_analytics(task_data: LogAnalytics):
    """Handle analytics logging tasks."""
    print(f"Logging analytics: {task_data.event}")
    time.sleep(1)  # Simulate work
    print("Logging Analytics done")


if __name__ == "__main__":
    """Run the daemon with custom configuration."""
    config = DaemonConfig(worker_threads=3, port=8080, log_level="INFO")

    daemon = TaskDaemon(config)
    print("Starting TaskDaemon on port 8080...")
    daemon.run()

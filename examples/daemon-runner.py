#!/usr/bin/env python3
"""Basic usage example for TaskDaemon."""

import time
from task_daemon import TaskDaemon, DaemonConfig, task_handler


# Define task handlers using decorators
@task_handler
def send_email(task_data):
    """Handle email sending tasks."""
    print(f"Sending email to {task_data.get('recipient', 'unknown')}")
    time.sleep(1)  # Simulate work


@task_handler
def log_analytics(task_data):
    """Handle analytics logging tasks."""
    print(f"Logging analytics: {task_data.get('event', 'unknown')}")
    time.sleep(1)  # Simulate work


if __name__ == "__main__":
    """Run the daemon with custom configuration."""
    config = DaemonConfig(worker_threads=3, port=8080, log_level="INFO")

    daemon = TaskDaemon(config)
    print("Starting TaskDaemon on port 8080...")
    daemon.run()

#!/usr/bin/env python3
"""Docker service example for TaskDaemon."""

import time
import os
from task_daemon import TaskDaemon, DaemonConfig, task_handler


@task_handler
def image_resize(task_data):
    """Handle image resizing tasks."""
    print(f"Resizing image: {task_data.get('image_url', 'unknown')}")
    size = task_data.get("size", "100x100")
    print(f"Target size: {size}")
    time.sleep(3)  # Simulate processing
    return {"status": "resized", "size": size}


@task_handler
def backup_data(task_data):
    """Handle data backup tasks."""
    source = task_data.get("source", "unknown")
    print(f"Backing up data from: {source}")
    time.sleep(2)  # Simulate backup
    return {"status": "backed_up", "source": source}


@task_handler
def send_notification(task_data):
    """Handle notification sending."""
    message = task_data.get("message", "No message")
    recipient = task_data.get("recipient", "unknown")
    print(f"Sending notification to {recipient}: {message}")
    time.sleep(1)  # Simulate sending
    return {"status": "sent", "recipient": recipient}


if __name__ == "__main__":
    """Run the daemon with Docker-optimized configuration."""
    config = DaemonConfig(
        worker_threads=int(os.getenv("DAEMON_WORKERS", 4)),
        port=int(os.getenv("DAEMON_PORT", 8080)),
        host=os.getenv("DAEMON_HOST", "0.0.0.0"),
        db_path=os.getenv("DAEMON_DB_PATH", "/data/queue.db"),
        log_level=os.getenv("DAEMON_LOG_LEVEL", "INFO"),
    )

    print(f"Starting Docker TaskDaemon on {config.host}:{config.port}")
    print(f"Workers: {config.worker_threads}, DB: {config.db_path}")

    daemon = TaskDaemon(config)
    daemon.run()

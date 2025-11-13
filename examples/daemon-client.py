#!/usr/bin/env python3
"""Basic example of DaemonClient.
Use this after running the daemon-runner.py
"""

import json
import time
import logging
from task_daemon import DaemonClient
from examples.inputs import LogAnalytics, SendEmailInput

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
client = DaemonClient(daemon_url="http://localhost:8080")

if __name__ == "__main__":
    # Queue a task
    task_id = client.queue_task(
        task_type="send_email", task_data=SendEmailInput(recipient="test@example.com")
    )
    logger.info(f"Queued task {task_id}")

    # Get task details
    task = client.get_task(task_id)
    if task:
        print(f"\nTask details:")
        print(task)

    # Wait and check again
    time.sleep(2)
    task = client.get_task(task_id)
    if task:
        print(f"\nUpdated task:")
        print(task)

    # Get recent tasks
    print(f"\nRecent tasks:")
    tasks = client.get_tasks()
    for task in tasks:
        print(task)

    # Example: redrive a failed task (if any exist)
    for task in tasks:
        if task.status == "failed":
            logger.info(f"Redriving failed task {task.id}")
            success = client.redrive_task(task.id)
            logger.info(f"Redrive successful: {success}")
            break

    print(f"Deleting task: {task_id}")
    tasks = client.get_tasks(limit=5)
    for task in tasks:
        client.delete_task(task.id)

    print(f"Recent tasks:")
    tasks = client.get_tasks()
    for task in tasks:
        print(task)

#!/usr/bin/env python3
"""Basic example of DaemonClient.
Use this after running the daemon-runner.py
"""

import json
import time
import logging
from task_daemon import DaemonClient

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
client = DaemonClient()

if __name__ == "__main__":
    # Queue a task
    task_id = client.queue_task(
        "send_email",
        {
            "recipient": "test@example.com",
        },
    )
    logger.info(f"Queued task {task_id}")

    # Get task details
    task = client.get_task(task_id)
    if task:
        print(f"\nTask details:")
        print(json.dumps(task, indent=2))

    # Wait and check again
    time.sleep(2)
    task = client.get_task(task_id)
    if task:
        print(f"\nUpdated task:")
        print(json.dumps(task, indent=2))

    # Get recent tasks
    tasks = client.get_tasks(limit=5)
    print(f"\nRecent tasks:")
    print(json.dumps(tasks, indent=2))

    # Example: redrive a failed task (if any exist)
    for task in tasks:
        if task.get("status") == "failed":
            logger.info(f"Redriving failed task {task['id']}")
            success = client.redrive_task(task["id"])
            logger.info(f"Redrive successful: {success}")
            break

    print(f"Deleting task: {task_id}")
    tasks = client.get_tasks(limit=5)
    for task in tasks:
        client.delete_task(task.get("id"))

    print(f"Recent tasks:")
    tasks = client.get_tasks(limit=5)
    print(json.dumps(tasks, indent=2))

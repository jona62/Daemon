#!/usr/bin/env python3
"""Example showing how to use different queue implementations."""

from task_daemon import TaskDaemon, DaemonConfig, task_handler, MemoryQueue


@task_handler
def process_data(task_data):
    """Handle data processing tasks."""
    print(f"Processing: {task_data.get('data', 'unknown')}")
    return {"status": "processed", "items": len(task_data.get("data", []))}


if __name__ == "__main__":
    # Use in-memory queue instead of persistent SQLite queue
    config = DaemonConfig(port=8080, log_level="INFO")
    memory_queue = MemoryQueue()

    daemon = TaskDaemon(config, queue=memory_queue)
    print("Starting TaskDaemon with in-memory queue on port 8080...")
    daemon.run()

#!/usr/bin/env python3
"""Daemon using direct registration."""

from task_daemon import TaskDaemon, DaemonConfig
from examples.tasks import get_all_handlers


if __name__ == "__main__":
    config = DaemonConfig(worker_threads=3, port=8080, log_level="INFO", max_retries=2)
    daemon = TaskDaemon(config)

    # Direct registration
    for handler in get_all_handlers():
        daemon.register_handler(handler)

    print("🚀 Starting TaskDaemon with direct registration...")
    print("🌐 API docs: http://localhost:8080/docs")
    daemon.run()

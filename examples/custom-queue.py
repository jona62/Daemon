#!/usr/bin/env python3
"""Daemon using MemoryQueue with direct registration."""

from task_daemon import TaskDaemon, DaemonConfig, MemoryQueue
from examples.tasks import get_all_handlers


if __name__ == "__main__":
    config = DaemonConfig(worker_threads=2, port=8081, log_level="INFO")
    daemon = TaskDaemon(config, queue=MemoryQueue())

    # Direct registration
    for handler in get_all_handlers():
        daemon.register_handler(handler)

    print("🚀 Starting TaskDaemon with MemoryQueue...")
    print("⚠️  Tasks will be lost on restart (in-memory only)")
    print("🌐 Running on: http://localhost:8081")
    daemon.run()

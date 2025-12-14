#!/usr/bin/env python3
"""Memory queue example (no persistence)."""

from task_daemon import TaskDaemon, DaemonConfig, MemoryQueue

def process_task(event):
    return {"status": "done"}

config = DaemonConfig(port=8082)
daemon = TaskDaemon(config, queue=MemoryQueue())
daemon.register_handler(process_task)
daemon.run()

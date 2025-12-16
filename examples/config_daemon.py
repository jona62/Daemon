#!/usr/bin/env python3
"""Configuration example."""

from task_daemon import TaskDaemon, DaemonConfig


def process_task(event):
    return {"status": "done"}


config = DaemonConfig(worker_threads=4, port=8080, max_retries=3, log_level="INFO")

daemon = TaskDaemon(config)
daemon.register_handler(process_task)
daemon.run()

#!/usr/bin/env python3
"""Docker service using builder pattern."""

import os
from task_daemon import DaemonBuilder
from examples.tasks import get_all_handlers


if __name__ == "__main__":
    # Builder pattern with environment configuration
    daemon = DaemonBuilder().with_config(
        worker_threads=int(os.getenv("DAEMON_WORKERS", 4)),
        port=int(os.getenv("DAEMON_PORT", 8080)),
        host=os.getenv("DAEMON_HOST", "0.0.0.0"),
        db_path=os.getenv("DAEMON_DB_PATH", "/data/queue.db"),
        log_level=os.getenv("DAEMON_LOG_LEVEL", "INFO"),
    )

    # Add all handlers
    for handler in get_all_handlers():
        daemon.add_handler(handler)

    daemon = daemon.build()

    print("🐳 Starting Docker TaskDaemon with builder pattern...")
    daemon.run()

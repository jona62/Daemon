#!/usr/bin/env python3
"""CLI entry point for TaskDaemon."""

import argparse
import sys
from .daemon import TaskDaemon
from .config import DaemonConfig


def main():
    parser = argparse.ArgumentParser(
        description="TaskDaemon - Configurable task processing system"
    )
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument(
        "--workers", type=int, default=None, help="Number of worker threads"
    )
    parser.add_argument("--db-path", default=None, help="Database path")
    parser.add_argument("--log-level", default=None, help="Log level")
    parser.add_argument(
        "--config-from-env", action="store_true", help="Load config from environment"
    )

    args = parser.parse_args()

    # Create config
    if args.config_from_env:
        config = DaemonConfig.from_env()
    else:
        config = DaemonConfig()

    # Override with CLI args
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.workers:
        config.worker_threads = args.workers
    if args.db_path:
        config.db_path = args.db_path
    if args.log_level:
        config.log_level = args.log_level

    # Start daemon
    daemon = TaskDaemon(config)
    try:
        daemon.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        daemon.stop_workers()
        sys.exit(0)


if __name__ == "__main__":
    main()

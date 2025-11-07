"""Configuration management for Task Daemon."""

import os
from dataclasses import dataclass


@dataclass
class DaemonConfig:
    """Configuration for TaskDaemon with sensible defaults."""

    # Database
    db_path: str = "/tmp/task_queue.db"

    # Worker settings
    worker_threads: int = 2
    max_retries: int = 3
    worker_sleep: float = 0.1

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080

    # Timeouts
    task_timeout: float = 30.0
    client_timeout: float = 0.1

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "DaemonConfig":
        """Create config from environment variables."""
        return cls(
            db_path=os.getenv("DAEMON_DB_PATH", cls.db_path),
            worker_threads=int(os.getenv("DAEMON_WORKERS", cls.worker_threads)),
            max_retries=int(os.getenv("DAEMON_MAX_RETRIES", cls.max_retries)),
            worker_sleep=float(os.getenv("DAEMON_WORKER_SLEEP", cls.worker_sleep)),
            host=os.getenv("DAEMON_HOST", cls.host),
            port=int(os.getenv("DAEMON_PORT", cls.port)),
            task_timeout=float(os.getenv("DAEMON_TASK_TIMEOUT", cls.task_timeout)),
            client_timeout=float(
                os.getenv("DAEMON_CLIENT_TIMEOUT", cls.client_timeout)
            ),
            log_level=os.getenv("DAEMON_LOG_LEVEL", cls.log_level),
        )

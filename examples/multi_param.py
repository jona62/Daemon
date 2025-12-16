#!/usr/bin/env python3
"""Example with multiple parameter handlers."""

from task_daemon import TaskDaemon


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone with optional greeting."""
    return f"{greeting}, {name}!"


if __name__ == "__main__":
    daemon = TaskDaemon()
    daemon.register_handler(add)
    daemon.register_handler(greet)
    daemon.run()

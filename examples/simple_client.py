#!/usr/bin/env python3
"""Simple client usage example."""

from examples.pydantic_daemon import EmailInput
from task_daemon import DaemonClient
import time

client = DaemonClient("http://localhost:8080", timeout=5.0)

# Queue tasks
func_input = EmailInput(
    recipient="user@example.com", subject="Hello", body="Test message"
)
task_id = client.queue_task("send_email", func_input)
print(f"Queued task: {task_id}")

# Wait and check status
time.sleep(2)
task = client.get_task(task_id)
print(f"Status: {task.status}")
print(f"Result: {task.result}")

task_id = client.queue_task("simple_calculator", 1, 2)
print(f"Queued task: {task_id}")

# Wait and check status
time.sleep(2)
task = client.get_task(task_id)
print(f"Status: {task.status}")
print(f"Result: {task.result}")
# Check health
health = client.health_check()
print(f"Daemon: {health.status}, Queue: {health.queue_size}")

#!/usr/bin/env python3
"""Pydantic validation example."""

from task_daemon import TaskDaemon
from pydantic import BaseModel

class EmailInput(BaseModel):
    recipient: str
    subject: str
    body: str

class EmailOutput(BaseModel):
    status: str
    message_id: str

def send_email(task_data: EmailInput) -> EmailOutput:
    print(f"Sending: {task_data.subject} to {task_data.recipient}")
    return EmailOutput(status="sent", message_id="msg-123")

if __name__ == "__main__":
    daemon = TaskDaemon()
    daemon.register_handler(send_email)
    daemon.run()

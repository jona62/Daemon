"""Centralized task handlers for all daemon examples."""

from datetime import datetime
import time
from pydantic import BaseModel


# Pydantic Models
class EmailInput(BaseModel):
    recipient: str
    subject: str = "Test Email"
    body: str = "Hello World"


class EmailOutput(BaseModel):
    status: str
    sent_at: str
    message_id: str


class DataInput(BaseModel):
    operation: str
    data: dict


class DataOutput(BaseModel):
    status: str
    items_processed: int
    operation: str


class NotificationInput(BaseModel):
    user_id: str
    message: str
    channel: str = "email"


# Task Handlers (no decorators)
def send_email(task_data: EmailInput) -> EmailOutput:
    """Send email with Pydantic validation."""
    print(f"📧 Sending email to {task_data.recipient}")
    print(f"   Subject: {task_data.subject}")
    time.sleep(1)
    return EmailOutput(
        status="sent",
        sent_at=datetime.now().isoformat(),
        message_id=f"msg-{int(time.time())}",
    )


def process_data(task_data: DataInput) -> DataOutput:
    """Process data with structured input/output."""
    print(f"🔄 Processing data: {task_data.operation}")
    print(f"   Data keys: {list(task_data.data.keys())}")
    time.sleep(2)
    return DataOutput(
        status="processed",
        items_processed=len(task_data.data),
        operation=task_data.operation,
    )


def send_notification(task_data: NotificationInput):
    """Send notification (simple return)."""
    print(f"🔔 Notification to {task_data.user_id} via {task_data.channel}")
    print(f"   Message: {task_data.message}")
    time.sleep(0.5)
    return {"delivered": True, "channel": task_data.channel}


def backup_data(event):
    """Legacy handler (dict input/output)."""
    print(f"💾 Backing up: {event.get('source', 'unknown')}")
    time.sleep(3)
    return {"status": "backup_complete", "files": event.get("file_count", 0)}


def image_resize(event):
    """Image processing handler."""
    print(f"🖼️  Resizing image: {event.get('filename', 'unknown')}")
    size = event.get("size", "100x100")
    time.sleep(1.5)
    return {"status": "resized", "new_size": size, "format": "jpg"}


def failing_task(event):
    """Handler that demonstrates failure."""
    print("💥 This task will fail...")
    raise Exception("Simulated task failure")


def user_signup(event):
    """User signup handler."""
    print(f"👤 Processing signup for {event.get('email', 'unknown')}")
    time.sleep(1)
    return {"status": "signup_processed", "user_id": event.get("user_id")}


def log_analytics(event):
    """Analytics logging handler."""
    print(f"📊 Logging analytics: {event.get('event', 'unknown')}")
    time.sleep(0.5)
    return {"logged": True, "event": event.get("event")}


def get_all_handlers():
    """Return all task handlers for registration."""
    return [
        send_email,
        process_data,
        send_notification,
        backup_data,
        image_resize,
        failing_task,
        user_signup,
        log_analytics,
    ]

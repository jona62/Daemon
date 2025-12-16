#!/usr/bin/env python3
"""Basic daemon example with task handlers."""

from task_daemon import TaskDaemon


# Define handlers - function name becomes task type
def send_email(event):
    recipient = event.get("recipient")
    print(f"Sending email to {recipient}")
    return {"status": "sent", "recipient": recipient}


def process_data(event):
    data = event.get("data", {})
    print(f"Processing {len(data)} items")
    return {"status": "processed", "items": len(data)}


if __name__ == "__main__":
    daemon = TaskDaemon()
    daemon.register_handler(send_email)
    daemon.register_handler(process_data)
    daemon.run()

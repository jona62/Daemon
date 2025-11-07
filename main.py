import time
from task_daemon import TaskDaemon, DaemonConfig, task_handler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define task handlers using decorators
@task_handler
def send_email(event):
    """Send email handler - function name becomes task type."""
    logger.info(f"Sending email to {event.get('recipient', 'unknown')}")
    logger.info(f"Subject: {event.get('subject', 'No subject')}")
    time.sleep(5)  # Simulate work
    return {"status": "email_sent", "recipient": event.get("recipient")}


@task_handler
def process_data(event):
    """Process data handler."""
    logger.info(f"Processing data with operation: {event.get('operation', 'default')}")
    data = event.get("data", {})
    time.sleep(5)  # Simulate work
    return {"status": "data_processed", "items": len(data)}


@task_handler
def user_signup(event):
    """User signup handler."""
    logger.info(f"Processing user signup for {event.get('email', 'unknown')}")
    time.sleep(5)  # Simulate work
    return {"status": "signup_processed", "user_id": event.get("user_id")}


if __name__ == "__main__":
    config = DaemonConfig(worker_threads=3, port=8080, log_level="INFO")
    daemon = TaskDaemon(config)
    daemon.run()

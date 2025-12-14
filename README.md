# TaskDaemon

A configurable task processing system with monitoring, built with FastAPI.

## Features

- 🔧 **Configurable**: Environment variables, CLI args, or programmatic config
- 📊 **Monitoring**: Prometheus metrics and health checks
- 🎯 **Type-Safe**: Pydantic validation for inputs and outputs
- 🔄 **Persistent**: SQLite queue with retry logic
- 🧵 **Multi-threaded**: Configurable worker threads
- ⚡ **FastAPI**: High-performance async API with OpenAPI docs
- 🐳 **Docker Ready**: Complete Docker and Docker Compose support

## Quick Start

### Installation

```bash
pip install task-daemon
```

### Basic Usage

```python
from task_daemon import TaskDaemon

# Define handlers - function name becomes task type
def send_email(event):
    print(f"Sending email to {event.get('recipient')}")
    return {"status": "sent"}

def process_data(event):
    print(f"Processing {len(event.get('data', {}))} items")
    return {"status": "processed"}

# Register and run
daemon = TaskDaemon()
daemon.register_handler(send_email)
daemon.register_handler(process_data)
daemon.run()  # Starts on localhost:8080
```

### Pydantic Validation

```python
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
    """Type-safe handler with automatic validation."""
    print(f"Sending: {task_data.subject} to {task_data.recipient}")
    return EmailOutput(status="sent", message_id="msg-123")

daemon = TaskDaemon()
daemon.register_handler(send_email)
daemon.run()
```

**Benefits:**
- ✅ Automatic input validation
- ✅ Type safety with IDE support
- ✅ Structured output serialization
- ✅ Clear validation errors

### Client Usage

```python
from task_daemon import DaemonClient

client = DaemonClient("http://localhost:8080")

# Queue task
task_id = client.queue_task("send_email", {
    "recipient": "user@example.com",
    "subject": "Hello",
    "body": "Test message"
})

# Check status
task = client.get_task(task_id)
print(f"Status: {task.status}")
print(f"Result: {task.result}")

# Health check
health = client.health_check()
print(f"Queue size: {health.queue_size}")
```

## Configuration

### Environment Variables

```bash
export DAEMON_WORKERS=4
export DAEMON_PORT=8080
export DAEMON_DB_PATH=/tmp/tasks.db
export DAEMON_LOG_LEVEL=INFO
```

### Programmatic

```python
from task_daemon import TaskDaemon, DaemonConfig

config = DaemonConfig(
    worker_threads=4,
    port=8080,
    max_retries=3,
    log_level="INFO"
)

daemon = TaskDaemon(config)
daemon.register_handler(my_handler)
daemon.run()
```

### CLI

```bash
task-daemon --workers 4 --port 8080 --log-level INFO
```

## Queue Types

### PersistentQueue (Default)

SQLite-based, survives restarts, supports multiple instances.

```python
daemon = TaskDaemon()  # Uses PersistentQueue by default
```

### MemoryQueue

In-memory, faster, no persistence.

```python
from task_daemon import MemoryQueue

daemon = TaskDaemon(queue=MemoryQueue())
```

## API Endpoints

- `POST /queue` - Queue new task
- `GET /health` - Health check
- `GET /api/tasks` - List recent tasks
- `GET /api/tasks/{id}` - Get task details
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/redrive` - Retry failed task
- `GET /metrics` - Prometheus metrics
- `GET /api/metrics` - JSON metrics
- `GET /docs` - Interactive API docs (Swagger UI)
- `GET /redoc` - Alternative API docs

## Docker

### Simple Run

```bash
docker build -t task-daemon .
docker run -p 8080:8080 task-daemon
```

### With Prometheus

```bash
docker-compose up
```

Access:
- TaskDaemon: http://localhost:8080
- Prometheus: http://localhost:9090

## Examples

```bash
# Basic daemon
python examples/basic_daemon.py

# Pydantic validation
python examples/pydantic_daemon.py

# Custom configuration
python examples/config_daemon.py

# Memory queue
python examples/memory_queue.py

# Client usage
python examples/simple_client.py
```

See [examples/README.md](examples/README.md) for details.

## Development

```bash
# Install
pip install -e ".[dev]"

# Test
pytest

# Format
black task_daemon/
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│         FastAPI Server          │
│  ┌──────────────────────────┐   │
│  │   POST /queue            │   │
│  │   GET /api/tasks         │   │
│  │   GET /health            │   │
│  └──────────────────────────┘   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Queue (SQLite/Memory)      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Worker Threads (N)         │
│  ┌────────────────────────┐     │
│  │  Task Handler Registry │     │
│  │  - send_email()        │     │
│  │  - process_data()      │     │
│  │  - custom_handler()    │     │
│  └────────────────────────┘     │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│    Metrics (Prometheus)         │
└─────────────────────────────────┘
```

## License

MIT

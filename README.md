# TaskDaemon

A configurable task processing system with monitoring, built with FastAPI and designed for easy integration and deployment.

## Features

- 🔧 **Configurable**: Sensible defaults with environment variable overrides
- 📊 **Monitoring**: Built-in Prometheus metrics and health checks
- 🎯 **Easy Integration**: Multiple registration patterns (decorators, direct, builder)
- 🐳 **Docker Ready**: Complete Docker and Docker Compose support
- 🔄 **Persistent Queue**: SQLite-based task queue with retry logic
- 🧵 **Multi-threaded**: Configurable worker threads
- ⚡ **FastAPI**: High-performance async API with automatic OpenAPI docs
- 🔍 **Pydantic**: Type-safe request/response models

## Quick Start

### Installation

```bash
pip install task-daemon
```

### Basic Usage

```python
from task_daemon import TaskDaemon, DaemonBuilder, DaemonConfig

# Define task handlers - function name becomes task type
def send_email(event):
    print(f"Sending email to {event.get('recipient')}")
    return {"status": "sent", "recipient": event.get('recipient')}

def process_data(event):
    print(f"Processing: {event.get('data')}")
    return {"status": "processed", "items": len(event.get('data', {}))}

# Option 1: Direct Registration
daemon = TaskDaemon(DaemonConfig())
daemon.register_handler(send_email)
daemon.register_handler(process_data)
daemon.run()  # Starts on localhost:8080

# Option 2: Builder Pattern
daemon = (DaemonBuilder()
          .with_config(worker_threads=4, port=8080)
          .add_handler(send_email)
          .add_handler(process_data)
          .build())
daemon.run()

# Option 3: Decorator Pattern
from task_daemon import task_handler

@task_handler
def decorator_handler(event):
    return {"status": "processed"}

daemon = TaskDaemon()
daemon.run()
```

### Pydantic Integration

TaskDaemon provides full Pydantic support for type-safe task handlers with automatic validation and serialization:

```python
from task_daemon import TaskDaemon, task_handler
from pydantic import BaseModel, EmailStr
from typing import List

class EmailInput(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

class EmailOutput(BaseModel):
    status: str
    message_id: str
    timestamp: str

@task_handler
def send_email(task_data: EmailInput) -> EmailOutput:
    """Type-safe email handler with automatic validation."""
    print(f"Sending email to {task_data.recipient}")
    # task_data is automatically validated against EmailInput model
  
    return EmailOutput(
        status="sent",
        message_id="msg-12345",
        timestamp="2023-01-01T12:00:00Z"
    )
    # Output automatically serialized and stored

# Run daemon
daemon = TaskDaemon()
daemon.run()
```

**Benefits:**

- ✅ **Automatic Validation**: Input data validated against Pydantic models
- ✅ **Type Safety**: Full IDE support with autocomplete and error detection
- ✅ **Structured Outputs**: Complex results properly serialized/deserialized
- ✅ **Error Handling**: Clear validation errors for malformed data
- ✅ **Backward Compatible**: Works alongside non-Pydantic handlers

**⚠️ Important**: Register task handlers using direct registration (`daemon.register_handler(func)`), builder pattern (`.add_handler(func)`), or `@task_handler` decorators before starting the daemon. Running without handlers will start the service but tasks will remain unprocessed in the queue.

### Examples

Run the consolidated examples:

```bash
# Start daemon with all example handlers
python examples/daemon.py

# In another terminal, test all scenarios
python examples/client.py
```

**Available daemon variants:**

- `daemon.py` - Direct registration (port 8080)
- `daemon_builder.py` - Builder pattern (port 8081)
- `custom-queue.py` - MemoryQueue (port 8082)

See [examples/README.md](examples/README.md) for detailed feature testing guide.

### Client Usage

```python
from task_daemon import DaemonClient

client = DaemonClient("http://localhost:8080")

# Queue tasks with any data format
task_id = client.queue_task("send_email", {
    "recipient": "user@example.com",
    "subject": "Hello",
    "body": "Welcome!"
})

# Get task details with metadata
task = client.get_task(task_id)
print(task)  # Shows status, attempts, errors, result, timestamps

# Redrive failed tasks
client.redrive_task(task_id)

# Delete tasks from queue
client.delete_task(task_id)

# Check status
health = client.health_check()
metrics = client.get_metrics()
```

## Configuration

### Environment Variables

```bash
export DAEMON_WORKERS=4
export DAEMON_PORT=8080
export DAEMON_DB_PATH=/tmp/tasks.db
export DAEMON_LOG_LEVEL=INFO
```

### Programmatic Configuration

```python
from task_daemon import TaskDaemon, DaemonConfig

config = DaemonConfig(
    worker_threads=4,
    port=8080,
    db_path="/tmp/tasks.db",
    max_retries=3
)

daemon = TaskDaemon(config)
daemon.run()
```

## Queue Types

TaskDaemon supports multiple queue implementations through a pluggable interface:

### PersistentQueue (Default)

**SQLite-based persistent storage**

```python
from task_daemon import TaskDaemon, DaemonConfig

# Default - uses PersistentQueue automatically
daemon = TaskDaemon(config)
```

**When to use:**

- ✅ Production deployments
- ✅ Task durability required (survives restarts)
- ✅ Task history and auditing needed
- ✅ Multiple daemon instances (shared database)

### MemoryQueue

**In-memory storage for speed**

```python
from task_daemon import TaskDaemon, DaemonConfig, MemoryQueue

daemon = TaskDaemon(config, queue=MemoryQueue())
```

**When to use:**

- ✅ Development and testing
- ✅ High-performance scenarios (no disk I/O)
- ✅ Temporary/ephemeral workloads
- ❌ Tasks lost on restart
- ❌ Single daemon instance only

### Custom Queue Implementation

```python
from task_daemon import QueueInterface

class MyCustomQueue(QueueInterface):
    def enqueue(self, task_type: str, task_data: Any) -> int:
        # Your implementation
        pass
    # ... implement all abstract methods

daemon = TaskDaemon(config, queue=MyCustomQueue())
```

**Examples:** Redis, RabbitMQ, AWS SQS, or database-specific implementations.

## Docker Deployment

### Simple Docker Run

```bash
docker build -t task-daemon .
docker run -p 8080:8080 -v $(pwd)/data:/data task-daemon
```

The Docker image runs `examples/docker-service.py` which includes handlers for:

- `image_resize` - Image processing tasks
- `backup_data` - Data backup operations
- `send_notification` - Notification delivery

**Metrics**: Manual access only via `/metrics` and `/api/metrics` endpoints. No persistence or historical data.

### Docker Compose (with Prometheus)

```bash
docker-compose up -d
```

**Metrics**: Full monitoring stack with automatic collection, persistence, and historical data.

Access:

- TaskDaemon: http://localhost:8080
- Prometheus: http://localhost:9090

## Metrics Comparison

| Method                   | Metrics Access         | Persistence | Historical Data | Auto Collection  |
| ------------------------ | ---------------------- | ----------- | --------------- | ---------------- |
| **Python Direct**  | Manual endpoints       | ❌          | ❌              | ❌               |
| **Docker Run**     | Manual endpoints       | ❌          | ❌              | ❌               |
| **Docker Compose** | Prometheus + endpoints | ✅          | ✅              | ✅ (5s interval) |

### Metrics Endpoints (All Methods)

- `GET /metrics` - Prometheus format
- `GET /api/metrics` - JSON format

## API Endpoints

- `POST /queue` - Queue new task
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /api/metrics` - JSON metrics
- `GET /api/tasks` - Recent tasks
- `GET /api/tasks/{id}` - Get specific task with metadata
- `DELETE /api/tasks/{id}` - Delete task from queue
- `POST /api/tasks/{id}/redrive` - Redrive failed task
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## CLI Usage

```bash
# Start with defaults
task-daemon

# Custom configuration
task-daemon --workers 4 --port 8080 --log-level DEBUG

# From environment
task-daemon --config-from-env
```

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black task_daemon/

# Run example
python main.py
```

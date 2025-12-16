# TaskDaemon

A configurable task processing system with monitoring, built with FastAPI.

## Features

- 🔧 **Configurable**: Environment variables, CLI args, or programmatic config
- 📊 **Monitoring**: Prometheus metrics and health checks
- 🎯 **Type-Safe**: Pydantic validation for inputs and outputs
- 🔄 **Persistent**: SQLite queue with retry logic
- 🧵 **Multi-threaded**: Configurable worker threads
- ⚡ **FastAPI**: High-performance async API with OpenAPI docs
- 🚀 **gRPC Support**: Multi-language clients via Protocol Buffers
- 📦 **Protocol Options**: JSON or MessagePack serialization
- 🌍 **Multi-Language**: Use from Python, Kotlin, Go, Java, C++, and more
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

### Multiple Parameters

```python
from task_daemon import TaskDaemon

def add(a: int, b: int) -> int:
    """Handler with multiple parameters."""
    return a + b

def greet(name: str, greeting: str = "Hello") -> str:
    """Handler with default parameter."""
    return f"{greeting}, {name}!"

daemon = TaskDaemon()
daemon.register_handler(add)
daemon.register_handler(greet)
daemon.run()
```

Queue tasks with parameter dict:
```python
# Dict format
client.queue_task("add", {"a": 5, "b": 3})  # Returns 8

# Kwargs format
client.queue_task("add", a=5, b=3)  # Returns 8

# Positional args
client.queue_task("add", 5, 3)  # Returns 8

client.queue_task("greet", {"name": "World"})  # Returns "Hello, World!"
client.queue_task("greet", name="World")  # Returns "Hello, World!"
```


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

### gRPC Client (Multi-Language)

**Python:**
```python
from task_daemon.client.grpc_client import GRPCDaemonClient

with GRPCDaemonClient("localhost:50051") as client:
    task_id = client.queue_task("send_email", {
        "recipient": "user@example.com"
    })
    task = client.get_task(task_id)
```

**Kotlin:**
```kotlin
val client = TaskDaemonGrpcKt.TaskDaemonCoroutineStub(channel)
val request = taskRequest {
    taskType = "send_email"
    taskDataJson = """{"recipient": "user@example.com"}"""
}
val response = client.queueTask(request)
```

See [clients/](clients/) for complete examples in multiple languages.

### Protocol Options

**HTTP with JSON (default):**
```python
client = DaemonClient("http://localhost:8080", protocol="json")
```

**HTTP with MessagePack (3-5x faster):**
```python
client = DaemonClient("http://localhost:8080", protocol="msgpack")
```

**gRPC with JSON:**
```python
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="json")
```

**gRPC with MessagePack:**
```python
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="msgpack")
```

See [docs/PROTOCOLS.md](docs/PROTOCOLS.md) for performance benchmarks.

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

## Server Modes

### HTTP Server (Default)

```python
daemon = TaskDaemon()
daemon.register_handler(my_handler)
daemon.run()  # HTTP on port 8080
```

### gRPC Server

```python
daemon = TaskDaemon()
daemon.register_handler(my_handler)
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="json")  # gRPC only
```

### Both HTTP and gRPC

```python
import threading
from task_daemon.grpc_service import serve_grpc

daemon = TaskDaemon()
daemon.register_handler(my_handler)

# Start gRPC in background
grpc_server = serve_grpc(daemon, port=50051, protocol="json")
daemon.start_workers()

# Start HTTP in foreground
daemon.run()
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

**Custom Port:**

```bash
# export variables
export DAEMON_PORT=8081
export DAEMON_WORKERS=8
docker-compose up
```

Or create a `.env` file:

```
DAEMON_PORT=8081
DAEMON_WORKERS=8
DAEMON_LOG_LEVEL=DEBUG
```

## Multi-Language Clients

TaskDaemon supports clients in any language via gRPC:

### Kotlin Client

```bash
cd clients/kotlin
./gradlew run
```

Full example with:
- Type-safe data classes
- Jackson JSON serialization
- Coroutine-based async operations

See [clients/kotlin/README.md](clients/kotlin/README.md)

### Other Languages

The same `.proto` file enables clients in:
- **Go** - High-performance microservices
- **Java** - Enterprise applications
- **C++** - Low-level systems
- **C#** - .NET applications
- **Node.js** - JavaScript/TypeScript
- **Ruby** - Rails applications
- **PHP** - Web applications
- **Dart** - Flutter mobile apps

See [clients/README.md](clients/README.md) for details.

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

# Regenerate protobuf files (after modifying .proto)
python generate_proto.py
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

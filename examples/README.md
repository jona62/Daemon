# TaskDaemon Examples

Simple examples demonstrating TaskDaemon features.

## Quick Start

### 1. Basic Daemon

```bash
python examples/basic_daemon.py
```

Simple task handlers with dict input/output.

### 2. Pydantic Validation

```bash
python examples/pydantic_daemon.py
```

Type-safe handlers with automatic validation.

### 3. Custom Configuration

```bash
python examples/config_daemon.py
```

Configure workers, port, retries, and logging.

### 4. Memory Queue

```bash
python examples/memory_queue.py
```

In-memory queue (no persistence, faster).

## Client Usage

Start any daemon, then:

```bash
python examples/simple_client.py
```

## Testing All Features

```bash
# Start daemon with example handlers
python examples/daemon.py

# In another terminal, run comprehensive tests
python examples/client.py
```

## API Endpoints

- `POST /queue` - Queue task
- `GET /health` - Health check
- `GET /api/tasks` - List tasks
- `GET /api/tasks/{id}` - Get task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/redrive` - Retry failed task
- `GET /metrics` - Prometheus metrics
- `GET /docs` - API documentation

## Docker

```bash
docker-compose up
```

Access:
- Daemon: http://localhost:8080
- Prometheus: http://localhost:9090

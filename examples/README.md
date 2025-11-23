# TaskDaemon Examples

This directory demonstrates different TaskDaemon features and registration patterns.

## Quick Start

1. **Start a daemon** (choose one):

   ```bash
   python daemon.py          # Direct registration (port 8080)
   python custom-queue.py    # MemoryQueue (port 8081)
   ```
2. **Run client tests**:

   ```bash
   python client.py
   ```

## Registration Patterns

### 🔧 Direct Registration

```python
daemon = TaskDaemon(config)
for handler in get_all_handlers():
    daemon.register_handler(handler)  # Uses function name as task type
```

### 🏗️ Builder Pattern

```python
daemon = (DaemonBuilder()
          .with_config(worker_threads=3, port=8081)
          .add_handler(send_email)
          .add_handler(process_data)
          .build())
```

### 🎯 Decorator Pattern

```python
@task_handler
def send_email(event):
    return {"status": "sent"}
```

**All patterns:**

- ✅ Use function name as task type automatically
- ✅ Support Pydantic validation
- ✅ Provide clear registration visibility
- ✅ Work with mixed handler types

---

## Examples Overview

### 📁 `tasks.py` - Centralized Task Handlers

**All task handlers in one file (no decorators)**

**Handlers included:**

- `send_email` - Pydantic email handler with validation
- `process_data` - Pydantic data processing with structured I/O
- `send_notification` - Pydantic notification handler
- `backup_data` - Legacy dict-based handler
- `image_resize` - Image processing simulation
- `failing_task` - Demonstrates error handling
- `user_signup` - User registration handler
- `log_analytics` - Analytics logging handler

**Features:**

- ✅ Mixed handler types (Pydantic + legacy)
- ✅ No decorator dependencies
- ✅ Functional registration via `get_all_handlers()`

---

### 🧪 `client.py` - Consolidated Test Suite

**All client scenarios in one file**

```bash
python client.py
```

**Test scenarios:**

1. **Basic Operations** - Queue tasks, check status, get results
2. **Pydantic Validation** - Test type safety and validation errors
3. **Failure Handling** - Test retries, redrive, and error recovery
4. **Monitoring** - Test metrics, health checks, and task history

**Expected output:**

```
🧪 TaskDaemon Client Test Suite
🔍 SCENARIO: Basic Operations
Status: healthy
✅ Queued 3 tasks
📋 Results:
Email           | Status: completed  | Result: {'status': 'sent', ...}

🔬 SCENARIO: Pydantic Validation
Validation error (expected): 422 Client Error...

💥 SCENARIO: Failure Handling  
Status: failed
Attempts: 3
🔄 Testing redrive...

📊 SCENARIO: Monitoring
Tasks Received: 15
Queue: 2 | Processed: 13
```

---

## Daemon Variants

### 🚀 `daemon.py` - Standard Daemon

- **Port**: 8080
- **Registration**: Direct registration
- **Queue**: PersistentQueue (SQLite)

### 💾 `custom-queue.py` - Memory Queue

- **Port**: 8082
- **Registration**: Direct registration
- **Queue**: MemoryQueue (in-memory, faster but not persistent)

### 🐳 `docker-service.py` - Docker Service

- **Port**: Configurable via environment
- **Registration**: Builder pattern
- **Queue**: PersistentQueue (SQLite)
- **Environment**: Docker-optimized with env var configuration

---

## Testing Different Features

### 🎯 Core Functionality

```bash
# Start daemon
python daemon.py

# Test all scenarios
python client.py

# API documentation
open http://localhost:8080/docs
```

### 🔒 Registration Patterns

```bash
# Test different registration methods
python daemon.py          # Direct registration
python custom-queue.py    # MemoryQueue + direct registration
```

### 🛠️ Error Handling & Validation

```bash
# Run client tests (includes validation & failure scenarios)
python client.py

# Check specific scenarios in the output
```

### 📈 Monitoring & Metrics

```bash
# Prometheus metrics
curl http://localhost:8080/metrics

# JSON metrics  
curl http://localhost:8080/api/metrics

# Health check
curl http://localhost:8080/health
```

### 🔧 Advanced Configuration

```bash
# Custom configuration
DAEMON_WORKERS=5 DAEMON_LOG_LEVEL=DEBUG python daemon.py

# Different ports for multiple instances
python daemon.py &          # Port 8080
python custom-queue.py &    # Port 8081
```

## API Endpoints

With any daemon running, explore the interactive API:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **Health**: http://localhost:8080/health
- **Metrics**: http://localhost:8080/metrics

## Troubleshooting

**Port already in use:**

```bash
lsof -ti :8080 | xargs kill
```

**No handlers registered:**

- Ensure daemon calls `daemon.register_handler()` or uses builder pattern
- Check that `get_all_handlers()` returns functions

**Import errors:**

- Run from examples directory: `cd examples && python daemon.py`
- Ensure TaskDaemon is installed: `pip install -e .`

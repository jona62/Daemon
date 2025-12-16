# TaskDaemon Clients

Multi-language client examples demonstrating TaskDaemon's gRPC support.

## Available Clients

### Kotlin

Location: `clients/kotlin/`

Type-safe Kotlin client using:

- gRPC Kotlin coroutines
- Jackson for JSON serialization
- Gradle build with protobuf plugin

See [kotlin/README.md](kotlin/README.md) for details.

## Adding New Clients

TaskDaemon's gRPC interface can be used from any language that supports Protocol Buffers:

### Supported Languages

- ✅ **Kotlin** (implemented)
- 🔲 **Go** - High-performance, great for microservices
- 🔲 **Java** - Enterprise applications
- 🔲 **C++** - Low-level, high-performance systems
- 🔲 **C#** - .NET applications
- 🔲 **Node.js** - JavaScript/TypeScript applications
- 🔲 **Ruby** - Rails applications
- 🔲 **PHP** - Web applications
- 🔲 **Dart** - Flutter mobile apps

### Steps to Create a Client

1. **Copy the proto file:**

   ```bash
   cp ../task_daemon/proto/task_daemon.proto your-client/proto/
   ```
2. **Generate code for your language:**

   - Use the appropriate protoc plugin for your language
   - See: https://grpc.io/docs/languages/
3. **Connect to the daemon:**

   ```
   localhost:50051  # Default gRPC port
   ```
4. **Call the RPC methods:**

   - `QueueTask` - Submit tasks
   - `GetTask` - Check task status
   - `GetHealth` - Health check
   - `GetMetrics` - Get metrics
   - `ListTasks` - List recent tasks
   - `DeleteTask` - Delete a task
   - `RedriveTask` - Retry failed task

## Protocol

All clients use the same Protocol Buffer definition (`task_daemon.proto`), ensuring:

- Type safety across languages
- Consistent API
- Efficient binary serialization
- Backward compatibility

## Running the Server

Start TaskDaemon with gRPC:

```python
from task_daemon import TaskDaemon

def my_handler(data):
    return {"result": "processed"}

daemon = TaskDaemon()
daemon.register_handler(my_handler)
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="json")
```

Then run any client to interact with it!

# Protocol Support

TaskDaemon supports multiple serialization protocols for both HTTP and gRPC interfaces, allowing you to choose the best option for your use case.

## Available Protocols

### JSON (Default)
- **Format**: Text-based, human-readable
- **Use case**: Universal compatibility, debugging, cross-language support
- **Performance**: Baseline

### MessagePack
- **Format**: Binary, compact
- **Use case**: High-performance applications, large payloads
- **Performance**: 3-5x faster, 40-67% smaller payloads

## HTTP API

### JSON Protocol (Default)

```python
from task_daemon import DaemonClient

client = DaemonClient("http://localhost:8080", protocol="json")
task_id = client.queue_task("process_data", {"items": [1, 2, 3]})
```

### MessagePack Protocol

```python
from task_daemon import DaemonClient

client = DaemonClient("http://localhost:8080", protocol="msgpack")
task_id = client.queue_task("process_data", {"items": [1, 2, 3]})
```

The protocol is automatically negotiated via the `Content-Type` header:
- JSON: `application/json`
- MessagePack: `application/msgpack`

## gRPC API

### JSON Protocol (Default)

```python
from task_daemon.client.grpc_client import GRPCDaemonClient

with GRPCDaemonClient("localhost:50051", protocol="json") as client:
    task_id = client.queue_task("process_data", {"items": [1, 2, 3]})
    task = client.get_task(task_id)
```

### MessagePack Protocol

```python
from task_daemon.client.grpc_client import GRPCDaemonClient

with GRPCDaemonClient("localhost:50051", protocol="msgpack") as client:
    task_id = client.queue_task("process_data", {"items": [1, 2, 3]})
    task = client.get_task(task_id)
```

## Server Configuration

### HTTP Server

Run HTTP server only (default):

```python
daemon = TaskDaemon()
daemon.register_handler(my_handler)
daemon.run()  # HTTP on port 8080, supports both JSON and MessagePack
```

The HTTP server automatically supports both protocols based on the `Content-Type` header sent by the client.

### gRPC Server

Run gRPC server only:

```python
daemon = TaskDaemon()
daemon.register_handler(my_handler)
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="json")  # gRPC only
```

Or with MessagePack:

```python
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="msgpack")
```

### Running Both HTTP and gRPC

If you need both servers (e.g., during migration), run them separately:

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

## Performance Comparison

Based on benchmark tests with various payload sizes:

| Metric | JSON | MessagePack | Improvement |
|--------|------|-------------|-------------|
| **Small Data** (100 bytes) | 1.0x | 3.4x faster | 42% smaller |
| **Medium Data** (10KB) | 1.0x | 4.3x faster | 67% smaller |
| **Large Data** (1MB) | 1.0x | 3.2x faster | 48% smaller |

## Choosing a Protocol

### Use JSON when:
- ✅ You need human-readable data for debugging
- ✅ You're integrating with systems that only support JSON
- ✅ You want maximum compatibility across languages
- ✅ Performance is not critical

### Use MessagePack when:
- ✅ You need maximum performance
- ✅ You're transferring large payloads
- ✅ You want to reduce bandwidth usage
- ✅ You're working in a controlled environment (Python to Python)

## Architecture

### Data Flow

```
Client → Protocol Serialization → Transport (HTTP/gRPC) → Protocol Deserialization → Server
```

### Key Points

1. **Protocol Layer**: Handles serialization/deserialization of task data
2. **Transport Layer**: gRPC/Protobuf handles RPC efficiency (HTTP/2, multiplexing, compression)
3. **Storage Layer**: SQLite stores data as JSON strings (protocol-agnostic)

### Why Base64 for MessagePack over gRPC?

MessagePack produces binary data that can't be stored in Protobuf string fields (which expect UTF-8). We use base64 encoding as a transport wrapper:

```
Task Data → MessagePack (binary) → Base64 (ASCII) → Protobuf String → gRPC/HTTP2
```

This adds minimal overhead (~33% size increase) but is still more efficient than JSON for large payloads, and gRPC's HTTP/2 compression helps offset the base64 overhead.

## Examples

See `examples/grpc_protocols.py` for a complete working example demonstrating both protocols.

## Migration Guide

### From JSON to MessagePack

No code changes needed on the server side. Just update your client:

```python
# Before
client = DaemonClient("http://localhost:8080", protocol="json")

# After
client = DaemonClient("http://localhost:8080", protocol="msgpack")
```

### Mixed Protocol Usage

You can use different protocols for different clients simultaneously:

```python
# Client A uses JSON
client_a = DaemonClient("http://localhost:8080", protocol="json")

# Client B uses MessagePack
client_b = DaemonClient("http://localhost:8080", protocol="msgpack")

# Both work with the same server!
```

## Troubleshooting

### "UnicodeDecodeError" with MessagePack

Make sure both client and server are using the same protocol:

```python
# Server
daemon.run_with_grpc(grpc_port=50051, grpc_protocol="msgpack")

# Client
client = GRPCDaemonClient("localhost:50051", protocol="msgpack")
```

### Performance Not Improving

- Verify you're using MessagePack on both client and server
- Check payload size (benefits are more noticeable with larger data)
- Profile your network vs. serialization overhead

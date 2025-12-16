# Binary Protocol Implementation Plan

## Current State

**Architecture:**
- HTTP/JSON API (FastAPI)
- JSON serialization for task data
- REST endpoints for task management

**Limitations:**
- JSON overhead for large payloads
- No native binary data support
- String-based serialization inefficient for complex types
- HTTP overhead for each request

## Goals

1. **Better Serialization**: Efficient binary encoding for complex data types
2. **Performance**: Reduce serialization/deserialization overhead
3. **Type Safety**: Preserve Python types across the wire
4. **Backward Compatibility**: Keep existing HTTP/JSON API
5. **Flexibility**: Support multiple protocols

## Protocol Options

### Option 1: gRPC (Recommended)

**Pros:**
- Industry standard, battle-tested
- Built-in code generation from .proto files
- HTTP/2 multiplexing
- Streaming support (useful for long-running tasks)
- Strong typing with Protocol Buffers
- Excellent performance
- Good Python support

**Cons:**
- Requires .proto file definitions
- More complex setup
- Additional dependency (grpcio)
- Learning curve for Protocol Buffers

**Implementation Complexity:** Medium

**Use Case:** Production systems, microservices, high-performance requirements

---

### Option 2: MessagePack over HTTP

**Pros:**
- Drop-in replacement for JSON
- Minimal code changes
- 2-5x smaller than JSON
- Faster serialization
- Supports binary data natively
- Simple to implement

**Cons:**
- Still uses HTTP overhead
- Not as efficient as gRPC
- No schema validation
- No streaming support

**Implementation Complexity:** Low

**Use Case:** Quick wins, gradual migration, simple binary data

---

### Option 3: Apache Thrift

**Pros:**
- Similar to gRPC but more flexible
- Multiple protocol options (binary, compact, JSON)
- Cross-language support
- Good performance

**Cons:**
- Less popular than gRPC
- More complex than MessagePack
- Requires IDL definitions
- Smaller community

**Implementation Complexity:** Medium-High

**Use Case:** Multi-language environments, need for flexibility

---

### Option 4: Cap'n Proto

**Pros:**
- Zero-copy serialization
- Extremely fast
- Schema evolution support
- No parsing step

**Cons:**
- Less mature ecosystem
- Smaller community
- Limited Python support
- Steeper learning curve

**Implementation Complexity:** High

**Use Case:** Extreme performance requirements, low-latency systems

---

### Option 5: Python Pickle (Not Recommended)

**Pros:**
- Native Python support
- Handles any Python object
- No schema needed

**Cons:**
- **Security risk** (arbitrary code execution)
- Python-only
- Not human-readable
- Version compatibility issues

**Implementation Complexity:** Very Low

**Use Case:** Internal systems only, trusted environments

---

### Option 6: Custom Binary Protocol

**Pros:**
- Full control
- Optimized for specific use case
- No external dependencies

**Cons:**
- High maintenance burden
- Reinventing the wheel
- Prone to bugs
- No tooling support

**Implementation Complexity:** Very High

**Use Case:** Very specific requirements, educational purposes

## Recommended Approach: Hybrid (MessagePack + gRPC)

### Phase 1: MessagePack over HTTP (Quick Win)
**Timeline:** 1-2 days

**Benefits:**
- Minimal changes to existing code
- Immediate performance improvement
- Easy to test and rollback
- Keeps HTTP/JSON as fallback

**Implementation:**
```python
# Add content-type negotiation
# Accept: application/msgpack -> use MessagePack
# Accept: application/json -> use JSON (default)
```

### Phase 2: gRPC Service (Long-term)
**Timeline:** 1-2 weeks

**Benefits:**
- Production-grade solution
- Better performance
- Streaming support
- Type safety

**Implementation:**
- Define .proto schema
- Generate Python code
- Implement gRPC service alongside HTTP
- Gradual migration

## Implementation Steps

### Phase 1: MessagePack (Immediate)

#### Step 1: Add MessagePack Support
```bash
pip install msgpack
```

#### Step 2: Create Protocol Abstraction
```python
# task_daemon/protocols/base.py
class Protocol:
    def serialize(self, data: Any) -> bytes: ...
    def deserialize(self, data: bytes) -> Any: ...

# task_daemon/protocols/json_protocol.py
class JSONProtocol(Protocol): ...

# task_daemon/protocols/msgpack_protocol.py
class MessagePackProtocol(Protocol): ...
```

#### Step 3: Update API Endpoints
```python
# Add content-type negotiation
@app.post("/queue")
async def enqueue(request: Request):
    content_type = request.headers.get("content-type")
    protocol = get_protocol(content_type)
    data = await protocol.deserialize(request.body())
    # ... process task
```

#### Step 4: Update Client
```python
class DaemonClient:
    def __init__(self, url: str, protocol: str = "json"):
        self.protocol = get_protocol(protocol)
```

#### Step 5: Benchmark
- Compare JSON vs MessagePack performance
- Measure serialization time
- Measure payload size
- Test with various data types

**Estimated Effort:** 4-8 hours

---

### Phase 2: gRPC (Future)

#### Step 1: Define Protocol Buffers Schema
```protobuf
// task_daemon.proto
syntax = "proto3";

service TaskDaemon {
  rpc QueueTask(TaskRequest) returns (TaskResponse);
  rpc GetTask(TaskIdRequest) returns (TaskInfo);
  rpc GetHealth(Empty) returns (HealthStatus);
  rpc StreamTasks(StreamRequest) returns (stream TaskInfo);
}

message TaskRequest {
  string task_type = 1;
  bytes task_data = 2;  // Serialized with MessagePack
}

message TaskResponse {
  int32 task_id = 1;
}
```

#### Step 2: Generate Python Code
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. task_daemon.proto
```

#### Step 3: Implement gRPC Service
```python
# task_daemon/grpc_service.py
class TaskDaemonServicer(task_daemon_pb2_grpc.TaskDaemonServicer):
    def QueueTask(self, request, context):
        task_id = self.daemon.queue.enqueue(
            request.task_type,
            msgpack.unpackb(request.task_data)
        )
        return task_daemon_pb2.TaskResponse(task_id=task_id)
```

#### Step 4: Run Both Servers
```python
# HTTP on 8080
# gRPC on 50051
```

#### Step 5: Create gRPC Client
```python
class GRPCDaemonClient:
    def __init__(self, url: str):
        self.channel = grpc.insecure_channel(url)
        self.stub = task_daemon_pb2_grpc.TaskDaemonStub(self.channel)
```

**Estimated Effort:** 2-3 days

---

## Performance Comparison (Estimated)

| Protocol | Serialization Speed | Payload Size | Complexity | Recommendation |
|----------|-------------------|--------------|------------|----------------|
| JSON | Baseline (1x) | Baseline (1x) | Low | ✅ Current |
| MessagePack | 2-3x faster | 0.4-0.6x | Low | ✅ Phase 1 |
| gRPC | 5-10x faster | 0.3-0.5x | Medium | ✅ Phase 2 |
| Thrift | 4-8x faster | 0.3-0.5x | Medium-High | ⚠️ Alternative |
| Cap'n Proto | 10-20x faster | 0.2-0.4x | High | ⚠️ Overkill |

## Migration Strategy

### Backward Compatibility

**Option A: Content Negotiation (Recommended)**
```python
# Client specifies protocol
client = DaemonClient(protocol="msgpack")  # or "json"

# Server auto-detects from Content-Type header
```

**Option B: Separate Endpoints**
```python
# /queue -> JSON (default)
# /queue/msgpack -> MessagePack
# /queue/grpc -> gRPC
```

**Option C: Version Prefix**
```python
# /v1/queue -> JSON
# /v2/queue -> MessagePack
```

### Testing Strategy

1. **Unit Tests**: Test each protocol independently
2. **Integration Tests**: Test protocol switching
3. **Performance Tests**: Benchmark all protocols
4. **Compatibility Tests**: Ensure JSON still works
5. **Load Tests**: Test under high concurrency

## Decision Matrix

| Requirement | MessagePack | gRPC | Recommendation |
|-------------|-------------|------|----------------|
| Quick implementation | ✅ | ❌ | MessagePack |
| Best performance | ❌ | ✅ | gRPC |
| Streaming support | ❌ | ✅ | gRPC |
| Simple migration | ✅ | ❌ | MessagePack |
| Production-ready | ✅ | ✅ | Both |
| Type safety | ⚠️ | ✅ | gRPC |
| Binary data | ✅ | ✅ | Both |

## Recommended Timeline

**Week 1:**
- [ ] Implement MessagePack protocol abstraction
- [ ] Add content-type negotiation
- [ ] Update client with protocol option
- [ ] Write unit tests
- [ ] Benchmark performance

**Week 2:**
- [ ] Define gRPC .proto schema
- [ ] Generate Python code
- [ ] Implement gRPC service
- [ ] Create gRPC client
- [ ] Integration tests

**Week 3:**
- [ ] Performance testing
- [ ] Documentation
- [ ] Migration guide
- [ ] Production deployment

## Next Steps

1. **Validate Requirements**: Confirm performance needs
2. **Prototype MessagePack**: Quick proof of concept
3. **Benchmark**: Measure actual performance gains
4. **Decide on Phase 2**: Based on Phase 1 results
5. **Plan Migration**: Create detailed migration plan

## Questions to Answer

- [ ] What's the average task payload size?
- [ ] What's the current throughput (tasks/sec)?
- [ ] What's the target throughput?
- [ ] Are there specific bottlenecks?
- [ ] Is streaming needed for long-running tasks?
- [ ] Do we need cross-language support?
- [ ] What's the deployment environment?

## Resources

- MessagePack: https://msgpack.org/
- gRPC: https://grpc.io/
- Protocol Buffers: https://protobuf.dev/
- Performance comparison: https://github.com/alecthomas/go_serialization_benchmarks

## Conclusion

**Immediate Action:** Implement MessagePack (Phase 1)
- Low risk, high reward
- Easy to implement and test
- Provides immediate performance improvement
- Keeps options open for Phase 2

**Future Consideration:** gRPC (Phase 2)
- Evaluate after Phase 1 results
- Implement if streaming or extreme performance needed
- Can coexist with HTTP/MessagePack

# TaskDaemon Kotlin Client

Kotlin gRPC client for TaskDaemon demonstrating multi-language support.

## Project Structure

```
DaemonKotlinClient/
├── build.gradle.kts          # Gradle build with protobuf plugin
├── settings.gradle.kts        # Project settings
├── src/
│   └── main/
│       ├── proto/
│       │   └── task_daemon.proto  # Protobuf definition (copied from Python project)
│       └── kotlin/
│           └── com/example/daemon/
│               └── Main.kt        # Kotlin client application
└── test.sh                    # Test script to run daemon + client
```

## Prerequisites

- JDK 17 or higher
- Python 3.11+ with TaskDaemon installed
- Gradle (wrapper included)

## Build

```bash
./gradlew build
```

This will:
1. Download all dependencies (gRPC, Protobuf, Kotlin coroutines)
2. Generate Kotlin code from `task_daemon.proto`
3. Compile the Kotlin application

Generated code appears in:
```
build/generated/source/proto/main/
├── kotlin/taskdaemon/          # Protobuf message classes
└── grpckt/taskdaemon/          # gRPC stub classes
```

## Run

### Option 1: Automated Test

```bash
./test.sh
```

This script:
1. Starts TaskDaemon gRPC server (Python)
2. Runs the Kotlin client
3. Cleans up

### Option 2: Manual

**Terminal 1 - Start Python daemon:**
```bash
cd ../../
python3 -c "
from task_daemon import TaskDaemon

def add(a: int, b: int) -> int:
    return a + b

daemon = TaskDaemon()
daemon.register_handler(add)
daemon.run_with_grpc(grpc_port=50051, grpc_protocol='json')
"
```

**Terminal 2 - Run Kotlin client:**
```bash
./gradlew run
```

## What It Demonstrates

The Kotlin client shows:

1. **Health Check** - Verify daemon is running
2. **Queue Task** - Send an "add" task with JSON data
3. **Get Task** - Retrieve task details and result
4. **List Tasks** - Get recent tasks
5. **Get Metrics** - Fetch daemon metrics

## Key Features

### Type-Safe API

The generated Kotlin code provides type-safe builders:

```kotlin
val taskRequest = taskRequest {
    taskType = "add"
    taskDataJson = """{"a": 10, "b": 20}"""
}
```

### Coroutine Support

Uses Kotlin coroutines for async operations:

```kotlin
fun main() = runBlocking {
    val client = TaskDaemonGrpcKt.TaskDaemonCoroutineStub(channel)
    val response = client.queueTask(taskRequest)  // Suspending call
}
```

### Cross-Language

This demonstrates TaskDaemon's multi-language support:
- **Server**: Python
- **Client**: Kotlin
- **Protocol**: gRPC/Protobuf

The same `.proto` file can generate clients for:
- Go
- Java
- C++
- C#
- Node.js
- Ruby
- PHP
- Dart

## Dependencies

Defined in `build.gradle.kts`:

- `io.grpc:grpc-kotlin-stub` - Kotlin gRPC support
- `io.grpc:grpc-protobuf` - Protobuf serialization
- `io.grpc:grpc-netty` - Network transport
- `com.google.protobuf:protobuf-kotlin` - Kotlin protobuf runtime
- `kotlinx-coroutines-core` - Coroutine support

## Gradle Plugins

- `kotlin("jvm")` - Kotlin JVM compilation
- `com.google.protobuf` - Protobuf code generation

## Troubleshooting

**Build fails with "protoc not found":**
- The protobuf plugin downloads protoc automatically
- Ensure you have internet connection

**Connection refused:**
- Make sure TaskDaemon is running on port 50051
- Check with: `lsof -i :50051`

**Wrong Java version:**
- This project requires JDK 17+
- Check with: `java -version`
- Set JAVA_HOME if needed

## Next Steps

To add more task types:

1. Add handler in Python daemon:
```python
def multiply(x: int, y: int) -> int:
    return x * y

daemon.register_handler(multiply)
```

2. Call from Kotlin:
```kotlin
val request = taskRequest {
    taskType = "multiply"
    taskDataJson = """{"x": 5, "y": 3}"""
}
```

No proto changes needed - the protocol is dynamic!

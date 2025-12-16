#!/bin/bash

echo "Starting TaskDaemon gRPC server..."
cd ../../

# Start daemon in background
python3 -c "
from task_daemon import TaskDaemon

def add(a: int, b: int) -> int:
    return a + b

daemon = TaskDaemon()
daemon.register_handler(add)
daemon.run_with_grpc(grpc_port=50051, grpc_protocol='json')
" &

DAEMON_PID=$!
echo "Daemon started with PID $DAEMON_PID"

# Wait for daemon to start
sleep 3

# Run Kotlin client
echo ""
echo "Running Kotlin client..."
cd clients/kotlin
./gradlew run --quiet --console=plain

# Cleanup
echo ""
echo "Stopping daemon..."
kill $DAEMON_PID
wait $DAEMON_PID 2>/dev/null

echo "Done!"

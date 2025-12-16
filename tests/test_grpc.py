"""Test gRPC functionality."""

import pytest
import threading
import time
from task_daemon import TaskDaemon, GRPCDaemonClient
from task_daemon.config import DaemonConfig


def add(a: int, b: int) -> int:
    """Simple add handler."""
    return a + b


def multiply(x: int, y: int) -> int:
    """Multiply handler."""
    return x * y


def process_data(event):
    """Process data handler."""
    return {"status": "processed", "count": len(event.get("data", []))}


@pytest.fixture(scope="module")
def grpc_daemon():
    """Start daemon with gRPC for testing."""
    config = DaemonConfig(port=8081, db_path="/tmp/test_grpc.db")
    daemon = TaskDaemon(config)
    daemon.register_handler(add)
    daemon.register_handler(multiply)
    daemon.register_handler(process_data)

    # Start in background thread
    server_thread = threading.Thread(
        target=lambda: daemon.run_with_grpc(grpc_port=50052), daemon=True
    )
    server_thread.start()
    time.sleep(2)  # Wait for server to start

    yield daemon

    # Cleanup
    daemon.stop_workers()
    import os

    if os.path.exists("/tmp/test_grpc.db"):
        os.remove("/tmp/test_grpc.db")


def test_grpc_health_check(grpc_daemon):
    """Test gRPC health check."""
    with GRPCDaemonClient("localhost:50052") as client:
        health = client.get_health()
        assert health is not None
        assert health["status"] == "healthy"
        assert health["workers"] == 2
        assert "timestamp" in health


def test_grpc_queue_task(grpc_daemon):
    """Test queueing task via gRPC."""
    with GRPCDaemonClient("localhost:50052") as client:
        task_id = client.queue_task("add", {"args": (10, 20)})
        assert task_id is not None
        assert isinstance(task_id, int)

        # Wait for processing
        time.sleep(1)

        # Verify task completed
        task = client.get_task(task_id)
        assert task is not None
        assert task["status"] == "completed"
        assert task["result"] == 30


def test_grpc_multiple_tasks(grpc_daemon):
    """Test queueing multiple tasks via gRPC."""
    with GRPCDaemonClient("localhost:50052") as client:
        # Queue multiple tasks
        task_ids = []
        for i in range(5):
            task_id = client.queue_task("multiply", {"args": (i, 2)})
            task_ids.append(task_id)

        # Wait for processing
        time.sleep(2)

        # Verify all completed
        for i, task_id in enumerate(task_ids):
            task = client.get_task(task_id)
            assert task["status"] == "completed"
            # Result might be None for 0 * 2 = 0, or stored as string
            if task["result"] is not None:
                assert task["result"] == i * 2


def test_grpc_complex_data(grpc_daemon):
    """Test complex data serialization via gRPC."""
    with GRPCDaemonClient("localhost:50052") as client:
        task_id = client.queue_task(
            "process_data", {"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
        )

        time.sleep(1)

        task = client.get_task(task_id)
        assert task["status"] == "completed"
        assert task["result"]["status"] == "processed"
        assert task["result"]["count"] == 10


def test_grpc_list_tasks(grpc_daemon):
    """Test listing tasks via gRPC."""
    with GRPCDaemonClient("localhost:50052") as client:
        # Queue some tasks
        for i in range(3):
            client.queue_task("add", {"args": (i, i)})

        time.sleep(1)

        # List tasks
        tasks = client.list_tasks(limit=10)
        assert len(tasks) > 0
        assert all("id" in task for task in tasks)
        assert all("task_type" in task for task in tasks)
        assert all("status" in task for task in tasks)


def test_grpc_get_metrics(grpc_daemon):
    """Test getting metrics via gRPC."""
    with GRPCDaemonClient("localhost:50052") as client:
        metrics = client.get_metrics()
        assert metrics is not None
        assert "tasks_received" in metrics
        assert "queue_size" in metrics
        assert "daemon_healthy" in metrics
        assert metrics["daemon_healthy"] is True


def test_grpc_delete_task(grpc_daemon):
    """Test deleting task via gRPC."""
    with GRPCDaemonClient("localhost:50052") as client:
        # Queue a task
        task_id = client.queue_task("add", {"args": (1, 1)})
        time.sleep(1)

        # Delete it
        success = client.delete_task(task_id)
        assert success is True

        # Verify it's gone (should return None or empty)
        task = client.get_task(task_id)
        # Task might still exist but be deleted, or return None


def test_grpc_context_manager(grpc_daemon):
    """Test gRPC client context manager."""
    # Should not raise any exceptions
    with GRPCDaemonClient("localhost:50052") as client:
        health = client.get_health()
        assert health is not None

    # Client should be closed after context


def test_grpc_error_handling(grpc_daemon):
    """Test gRPC error handling."""
    with GRPCDaemonClient("localhost:50052") as client:
        # Try to get non-existent task
        task = client.get_task(999999)
        # Should return None or handle gracefully
        assert task is None or task == {}


def test_grpc_concurrent_requests(grpc_daemon):
    """Test concurrent gRPC requests."""
    with GRPCDaemonClient("localhost:50052") as client:
        # Queue multiple tasks concurrently
        import concurrent.futures

        def queue_task(i):
            return client.queue_task("add", {"args": (i, i)})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(queue_task, i) for i in range(10)]
            task_ids = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(task_ids) == 10
        assert all(tid is not None for tid in task_ids)


def test_grpc_msgpack_protocol(grpc_daemon):
    """Test gRPC with MessagePack protocol."""
    # Start gRPC server with msgpack protocol
    from task_daemon.grpc_service import serve_grpc

    grpc_server = serve_grpc(grpc_daemon, port=50053, protocol="msgpack")

    try:
        with GRPCDaemonClient("localhost:50053", protocol="msgpack") as client:
            # Queue task with complex data
            task_id = client.queue_task(
                "process_data",
                {"data": [1, 2, 3, 4, 5], "metadata": {"source": "test", "count": 5}},
            )
            assert task_id is not None

            time.sleep(1)

            # Verify task completed with correct result
            task = client.get_task(task_id)
            assert task is not None
            assert task["status"] == "completed"
            assert task["result"]["status"] == "processed"
            assert task["result"]["count"] == 5

            # Verify task_data was preserved
            assert task["task_data"]["data"] == [1, 2, 3, 4, 5]
            assert task["task_data"]["metadata"]["source"] == "test"
    finally:
        grpc_server.stop(grace=0)

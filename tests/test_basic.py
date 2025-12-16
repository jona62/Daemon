"""Basic tests for TaskDaemon."""

import pytest
import os
import threading
import time
from unittest.mock import Mock, patch
from task_daemon import TaskDaemon, DaemonClient, DaemonConfig, task_handler
from task_daemon.core import clear_handlers


@pytest.fixture
def config():
    """Test configuration."""
    db_path = "/tmp/test_queue_clean.db"
    # Remove existing test db to ensure clean state
    if os.path.exists(db_path):
        os.remove(db_path)

    return DaemonConfig(
        port=8081,  # Different port for testing
        db_path=db_path,
        worker_threads=1,
        log_level="ERROR",  # Reduce noise in tests
    )


@pytest.fixture
def daemon(config):
    """Test daemon instance."""
    clear_handlers()  # Clear any existing handlers
    from prometheus_client import CollectorRegistry

    registry = CollectorRegistry()  # Use separate registry for each test
    return TaskDaemon(config, metrics_registry=registry)


def test_task_handler_registration():
    """Test task handler decorator registration."""
    clear_handlers()

    @task_handler
    def test_task(data):
        return f"processed: {data}"

    from task_daemon.core import get_task_handler

    handler = get_task_handler("test_task")
    assert handler is not None
    assert handler({"test": "data"}) == "processed: {'test': 'data'}"


def test_daemon_config():
    """Test configuration creation."""
    config = DaemonConfig(worker_threads=5, port=9000)
    assert config.worker_threads == 5
    assert config.port == 9000
    assert config.db_path == "/tmp/task_queue.db"  # default


def test_daemon_client():
    """Test daemon client basic functionality."""
    client = DaemonClient("http://localhost:8080")

    # These will fail since no daemon is running, but test the interface
    health = client.health_check()
    assert health.status in ["healthy", "error", "unhealthy"]


def test_queue_operations(daemon):
    """Test queue basic operations."""
    queue = daemon.queue

    # Test enqueue/dequeue
    task_id = queue.enqueue("test_type", {"data": "test"})
    assert task_id is not None

    task = queue.dequeue()
    assert task is not None
    assert task[1] == "test_type"  # task_type
    assert task[2]["data"] == "test"  # task_data

    # Mark complete with result
    result = {"status": "success"}
    queue.mark_complete(task[0], result)
    assert queue.size() == 0


def test_queue_new_features(daemon):
    """Test new queue features: get_task, delete_task, redrive_task."""
    queue = daemon.queue

    # Test get_task
    task_id = queue.enqueue("test_type", {"data": "test"})
    task_details = queue.get_task(task_id)
    assert task_details is not None
    assert task_details["id"] == task_id
    assert task_details["task_type"] == "test_type"
    assert task_details["status"] == "pending"

    # Test delete_task
    assert queue.delete_task(task_id) is True
    assert queue.get_task(task_id) is None
    assert queue.delete_task(999) is False  # Non-existent task

    # Test redrive_task
    task_id = queue.enqueue("test_type", {"data": "test"})
    queue.mark_failed(task_id, "Test error", max_retries=0)  # Force to failed

    task_details = queue.get_task(task_id)
    assert task_details["status"] == "failed"

    assert queue.redrive_task(task_id) is True
    task_details = queue.get_task(task_id)
    assert task_details["status"] == "pending"
    assert task_details["last_error"] is None


@patch("requests.get")
@patch("requests.post")
@patch("requests.delete")
def test_client_new_methods(mock_delete, mock_post, mock_get):
    """Test new client methods."""
    client = DaemonClient("http://localhost:8080")

    # Test get_task
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "id": 1,
        "status": "completed",
        "task_type": "test",
        "task_data": "{}",
        "created_at": "2023-01-01",
        "attempts": 0,
    }

    task = client.get_task(1)
    assert task.id == 1  # Pydantic model attribute access
    assert task.status == "completed"
    mock_get.assert_called_with("http://localhost:8080/api/tasks/1", timeout=0.1)

    # Test get_task not found
    mock_get.return_value.status_code = 404
    task = client.get_task(999)
    assert task is None

    # Test delete_task
    mock_delete.return_value.status_code = 200
    result = client.delete_task(1)
    assert result is True
    mock_delete.assert_called_with("http://localhost:8080/api/tasks/1", timeout=0.1)

    # Test delete_task failure
    mock_delete.return_value.status_code = 404
    result = client.delete_task(999)
    assert result is False

    # Test redrive_task
    mock_post.return_value.status_code = 200
    result = client.redrive_task(1)
    assert result is True
    mock_post.assert_called_with(
        "http://localhost:8080/api/tasks/1/redrive", timeout=0.1
    )

    # Test redrive_task failure
    mock_post.return_value.status_code = 404
    result = client.redrive_task(999)
    assert result is False


def test_mark_complete_with_result(daemon):
    """Test marking tasks complete with results."""
    queue = daemon.queue

    task_id = queue.enqueue("test_type", {"data": "test"})
    result = {"status": "success", "processed_items": 5}

    queue.mark_complete(task_id, result)

    task_details = queue.get_task(task_id)
    assert task_details["status"] == "completed"
    assert task_details["result"] is not None
    assert "processed_items" in task_details["result"]


def test_database_cleanup_on_init():
    """Test that database can be explicitly cleared."""
    from prometheus_client import CollectorRegistry

    db_path = "/tmp/test_cleanup.db"

    # Create a database with some data
    config1 = DaemonConfig(db_path=db_path)
    daemon1 = TaskDaemon(config1, metrics_registry=CollectorRegistry())
    task_id = daemon1.queue.enqueue("test", {"data": "test"})
    assert daemon1.queue.get_task(task_id) is not None

    # Clear database explicitly
    daemon1.queue.clear_database()
    assert daemon1.queue.get_task(task_id) is None  # Should be gone

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


def test_memory_queue_implementation():
    """Test that daemon works with different queue implementations."""
    from prometheus_client import CollectorRegistry
    from task_daemon.core import MemoryQueue

    config = DaemonConfig(port=8082)
    memory_queue = MemoryQueue()
    daemon = TaskDaemon(
        config, metrics_registry=CollectorRegistry(), queue=memory_queue
    )

    # Test basic queue operations
    task_id = daemon.queue.enqueue("test_type", {"data": "test"})
    assert task_id == 1  # Memory queue starts at 1

    task = daemon.queue.dequeue()
    assert task is not None
    assert task[1] == "test_type"

    # Test new features work with memory queue
    daemon.queue.mark_complete(task_id, {"result": "success"})
    task_details = daemon.queue.get_task(task_id)
    assert task_details["status"] == "completed"
    assert task_details["result"]["result"] == "success"


def test_pydantic_output_serialization():
    """Test that Pydantic model outputs are properly serialized."""
    from prometheus_client import CollectorRegistry
    from pydantic import BaseModel

    class TestInput(BaseModel):
        message: str

    class TestOutput(BaseModel):
        status: str
        processed_message: str

    # Clear handlers and register new one
    clear_handlers()

    @task_handler
    def test_pydantic_handler(data: TestInput) -> TestOutput:
        return TestOutput(
            status="success", processed_message=f"Processed: {data.message}"
        )

    config = DaemonConfig(port=8095, db_path="/tmp/test_pydantic_output.db")
    daemon = TaskDaemon(config, metrics_registry=CollectorRegistry())

    # Clear database
    daemon.queue.clear_database()

    # Start workers
    daemon.start_workers()

    try:
        # Queue task
        task_id = daemon.queue.enqueue(
            "test_pydantic_handler", {"message": "Hello World"}
        )

        # Wait for processing
        import time

        time.sleep(2)

        # Check result
        task = daemon.queue.get_task(task_id)
        assert task is not None
        assert task["status"] == "completed"

        # Result should be serialized as JSON string
        result = task["result"]
        assert result is not None
        assert isinstance(result, str)  # Stored as JSON string

        # Parse the JSON to verify structure
        import json

        parsed_result = json.loads(result)
        assert parsed_result["status"] == "success"
        assert parsed_result["processed_message"] == "Processed: Hello World"

    finally:
        daemon.stop_workers()
        # Cleanup
        import os

        if os.path.exists("/tmp/test_pydantic_output.db"):
            os.remove("/tmp/test_pydantic_output.db")


def test_multiple_parameter_handlers():
    """Test handlers with multiple parameters."""

    def add(a: int, b: int) -> int:
        return a + b

    def greet(name: str, greeting: str = "Hello") -> str:
        return f"{greeting}, {name}!"

    def no_params() -> str:
        return "called"

    daemon = TaskDaemon()
    daemon.register_handler(add)
    daemon.register_handler(greet)
    daemon.register_handler(no_params)

    # Test multiple parameters with dict
    result = daemon._invoke_handler(add, {"a": 5, "b": 3})
    assert result == 8

    # Test with default parameter
    result = daemon._invoke_handler(greet, {"name": "World"})
    assert result == "Hello, World!"

    # Test override default
    result = daemon._invoke_handler(greet, {"name": "Alice", "greeting": "Hi"})
    assert result == "Hi, Alice!"

    # Test no parameters
    result = daemon._invoke_handler(no_params, {})
    assert result == "called"

    # Test positional args format
    result = daemon._invoke_handler(add, {"args": (10, 20)})
    assert result == 30


#!/usr/bin/env python3
"""Consolidated client tests - all scenarios in one file."""

from task_daemon import DaemonClient
import time


def scenario_basic_operations():
    """Test basic task operations."""
    print("🔍 SCENARIO: Basic Operations")
    client = DaemonClient("http://localhost:8080")

    # Health check
    health = client.health_check()
    print(f"Status: {health.status}")

    # Queue different task types
    tasks = []

    email_id = client.queue_task(
        "send_email",
        {
            "recipient": "user@example.com",
            "subject": "Welcome!",
            "body": "Thanks for signing up",
        },
    )
    tasks.append(("Email", email_id))

    data_id = client.queue_task(
        "process_data",
        {"operation": "transform", "data": {"users": 100, "orders": 250}},
    )
    tasks.append(("Data Processing", data_id))

    backup_id = client.queue_task(
        "backup_data", {"source": "/data/users", "file_count": 1500}
    )
    tasks.append(("Backup", backup_id))

    print(f"✅ Queued {len(tasks)} tasks")

    # Wait and check results
    time.sleep(4)

    print("📋 Results:")
    for name, task_id in tasks:
        task = client.get_task(task_id)
        print(f"{name:15} | Status: {task.status:10} | Result: {task.result}")

    return tasks


def scenario_pydantic_validation():
    """Test Pydantic validation scenarios."""
    print("\n🔬 SCENARIO: Pydantic Validation")
    client = DaemonClient("http://localhost:8080")

    # Valid data processing
    valid_id = client.queue_task(
        "process_data",
        {
            "operation": "analyze",
            "data": {"metrics": [1, 2, 3], "timestamp": "2023-01-01"},
        },
    )

    # Invalid data type (should fail validation)
    try:
        invalid_id = client.queue_task(
            "process_data",
            {
                "operation": "analyze",
                "data": "not-a-dict",  # Should be dict, not string
            },
        )
        print(f"Invalid task queued: {invalid_id}")
    except Exception as e:
        print(f"Validation error (expected): {e}")
        invalid_id = None

    # Missing required field
    try:
        missing_id = client.queue_task(
            "send_email",
            {
                "subject": "No recipient"
                # Missing 'recipient' field
            },
        )
        print(f"Missing field task queued: {missing_id}")
    except Exception as e:
        print(f"Validation error (expected): {e}")
        missing_id = None

    time.sleep(3)

    print("📊 Validation Results:")
    for task_id in [valid_id, invalid_id, missing_id]:
        if task_id:
            task = client.get_task(task_id)
            print(f"Task {task_id}: {task.status}")
            if task.last_error:
                print(f"  Error: {task.last_error}")


def scenario_failure_handling():
    """Test failure scenarios and recovery."""
    print("\n💥 SCENARIO: Failure Handling")
    client = DaemonClient("http://localhost:8080")

    # Queue a task that will fail
    fail_id = client.queue_task("failing_task", {"data": "test"})
    print(f"Failing task ID: {fail_id}")

    # Wait for failure and retries
    time.sleep(6)

    task = client.get_task(fail_id)
    print(f"Status: {task.status}")
    print(f"Attempts: {task.attempts}")
    print(f"Error: {task.last_error}")

    # Test redrive
    print("🔄 Testing redrive...")
    try:
        client.redrive_task(fail_id)
        time.sleep(2)
        task = client.get_task(fail_id)
        print(f"After redrive - Status: {task.status}, Attempts: {task.attempts}")
    except Exception as e:
        print(f"Redrive failed: {e}")

    # Cleanup
    try:
        client.delete_task(fail_id)
        print("✅ Task deleted")
    except Exception as e:
        print(f"Delete failed: {e}")


def scenario_monitoring():
    """Test monitoring and metrics."""
    print("\n📊 SCENARIO: Monitoring")
    client = DaemonClient("http://localhost:8080")

    # Health status
    health = client.health_check()
    print(f"Status: {health.status}")
    print(f"Queue Size: {health.queue_size}")
    print(f"Workers: {health.workers}")

    # Current metrics
    metrics = client.get_metrics()
    print(f"Tasks Received: {metrics.tasks_received}")
    print(f"Tasks Processed: {metrics.tasks_processed}")
    print(f"Tasks Failed: {metrics.tasks_failed}")

    # Generate activity
    print("🚀 Generating activity...")
    task_ids = []
    for i in range(3):
        task_id = client.queue_task(
            "image_resize", {"filename": f"image_{i}.jpg", "size": "200x200"}
        )
        task_ids.append(task_id)

    # Monitor progress
    for _ in range(2):
        time.sleep(2)
        metrics = client.get_metrics()
        print(f"Queue: {metrics.queue_size} | Processed: {metrics.tasks_processed}")

    # Recent tasks
    print("📋 Recent Tasks:")
    recent = client.get_tasks(limit=5)
    for task in recent:
        print(f"ID {task.id:3} | {task.task_type:15} | {task.status:10}")

    # Cleanup
    for task_id in task_ids:
        try:
            client.delete_task(task_id)
        except:
            pass


def main():
    """Run all test scenarios."""
    print("🧪 TaskDaemon Client Test Suite")
    print("=" * 50)

    try:
        scenario_basic_operations()
        scenario_pydantic_validation()
        scenario_failure_handling()
        scenario_monitoring()

        print("\n✅ All scenarios completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure daemon is running: python daemon.py")


if __name__ == "__main__":
    main()

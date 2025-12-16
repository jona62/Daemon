"""Example demonstrating gRPC with JSON and MessagePack protocols."""

import time
from task_daemon import TaskDaemon
from task_daemon.client.grpc_client import GRPCDaemonClient


def process_order(order_data: dict) -> dict:
    """Process an order."""
    print(f"Processing order {order_data.get('order_id')}")
    return {
        "status": "processed",
        "order_id": order_data.get("order_id"),
        "items_count": len(order_data.get("items", [])),
        "total": sum(item.get("price", 0) for item in order_data.get("items", [])),
    }


def main():
    # Create daemon with handler
    daemon = TaskDaemon()
    daemon.register_handler(process_order)

    # Start gRPC server with JSON protocol in background thread
    import threading

    server_thread = threading.Thread(
        target=lambda: daemon.run_with_grpc(grpc_port=50051, grpc_protocol="json"),
        daemon=True,
    )
    server_thread.start()
    time.sleep(2)  # Wait for server to start

    print("=" * 60)
    print("Testing gRPC with JSON Protocol")
    print("=" * 60)

    # Test with JSON protocol
    with GRPCDaemonClient("localhost:50051", protocol="json") as client:
        order = {
            "order_id": "ORD-001",
            "customer": "Alice",
            "items": [
                {"name": "Widget", "price": 29.99, "qty": 2},
                {"name": "Gadget", "price": 49.99, "qty": 1},
            ],
        }

        task_id = client.queue_task("process_order", order)
        print(f"✓ Queued task {task_id} with JSON protocol")

        time.sleep(1)

        task = client.get_task(task_id)
        print(f"✓ Task status: {task['status']}")
        print(f"✓ Result: {task['result']}")

    print("\n" + "=" * 60)
    print("Testing gRPC with MessagePack Protocol")
    print("=" * 60)

    # Start another gRPC server with MessagePack protocol
    from task_daemon.grpc_service import serve_grpc

    msgpack_server = serve_grpc(daemon, port=50052, protocol="msgpack")

    try:
        # Test with MessagePack protocol
        with GRPCDaemonClient("localhost:50052", protocol="msgpack") as client:
            order = {
                "order_id": "ORD-002",
                "customer": "Bob",
                "items": [
                    {"name": "Doohickey", "price": 19.99, "qty": 3},
                    {"name": "Thingamajig", "price": 39.99, "qty": 2},
                ],
            }

            task_id = client.queue_task("process_order", order)
            print(f"✓ Queued task {task_id} with MessagePack protocol")

            time.sleep(1)

            task = client.get_task(task_id)
            print(f"✓ Task status: {task['status']}")
            print(f"✓ Result: {task['result']}")

            # List all tasks
            tasks = client.list_tasks(limit=5)
            print(f"\n✓ Retrieved {len(tasks)} recent tasks")
            for t in tasks:
                print(f"  - Task {t['id']}: {t['task_type']} ({t['status']})")
    finally:
        msgpack_server.stop(grace=0)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("✓ Both JSON and MessagePack protocols work with gRPC")
    print("✓ MessagePack provides better performance for binary data")
    print("✓ JSON is more human-readable and universally compatible")
    print("✓ Choose based on your use case!")


if __name__ == "__main__":
    main()

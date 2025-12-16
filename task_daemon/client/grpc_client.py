"""gRPC client for TaskDaemon."""

import grpc
import base64
from typing import Optional, List, Dict, Any

from ..proto import task_daemon_pb2, task_daemon_pb2_grpc
from ..protocols import JSONProtocol, MessagePackProtocol


class GRPCDaemonClient:
    """gRPC client for TaskDaemon."""

    def __init__(self, address: str = "localhost:50051", protocol: str = "json"):
        """Initialize gRPC client.

        Args:
            address: gRPC server address (host:port)
            protocol: Protocol for task data serialization ("json" or "msgpack")
        """
        self.address = address
        self.protocol_name = protocol
        self.protocol = (
            MessagePackProtocol() if protocol == "msgpack" else JSONProtocol()
        )
        self.channel = grpc.insecure_channel(address)
        self.stub = task_daemon_pb2_grpc.TaskDaemonStub(self.channel)

    def close(self):
        """Close the gRPC channel."""
        self.channel.close()

    def queue_task(
        self, task_type: str, task_data: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """Queue a task.

        Args:
            task_type: Type of task
            task_data: Task data (will be serialized using configured protocol)

        Returns:
            Task ID if successful, None otherwise
        """
        try:
            # Serialize using configured protocol
            data_bytes = self.protocol.serialize(task_data or {})

            # For msgpack, use base64 encoding since protobuf string field expects UTF-8
            if self.protocol_name == "msgpack":
                data_str = base64.b64encode(data_bytes).decode("ascii")
            else:
                data_str = data_bytes.decode("utf-8")

            request = task_daemon_pb2.TaskRequest(
                task_type=task_type, task_data_json=data_str
            )
            response = self.stub.QueueTask(request)
            return response.task_id
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return None

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task information.

        Args:
            task_id: Task ID

        Returns:
            Task information dict or None
        """
        try:
            request = task_daemon_pb2.TaskIdRequest(task_id=task_id)
            response = self.stub.GetTask(request)

            # Decode based on protocol
            if self.protocol_name == "msgpack":
                task_data = (
                    self.protocol.deserialize(base64.b64decode(response.task_data))
                    if response.task_data
                    else None
                )
                result = (
                    self.protocol.deserialize(base64.b64decode(response.result))
                    if response.result
                    else None
                )
            else:
                task_data = (
                    self.protocol.deserialize(response.task_data.encode())
                    if response.task_data
                    else None
                )
                result = (
                    self.protocol.deserialize(response.result.encode())
                    if response.result
                    else None
                )

            return {
                "id": response.id,
                "task_type": response.task_type,
                "task_data": task_data,
                "status": response.status,
                "created_at": response.created_at,
                "completed_at": response.completed_at,
                "attempts": response.attempts,
                "last_error": response.last_error,
                "result": result,
            }
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return None

    def get_health(self) -> Optional[Dict[str, Any]]:
        """Get health status.

        Returns:
            Health status dict or None
        """
        try:
            request = task_daemon_pb2.Empty()
            response = self.stub.GetHealth(request)
            return {
                "status": response.status,
                "queue_size": response.queue_size,
                "timestamp": response.timestamp,
                "workers": response.workers,
            }
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return None

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get metrics summary.

        Returns:
            Metrics dict or None
        """
        try:
            request = task_daemon_pb2.Empty()
            response = self.stub.GetMetrics(request)
            return {
                "tasks_received": response.tasks_received,
                "tasks_processed_success": response.tasks_processed_success,
                "tasks_processed_failed": response.tasks_processed_failed,
                "queue_size": response.queue_size,
                "daemon_healthy": response.daemon_healthy,
            }
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return None

    def list_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent tasks.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of task dicts
        """
        try:
            request = task_daemon_pb2.ListTasksRequest(limit=limit)
            response = self.stub.ListTasks(request)

            tasks = []
            for task in response.tasks:
                # Decode based on protocol
                if self.protocol_name == "msgpack":
                    task_data = (
                        self.protocol.deserialize(base64.b64decode(task.task_data))
                        if task.task_data
                        else None
                    )
                    result = (
                        self.protocol.deserialize(base64.b64decode(task.result))
                        if task.result
                        else None
                    )
                else:
                    task_data = (
                        self.protocol.deserialize(task.task_data.encode())
                        if task.task_data
                        else None
                    )
                    result = (
                        self.protocol.deserialize(task.result.encode())
                        if task.result
                        else None
                    )

                tasks.append(
                    {
                        "id": task.id,
                        "task_type": task.task_type,
                        "task_data": task_data,
                        "status": task.status,
                        "created_at": task.created_at,
                        "completed_at": task.completed_at,
                        "attempts": task.attempts,
                        "last_error": task.last_error,
                        "result": result,
                    }
                )
            return tasks
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return []

    def delete_task(self, task_id: int) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if successful, False otherwise
        """
        try:
            request = task_daemon_pb2.TaskIdRequest(task_id=task_id)
            response = self.stub.DeleteTask(request)
            return response.success
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return False

    def redrive_task(self, task_id: int) -> bool:
        """Redrive a failed task.

        Args:
            task_id: Task ID

        Returns:
            True if successful, False otherwise
        """
        try:
            request = task_daemon_pb2.TaskIdRequest(task_id=task_id)
            response = self.stub.RedriveTask(request)
            return response.success
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()}: {e.details()}")
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

"""gRPC service implementation for TaskDaemon."""

import grpc
import json
import base64
from concurrent import futures
from datetime import datetime
from typing import Optional

from .proto import task_daemon_pb2, task_daemon_pb2_grpc
from .daemon.daemon import TaskDaemon
from .protocols import JSONProtocol, MessagePackProtocol


class TaskDaemonServicer(task_daemon_pb2_grpc.TaskDaemonServicer):
    """gRPC servicer for TaskDaemon."""

    def __init__(self, daemon: TaskDaemon, protocol: str = "json"):
        self.daemon = daemon
        self.protocol_name = protocol
        self.protocol = (
            MessagePackProtocol() if protocol == "msgpack" else JSONProtocol()
        )

    def QueueTask(self, request, context):
        """Queue a new task."""
        try:
            # Deserialize task data using configured protocol
            if self.protocol_name == "msgpack":
                data_bytes = (
                    base64.b64decode(request.task_data_json)
                    if request.task_data_json
                    else b"{}"
                )
            else:
                data_bytes = (
                    request.task_data_json.encode() if request.task_data_json else b"{}"
                )

            task_data = self.protocol.deserialize(data_bytes)

            # Queue the task
            task_id = self.daemon.queue.enqueue(request.task_type, task_data)
            self.daemon.metrics.task_received()
            self.daemon.metrics.update_queue_size(self.daemon.queue.size())

            return task_daemon_pb2.TaskResponse(task_id=task_id)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.TaskResponse()

    def GetTask(self, request, context):
        """Get task information."""
        try:
            task = self.daemon.queue.get_task(request.task_id)
            if not task:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Task {request.task_id} not found")
                return task_daemon_pb2.TaskInfo()

            # Database stores as JSON strings - parse then re-serialize with protocol
            import json as json_lib

            task_data = json_lib.loads(task["task_data"]) if task["task_data"] else {}
            result = json_lib.loads(task.get("result")) if task.get("result") else None

            # Serialize with protocol and encode for transport
            task_data_bytes = self.protocol.serialize(task_data)
            result_bytes = (
                self.protocol.serialize(result) if result is not None else b""
            )

            if self.protocol_name == "msgpack":
                task_data_str = base64.b64encode(task_data_bytes).decode("ascii")
                result_str = (
                    base64.b64encode(result_bytes).decode("ascii")
                    if result_bytes
                    else ""
                )
            else:
                task_data_str = task_data_bytes.decode("utf-8")
                result_str = result_bytes.decode("utf-8") if result_bytes else ""

            return task_daemon_pb2.TaskInfo(
                id=task["id"],
                task_type=task["task_type"],
                task_data=task_data_str,
                status=task["status"],
                created_at=task["created_at"] or "",
                completed_at=task.get("completed_at") or "",
                attempts=task.get("attempts", 0),
                last_error=task.get("last_error") or "",
                result=result_str,
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.TaskInfo()

    def GetHealth(self, request, context):
        """Get health status."""
        try:
            return task_daemon_pb2.HealthStatus(
                status="healthy",
                queue_size=self.daemon.queue.size(),
                timestamp=datetime.utcnow().isoformat(),
                workers=len(self.daemon._workers),
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.HealthStatus()

    def GetMetrics(self, request, context):
        """Get metrics summary."""
        try:
            metrics = self.daemon.metrics.get_summary()
            return task_daemon_pb2.MetricsSummary(
                tasks_received=metrics.get("tasks_received", 0),
                tasks_processed_success=metrics.get("tasks_processed_success", 0),
                tasks_processed_failed=metrics.get("tasks_processed_failed", 0),
                queue_size=metrics.get("queue_size", 0),
                daemon_healthy=metrics.get("daemon_healthy", False),
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.MetricsSummary()

    def ListTasks(self, request, context):
        """List recent tasks."""
        try:
            import json as json_lib

            limit = request.limit if request.limit > 0 else 20
            tasks = self.daemon.queue.get_recent_tasks(limit)

            task_list = []
            for task in tasks:
                # Database stores as JSON strings - parse then re-serialize with protocol
                task_data = (
                    json_lib.loads(task["task_data"]) if task["task_data"] else {}
                )
                result = (
                    json_lib.loads(task.get("result")) if task.get("result") else None
                )

                # Serialize with protocol and encode for transport
                task_data_bytes = self.protocol.serialize(task_data)
                result_bytes = (
                    self.protocol.serialize(result) if result is not None else b""
                )

                if self.protocol_name == "msgpack":
                    task_data_str = base64.b64encode(task_data_bytes).decode("ascii")
                    result_str = (
                        base64.b64encode(result_bytes).decode("ascii")
                        if result_bytes
                        else ""
                    )
                else:
                    task_data_str = task_data_bytes.decode("utf-8")
                    result_str = result_bytes.decode("utf-8") if result_bytes else ""

                task_list.append(
                    task_daemon_pb2.TaskInfo(
                        id=task["id"],
                        task_type=task["task_type"],
                        task_data=task_data_str,
                        status=task["status"],
                        created_at=task["created_at"] or "",
                        completed_at=task.get("completed_at") or "",
                        attempts=task.get("attempts", 0),
                        last_error=task.get("last_error") or "",
                        result=result_str,
                    )
                )

            return task_daemon_pb2.TaskList(tasks=task_list)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.TaskList()

    def DeleteTask(self, request, context):
        """Delete a task."""
        try:
            success = self.daemon.queue.delete_task(request.task_id)
            if success:
                self.daemon.metrics.update_queue_size(self.daemon.queue.size())
                return task_daemon_pb2.DeleteResponse(
                    success=True, message="Task deleted"
                )
            else:
                return task_daemon_pb2.DeleteResponse(
                    success=False, message="Task not found"
                )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.DeleteResponse(success=False, message=str(e))

    def RedriveTask(self, request, context):
        """Redrive a failed task."""
        try:
            success = self.daemon.queue.redrive_task(request.task_id)
            if success:
                self.daemon.metrics.update_queue_size(self.daemon.queue.size())
                return task_daemon_pb2.RedriveResponse(
                    success=True, message="Task redriven"
                )
            else:
                return task_daemon_pb2.RedriveResponse(
                    success=False, message="Task not found or not failed"
                )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_daemon_pb2.RedriveResponse(success=False, message=str(e))


def serve_grpc(
    daemon: TaskDaemon, port: int = 50051, max_workers: int = 10, protocol: str = "json"
):
    """Start gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    task_daemon_pb2_grpc.add_TaskDaemonServicer_to_server(
        TaskDaemonServicer(daemon, protocol=protocol), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server

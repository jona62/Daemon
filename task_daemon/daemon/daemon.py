"""Main TaskDaemon implementation."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import threading
import time
import logging
import uvicorn
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ..config import DaemonConfig
from ..core.persistent_queue import PersistentQueue
from ..core.queue import Queue
from ..core.metrics import MetricsCollector
from ..core.decorators import get_task_handler, register_handler


class TaskRequest(BaseModel):
    """Request model for queuing tasks."""

    type: str
    data: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Response model for queued tasks."""

    task_id: int


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    queue_size: int
    timestamp: str
    workers: int


class TaskDaemon:
    """Configurable task processing daemon with FastAPI."""

    def __init__(
        self,
        config: Optional[DaemonConfig] = None,
        metrics_registry=None,
        queue: Optional[Queue] = None,
    ):
        self.config = config or DaemonConfig()
        self.queue = queue or PersistentQueue(self.config.db_path)
        self.metrics = MetricsCollector(metrics_registry)
        self.app = FastAPI(title="TaskDaemon", version="0.1.0")
        self._setup_logging()
        self._setup_routes()
        self._workers = []
        self._running = False

    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def _invoke_handler(self, handler, task_data):
        """Invoke handler with proper type conversion for input and output."""
        import inspect
        from pydantic import BaseModel

        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        # No parameters - call with no args
        if not params:
            result = handler()
        # Single parameter - existing behavior
        elif len(params) == 1:
            if task_data is not None:
                expected_type = params[0].annotation
                if expected_type != inspect.Parameter.empty and hasattr(
                    expected_type, "model_validate"
                ):
                    task_input = expected_type.model_validate(task_data)
                    result = handler(task_input)
                else:
                    result = handler(task_data)
            else:
                result = handler(task_data)
        # Multiple parameters
        else:
            if isinstance(task_data, dict):
                # Check if it's positional args format
                if "args" in task_data and len(task_data) == 1:
                    result = handler(*task_data["args"])
                else:
                    # Unpack dict as kwargs
                    result = handler(**task_data)
            else:
                result = handler(task_data)

        # Handle output serialization
        if isinstance(result, BaseModel):
            serialized = result.model_dump()
            self.logger.debug(f"Serialized Pydantic result: {serialized}")
            return serialized
        return result

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            return HealthResponse(
                status="healthy",
                queue_size=self.queue.size(),
                timestamp=datetime.utcnow().isoformat(),
                workers=len(self._workers),
            )

        @self.app.get("/metrics", response_class=PlainTextResponse)
        async def metrics():
            return self.metrics.get_prometheus_metrics()

        @self.app.get("/api/metrics")
        async def api_metrics():
            return self.metrics.get_summary()

        @self.app.post("/queue", response_model=TaskResponse, status_code=200)
        async def enqueue(task_request: TaskRequest):
            try:
                # Use the data field directly, or fall back to empty dict
                task_data = task_request.data or {}

                task_id = self.queue.enqueue(task_request.type, task_data)
                self.metrics.task_received()
                self.metrics.update_queue_size(self.queue.size())
                self.logger.info(f"Task {task_id} queued: {task_request.type}")
                return TaskResponse(task_id=task_id)
            except Exception as e:
                self.logger.error(f"Error enqueueing: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/tasks")
        async def get_tasks(limit: int = 20) -> List[Dict[str, Any]]:
            try:
                return self.queue.get_recent_tasks(limit)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/tasks/{task_id}")
        async def get_task(task_id: int):
            try:
                task = self.queue.get_task(task_id)
                if task:
                    return task
                raise HTTPException(status_code=404, detail="Task not found")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/api/tasks/{task_id}")
        async def delete_task(task_id: int):
            try:
                if self.queue.delete_task(task_id):
                    self.metrics.update_queue_size(self.queue.size())
                    return {"message": "Task deleted"}
                raise HTTPException(status_code=404, detail="Task not found")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/tasks/{task_id}/redrive")
        async def redrive_task(task_id: int):
            try:
                if self.queue.redrive_task(task_id):
                    self.metrics.update_queue_size(self.queue.size())
                    return {"message": "Task redriven"}
                raise HTTPException(
                    status_code=404, detail="Task not found or not failed"
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _worker(self):
        """Worker thread function."""
        self.logger.info("Worker started")
        while self._running:
            try:
                task = self.queue.dequeue()
                if task:
                    task_id, task_type, task_data = task
                    start_time = time.time()

                    try:
                        handler = get_task_handler(task_type)
                        if handler:
                            result = self._invoke_handler(handler, task_data)
                            self.queue.mark_complete(task_id, result)
                            self.logger.info(f"Task {task_id} completed: {result}")
                        else:
                            self.logger.warning(
                                f"No handler for task type: {task_type}"
                            )
                            self.queue.mark_complete(task_id)
                        duration = time.time() - start_time
                        self.metrics.task_processed("success", duration)
                        self.logger.info(f"Task {task_id} completed in {duration:.2f}s")

                    except Exception as e:
                        self.queue.mark_failed(task_id, str(e), self.config.max_retries)
                        self.metrics.task_processed("failed")
                        self.logger.error(f"Task {task_id} failed: {e}")

                    self.metrics.update_queue_size(self.queue.size())
                else:
                    if self.config.worker_sleep > 0.0:
                        time.sleep(self.config.worker_sleep)

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                time.sleep(1)

    def start_workers(self):
        """Start worker threads."""
        self._running = True
        for _ in range(self.config.worker_threads):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self._workers.append(worker)
        self.logger.info(f"Started {self.config.worker_threads} workers")

    def stop_workers(self):
        """Stop worker threads."""
        self._running = False
        self.logger.info("Stopping workers")

    def register_handler(self, handler_func):
        """Register a task handler using function name as task type."""
        register_handler(handler_func)
        task_type = handler_func.__name__
        self.logger.info(f"Registered handler: {task_type}")
        return self

    def run(self, **kwargs):
        """Run the daemon server."""
        self.start_workers()
        self.metrics.set_health(True)

        uvicorn_kwargs = {
            "host": self.config.host,
            "port": self.config.port,
            "log_level": self.config.log_level.lower(),
            **kwargs,
        }

        try:
            uvicorn.run(self.app, **uvicorn_kwargs)
        finally:
            self.stop_workers()
            self.metrics.set_health(False)

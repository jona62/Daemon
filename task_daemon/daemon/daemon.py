"""Main TaskDaemon implementation."""

from flask import Flask, request, jsonify
import threading
import time
import logging
from datetime import datetime
from typing import Optional

from ..config import DaemonConfig
from ..core.queue import PersistentQueue
from ..core.metrics import MetricsCollector
from ..core.decorators import get_task_handler


class TaskDaemon:
    """Configurable task processing daemon with Flask API."""

    def __init__(self, config: Optional[DaemonConfig] = None, metrics_registry=None):
        self.config = config or DaemonConfig()
        self.queue = PersistentQueue(self.config.db_path)
        self.metrics = MetricsCollector(metrics_registry)
        self.app = Flask(__name__)
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

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify(
                {
                    "status": "healthy",
                    "queue_size": self.queue.size(),
                    "timestamp": datetime.utcnow().isoformat(),
                    "workers": len(self._workers),
                }
            )

        @self.app.route("/metrics", methods=["GET"])
        def metrics():
            return self.metrics.get_prometheus_metrics()

        @self.app.route("/api/metrics", methods=["GET"])
        def api_metrics():
            return jsonify(self.metrics.get_summary())

        @self.app.route("/queue", methods=["POST"])
        def enqueue():
            try:
                data = request.get_json()
                task_type = data.get("type", "default")
                task_id = self.queue.enqueue(task_type, data)
                self.metrics.task_received()
                self.metrics.update_queue_size(self.queue.size())
                self.logger.info(f"Task {task_id} queued: {task_type}")
                return jsonify({"task_id": task_id}), 202
            except Exception as e:
                self.logger.error(f"Error enqueueing: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/tasks", methods=["GET"])
        def get_tasks():
            try:
                limit = request.args.get("limit", 20, type=int)
                tasks = self.queue.get_recent_tasks(limit)
                return jsonify(tasks)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/tasks/<int:task_id>", methods=["GET"])
        def get_task(task_id):
            try:
                task = self.queue.get_task(task_id)
                if task:
                    return jsonify(task)
                return jsonify({"error": "Task not found"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
        def delete_task(task_id):
            try:
                if self.queue.delete_task(task_id):
                    self.metrics.update_queue_size(self.queue.size())
                    return jsonify({"message": "Task deleted"}), 200
                return jsonify({"error": "Task not found"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/tasks/<int:task_id>/redrive", methods=["POST"])
        def redrive_task(task_id):
            try:
                if self.queue.redrive_task(task_id):
                    self.metrics.update_queue_size(self.queue.size())
                    return jsonify({"message": "Task redriven"}), 200
                return jsonify({"error": "Task not found or not failed"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500

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
                            result = handler(task_data)
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

    def run(self, **kwargs):
        """Run the daemon server."""
        self.start_workers()
        self.metrics.set_health(True)

        flask_kwargs = {"host": self.config.host, "port": self.config.port, **kwargs}

        try:
            self.app.run(**flask_kwargs)
        finally:
            self.stop_workers()
            self.metrics.set_health(False)

"""Persistent task queue implementation."""

import sqlite3
import json
import threading
import os
from typing import Optional, Tuple, Any, Dict


class PersistentQueue:
    """Thread-safe persistent task queue using SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_db()

    def init_db(self):
        """Initialize database schema. Deletes existing database."""
        # Delete existing database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    task_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    last_error TEXT,
                    result TEXT
                )
            """
            )
            conn.commit()

    def enqueue(self, task_type: str, task_data: Any) -> int:
        """Add task to queue. Returns task ID."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO tasks (task_type, task_data) VALUES (?, ?)",
                    (task_type, json.dumps(task_data)),
                )
                return cursor.lastrowid

    def dequeue(self) -> Optional[Tuple[int, str, Any]]:
        """Get next pending task. Returns (id, task_type, task_data) or None."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, task_type, task_data FROM tasks 
                    WHERE status = 'pending' 
                    ORDER BY id ASC LIMIT 1
                """
                )
                row = cursor.fetchone()
                if row:
                    task_id, task_type, task_data = row
                    conn.execute(
                        "UPDATE tasks SET status = ? WHERE id = ?",
                        ("processing", task_id),
                    )
                    conn.commit()
                    return task_id, task_type, json.loads(task_data)
                return None

    def mark_complete(self, task_id: int, result: Any = None):
        """Mark task as completed (terminal state)."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP, result = ? 
                    WHERE id = ?
                    """,
                    ("completed", json.dumps(result) if result else None, task_id),
                )
                conn.commit()

    def mark_failed(self, task_id: int, error: str, max_retries: int = 3):
        """Mark task as failed, retry if under max attempts."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT attempts FROM tasks WHERE id = ?", (task_id,)
                )
                result = cursor.fetchone()
                if not result:
                    return

                attempts = result[0]
                if attempts >= max_retries:
                    conn.execute(
                        """
                        UPDATE tasks SET status = ?, last_error = ? WHERE id = ?
                    """,
                        ("failed", error, task_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE tasks SET status = ?, attempts = ?, last_error = ? WHERE id = ?
                    """,
                        ("pending", attempts + 1, error, task_id),
                    )
                conn.commit()

    def size(self) -> int:
        """Get number of pending tasks."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status = ?", ("pending",)
            )
            return cursor.fetchone()[0]

    def get_recent_tasks(self, limit: int = 20) -> list:
        """Get recent tasks for monitoring."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, task_type, task_data, status, created_at, completed_at, 
                       attempts, last_error, result
                FROM tasks ORDER BY id DESC LIMIT ?
            """,
                (limit,),
            )
            return [
                dict(zip([col[0] for col in cursor.description], row))
                for row in cursor.fetchall()
            ]

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID with all metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, task_type, task_data, status, created_at, completed_at,
                       attempts, last_error, result
                FROM tasks WHERE id = ?
                """,
                (task_id,),
            )
            row = cursor.fetchone()
            if row:
                return dict(zip([col[0] for col in cursor.description], row))
            return None

    def delete_task(self, task_id: int) -> bool:
        """Delete task from queue. Returns True if task existed."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0

    def redrive_task(self, task_id: int) -> bool:
        """Redrive a failed task by resetting it to pending. Returns True if successful."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE tasks SET status = 'pending', last_error = NULL 
                    WHERE id = ? AND status = 'failed'
                    """,
                    (task_id,),
                )
                conn.commit()
                return cursor.rowcount > 0

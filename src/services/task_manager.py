import uuid
import time
import os
import shutil
from typing import Dict, Optional, Any

from src.utils.logger import logger

class TaskManager:
    _instance = None
    
    # In-memory storage: { task_id: { status, progress, ... } }
    # Production note: Ideally use Redis for this.
    _tasks: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def create_task(cls) -> str:
        """Creates a new task ID and initializes its state."""
        # async with cls._lock:
        task_id = str(uuid.uuid4())
        cls._tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "created_at": time.time(),
            "file_path": None,
            "filename": None,
            "error": None
        }
        logger.info(f"[TaskManager] Task created: {task_id}")
        return task_id

    @classmethod
    async def update_progress(cls, task_id: str, progress: int):
        """Updates the percentage progress of a task."""
        # Not locking here for performance as dict assignment is atomic-ish in CPython, 
        # but in async context with multiple workers specific locking might be needed. 
        # For this MVP, avoiding lock spam on every 1% increment.
        if task_id in cls._tasks:
            cls._tasks[task_id]["progress"] = progress
            cls._tasks[task_id]["status"] = "processing"

    @classmethod
    async def complete_task(cls, task_id: str, file_path: str, filename: str):
        """Marks task as completed and stores key information."""
        # async with cls._lock:
        if task_id in cls._tasks:
            cls._tasks[task_id]["status"] = "completed"
            cls._tasks[task_id]["progress"] = 100
            cls._tasks[task_id]["file_path"] = file_path
            cls._tasks[task_id]["filename"] = filename
            logger.info(f"[TaskManager] Task completed: {task_id}")

    @classmethod
    async def fail_task(cls, task_id: str, error_msg: str):
        """Marks task as failed."""
        # async with cls._lock:
        if task_id in cls._tasks:
            cls._tasks[task_id]["status"] = "failed"
            cls._tasks[task_id]["error"] = error_msg
            logger.error(f"[TaskManager] Task failed: {task_id} - {error_msg}")

    @classmethod
    def get_task(cls, task_id: str) -> Optional[Dict[str, Any]]:
        return cls._tasks.get(task_id)

    @classmethod
    async def cleanup_task(cls, task_id: str):
        """Removes task from memory and deletes temporary file."""
        # async with cls._lock:
        task = cls._tasks.pop(task_id, None)
        if task and task.get("file_path"):
            try:
                path = task["file_path"]
                if os.path.exists(path):
                    os.remove(path)
                    logger.info(f"[TaskManager] Cleaned up file: {path}")
            except Exception as e:
                logger.error(f"[TaskManager] Error cleaning up file for task {task_id}: {e}")

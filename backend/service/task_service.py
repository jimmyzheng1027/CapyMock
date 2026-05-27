from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(StrEnum):
    """Task status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """Progress update for a task."""
    status: TaskStatus
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskResult:
    """Final result of a task."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class TaskService:
    """Generic async task service for long-running operations."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskResult] = {}
        self._progress_queues: dict[str, asyncio.Queue[TaskProgress]] = {}
        self._cancel_tokens: dict[str, asyncio.Event] = {}

    def create_task(self, task_id: str | None = None) -> str:
        """Create a new task and return its ID."""
        task_id = task_id or str(uuid.uuid4())
        self._tasks[task_id] = TaskResult(task_id=task_id, status=TaskStatus.PENDING)
        self._progress_queues[task_id] = asyncio.Queue()
        self._cancel_tokens[task_id] = asyncio.Event()
        return task_id

    def get_task(self, task_id: str) -> TaskResult | None:
        """Get task result by ID."""
        return self._tasks.get(task_id)

    def get_cancel_token(self, task_id: str) -> asyncio.Event:
        """Get cancel token for a task."""
        return self._cancel_tokens.get(task_id, asyncio.Event())

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        """Update task progress."""
        if task_id not in self._progress_queues:
            return

        update = TaskProgress(
            status=TaskStatus.RUNNING,
            progress=progress,
            message=message,
            data=data or {},
        )
        await self._progress_queues[task_id].put(update)

    async def complete_task(self, task_id: str, result: Any) -> None:
        """Mark task as completed with result."""
        if task_id not in self._tasks:
            return

        self._tasks[task_id].status = TaskStatus.COMPLETED
        self._tasks[task_id].result = result
        self._tasks[task_id].completed_at = datetime.utcnow()

        # Send final progress update
        update = TaskProgress(
            status=TaskStatus.COMPLETED,
            progress=1.0,
            message="Task completed",
        )
        await self._progress_queues[task_id].put(update)

    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        if task_id not in self._tasks:
            return

        self._tasks[task_id].status = TaskStatus.FAILED
        self._tasks[task_id].error = error
        self._tasks[task_id].completed_at = datetime.utcnow()

        # Send failure progress update
        update = TaskProgress(
            status=TaskStatus.FAILED,
            progress=0.0,
            message=error,
        )
        await self._progress_queues[task_id].put(update)

    async def cancel_task(self, task_id: str) -> None:
        """Cancel a running task."""
        if task_id not in self._tasks:
            return

        self._cancel_tokens[task_id].set()
        self._tasks[task_id].status = TaskStatus.CANCELLED
        self._tasks[task_id].completed_at = datetime.utcnow()

        # Send cancellation progress update
        update = TaskProgress(
            status=TaskStatus.CANCELLED,
            progress=0.0,
            message="Task cancelled",
        )
        await self._progress_queues[task_id].put(update)

    async def stream_progress(self, task_id: str) -> AsyncIterator[TaskProgress]:
        """Stream progress updates for a task."""
        if task_id not in self._progress_queues:
            return

        queue = self._progress_queues[task_id]

        while True:
            try:
                # Wait for progress update with timeout
                update = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield update

                # Stop streaming on terminal states
                if update.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ):
                    break
            except TimeoutError:
                # Send keepalive
                yield TaskProgress(
                    status=TaskStatus.RUNNING,
                    message="keepalive",
                )
            except Exception as e:
                logger.error(f"Progress stream error: {e}")
                break

    def is_cancelled(self, task_id: str) -> bool:
        """Check if a task has been cancelled."""
        token = self._cancel_tokens.get(task_id)
        return token is not None and token.is_set()


# Global task service instance
task_service = TaskService()

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from service.task_service import TaskStatus, task_service

logger = logging.getLogger(__name__)

router = APIRouter()


class TaskResponse(BaseModel):
    """Response for task submission."""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Response for task status check."""
    task_id: str
    status: str
    progress: float | None = None
    result: dict | None = None
    error: str | None = None


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get task status and result."""
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        progress=1.0 if task.status == TaskStatus.COMPLETED else None,
        result=task.result if task.status == TaskStatus.COMPLETED else None,
        error=task.error,
    )


@router.get("/tasks/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """SSE endpoint for streaming task progress."""
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # If task is already completed, return immediately
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        async def single_event():
            data = {
                "status": task.status.value,
                "progress": 1.0,
                "message": "Task already completed",
            }
            yield f"data: {json.dumps(data)}\n\n"

        return StreamingResponse(
            single_event(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def event_generator() -> AsyncIterator[str]:
        async for update in task_service.stream_progress(task_id):
            data = {
                "status": update.status.value,
                "progress": update.progress,
                "message": update.message,
                "data": update.data,
            }
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    task = task_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    await task_service.cancel_task(task_id)
    return {"status": "ok", "task_id": task_id}

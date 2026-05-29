from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agent.factory import AgentFactory
from api.deps import get_agent_factory
from api.schemas import EventType
from service.task_service import task_service
from storage.session.store import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request to start GitHub analysis."""
    repo_url: str
    session_id: str | None = None


class AnalysisResponse(BaseModel):
    """Response for analysis submission."""
    task_id: str
    status: str


@router.post("/analysis", response_model=AnalysisResponse)
async def submit_analysis(
    request: AnalysisRequest,
    agent_factory: AgentFactory = Depends(get_agent_factory),
):
    """Submit a GitHub repository analysis task."""
    # Create task
    task_id = task_service.create_task()

    # Run analysis in background
    asyncio.create_task(
        _run_analysis(
            task_id=task_id,
            repo_url=request.repo_url,
            session_id=request.session_id,
            agent_factory=agent_factory,
        )
    )

    return AnalysisResponse(task_id=task_id, status="pending")


async def _run_analysis(
    task_id: str,
    repo_url: str,
    session_id: str | None,
    agent_factory: AgentFactory,
):
    """Run GitHub analysis in background."""
    try:
        # Update progress: starting
        await task_service.update_progress(
            task_id, 0.1, "Starting analysis..."
        )

        # Check for cancellation
        if task_service.is_cancelled(task_id):
            return

        # Create a temporary session for analysis if not provided
        if not session_id:
            session_id = f"analysis-{task_id}"
            store = SessionStore()
            store.create("system", session_id, "summary-generator")

        # Update progress: creating agent
        await task_service.update_progress(
            task_id, 0.2, "Preparing analysis agent..."
        )

        # Create agent
        agent = agent_factory.create(
            profile_id="summary-generator",
            session_id=session_id,
            mode="text",
            user_id="system",
        )
        # Update progress: analyzing
        await task_service.update_progress(
            task_id, 0.3, f"Analyzing repository: {repo_url}"
        )

        # Run agent with analysis prompt
        analysis_prompt = f"""Analyze the GitHub repository: {repo_url}

Please provide:
1. Repository overview and structure
2. Main technologies used
3. Key features and functionality
4. Code quality observations
5. Notable patterns or architecture

Use the query_github_analysis tool if available, otherwise provide analysis based on the URL."""

        collected_events = []
        response_text = ""

        async for event in agent.run(analysis_prompt):
            # Check for cancellation
            if task_service.is_cancelled(task_id):
                return

            collected_events.append(event)

            # Update progress based on events
            if event.type == EventType.TOOL_CALL_START:
                await task_service.update_progress(
                    task_id, 0.5, f"Using tool: {event.payload.get('tool_name', 'unknown')}"
                )
            elif event.type == EventType.ASSISTANT_TEXT_DELTA:
                # Update progress periodically
                pass
            elif event.type == EventType.ASSISTANT_TEXT_DONE:
                response_text = event.payload.get("text", "")
                await task_service.update_progress(
                    task_id, 0.9, "Finalizing analysis..."
                )

        # Complete task with result
        result = {
            "repo_url": repo_url,
            "analysis": response_text,
            "events": [e.model_dump() for e in collected_events],
        }

        await task_service.complete_task(task_id, result)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        await task_service.fail_task(task_id, str(e))

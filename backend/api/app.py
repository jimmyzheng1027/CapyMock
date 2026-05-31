from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.context.skill_loader import SkillLoader
from agent.factory import AgentFactory
from trace import init_tracing, is_tracing_enabled, shutdown_tracing
from agent.profile_loader import ProfileLoader
from api.chat import router as sse_router
from api.github_analysis import router as analysis_router
from api.jd_analysis import router as jd_router
from api.resume_analysis import router as resume_router
from api.sessions import router as api_router
from api.tasks import router as tasks_router
from api.ws import router as ws_router
from storage.db.engine import init_db
from storage.session.store import SessionStore
from tool.builtins import TOOLS
from tool.registry import ToolRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Initialize database
    await init_db()

    # Load profiles
    profile_loader = ProfileLoader("config/agents")
    profiles = profile_loader.load_all()
    print(f"Loaded {len(profiles)} agent profiles")

    # Initialize tool registry
    tool_registry = ToolRegistry(tools=TOOLS)
    print(f"Registered {len(tool_registry.all())} tools")

    # Initialize skill loader
    skill_loader = SkillLoader("data/skill")
    skills = skill_loader.load_all()
    print(f"Loaded {len(skills)} skills")

    # Initialize session store
    session_store = SessionStore()

    init_tracing()
    if is_tracing_enabled():
        print("Langfuse tracing enabled")
    else:
        print("Tracing disabled (noop)")

    # Initialize agent factory
    agent_factory = AgentFactory(
        profile_loader=profile_loader,
        tool_registry=tool_registry,
        session_store=session_store,
        skill_loader=skill_loader,
    )

    # Store in app state
    app.state.agent_factory = agent_factory
    app.state.session_store = session_store
    app.state.profile_loader = profile_loader

    yield

    shutdown_tracing()
    print("Shutting down...")


app = FastAPI(
    title="CapyMock API",
    description="AI Interview Preparation Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(sse_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(jd_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "CapyMock API"}

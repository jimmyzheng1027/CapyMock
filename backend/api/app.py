from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.context.skill_loader import SkillLoader
from agent.factory import AgentFactory
from agent.profile_loader import ProfileLoader
from api.github_analysis import router as analysis_router
from api.sessions import router as api_router
from api.chat import router as sse_router
from api.tasks import router as tasks_router
from api.ws import router as ws_router
from config.settings import settings
from storage.db.engine import init_db
from storage.session.store import SessionStore
from tool.builtins import TOOLS
from tool.registry import ToolRegistry
from tracer.langfuse_tracer import LangfuseTracer
from tracer.noop import NoopTracer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Initialize database
    await init_db()

    # Load profiles
    profile_loader = ProfileLoader("backend/config/agents")
    profiles = profile_loader.load_all()
    print(f"Loaded {len(profiles)} agent profiles")

    # Initialize tool registry
    tool_registry = ToolRegistry(tools=TOOLS)
    print(f"Registered {len(tool_registry.all())} tools")

    # Initialize skill loader
    skill_loader = SkillLoader("backend/data/skill")
    skills = skill_loader.load_all()
    print(f"Loaded {len(skills)} skills")

    # Initialize session store
    session_store = SessionStore()

    # Initialize tracer
    if settings.TRACER == "langfuse":
        tracer = LangfuseTracer(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        print("Using Langfuse tracer")
    else:
        tracer = NoopTracer()
        print("Using Noop tracer")

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
    app.state.tracer = tracer

    yield

    # Shutdown
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
app.include_router(ws_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "CapyMock API"}

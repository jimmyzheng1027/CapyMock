from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from storage.db.models import Base

# Ensure parent directory exists
_db_path = os.path.abspath(settings.SQLITE_PATH)
os.makedirs(os.path.dirname(_db_path), exist_ok=True)

# Create async engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{_db_path.replace(os.sep, '/')}",
    echo=False,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize the database, creating tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get a new async database session."""
    async with async_session_factory() as session:
        yield session

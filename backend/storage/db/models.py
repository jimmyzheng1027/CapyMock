from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class Session(Base):
    """Session metadata stored in SQLite."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    profile_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")  # active, paused, completed, abandoned
    mode = Column(String, nullable=False, default="text")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_event_ts = Column(DateTime, nullable=True)
    event_count = Column(Integer, nullable=False, default=0)
    turn_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)  # JSON string of summary dict

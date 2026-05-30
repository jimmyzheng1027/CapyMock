from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
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
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=True, index=True)


class RepoAnalysis(Base):
    """GitHub repository analysis result stored in SQLite."""

    __tablename__ = "repo_analyses"

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    owner = Column(String, nullable=False)
    repo = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, running, done, failed
    result_json = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)


class Resume(Base):
    """Resume stored in SQLite."""

    __tablename__ = "resumes"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    parsed_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

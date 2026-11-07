"""Production database abstraction layer supporting PostgreSQL and SQLite.

Handles connection pooling, engine lifecycle, automatic table migration,
and unified CRUD for decisions, multi-agent checkpoints, and reports.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

try:
    from sqlalchemy import (
        Column,
        Integer,
        BigInteger,
        String,
        Text,
        Numeric,
        DateTime,
        create_engine,
        text,
    )
    from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
    _SQLA_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    _SQLA_AVAILABLE = False
    Base = object
    Column = Integer = BigInteger = String = Text = Numeric = DateTime = None
    create_engine = text = declarative_base = sessionmaker = scoped_session = None

logger = logging.getLogger("venturetwin.db")


# ── Database Models ────────────────────────────────────────────────────────────

if _SQLA_AVAILABLE:
    class DecisionModel(Base):
        __tablename__ = "decisions"

        id = Column(String(64), primary_key=True)
        question = Column(Text, nullable=False)
        decision_type = Column(String(64), nullable=False)
        objective = Column(Text, nullable=True)
        status = Column(String(32), nullable=False, default="pending")
        chosen_strategy = Column(String(128), nullable=True)
        approval_status = Column(String(32), nullable=False, default="pending")
        approved_at = Column(DateTime(timezone=True), nullable=True)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
        updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


    class CheckpointModel(Base):
        __tablename__ = "checkpoints"

        id = Column(BigInteger, primary_key=True, autoincrement=True)
        decision_id = Column(String(64), index=True, nullable=False)
        task_id = Column(String(128), index=True, nullable=False)
        state_json = Column(Text, nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


    class DecisionReportModel(Base):
        __tablename__ = "decision_reports"

        decision_id = Column(String(64), primary_key=True)
        recommendation = Column(Text, nullable=False)
        confidence = Column(String(32), nullable=False)
        primary_strategy = Column(String(128), nullable=False)
        headline_thesis = Column(Text, nullable=False)
        report_json = Column(Text, nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


    class HistoricalCalibrationModel(Base):
        __tablename__ = "historical_calibrations"

        id = Column(BigInteger, primary_key=True, autoincrement=True)
        decision_id = Column(String(64), nullable=True)
        title = Column(String(255), nullable=False)
        category = Column(String(64), nullable=False)
        decision_quarter = Column(String(16), nullable=False)
        predicted_mrr_12 = Column(Numeric(14, 2), nullable=True)
        actual_mrr_12 = Column(Numeric(14, 2), nullable=True)
        percentage_error = Column(Numeric(6, 2), nullable=True)
        most_wrong_assumption = Column(String(128), nullable=True)
        retrospective_summary = Column(Text, nullable=True)
        status = Column(String(32), nullable=False, default="evaluated")
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


    class WorkflowEventModel(Base):
        __tablename__ = "workflow_events"

        id = Column(BigInteger, primary_key=True, autoincrement=True)
        decision_id = Column(String(64), index=True, nullable=False)
        event_type = Column(String(64), nullable=False)
        agent = Column(String(64), nullable=True)
        payload_json = Column(Text, nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

else:
    DecisionModel = CheckpointModel = DecisionReportModel = HistoricalCalibrationModel = WorkflowEventModel = None


# ── Engine & Session Management ────────────────────────────────────────────────

DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent.parent / "data" / "checkpoints.sqlite"


def get_database_url() -> str:
    """Retrieve and normalize database URL from environment."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    # Normalize Supabase / Railway postgres:// to postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


_DATABASE_URL = get_database_url()
_IS_SQLITE = _DATABASE_URL.startswith("sqlite")

if _SQLA_AVAILABLE:
    _engine_kwargs: Dict[str, Any] = {"echo": False}
    if not _IS_SQLITE:
        _engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        })
    else:
        # SQLite single-thread/connect settings
        _engine_kwargs.update({"connect_args": {"check_same_thread": False}})

    engine = create_engine(_DATABASE_URL, **_engine_kwargs)
    SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db_session = scoped_session(SessionFactory)
else:
    engine = None
    SessionFactory = None
    db_session = None


def init_db() -> None:
    """Initialize all schema tables and run auto-migrations."""
    if not _SQLA_AVAILABLE or engine is None:
        logger.info("SQLAlchemy not installed; using standard library SQLite storage.")
        return
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database schema initialized successfully via {'SQLite' if _IS_SQLITE else 'PostgreSQL'}.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise


def get_db_session():
    """Context manager / dependency provider for DB sessions."""
    if not _SQLA_AVAILABLE or SessionFactory is None:
        yield None
        return
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


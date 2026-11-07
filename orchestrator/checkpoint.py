"""Dual-engine workflow state checkpointing and recovery engine.

Supports hosted PostgreSQL in production via DATABASE_URL and local SQLite
fallback for development and testing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from state.shared_state import WorkflowState
from orchestrator.db import CheckpointModel, SessionFactory, engine, _IS_SQLITE, init_db

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "checkpoints.sqlite"


class CheckpointStore:
    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        # If an explicit db_path is given (e.g. in tests), force local SQLite for isolation
        self.explicit_sqlite_path = Path(db_path) if db_path else None
        self.use_hosted_db = self.explicit_sqlite_path is None and not _IS_SQLITE

        if self.explicit_sqlite_path:
            self.explicit_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite(self.explicit_sqlite_path)
        elif not self.use_hosted_db:
            DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite(DEFAULT_DB_PATH)
        else:
            # Hosted PostgreSQL - ensure tables exist
            init_db()

    def _init_sqlite(self, path: Path) -> None:
        conn = sqlite3.connect(path)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision_id TEXT NOT NULL,
                        task_id TEXT NOT NULL,
                        state_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decision ON checkpoints(decision_id);")
        finally:
            conn.close()

    def save_checkpoint(self, state: WorkflowState, task_id: str) -> int:
        """Persist current workflow snapshot after task completion."""
        state_dict = state.model_dump()
        state_json = json.dumps(state_dict)

        if self.use_hosted_db:
            with SessionFactory() as session:
                cp = CheckpointModel(
                    decision_id=state.decision.id,
                    task_id=task_id,
                    state_json=state_json,
                )
                session.add(cp)
                session.commit()
                return int(cp.id)

        # SQLite execution path
        target_path = self.explicit_sqlite_path or DEFAULT_DB_PATH
        conn = sqlite3.connect(target_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO checkpoints (decision_id, task_id, state_json) VALUES (?, ?, ?)",
                    (state.decision.id, task_id, state_json),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def load_latest_checkpoint(self, decision_id: str) -> Optional[WorkflowState]:
        """Retrieve the latest checkpoint for a given decision."""
        if self.use_hosted_db:
            with SessionFactory() as session:
                cp = (
                    session.query(CheckpointModel)
                    .filter(CheckpointModel.decision_id == decision_id)
                    .order_by(CheckpointModel.id.desc())
                    .first()
                )
                if not cp:
                    return None
                return WorkflowState.model_validate(json.loads(cp.state_json))

        # SQLite execution path
        target_path = self.explicit_sqlite_path or DEFAULT_DB_PATH
        conn = sqlite3.connect(target_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT state_json FROM checkpoints 
                WHERE decision_id = ? 
                ORDER BY id DESC LIMIT 1
                """,
                (decision_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            state_data = json.loads(row["state_json"])
            return WorkflowState.model_validate(state_data)
        finally:
            conn.close()

    def list_checkpoints(self, decision_id: str) -> List[Dict[str, Any]]:
        """List checkpoint history for auditability."""
        if self.use_hosted_db:
            with SessionFactory() as session:
                cps = (
                    session.query(CheckpointModel)
                    .filter(CheckpointModel.decision_id == decision_id)
                    .order_by(CheckpointModel.id.asc())
                    .all()
                )
                return [
                    {
                        "id": cp.id,
                        "task_id": cp.task_id,
                        "created_at": cp.created_at.isoformat() if cp.created_at else None,
                    }
                    for cp in cps
                ]

        # SQLite execution path
        target_path = self.explicit_sqlite_path or DEFAULT_DB_PATH
        conn = sqlite3.connect(target_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, task_id, created_at FROM checkpoints WHERE decision_id = ? ORDER BY id ASC",
                (decision_id,),
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def clear(self, decision_id: Optional[str] = None) -> None:
        if self.use_hosted_db:
            with SessionFactory() as session:
                if decision_id:
                    session.query(CheckpointModel).filter(
                        CheckpointModel.decision_id == decision_id
                    ).delete()
                else:
                    session.query(CheckpointModel).delete()
                session.commit()
            return

        # SQLite execution path
        target_path = self.explicit_sqlite_path or DEFAULT_DB_PATH
        conn = sqlite3.connect(target_path)
        try:
            with conn:
                if decision_id:
                    conn.execute("DELETE FROM checkpoints WHERE decision_id = ?", (decision_id,))
                else:
                    conn.execute("DELETE FROM checkpoints")
        finally:
            conn.close()

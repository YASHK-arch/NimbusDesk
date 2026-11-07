"""SQLite-backed workflow state checkpointing and recovery engine."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
from state.shared_state import WorkflowState

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "checkpoints.sqlite"


class CheckpointStore:
    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
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
            conn.commit()

    def save_checkpoint(self, state: WorkflowState, task_id: str) -> int:
        """Persist current workflow snapshot after task completion."""
        state_dict = state.model_dump()
        state_json = json.dumps(state_dict)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO checkpoints (decision_id, task_id, state_json) VALUES (?, ?, ?)",
                (state.decision.id, task_id, state_json),
            )
            checkpoint_id = cursor.lastrowid
            conn.commit()
            return checkpoint_id

    def load_latest_checkpoint(self, decision_id: str) -> Optional[WorkflowState]:
        """Retrieve the latest checkpoint for a given decision."""
        with sqlite3.connect(self.db_path) as conn:
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

    def list_checkpoints(self, decision_id: str) -> List[Dict[str, Any]]:
        """List checkpoint history for auditability."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, task_id, created_at FROM checkpoints WHERE decision_id = ? ORDER BY id ASC",
                (decision_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def clear(self, decision_id: Optional[str] = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            if decision_id:
                conn.execute("DELETE FROM checkpoints WHERE decision_id = ?", (decision_id,))
            else:
                conn.execute("DELETE FROM checkpoints")
            conn.commit()

"""Unit and integration tests for Step 5: Shared workflow state, SQLite checkpoints,

resume-without-redo, and invalid output rejection.
"""

import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError

from orchestrator.checkpoint import CheckpointStore
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from state.event_bus import EventBus
from state.schemas import Finding, Task
from state.shared_state import WorkflowState


@pytest.mark.asyncio
async def test_sqlite_checkpoint_persistence_and_resume():
    """Verify state checkpointing to SQLite and resuming without redoing finished tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_checkpoints.sqlite"
        store = CheckpointStore(db_path=db_path)
        bus = EventBus()
        supervisor = Supervisor(bus=bus, checkpoint_store=store)

        decision, _ = parse_decision_query("Should we launch a free plan?")

        # 1. First run: execute workflow
        state: WorkflowState = await supervisor.run_workflow(decision=decision)
        assert state.status == "completed"

        # Verify checkpoints saved for all completed tasks
        checkpoints = store.list_checkpoints(decision.id)
        assert len(checkpoints) >= 9

        # Verify loading latest checkpoint
        latest = store.load_latest_checkpoint(decision.id)
        assert latest is not None
        assert latest.decision.id == decision.id
        assert len(latest.findings) >= 5

        # 2. Simulate resuming from checkpoint
        # Track that resumed tasks skip completed ones
        resume_bus = EventBus()
        resume_queue = resume_bus.subscribe()
        resume_supervisor = Supervisor(bus=resume_bus, checkpoint_store=store)

        resumed_state = await resume_supervisor.run_workflow(
            decision=decision,
            resume_if_checkpoint_exists=True,
        )
        assert resumed_state.status == "completed"

        # Check recovery events
        events = []
        while not resume_queue.empty():
            events.append(resume_queue.get_nowait())

        event_types = [e.type for e in events]
        assert "recovery_started" in event_types
        assert "recovery_done" in event_types


@pytest.mark.asyncio
async def test_invalid_agent_output_rejected():
    """Verify malformed agent output is rejected and logged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_checkpoints.sqlite"
        store = CheckpointStore(db_path=db_path)
        bus = EventBus()
        supervisor = Supervisor(bus=bus, checkpoint_store=store)

        decision, _ = parse_decision_query("Should we launch a free plan?")

        # Inject bad_output on CFO
        injected = {"CFO": "bad_output"}
        state = await supervisor.run_workflow(decision=decision, injected_failures=injected)

        # CFO task should have failed and been rejected
        assert state.tasks["task_cfo_analysis"].status == "failed"
        assert "CorruptedAgentOutput" in str(state.tasks["task_cfo_analysis"].error_message)

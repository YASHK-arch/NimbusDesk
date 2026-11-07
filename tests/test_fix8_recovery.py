"""Tests for Fix 8: Real failure recovery, persistent failure handling, BackupAnalyst substitution, and failed workflow status."""

import pytest
from httpx import AsyncClient, ASGITransport
from api.app import app
from orchestrator.supervisor import Supervisor
from orchestrator.parser import parse_decision_query
from state.schemas import FailureInjection
from orchestrator.checkpoint import CheckpointStore


@pytest.mark.asyncio
async def test_transient_failure_retries_and_succeeds_without_degraded_banner():
    """Case 1: Transient failure (persist=False, fail_attempts=1). Retries and completes cleanly."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    
    # Growth agent fails on attempt 1 only
    injected = {
        "Growth": FailureInjection(
            agent="Growth",
            failure_type="exception",
            persist=False,
            fail_attempts=1,
        )
    }
    
    state = await supervisor.run_workflow(decision=decision, injected_failures=injected)
    assert state.status == "completed"
    assert state.report is not None
    assert state.report.get("degraded_agent_banner") is None
    assert state.report["sections"]["executive_summary"].get("degraded_agent_banner") is None
    # Growth finding should be present and not degraded
    assert "Growth" in state.findings
    assert state.findings["Growth"].degraded is False


@pytest.mark.asyncio
async def test_persistent_agent_failure_falls_back_to_backup_analyst_and_caps_confidence():
    """Case 2: Persistent agent failure (persist=True). Supervisor falls back to BackupAnalyst, caps confidence at Low."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    
    injected = {
        "Growth": FailureInjection(
            agent="Growth",
            failure_type="exception",
            persist=True,
            fail_attempts=3,
        )
    }
    
    state = await supervisor.run_workflow(decision=decision, injected_failures=injected)
    assert state.status == "completed"
    assert state.report is not None
    
    # Degraded banner must be present
    banner = state.report.get("degraded_agent_banner")
    assert banner is not None
    assert "WARNING: Analysis from" in banner
    assert "Growth" in banner
    assert "capped at Low" in banner
    
    # Confidence must be capped at Low
    assert state.report["confidence"] == "Low"
    assert state.report["sections"]["executive_summary"]["confidence"] == "Low"
    
    # Assumptions must include fallback_degraded provenance
    fallback_asms = [a for a in state.assumptions if a.provenance == "fallback_degraded"]
    assert len(fallback_asms) > 0


@pytest.mark.asyncio
async def test_core_task_failure_marks_workflow_failed_and_rejects_report():
    """Case 3: Injected failure on simulation task. Retries exhausted, workflow status is 'failed', report endpoint rejects."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    
    # Inject persistent failure on simulation task
    injected = {
        "task_simulation_resolution": FailureInjection(
            agent="task_simulation_resolution",
            failure_type="exception",
            persist=True,
            fail_attempts=3,
        )
    }
    
    state = await supervisor.run_workflow(decision=decision, injected_failures=injected)
    assert state.status == "failed"
    assert state.report is None
    
    # Checkpoint must exist in SQLite
    store = CheckpointStore()
    latest_ckpt = store.load_latest_checkpoint(decision.id)
    assert latest_ckpt is not None
    assert latest_ckpt.status == "failed"
    
    # API report endpoint must reject request for failed workflow
    from api.app import _WORKFLOW_STATES
    _WORKFLOW_STATES[decision.id] = state
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/decisions/{decision.id}/report")
        assert resp.status_code in (400, 404, 409)

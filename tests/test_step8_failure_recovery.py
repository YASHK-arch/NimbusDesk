"""Unit and integration tests for Step 8: Failure injection, detection, recovery policy,

and workflow completion.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import app
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from state.event_bus import EventBus


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_mode", ["timeout", "exception", "bad_output"])
async def test_failure_injection_and_recovery_all_modes(failure_mode: str):
    """Verify injecting timeout, exception, or bad_output into an agent still completes the workflow."""
    bus = EventBus()
    queue = bus.subscribe()
    supervisor = Supervisor(bus=bus)

    decision, _ = parse_decision_query("Should we launch a free plan?")
    # Inject into CTO
    injected = {"CTO": failure_mode}

    state = await supervisor.run_workflow(decision=decision, injected_failures=injected)

    # 1. Entire workflow must finish successfully despite fault
    assert state.status == "completed"
    assert "CTO" in state.findings

    # 2. Event stream must reflect failure and recovery
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    event_types = [e.type for e in events]
    assert "agent_failed" in event_types
    assert "recovery_started" in event_types
    assert "recovery_done" in event_types

    # Find the specific agent failure event
    failed_ev = next(e for e in events if e.type == "agent_failed" and e.agent == "CTO")
    assert failed_ev is not None

    recovery_done_ev = next(e for e in events if e.type == "recovery_done")
    assert recovery_done_ev is not None


@pytest.mark.asyncio
async def test_inject_failure_api_endpoint():
    """Verify POST /api/decisions/{id}/inject-failure endpoint registers chaos payloads."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/decisions/dec-12345/inject-failure",
            json={"agent": "Growth", "mode": "timeout"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failure_injected"
        assert data["decision_id"] == "dec-12345"
        assert data["agent"] == "Growth"
        assert data["mode"] == "timeout"

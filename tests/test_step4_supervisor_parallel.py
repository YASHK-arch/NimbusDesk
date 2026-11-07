"""Unit and integration tests for Step 4: Supervisor architecture, parallel execution,

dependency synchronization, and ordered event streaming.
"""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from state.event_bus import EventBus
from state.shared_state import WorkflowState


@pytest.mark.asyncio
async def test_supervisor_parallel_execution_and_timestamps():
    """Verify independent agent tasks execute concurrently in parallel with overlapping timestamps."""
    bus = EventBus()
    supervisor = Supervisor(bus=bus)

    decision, _ = parse_decision_query("Should we launch a free plan?")
    state: WorkflowState = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert len(state.findings) >= 5

    timeline = state.execution_timeline
    assert "task_cfo_analysis" in timeline
    assert "task_growth_analysis" in timeline
    assert "task_cto_analysis" in timeline
    assert "task_customer_analysis" in timeline
    assert "task_product_analysis" in timeline

    # Check timestamps: root tasks should all start almost simultaneously before any downstream tasks
    root_start_times = [
        timeline["task_cfo_analysis"]["start_time"],
        timeline["task_growth_analysis"]["start_time"],
        timeline["task_cto_analysis"]["start_time"],
        timeline["task_customer_analysis"]["start_time"],
        timeline["task_product_analysis"]["start_time"],
    ]

    # Verify that the difference between the earliest and latest start of the 5 parallel tasks is tiny (< 0.05s)
    spread = max(root_start_times) - min(root_start_times)
    assert spread < 0.05, f"Expected parallel dispatch, but start time spread was {spread:.4f}s"

    # Verify downstream task starts strictly after all 5 root tasks finish
    root_finish_times = [
        timeline["task_cfo_analysis"]["finish_time"],
        timeline["task_growth_analysis"]["finish_time"],
        timeline["task_cto_analysis"]["finish_time"],
        timeline["task_customer_analysis"]["finish_time"],
        timeline["task_product_analysis"]["finish_time"],
    ]
    max_root_finish = max(root_finish_times)
    conflict_start = timeline["task_conflict_detection"]["start_time"]
    assert conflict_start >= max_root_finish, (
        f"Downstream conflict task started ({conflict_start}) before all root tasks finished ({max_root_finish})"
    )

    # Verify report generation is strictly the last task
    report_start = timeline["task_report_generation"]["start_time"]
    verification_finish = timeline["task_workflow_verification"]["finish_time"]
    assert report_start >= verification_finish


@pytest.mark.asyncio
async def test_supervisor_event_stream_order():
    """Verify all event types from Section 5 are emitted in order and captured by subscriber queues."""
    bus = EventBus()
    queue = bus.subscribe()
    supervisor = Supervisor(bus=bus)

    decision, _ = parse_decision_query("Should we launch a free plan?")
    await supervisor.run_workflow(decision=decision)

    events = []
    while not queue.empty():
        events.append(queue.get_nowait())

    event_types = [e.type for e in events]

    # Check required event sequence
    assert "task_created" in event_types
    assert "agent_started" in event_types
    assert "finding_posted" in event_types
    assert "conflict_detected" in event_types
    assert "simulation_run" in event_types
    assert "verification_passed" in event_types
    assert "report_ready" in event_types

    # First events should be task_created
    assert event_types[0] == "task_created"
    # Last event should be report_ready
    assert event_types[-1] == "report_ready"

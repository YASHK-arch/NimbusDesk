"""FastAPI backend API for VentureTwin multi-agent coordination engine."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api.graph import get_company_dependency_graph
from orchestrator.checkpoint import CheckpointStore
from orchestrator.decomposer import decompose_decision
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from report.report_builder import render_report_markdown
from state.company import load_company_snapshot, load_seeded_decisions
from state.event_bus import event_bus
from state.schemas import DecisionRecord, FailureInjection, WorkflowEvent
from state.shared_state import WorkflowState

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VentureTwin: SwarmFlow Multi-Agent Coordination Engine",
    description="Operational Digital Twin & Decision Stress-Test Platform for SaaS Pricing and Packaging Decisions",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Runtime state registries
_WORKFLOW_STATES: Dict[str, WorkflowState] = {}
_ACTIVE_SUPERVISORS: Dict[str, Supervisor] = {}
_INJECTED_FAILURES: Dict[str, Dict[str, str]] = {}
_DECISION_HISTORY: List[DecisionRecord] = []
_checkpoint_store = CheckpointStore()


# Request Schemas
class DecisionSubmitRequest(BaseModel):
    question: str = Field(..., json_schema_extra={"example": "Should we launch a free plan?"})


class InjectFailureRequest(BaseModel):
    agent: str = Field(..., json_schema_extra={"example": "CTO"})
    mode: Optional[Literal["timeout", "exception", "bad_output", "corrupt_output"]] = None
    failure_type: Optional[Literal["timeout", "exception", "bad_output", "corrupt_output"]] = None
    persist: bool = False
    fail_attempts: int = 1


class ApprovalRequest(BaseModel):
    action: Literal["approve", "reject", "request_changes"] = "approve"
    chosen_strategy: str = Field(default="Strategy B (Usage Caps)")
    notes: Optional[str] = None


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "VentureTwin",
        "version": "0.1.0",
        "mock_mode": os.getenv("LLM_MOCK_MODE", "true").lower() in ("true", "1", "yes"),
    }


@app.get("/api/health")
async def api_health_check():
    return {
        "status": "ok",
        "service": "VentureTwin Multi-Agent Orchestration Platform",
        "synthetic_data": True,
    }


@app.get("/api/company")
async def get_company():
    """Retrieve synthetic company baseline (NimbusDesk)."""
    snapshot = load_company_snapshot()
    return snapshot.model_dump()


@app.post("/api/decisions")
async def submit_decision(req: DecisionSubmitRequest):
    """Submit a strategic decision, validate query, and start background workflow."""
    decision, is_supported = parse_decision_query(req.question)
    if not is_supported:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_decision_type",
                "message": decision.objective,
                "supported_types": ["free_plan", "price_change"],
            },
        )

    dag = decompose_decision(decision)
    supervisor = Supervisor(checkpoint_store=_checkpoint_store)
    _ACTIVE_SUPERVISORS[decision.id] = supervisor

    # Initial state
    state = WorkflowState(
        decision=decision,
        tasks={t.id: t for t in dag.tasks.values()},
        status="running",
    )
    _WORKFLOW_STATES[decision.id] = state

    # Trigger async background execution
    asyncio.create_task(_run_workflow_background(decision.id, decision, dag, supervisor))

    return {
        "decision_id": decision.id,
        "question": decision.question,
        "type": decision.type,
        "status": "running",
        "plan": dag.to_dict(),
    }


async def _run_workflow_background(decision_id: str, decision, dag, supervisor: Supervisor):
    try:
        injected = _INJECTED_FAILURES.get(decision_id, {})
        final_state = await supervisor.run_workflow(
            decision=decision,
            dag=dag,
            injected_failures=injected,
        )
        _WORKFLOW_STATES[decision_id] = final_state
    except Exception as e:
        logger.error(f"Error during workflow execution {decision_id}: {e}")
        if decision_id in _WORKFLOW_STATES:
            _WORKFLOW_STATES[decision_id].status = "failed"


@app.get("/api/decisions/{id}")
async def get_decision_status(id: str):
    """Fetch live status, DAG execution progress, and agent findings."""
    state = _WORKFLOW_STATES.get(id) or _checkpoint_store.load_latest_checkpoint(id)
    if not state:
        raise HTTPException(status_code=404, detail="Decision workflow not found")

    tasks_summary = [t.model_dump() for t in state.tasks.values()]
    findings_summary = {name: f.model_dump() for name, f in state.findings.items()}

    return {
        "decision_id": state.decision.id,
        "question": state.decision.question,
        "status": state.status,
        "tasks": tasks_summary,
        "findings": findings_summary,
        "has_report": state.report is not None,
    }


@app.get("/api/decisions/{id}/stream")
async def stream_events(id: str):
    """Server-Sent Events (SSE) streaming live telemetry to the UI."""
    async def sse_event_generator() -> AsyncGenerator[str, None]:
        queue = event_bus.subscribe()
        try:
            # Yield initial connection greeting
            init_event = json.dumps({"type": "stream_connected", "decision_id": id, "ts": datetime.now(timezone.utc).isoformat()})
            yield f"data: {init_event}\n\n"

            # Stream real-time events as they occur
            while True:
                try:
                    event: WorkflowEvent = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {json.dumps(event.model_dump())}\n\n"
                    if event.type == "report_ready":
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield f": keep-alive {datetime.now(timezone.utc).isoformat()}\n\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")


@app.post("/api/decisions/{id}/inject-failure")
async def inject_failure(id: str, req: InjectFailureRequest):
    """Chaos hook: inject timeout, exception, or bad_output into an agent or task."""
    f_type = req.failure_type or req.mode or "exception"
    inj = FailureInjection(
        agent=req.agent,
        failure_type=f_type,
        persist=req.persist,
        fail_attempts=req.fail_attempts,
    )
    _INJECTED_FAILURES.setdefault(id, {})[req.agent] = inj
    return {
        "status": "failure_injected",
        "decision_id": id,
        "agent": req.agent,
        "mode": inj.failure_type,
        "failure_type": inj.failure_type,
        "persist": inj.persist,
        "fail_attempts": inj.fail_attempts,
    }


@app.get("/api/decisions/{id}/report")
async def get_decision_report(id: str, format: Optional[str] = "json"):
    """Fetch the consolidated 10-section decision report."""
    state = _WORKFLOW_STATES.get(id) or _checkpoint_store.load_latest_checkpoint(id)
    if not state:
        raise HTTPException(status_code=404, detail="Decision not found")
    if state.status == "failed":
        raise HTTPException(
            status_code=409,
            detail=f"Workflow failed for decision {id}; no final report is available.",
        )
    if not state.report:
        raise HTTPException(status_code=404, detail="Report not ready or decision not found")

    if format == "markdown":
        md = render_report_markdown(state.report)
        return {"markdown": md}

    return state.report


@app.post("/api/decisions/{id}/approve")
async def approve_decision(id: str, req: ApprovalRequest):
    """Human approval gate: store decision record into history with predicted metrics."""
    state = _WORKFLOW_STATES.get(id) or _checkpoint_store.load_latest_checkpoint(id)
    if not state or not state.report:
        raise HTTPException(status_code=400, detail="Cannot approve decision: report is not ready")

    # Find metrics for chosen strategy from scenario table
    scenario_table = state.report["sections"]["scenario_table"]
    chosen_metrics = next((r for r in scenario_table if req.chosen_strategy.lower() in r["strategy"].lower()), scenario_table[0])

    record = DecisionRecord(
        decision_id=id,
        snapshot={
            "question": state.decision.question,
            "company_name": state.report["sections"]["company_position"]["company_name"],
            "baseline_mrr": state.report["sections"]["company_position"]["mrr"],
            "baseline_runway": state.report["sections"]["company_position"]["runway_months"],
        },
        chosen_strategy=req.chosen_strategy,
        predicted_metrics={
            "mrr_month_12": chosen_metrics.get("mrr_month_12_expected"),
            "runway_months_12": chosen_metrics.get("runway_months_12_expected"),
            "net_contribution_12": chosen_metrics.get("net_contribution_12"),
        },
        approved_at=datetime.now(timezone.utc).isoformat(),
        status="awaiting_outcome",
    )
    _DECISION_HISTORY.append(record)

    await event_bus.emit(
        event_type="decision_approved",
        agent="Supervisor",
        payload={"decision_id": id, "chosen_strategy": req.chosen_strategy, "action": req.action},
    )

    return {
        "status": "decision_recorded",
        "action": req.action,
        "record": record.model_dump(),
    }


@app.get("/api/history")
async def get_decision_history():
    """Return past seeded decisions for calibration plus live approved decisions."""
    seeded = load_seeded_decisions()
    live_records = [r.model_dump() for r in _DECISION_HISTORY]

    # Calculate average error across seeded decisions
    errors = [d.get("error_analysis", {}).get("absolute_error_pct", 0.0) for d in seeded]
    avg_error = round(sum(errors) / len(errors), 2) if errors else 0.0

    return {
        "seeded_decisions": seeded,
        "live_approved_decisions": live_records,
        "calibration": {
            "average_absolute_error_pct": avg_error,
            "most_wrong_assumptions": [
                {"assumption": "Marginal CPC saturation", "avg_error": 8.5},
                {"assumption": "Willingness to prepay", "avg_error": 13.5},
                {"assumption": "Pro tier price elasticity", "avg_error": 3.3},
            ],
            "note": "Calibration baseline calculated from seeded demo data.",
        },
    }


@app.get("/api/graph")
async def get_graph():
    """Return company operational dependency graph for React Flow."""
    return get_company_dependency_graph(highlight_affected=True)


# Static SPA mounting for production UI
UI_DIST_DIR = Path(__file__).resolve().parent.parent / "ui" / "dist"
if UI_DIST_DIR.exists() and (UI_DIST_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=UI_DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("health", "docs", "openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = UI_DIST_DIR / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(UI_DIST_DIR / "index.html")


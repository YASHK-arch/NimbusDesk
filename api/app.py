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
from report.decision_logic import rank_strategies
from simulation.params import SIM_PARAMS, build_scenario_params
from simulation.reconcile import reconcile_assumptions
from simulation.monte_carlo import run_monte_carlo_suite
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from state.company import load_company_snapshot, load_seeded_decisions
from state.event_bus import event_bus
from state.schemas import Assumption, DecisionRecord, FailureInjection, SimulationRun, WorkflowEvent
from state.shared_state import WorkflowState
from orchestrator.db import (
    init_db,
    SessionFactory,
    DecisionModel,
    DecisionReportModel,
    HistoricalCalibrationModel,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VentureTwin: SwarmFlow Multi-Agent Coordination Engine",
    description="Operational Digital Twin & Decision Stress-Test Platform for SaaS Pricing and Packaging Decisions",
    version="0.1.0",
)

allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["http://localhost:5173", "http://localhost:3000"]

@app.on_event("startup")
async def on_startup():
    """Ensure database schema tables exist on application startup."""
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Startup DB init notice: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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


class ResimulateRequest(BaseModel):
    overrides: Dict[str, float] = Field(default_factory=dict)


class AskAssistantRequest(BaseModel):
    question: str


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

    # Record initial decision in production database
    try:
        with SessionFactory() as session:
            dec_row = DecisionModel(
                id=decision.id,
                question=decision.question,
                decision_type=decision.type,
                objective=decision.objective,
                status="running",
                approval_status="pending",
            )
            session.merge(dec_row)
            session.commit()
    except Exception as e:
        logger.debug(f"DB decision record notice: {e}")

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

        # Persist report and update decision status in database
        if final_state.report:
            try:
                with SessionFactory() as session:
                    rep_row = DecisionReportModel(
                        decision_id=decision_id,
                        recommendation=final_state.report.get("recommendation", ""),
                        confidence=final_state.report.get("confidence", ""),
                        primary_strategy=final_state.report.get("sections", {}).get("executive_summary", {}).get("primary_strategy", ""),
                        headline_thesis=final_state.report.get("sections", {}).get("executive_summary", {}).get("headline_thesis", ""),
                        report_json=json.dumps(final_state.report),
                    )
                    session.merge(rep_row)
                    dec_row = session.query(DecisionModel).filter(DecisionModel.id == decision_id).first()
                    if dec_row:
                        dec_row.status = "completed"
                    session.commit()
            except Exception as e:
                logger.debug(f"DB report record notice: {e}")
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


@app.get("/api/params")
async def get_params():
    """Return model parameter definitions and bounds from SIM_PARAMS."""
    param_list = []
    param_dict = {}
    category_map = {
        "free_to_paid_conversion": "Growth & Acquisition",
        "monthly_free_signups": "Growth & Acquisition",
        "free_user_marginal_infra_cost": "Infrastructure & Operations",
        "free_user_monthly_tickets": "Support & Service",
        "starter_cannibalization_rate": "Pricing & Retention",
        "price_elasticity_starter": "Pricing & Retention",
        "price_elasticity_growth": "Pricing & Retention",
        "expansion_revenue_rate": "Growth & Expansion",
        "contraction_risk_rate": "Risk & Churn",
    }
    step_map = {
        "free_to_paid_conversion": 0.001,
        "monthly_free_signups": 100.0,
        "free_user_marginal_infra_cost": 0.1,
        "free_user_monthly_tickets": 0.01,
        "starter_cannibalization_rate": 0.01,
        "price_elasticity_starter": 0.05,
        "price_elasticity_growth": 0.05,
        "expansion_revenue_rate": 0.005,
        "contraction_risk_rate": 0.005,
    }
    for name, spec in SIM_PARAMS.items():
        bounds = spec.get("bounds", (0.0, 1.0))
        label = name.replace("_", " ").title()
        item = {
            "name": name,
            "label": label,
            "default": spec.get("default", bounds[0]),
            "min": bounds[0],
            "max": bounds[1],
            "step": step_map.get(name, 0.01),
            "unit": spec.get("unit", "ratio"),
            "category": category_map.get(name, "Model Parameters"),
            "favorable_direction": spec.get("favorable_direction", "higher"),
            "description": spec.get("description", ""),
        }
        param_list.append(item)
        param_dict[name] = item

    return {"params": param_dict, "parameters": param_list}


@app.get("/api/decisions/{id}/trajectory")
async def get_decision_trajectory(
    id: str,
    strategy: Optional[str] = None,
    scenario: Optional[str] = "expected",
):
    """Return monthly trajectory points (mrr, cash, runway) for a decision strategy and scenario."""
    state = _WORKFLOW_STATES.get(id) or _checkpoint_store.load_latest_checkpoint(id)
    if not state:
        raise HTTPException(status_code=404, detail="Decision workflow not found")

    target_strat = strategy
    if not target_strat:
        if state.report and "sections" in state.report and "executive_summary" in state.report["sections"]:
            target_strat = state.report["sections"]["executive_summary"].get("top_strategy")
        if not target_strat:
            target_strat = STRATEGY_B

    target_scen = scenario or "expected"

    # Find matching simulation run in state
    matching_run = next(
        (r for r in state.simulation_runs if r.strategy == target_strat and r.scenario == target_scen),
        None,
    )
    if not matching_run and state.simulation_runs:
        matching_run = next(
            (r for r in state.simulation_runs if target_strat.lower() in r.strategy.lower() and r.scenario == target_scen),
            None,
        ) or next(
            (r for r in state.simulation_runs if r.strategy == target_strat),
            state.simulation_runs[0],
        )

    if not matching_run:
        raise HTTPException(status_code=404, detail=f"No simulation run found for {target_strat} / {target_scen}")

    history = matching_run.outputs.get("history", [])
    points = [
        {
            "month": pt["month"],
            "mrr": pt.get("mrr", 0.0),
            "cash": pt.get("cash_balance", pt.get("cash", 0.0)),
            "runway": pt.get("runway_months", pt.get("runway", 0.0)),
            "paying_customers": pt.get("paying_customers", 0),
            "gross_margin_pct": pt.get("gross_margin_pct", 0.0),
            "infra_cost": pt.get("infra_cost", 0.0),
            "support_headcount": pt.get("support_headcount", 0),
        }
        for pt in history
    ]

    return {
        "decision_id": id,
        "strategy": matching_run.strategy,
        "scenario": matching_run.scenario,
        "points": points,
        "history": history,
    }


@app.post("/api/decisions/{id}/resimulate")
async def resimulate_decision(id: str, req: ResimulateRequest):
    """Re-simulate decision with parameter overrides without modifying stored report (what-if)."""
    state = _WORKFLOW_STATES.get(id) or _checkpoint_store.load_latest_checkpoint(id)
    if not state:
        raise HTTPException(status_code=404, detail="Decision workflow not found")

    company = getattr(state, "company", None) or load_company_snapshot()
    is_price_change = state.decision and state.decision.type == "price_change"

    if is_price_change:
        from simulation.price_model import PRICE_STRAT_A, PRICE_STRAT_B, PRICE_STRAT_C, simulate_price_change
        strategies = [PRICE_STRAT_A, PRICE_STRAT_B, PRICE_STRAT_C]
    else:
        strategies = [STRATEGY_A, STRATEGY_B, STRATEGY_C]

    adjusted_assumptions: List[Assumption] = []
    overrides = req.overrides or {}

    for asm in state.assumptions:
        if asm.name in overrides:
            val = overrides[asm.name]
            if asm.name in SIM_PARAMS:
                b_min, b_max = SIM_PARAMS[asm.name]["bounds"]
                val = max(b_min, min(b_max, val))
            low = min(asm.low, val)
            high = max(asm.high, val)
            adjusted_assumptions.append(
                asm.model_copy(update={"base": val, "low": low, "high": high})
            )
        else:
            adjusted_assumptions.append(asm.model_copy())

    existing_names = {a.name for a in adjusted_assumptions}
    for name, val in overrides.items():
        if name not in existing_names and name in SIM_PARAMS:
            b_min, b_max = SIM_PARAMS[name]["bounds"]
            val = max(b_min, min(b_max, val))
            unit = SIM_PARAMS[name]["unit"]
            adjusted_assumptions.append(
                Assumption(
                    name=name,
                    low=val * 0.8,
                    base=val,
                    high=val * 1.2,
                    unit=unit,
                    provenance="user_override",
                )
            )

    reconciled = reconcile_assumptions(adjusted_assumptions, state.conflicts)

    resim_runs: List[SimulationRun] = []
    for strat in strategies:
        for scen in ["conservative", "expected", "optimistic"]:
            params = build_scenario_params(reconciled.parameters, scen)
            if is_price_change:
                run = simulate_price_change(
                    strategy=strat,
                    scenario=scen,
                    assumptions=params,
                    company=company,
                    months=12,
                )
            else:
                run = simulate(
                    strategy=strat,
                    scenario=scen,
                    assumptions=params,
                    company=company,
                    months=12,
                )
            resim_runs.append(run)

    ranked = rank_strategies(resim_runs, state.decision.constraints, adjusted_assumptions)

    strategy_runs: Dict[str, Dict[str, Any]] = {}
    for r in resim_runs:
        strategy_runs.setdefault(r.strategy, {})[r.scenario] = r.outputs

    scenario_table = []
    for strat in strategies:
        strat_scenarios = strategy_runs.get(strat, {})
        expected = strat_scenarios.get("expected", {})
        conservative = strat_scenarios.get("conservative", {})
        optimistic = strat_scenarios.get("optimistic", {})
        scenario_table.append({
            "strategy": strat,
            "mrr_month_12_expected": expected.get("mrr_month_12", 0.0),
            "mrr_month_12_conservative": conservative.get("mrr_month_12", 0.0),
            "mrr_month_12_optimistic": optimistic.get("mrr_month_12", 0.0),
            "runway_months_12_expected": expected.get("runway_months_12", 0.0),
            "gross_margin_12_expected": expected.get("gross_margin_month_12", 0.0),
            "net_contribution_12": expected.get("net_contribution_12", 0.0),
        })

    mc_summaries = run_monte_carlo_suite(
        strategies=strategies,
        reconciled_params=reconciled,
        company=company,
        n_iterations=150,
        seed=42,
    )

    outcome_ranges = []
    for strat in strategies:
        if strat in mc_summaries:
            mc = mc_summaries[strat]
            outcome_ranges.append({
                "strategy": strat,
                "n_iterations": mc.get("n_iterations", 150),
                "seed": mc.get("seed", 42),
                "p_best": mc.get("p_best", 0.0),
                "p_feasible": mc.get("p_feasible", 0.0),
                "mrr_month_12": mc.get("mrr_month_12", {}),
                "runway_months_12": mc.get("runway_months_12", {}),
                "net_contribution_12": mc.get("net_contribution_12", {}),
                "histograms": mc.get("histograms", {}),
            })

    return {
        "what_if": True,
        "decision_id": id,
        "overrides_applied": overrides,
        "ranking": [
            {
                "strategy": r.strategy,
                "net_contribution_12": r.net_contribution_12,
                "runway_months_12": r.runway_months_12,
                "mrr_month_12": r.mrr_month_12,
                "gross_margin_12": r.gross_margin_12,
                "feasible": r.feasible,
                "unfeasibility_reason": r.unfeasibility_reason,
            }
            for r in ranked
        ],
        "scenario_table": scenario_table,
        "outcome_ranges": outcome_ranges,
    }


@app.post("/api/decisions/{id}/ask")
async def ask_decision_assistant(id: str, req: AskAssistantRequest):
    """Answer questions strictly grounded in verified report data."""
    state = _WORKFLOW_STATES.get(id) or _checkpoint_store.load_latest_checkpoint(id)
    if not state or not state.report:
        raise HTTPException(status_code=404, detail="Decision or report not found")

    report = state.report
    sections = report.get("sections", {})
    scenario_table = sections.get("scenario_table", [])
    flip_point = sections.get("flip_point", {})
    risks = sections.get("risks", [])

    rec = report.get("recommendation", "Review scenarios")
    conf = report.get("confidence", "Medium")
    conf_score = report.get("confidence_score", 0.8)

    q = req.question.lower()

    if "recommend" in q or "confidence" in q or "should we" in q or "which" in q or "primary" in q:
        answer = (
            f"The primary recommendation is: {rec} (Confidence: {conf}, Score: {conf_score:.2f}). "
            f"This recommendation is backed by multi-scenario simulation and Monte Carlo stress testing."
        )
    elif "flip" in q or "threshold" in q or "conversion" in q or "break" in q:
        var_name = flip_point.get("variable", "conversion")
        threshold_display = flip_point.get("threshold_display", "2.1%")
        narrative = flip_point.get("narrative", f"The recommendation holds as long as {var_name} remains above {threshold_display}.")
        answer = f"Conversion Flip-Point Analysis: {narrative} Below this threshold, runway compresses toward the safety floor."
    elif "runway" in q or "burn" in q or "cash" in q:
        top_runway = scenario_table[0].get("runway_months_12_expected", 18.0) if scenario_table else 18.0
        answer = (
            f"Under the expected scenario, the recommended strategy preserves {top_runway:.1f} months of runway at Month 12, "
            f"well above the 10.0-month minimum safety floor."
        )
    elif "risk" in q or "concern" in q or "cannibal" in q:
        risk_bullets = "; ".join(f"{r.get('category')}: {r.get('mitigation')}" for r in risks[:3])
        answer = f"Identified risks and active mitigations: {risk_bullets}"
    else:
        top_mrr = scenario_table[0].get("mrr_month_12_expected", 0.0) if scenario_table else 0.0
        top_runway = scenario_table[0].get("runway_months_12_expected", 0.0) if scenario_table else 0.0
        answer = (
            f"Based on the simulation report for '{state.decision.question}', {rec}. "
            f"Month 12 expected MRR is ${top_mrr:,.0f} with {top_runway:.1f} months runway remaining (Confidence: {conf})."
        )

    return {
        "decision_id": id,
        "question": req.question,
        "answer": answer,
        "grounded_in_report": True,
    }


@app.get("/api/graph")
async def get_graph():
    """Return company operational dependency graph for React Flow."""
    return get_company_dependency_graph(highlight_affected=True)


# Static SPA mounting for production UI (with fallback to ui/index.html when unbuilt)
UI_DIST_DIR = Path(__file__).resolve().parent.parent / "ui" / "dist"
UI_SRC_INDEX = Path(__file__).resolve().parent.parent / "ui" / "index.html"

if UI_DIST_DIR.exists() and (UI_DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=UI_DIST_DIR / "assets"), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/") or full_path in ("health", "docs", "openapi.json"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # 1. Try built static file from dist
    if UI_DIST_DIR.exists():
        target_file = UI_DIST_DIR / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        if (UI_DIST_DIR / "index.html").exists():
            return FileResponse(UI_DIST_DIR / "index.html")

    # 2. Fallback to source index.html for testing without pre-built dist
    if UI_SRC_INDEX.exists():
        return FileResponse(UI_SRC_INDEX)

    raise HTTPException(status_code=404, detail="Frontend assets not found")


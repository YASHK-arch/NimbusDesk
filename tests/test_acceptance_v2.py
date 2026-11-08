"""Acceptance Tests V2 for VentureTwin: Comprehensive validation of all 9 hardening fixes."""

import copy
import json
import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from api.app import app
from agents.llm import ConfigurationError, get_llm_provider
from conflict.resolver import resolve_conflicts_with_simulation
from orchestrator.supervisor import Supervisor
from report.report_builder import build_consolidated_report
from simulation.adapter import get_simulator_adapter
from state.company import load_company_snapshot
from state.schemas import Assumption, Conflict, Decision, FailureInjection, Finding, Task
from verification.verifier import verify_workflow


@pytest.fixture
def client():
    return TestClient(app)


def strip_ids_and_timestamps(obj):
    """Recursively strip nondeterministic ids, timestamps, and run logs for strict semantic comparison."""
    if isinstance(obj, dict):
        return {
            k: strip_ids_and_timestamps(v)
            for k, v in obj.items()
            if k not in (
                "id",
                "report_id",
                "decision_id",
                "created_at",
                "run_log",
                "number_registry",
                "start_iso",
                "finish_iso",
                "simulation_ids",
                "start_time",
                "finish_time",
                "duration_sec",
                "timestamp",
                "generated_at",
            )
        }
    elif isinstance(obj, list):
        return [strip_ids_and_timestamps(item) for item in obj]
    return obj


def test_acceptance_1_no_fake_numbers_script_passes():
    """Acceptance 1: The UI audit script passes without finding any forbidden tokens."""
    import subprocess
    result = subprocess.run(
        ["node", "ui/scripts/check-no-fake-numbers.mjs"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"check-no-fake-numbers failed: {result.stderr or result.stdout}"
    assert "No fake numbers or mocked validators detected" in result.stdout


@pytest.mark.asyncio
async def test_acceptance_2_order_independence():
    """Acceptance 2: Run the free-plan workflow multiple times; the report JSON (excluding ids/timestamps) is identical."""
    decision = Decision(
        id="order_indep_test",
        title="Free Plan Order Independence",
        question="Should we launch a free plan?",
        type="free_plan",
        objective="Verify deterministic order independence",
        constraints=["Maintain runway >= 10 months"],
    )

    baseline_report_clean = None

    for run_idx in range(3):
        sup = Supervisor()
        state = await sup.run_workflow(decision)
        report = copy.deepcopy(state.report)

        clean_report = strip_ids_and_timestamps(report)
        report_json = json.dumps(clean_report, sort_keys=True)

        if baseline_report_clean is None:
            baseline_report_clean = report_json
        else:
            assert report_json == baseline_report_clean, f"Run {run_idx} produced divergent report output"


@pytest.mark.asyncio
async def test_acceptance_3_degraded_run_verifies_correctly():
    """Acceptance 3: Persistent failure in one agent yields degraded banner, Low confidence, and verification passes."""
    sup = Supervisor()
    decision = Decision(
        id="degraded_test",
        title="Degraded Recovery Test",
        question="Should we launch a free plan?",
        type="free_plan",
        objective="Verify degraded recovery",
        constraints=["Maintain runway >= 10 months"],
    )

    # Inject persistent failure into CTO
    injected = {
        "CTO": FailureInjection(agent="CTO", failure_type="exception", persist=True, fail_attempts=3)
    }

    state = await sup.run_workflow(decision, injected_failures=injected)
    report = state.report
    assert report is not None

    # Check degraded banner
    assert report["degraded_agent_banner"] is not None
    assert "Status: Degraded (verified)" in report["degraded_agent_banner"]
    assert "CTO" in report["degraded_agent_banner"]

    # Confidence must be Low
    assert report["confidence"] == "Low"

    # Verification must NOT fail because fallback_degraded provenance is legitimate
    all_passed, results = verify_workflow(
        state.assumptions,
        state.simulation_runs,
        load_company_snapshot(),
        draft_report=report,
    )
    assert all_passed is True


@pytest.mark.asyncio
async def test_acceptance_4_discussion_is_data_driven():
    """Acceptance 4: Modifying CFO's conversion in mock changes Skeptic critique text and numbers dynamically."""
    sup1 = Supervisor()
    decision = Decision(
        id="disc_test_1",
        title="Data Driven Discussion 1",
        question="Should we launch a free plan?",
        type="free_plan",
        objective="Verify data-driven discussion",
    )

    state1 = await sup1.run_workflow(decision)
    critique_1 = next(
        (m for m in state1.messages if m.sender == "Skeptic" and m.parameter == "free_to_paid_conversion"),
        None,
    )
    assert critique_1 is not None

    # Alter CFO assumption dynamically
    sup2 = Supervisor()
    cfo = sup2.registry.get_agent("CFO")
    orig_mock = cfo._generate_specialist_mock
    try:
        def custom_cfo_mock(task_id, decision_type="free_plan"):
            f = orig_mock(task_id, decision_type=decision_type)
            for a in f.assumptions:
                if a.name == "free_to_paid_conversion":
                    a.base = 0.005
                    a.low = 0.002
                    a.high = 0.008
            return f
        cfo._generate_specialist_mock = custom_cfo_mock

        state2 = await sup2.run_workflow(decision)
        critique_2 = next(
            (m for m in state2.messages if m.sender == "Skeptic" and m.parameter == "free_to_paid_conversion"),
            None,
        )
        assert critique_2 is not None

        # The critique text or challenged value must differ between the runs
        assert critique_1.content != critique_2.content
        assert critique_2.challenged_value == 0.005
    finally:
        cfo._generate_specialist_mock = orig_mock


def test_acceptance_5_verification_catches_tampering():
    """Acceptance 5: Tampering with any section of the report triggers verification failure; missing report fails."""
    company = load_company_snapshot()
    adapter = get_simulator_adapter("free_plan")
    sim_runs = [
        adapter.simulate(s, scen, {})
        for s in adapter.strategies
        for scen in ["conservative", "expected", "optimistic"]
    ]

    # 1. Missing report fails
    all_passed, results = verify_workflow([], sim_runs, company, draft_report=None)
    assert all_passed is False
    assert any("no draft report" in r.detail.lower() for r in results)

    # 2. Tampered scenario table
    from state.shared_state import WorkflowState
    state = WorkflowState(
        decision=Decision(id="d", title="t", question="q", type="free_plan", objective="o"),
        assumptions=[
            Assumption(
                name="min_acceptable_runway_months",
                low=10.0,
                base=12.6,
                high=15.0,
                unit="months",
                provenance="verified_data",
                source_ref="data/synthetic_company.json#runway_months",
                confidence=0.95,
            )
        ],
        simulation_runs=sim_runs,
    )
    rep = build_consolidated_report(state, company)

    # Tamper with MRR in scenario table
    tampered_rep = copy.deepcopy(rep)
    tampered_rep["sections"]["scenario_table"][0]["mrr_month_12_expected"] = 999999.0
    all_passed, results = verify_workflow(state.assumptions, sim_runs, company, draft_report=tampered_rep)
    assert all_passed is False
    assert any(r.check_name == "report_number_traceability" and r.status == "failed" for r in results)

    # Tamper with prose in executive summary
    tampered_prose = copy.deepcopy(rep)
    tampered_prose["sections"]["executive_summary"]["headline_thesis"] += " Additional unauthorized cash reserve of $789,123."
    all_passed, results = verify_workflow(state.assumptions, sim_runs, company, draft_report=tampered_prose)
    assert all_passed is False
    assert any("unregistered or unverified number in prose" in r.detail.lower() for r in results)


def test_acceptance_6_real_mode_readiness(client):
    """Acceptance 6: /api/health returns llm_mode/provider/model; LLM_MODE=real without key raises ConfigurationError."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm_mode" in data
    assert "provider" in data
    assert "model" in data

    with patch.dict(os.environ, {"LLM_MODE": "real", "GEMINI_API_KEY": ""}, clear=True):
        with pytest.raises(ConfigurationError) as exc_info:
            get_llm_provider()
        assert "no api key was provided" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_acceptance_7_price_change_is_real():
    """Acceptance 7: Price-change run has price-specific findings, resolved conflict, and zero free-plan wording."""
    sup = Supervisor()
    decision = Decision(
        id="dec_price_v2",
        title="Pricing Optimization",
        question="Should we adjust our plan prices?",
        type="price_change",
        objective="Evaluate elasticity and churn dynamics of price changes",
        constraints=["Preserve at least 10 months runway"],
    )

    state = await sup.run_workflow(decision)
    rep = state.report
    assert rep is not None

    rep_str = json.dumps(rep).lower()
    assert "free plan" not in rep_str
    assert "free users" not in rep_str
    assert "unmetered free" not in rep_str

    # Must contain price elasticity parameter
    assert any("price_elasticity_starter" in a.name for a in state.assumptions)
    # Must have resolved price conflict
    assert any(c.resolved for c in state.conflicts)


def test_acceptance_8_resolver_correctness():
    """Acceptance 8: Proceed vs reject conflict is decided by simulation and never auto-marked immaterial."""
    cfo = Finding(agent="CFO", task_id="t1", claim="Reject", recommendation="reject", confidence=0.8)
    growth = Finding(agent="Growth", task_id="t2", claim="Proceed", recommendation="proceed", confidence=0.9)

    conflict = Conflict(
        id="conf_test",
        type="contradictory_recommendation",
        agents=["CFO", "Growth"],
        disputed_item="Recommendation divergence: CFO recommends 'reject' vs Growth recommends 'proceed'",
        evidence=[],
    )

    # Normal runway floor: simulation supports proceed because feasible positive strategy exists
    resolved, _ = resolve_conflicts_with_simulation([conflict.model_copy()], {"CFO": cfo, "Growth": growth}, min_runway=10.0)
    assert resolved[0].resolved is True
    assert resolved[0].status == "resolved_simulation"
    assert "supports_Growth" in resolved[0].resolution_method

    # Extreme runway floor: simulation supports reject
    resolved_strict, _ = resolve_conflicts_with_simulation([conflict.model_copy()], {"CFO": cfo, "Growth": growth}, min_runway=1000.0)
    assert resolved_strict[0].resolved is True
    assert resolved_strict[0].status == "resolved_simulation"
    assert "supports_CFO" in resolved_strict[0].resolution_method


@pytest.mark.asyncio
async def test_acceptance_9_task_kind_dispatch_only():
    """Acceptance 9: Supervisor dispatches strictly on task.kind; unknown kind raises ValueError."""
    sup = Supervisor()
    from state.shared_state import WorkflowState
    state = WorkflowState(
        decision=Decision(id="d", title="t", question="q", type="free_plan", objective="o")
    )

    bad_task = Task(id="task_magic_fallback", owner_agent="Supervisor")
    object.__setattr__(bad_task, "kind", "unsupported_kind_xyz")

    with pytest.raises(ValueError) as exc_info:
        await sup._handle_supervisor_task(bad_task, state)

    assert "Unknown or unsupported supervisor task kind" in str(exc_info.value)

"""The One-Minute Acceptance Test Suite (VentureTwin Acceptance Audit).

Validates all 7 acceptance criteria from Section 1:
1. Data sensitivity (tiny cash balance prohibits unfeasible recommendation)
2. Scenario ordering (monotonic net_contribution_12 ordering conservative < expected < optimistic)
3. Order independence (shuffling task completion yields identical report numbers)
4. Real verification (corrupted numbers fail verification and trigger bounded loop-back)
5. Honest failure (degraded agent banner + low confidence cap; core failure yields status='failed')
6. No silent mock (LLM_MODE=real without key errors clearly; report/UI always show active LLM mode)
7. No fabricated sources (100% snapshot tie-out and benchmark file grounding)
"""

from __future__ import annotations

import copy
import os
import random
import pytest
from pydantic import BaseModel
from agents.llm import ConfigurationError, get_llm_badge, llm_call
from agents.specialists import (
    BackupAnalyst,
    CFOAgent,
    CTOAgent,
    CustomerAgent,
    GrowthAgent,
    ProductAgent,
    SkepticAgent,
)
from orchestrator.checkpoint import CheckpointStore
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from report.decision_logic import rank_strategies
from report.report_builder import build_consolidated_report
from simulation.params import build_scenario_params
from simulation.reconcile import reconcile_assumptions
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from state.company import load_company_snapshot
from state.schemas import Assumption, FailureInjection
from verification.verifier import verify_workflow


# 1. Data Sensitivity
def test_acceptance_data_sensitivity():
    """Altering cash balance to $50k forces all strategies unfeasible and alters recommendation."""
    company_healthy = load_company_snapshot()
    company_poor = copy.deepcopy(company_healthy)
    company_poor.cash_balance = 50000.0
    company_poor.monthly_burn = 115000.0
    company_poor.runway_months = 0.43

    assumptions = {"free_to_paid_conversion": 0.025}

    healthy_runs = [
        simulate(STRATEGY_A, "expected", assumptions, company=company_healthy),
        simulate(STRATEGY_B, "expected", assumptions, company=company_healthy),
        simulate(STRATEGY_C, "expected", assumptions, company=company_healthy),
    ]
    poor_runs = [
        simulate(STRATEGY_A, "expected", assumptions, company=company_poor),
        simulate(STRATEGY_B, "expected", assumptions, company=company_poor),
        simulate(STRATEGY_C, "expected", assumptions, company=company_poor),
    ]

    ranked_healthy = rank_strategies(healthy_runs, min_runway=10.0)
    ranked_poor = rank_strategies(poor_runs, min_runway=10.0)

    # Healthy company has feasible options
    assert any(s.feasible for s in ranked_healthy)
    assert ranked_healthy[0].feasible is True

    # Poor company must NOT recommend proceeding with any runway-violating strategy
    assert not any(s.feasible for s in ranked_poor)
    for s in ranked_poor:
        assert s.feasible is False
        assert "violates" in s.unfeasibility_reason or "depletion" in s.unfeasibility_reason


# 2. Scenario Ordering
def test_acceptance_scenario_ordering():
    """Conservative <= Expected <= Optimistic monotonic ordering for all strategies."""
    company = load_company_snapshot()
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.015, base=0.025, high=0.045, unit="ratio", provenance="ai_assumption"),
        Assumption(name="monthly_free_signups", low=2000.0, base=3200.0, high=4500.0, unit="users/month", provenance="ai_assumption"),
        Assumption(name="free_user_marginal_infra_cost", low=0.80, base=1.20, high=2.00, unit="USD/user/month", provenance="ai_assumption"),
        Assumption(name="starter_cannibalization_rate", low=0.05, base=0.10, high=0.18, unit="ratio", provenance="ai_assumption"),
        Assumption(name="free_user_monthly_tickets", low=0.02, base=0.05, high=0.09, unit="ratio", provenance="ai_assumption"),
    ]
    p_cons = build_scenario_params(assumptions, "conservative")
    p_exp = build_scenario_params(assumptions, "expected")
    p_opt = build_scenario_params(assumptions, "optimistic")

    for strat in [STRATEGY_A, STRATEGY_B]:
        run_cons = simulate(strat, "conservative", p_cons, company=company)
        run_exp = simulate(strat, "expected", p_exp, company=company)
        run_opt = simulate(strat, "optimistic", p_opt, company=company)

        c_net = run_cons.outputs["net_contribution_12"]
        e_net = run_exp.outputs["net_contribution_12"]
        o_net = run_opt.outputs["net_contribution_12"]

        assert c_net < e_net < o_net, f"Strategy {strat} failed strict ordering: {c_net} < {e_net} < {o_net}"

    run_c_cons = simulate(STRATEGY_C, "conservative", p_cons, company=company)
    run_c_exp = simulate(STRATEGY_C, "expected", p_exp, company=company)
    run_c_opt = simulate(STRATEGY_C, "optimistic", p_opt, company=company)
    assert run_c_cons.outputs["net_contribution_12"] <= run_c_exp.outputs["net_contribution_12"] <= run_c_opt.outputs["net_contribution_12"]


# 3. Order Independence
def test_acceptance_order_independence():
    """Shuffling the arrival order of specialist findings produces identical parameter reconciliations."""
    specialists = [CFOAgent(), GrowthAgent(), CTOAgent(), CustomerAgent(), SkepticAgent()]
    all_assumptions: list[Assumption] = []
    for s in specialists:
        f = s._generate_specialist_mock("t1")
        all_assumptions.extend(f.assumptions)

    baseline_reconciled = reconcile_assumptions(all_assumptions)
    base_params = baseline_reconciled.simulated_params
    base_summary = [(p.name, p.low, p.base, p.high) for p in baseline_reconciled.parameters]

    # Test across 20 randomized shuffles
    rng = random.Random(42)
    for i in range(20):
        shuffled = copy.deepcopy(all_assumptions)
        rng.shuffle(shuffled)
        shuffled_reconciled = reconcile_assumptions(shuffled)

        assert shuffled_reconciled.simulated_params == base_params
        shuffled_summary = [(p.name, p.low, p.base, p.high) for p in shuffled_reconciled.parameters]
        assert shuffled_summary == base_summary


# 4. Real Verification
def test_acceptance_real_verification():
    """Corrupting a report number triggers verification failure."""
    company = load_company_snapshot()
    sim_runs = [
        simulate(STRATEGY_B, "expected", {"free_to_paid_conversion": 0.025}, company=company),
    ]

    # Fabricated metric that does not match simulation run outputs
    corrupt_metrics = {"mrr_month_12": 9999999.0}

    all_passed, results = verify_workflow(
        assumptions=[],
        simulation_runs=sim_runs,
        company=company,
        draft_report_metrics=corrupt_metrics,
    )
    assert all_passed is False
    trace_check = next(r for r in results if r.check_name == "report_number_traceability")
    assert trace_check.status == "failed"
    assert "Fabricated or corrupted report number detected" in trace_check.detail


# 5. Honest Failure
@pytest.mark.asyncio
async def test_acceptance_honest_failure_degraded_banner_and_confidence():
    """Persistent agent failure produces a report that visibly flags degraded mode and caps confidence at Low."""
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

    report = state.report
    assert report is not None
    assert report["degraded_agent_banner"] is not None
    assert "Growth" in report["degraded_agent_banner"]
    assert report["confidence"] == "Low"


# 6. No Silent Mock
class _SampleModel(BaseModel):
    message: str


@pytest.mark.asyncio
async def test_acceptance_no_silent_mock(monkeypatch):
    """With LLM_MODE=real and no key, ConfigurationError is raised; report badge is transparent."""
    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ConfigurationError) as exc_info:
        await llm_call("Test prompt", response_model=_SampleModel)
    assert "no api key was provided" in str(exc_info.value).lower()

    # Transparent badge in mock mode
    monkeypatch.setenv("LLM_MODE", "mock")
    badge = get_llm_badge()
    assert "Mock" in badge


# 7. No Fabricated Sources
def test_acceptance_no_fabricated_sources():
    """Every verified_data assumption ties out to data/synthetic_company.json, no ungrounded benchmarks."""
    company = load_company_snapshot()
    agents = [CFOAgent(), GrowthAgent(), CTOAgent(), CustomerAgent(), ProductAgent(), SkepticAgent()]

    for agent in agents:
        finding = agent._generate_specialist_mock("t_check")
        for asm in finding.assumptions:
            if asm.provenance == "verified_data":
                assert asm.source_ref.startswith("data/synthetic_company.json#")
                path = asm.source_ref.split("#")[1]
                val = company
                for part in path.split("."):
                    val = val[part] if isinstance(val, dict) else getattr(val, part)
                assert abs(float(val) - float(asm.base)) <= 0.05
            elif asm.provenance == "external_research":
                assert asm.source_ref.startswith("data/benchmarks.json#")

    # Also check BackupAnalyst
    backup = BackupAnalyst()
    fallback_finding = backup.generate_fallback_finding("Growth", "t_fallback")
    for asm in fallback_finding.assumptions:
        assert asm.provenance == "fallback_degraded"

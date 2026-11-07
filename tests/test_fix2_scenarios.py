"""Tests for Fix 2: Scenario parameter variation, stress test runs, and Assumption bounds validation."""

import pytest
from pydantic import ValidationError
from simulation.params import SIM_PARAMS, build_scenario_params
from simulation.saas_model import (
    simulate,
    STRATEGY_A,
    STRATEGY_B,
    STRATEGY_C,
)
from state.company import load_company_snapshot
from state.schemas import Assumption
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor


def test_assumption_bounds_validator():
    """Verify that Assumption enforces low <= base <= high."""
    # Valid assumption passes
    valid_asm = Assumption(
        name="free_to_paid_conversion",
        low=0.01,
        base=0.02,
        high=0.03,
        unit="ratio",
        provenance="ai_assumption",
    )
    assert valid_asm.low <= valid_asm.base <= valid_asm.high

    # Invalid: base < low
    with pytest.raises(ValidationError):
        Assumption(
            name="free_to_paid_conversion",
            low=0.05,
            base=0.02,
            high=0.06,
            unit="ratio",
            provenance="ai_assumption",
        )

    # Invalid: high < base
    with pytest.raises(ValidationError):
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.05,
            high=0.03,
            unit="ratio",
            provenance="ai_assumption",
        )


def test_build_scenario_params_divergence():
    """Verify build_scenario_params sets favorable vs unfavorable parameter bounds correctly."""
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.01, base=0.02, high=0.04, unit="ratio", provenance="ai_assumption"),
        Assumption(name="monthly_free_signups", low=2000.0, base=3000.0, high=5000.0, unit="users", provenance="ai_assumption"),
        Assumption(name="free_user_marginal_infra_cost", low=0.80, base=1.20, high=2.50, unit="USD", provenance="ai_assumption"),
        Assumption(name="starter_cannibalization_rate", low=0.05, base=0.10, high=0.20, unit="ratio", provenance="ai_assumption"),
        Assumption(name="free_user_monthly_tickets", low=0.02, base=0.05, high=0.10, unit="tickets/user/mo", provenance="ai_assumption"),
    ]

    conservative = build_scenario_params(assumptions, "conservative")
    expected = build_scenario_params(assumptions, "expected")
    optimistic = build_scenario_params(assumptions, "optimistic")

    # For conversion (favorable = higher), conservative should take low bound
    assert conservative["free_to_paid_conversion"] == 0.01
    assert expected["free_to_paid_conversion"] == 0.02
    assert optimistic["free_to_paid_conversion"] == 0.04

    # For infra cost (favorable = lower), conservative should take high bound
    assert conservative["free_user_marginal_infra_cost"] == 2.50
    assert expected["free_user_marginal_infra_cost"] == 1.20
    assert optimistic["free_user_marginal_infra_cost"] == 0.80


def test_scenario_ordering_conservative_expected_optimistic():
    """Verify conservative < expected < optimistic on net_contribution_12 for strategies with free levers."""
    company = load_company_snapshot()
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.01, base=0.025, high=0.05, unit="ratio", provenance="ai_assumption"),
        Assumption(name="monthly_free_signups", low=2000.0, base=3200.0, high=4500.0, unit="users", provenance="ai_assumption"),
        Assumption(name="free_user_marginal_infra_cost", low=0.80, base=1.20, high=2.00, unit="USD", provenance="ai_assumption"),
        Assumption(name="starter_cannibalization_rate", low=0.05, base=0.10, high=0.18, unit="ratio", provenance="ai_assumption"),
        Assumption(name="free_user_monthly_tickets", low=0.02, base=0.05, high=0.09, unit="tickets/user/mo", provenance="ai_assumption"),
    ]

    p_cons = build_scenario_params(assumptions, "conservative")
    p_exp = build_scenario_params(assumptions, "expected")
    p_opt = build_scenario_params(assumptions, "optimistic")

    for strat in [STRATEGY_A, STRATEGY_B]:
        run_cons = simulate(strat, "conservative", p_cons, company=company)
        run_exp = simulate(strat, "expected", p_exp, company=company)
        run_opt = simulate(strat, "optimistic", p_opt, company=company)

        c_nc = run_cons.outputs["net_contribution_12"]
        e_nc = run_exp.outputs["net_contribution_12"]
        o_nc = run_opt.outputs["net_contribution_12"]

        assert c_nc < e_nc < o_nc, f"Strategy {strat} failed strict ordering: {c_nc} < {e_nc} < {o_nc}"

    # Strategy C does not use free-plan levers, so conservative <= expected <= optimistic
    run_c_cons = simulate(STRATEGY_C, "conservative", p_cons, company=company)
    run_c_exp = simulate(STRATEGY_C, "expected", p_exp, company=company)
    run_c_opt = simulate(STRATEGY_C, "optimistic", p_opt, company=company)
    assert run_c_cons.outputs["net_contribution_12"] <= run_c_exp.outputs["net_contribution_12"] <= run_c_opt.outputs["net_contribution_12"]


@pytest.mark.asyncio
async def test_supervisor_runs_stress_scenarios_matrix():
    """Verify supervisor workflow executes all 3 strategies x 3 scenarios + 3 stress scenarios."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    scenarios_present = {r.scenario for r in state.simulation_runs}
    assert "conservative" in scenarios_present
    assert "expected" in scenarios_present
    assert "optimistic" in scenarios_present
    assert "stress_infra_doubles" in scenarios_present
    assert "stress_conversion_collapse" in scenarios_present
    assert "stress_large_customer_churn" in scenarios_present

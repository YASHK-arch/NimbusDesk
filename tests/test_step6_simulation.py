"""Unit tests for Step 6: Deterministic SaaS dynamics model, Monte Carlo distributions,

tornado sensitivity, and flip-point search.
"""

import pytest
from simulation.monte_carlo import run_monte_carlo
from simulation.saas_model import (
    STRATEGY_A,
    STRATEGY_B,
    STRATEGY_C,
    simulate,
)
from simulation.sensitivity import compute_tornado_sensitivity, find_flip_point
from state.schemas import Assumption


def test_simulation_determinism_and_reproducibility():
    """Verify that simulations produce bit-for-bit identical results for identical seeds."""
    params = {
        "free_to_paid_conversion": 0.025,
        "monthly_free_signups": 3000.0,
        "free_user_marginal_infra_cost": 1.20,
    }
    run1 = simulate(STRATEGY_B, "expected", params, seed=42)
    run2 = simulate(STRATEGY_B, "expected", params, seed=42)

    assert run1.outputs["mrr_month_12"] == run2.outputs["mrr_month_12"]
    assert run1.outputs["runway_months_12"] == run2.outputs["runway_months_12"]
    assert run1.outputs["net_contribution_12"] == run2.outputs["net_contribution_12"]


def test_simulation_metric_coverage():
    """Verify all required metrics are present at 6, 12, and 24 month horizons."""
    params = {"free_to_paid_conversion": 0.03}
    run = simulate(STRATEGY_A, "expected", params)
    out = run.outputs

    assert "mrr_month_6" in out
    assert "mrr_month_12" in out
    assert "mrr_month_24" in out
    assert "gross_margin_month_12" in out
    assert "runway_months_12" in out
    assert "support_headcount_12" in out
    assert "infra_cost_12" in out
    assert "net_contribution_12" in out
    assert len(out["history"]) == 24


def test_simulation_monotonicity():
    """Verify logical monotonicity: higher conversion never lowers MRR."""
    low_conv_params = {"free_to_paid_conversion": 0.015, "monthly_free_signups": 3000.0}
    high_conv_params = {"free_to_paid_conversion": 0.045, "monthly_free_signups": 3000.0}

    run_low = simulate(STRATEGY_B, "expected", low_conv_params)
    run_high = simulate(STRATEGY_B, "expected", high_conv_params)

    assert run_high.outputs["mrr_month_12"] > run_low.outputs["mrr_month_12"]
    assert run_high.outputs["mrr_month_24"] > run_low.outputs["mrr_month_24"]
    assert run_high.outputs["net_contribution_12"] > run_low.outputs["net_contribution_12"]


def test_monte_carlo_distributions():
    """Verify Monte Carlo computes p10 <= p50 <= p90 percentiles reproducibly."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.015,
            base=0.030,
            high=0.050,
            unit="%",
            provenance="external_research",
        ),
        Assumption(
            name="monthly_free_signups",
            low=2000,
            base=3500,
            high=5000,
            unit="users/mo",
            provenance="simulated_estimate",
        ),
    ]

    mc_results = run_monte_carlo(STRATEGY_B, assumptions, n_iterations=100, seed=123)
    mrr_stats = mc_results["mrr_month_12"]

    assert mrr_stats["p10"] <= mrr_stats["p50"] <= mrr_stats["p90"]
    assert mc_results["runway_months_12"]["p10"] <= mc_results["runway_months_12"]["p90"]


def test_tornado_sensitivity_ranking():
    """Verify Tornado sensitivity analysis correctly identifies and ranks top outcome drivers."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.03,
            high=0.06,
            unit="%",
            provenance="external_research",
        ),
        Assumption(
            name="free_user_marginal_infra_cost",
            low=0.80,
            base=1.20,
            high=1.60,
            unit="USD/user/mo",
            provenance="verified_data",
        ),
        Assumption(
            name="starter_cannibalization_rate",
            low=0.05,
            base=0.10,
            high=0.18,
            unit="%",
            provenance="simulated_estimate",
        ),
    ]

    tornado = compute_tornado_sensitivity(STRATEGY_B, assumptions)
    assert len(tornado) == 3
    # Items must be sorted descending by swing
    assert tornado[0]["swing"] >= tornado[1]["swing"] >= tornado[2]["swing"]
    # Conversion should be the top sensitivity driver
    assert tornado[0]["assumption_name"] == "free_to_paid_conversion"


def test_flip_point_search():
    """Verify flip-point search returns a valid threshold and plain language statement."""
    flip = find_flip_point(
        primary_strategy=STRATEGY_B,
        competing_strategy=STRATEGY_C,
        parameter_name="free_to_paid_conversion",
        param_min=0.005,
        param_max=0.060,
    )

    assert "threshold" in flip
    assert 0.005 <= flip["threshold"] <= 0.060
    assert "statement" in flip
    assert "Strategy B (Usage Caps)" in flip["statement"]
    assert "Strategy C" in flip["statement"]
    assert "%" in flip["statement"]


def test_distinct_scenarios_and_ordering():
    """Verify distinct parameter bounds across scenarios yield conservative < expected < optimistic on net_contribution_12."""
    from simulation.params import build_scenario_params

    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.012, base=0.025, high=0.045, unit="ratio", provenance="ai_assumption"),
        Assumption(name="monthly_free_signups", low=2000.0, base=3200.0, high=4500.0, unit="users", provenance="ai_assumption"),
        Assumption(name="free_user_marginal_infra_cost", low=0.80, base=1.20, high=2.00, unit="USD", provenance="ai_assumption"),
        Assumption(name="starter_cannibalization_rate", low=0.05, base=0.10, high=0.18, unit="ratio", provenance="ai_assumption"),
        Assumption(name="free_user_monthly_tickets", low=0.02, base=0.05, high=0.09, unit="tickets/user/mo", provenance="ai_assumption"),
    ]

    p_cons = build_scenario_params(assumptions, "conservative")
    p_exp = build_scenario_params(assumptions, "expected")
    p_opt = build_scenario_params(assumptions, "optimistic")

    # Strategy A & B have free-tier levers and must strictly satisfy conservative < expected < optimistic
    for strat in [STRATEGY_A, STRATEGY_B]:
        run_cons = simulate(strat, "conservative", p_cons)
        run_exp = simulate(strat, "expected", p_exp)
        run_opt = simulate(strat, "optimistic", p_opt)

        c_nc = run_cons.outputs["net_contribution_12"]
        e_nc = run_exp.outputs["net_contribution_12"]
        o_nc = run_opt.outputs["net_contribution_12"]

        assert c_nc < e_nc < o_nc, f"Strategy {strat} ordering failure: {c_nc} < {e_nc} < {o_nc}"

    # Strategy C does not use free-tier levers; satisfies conservative <= expected <= optimistic
    run_c_cons = simulate(STRATEGY_C, "conservative", p_cons)
    run_c_exp = simulate(STRATEGY_C, "expected", p_exp)
    run_c_opt = simulate(STRATEGY_C, "optimistic", p_opt)
    assert run_c_cons.outputs["net_contribution_12"] <= run_c_exp.outputs["net_contribution_12"] <= run_c_opt.outputs["net_contribution_12"]


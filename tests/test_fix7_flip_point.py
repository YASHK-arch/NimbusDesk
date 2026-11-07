"""Tests for Fix 7: Honest flip point calculation, removing midpoint fallback, and robust handling."""

import pytest
from simulation.sensitivity import find_flip_point
from simulation.saas_model import STRATEGY_B, STRATEGY_C, simulate
from state.company import load_company_snapshot


def test_flip_point_exists_and_converges():
    """Verify that when a flip point genuinely exists, exists=True and difference at flip is within tolerance."""
    company = load_company_snapshot()
    result = find_flip_point(
        primary_strategy=STRATEGY_B,
        competing_strategy=STRATEGY_C,
        parameter_name="free_to_paid_conversion",
        param_min=0.005,
        param_max=0.060,
        company=company,
    )

    assert result["exists"] is True
    assert result["flip_value"] is not None
    assert 0.005 <= result["flip_value"] <= 0.060
    assert "flips sign" in result["statement"]

    # At the flip value, net contribution of Strategy B should be very close to zero (sign flip)
    base = {
        "free_to_paid_conversion": result["flip_value"],
        "monthly_free_signups": 3500.0,
        "free_user_marginal_infra_cost": 1.20,
        "starter_cannibalization_rate": 0.12,
        "free_user_monthly_tickets": 0.05,
    }
    run_b = simulate(STRATEGY_B, "test", base, company=company)
    assert abs(run_b.outputs["net_contribution_12"]) < 1000.0, f"Expected outcome near 0 at flip point, got {run_b.outputs['net_contribution_12']}"
    assert abs(result["outcome_at_flip"]) < 1000.0


def test_no_flip_point_in_range_returns_exists_false_without_midpoint_fallback():
    """Verify that when both bounds produce the same sign, exists=False and flip_value is None (no midpoint invention)."""
    company = load_company_snapshot()
    # At conversion 0.035 to 0.060, Strategy B is strictly superior to Strategy C across the whole range
    result = find_flip_point(
        primary_strategy=STRATEGY_B,
        competing_strategy=STRATEGY_C,
        parameter_name="free_to_paid_conversion",
        param_min=0.035,
        param_max=0.060,
        company=company,
    )

    assert result["exists"] is False
    assert result["flip_value"] is None
    assert result["threshold"] is None
    assert "No flip point within tested range" in result["statement"]
    assert result["tested_range"] == [0.035, 0.060]
    assert "outcome_at_low" in result
    assert "outcome_at_high" in result

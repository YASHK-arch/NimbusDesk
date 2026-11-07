"""Tests proving Fix 11: Monte Carlo simulation with stored seeds, probability metrics (p_best, p_feasible),

triangular distribution sampling, outcome ranges in report, and verifier traceability.
"""

from __future__ import annotations

import copy
import pytest
from simulation.monte_carlo import run_monte_carlo_suite
from simulation.params import build_scenario_params
from simulation.reconcile import reconcile_assumptions
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C
from orchestrator.supervisor import Supervisor
from orchestrator.parser import parse_decision_query
from state.schemas import Assumption
from verification.verifier import verify_workflow


def test_monte_carlo_determinism_and_seed_variance():
    """Verify identical seed produces identical percentiles and probabilities, different seed varies."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.015,
            base=0.025,
            high=0.045,
            unit="ratio",
            provenance="simulated_estimate",
            confidence=0.7,
        ),
        Assumption(
            name="monthly_free_signups",
            low=2000.0,
            base=3200.0,
            high=4500.0,
            unit="users/month",
            provenance="simulated_estimate",
            confidence=0.8,
        ),
        Assumption(
            name="free_user_marginal_infra_cost",
            low=0.80,
            base=1.20,
            high=1.80,
            unit="USD/user/month",
            provenance="simulated_estimate",
            confidence=0.75,
        ),
    ]

    reconciled = reconcile_assumptions(assumptions)
    strategies = [STRATEGY_A, STRATEGY_B, STRATEGY_C]

    # Run 1 with seed=42
    results_seed42_a = run_monte_carlo_suite(
        strategies=strategies,
        reconciled_params=reconciled,
        n_iterations=200,
        seed=42,
    )

    # Run 2 with seed=42
    results_seed42_b = run_monte_carlo_suite(
        strategies=strategies,
        reconciled_params=reconciled,
        n_iterations=200,
        seed=42,
    )

    # Run 3 with seed=99
    results_seed99 = run_monte_carlo_suite(
        strategies=strategies,
        reconciled_params=reconciled,
        n_iterations=200,
        seed=99,
    )

    # Determinism test
    assert results_seed42_a[STRATEGY_B]["mrr_month_12"] == results_seed42_b[STRATEGY_B]["mrr_month_12"]
    assert results_seed42_a[STRATEGY_B]["p_best"] == results_seed42_b[STRATEGY_B]["p_best"]
    assert results_seed42_a[STRATEGY_B]["p_feasible"] == results_seed42_b[STRATEGY_B]["p_feasible"]

    # Variance test
    assert results_seed42_a[STRATEGY_B]["mrr_month_12"]["p50"] != results_seed99[STRATEGY_B]["mrr_month_12"]["p50"] or \
           results_seed42_a[STRATEGY_B]["p_best"] != results_seed99[STRATEGY_B]["p_best"]


def test_monte_carlo_p_best_sum_and_monotonicity():
    """Verify p_best sums to ~1 across all strategies, and p10 <= p50 <= p90."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.015,
            base=0.025,
            high=0.045,
            unit="ratio",
            provenance="simulated_estimate",
        ),
        Assumption(
            name="monthly_free_signups",
            low=2000.0,
            base=3200.0,
            high=4000.0,
            unit="users/month",
            provenance="simulated_estimate",
        ),
    ]
    reconciled = reconcile_assumptions(assumptions)
    strategies = [STRATEGY_A, STRATEGY_B, STRATEGY_C]

    results = run_monte_carlo_suite(
        strategies=strategies,
        reconciled_params=reconciled,
        n_iterations=250,
        seed=42,
        min_runway=10.0,
    )

    total_p_best = sum(results[s]["p_best"] for s in strategies)
    assert 0.98 <= total_p_best <= 1.02

    for s in strategies:
        mc = results[s]
        assert 0.0 <= mc["p_feasible"] <= 1.0
        assert 0.0 <= mc["p_best"] <= 1.0

        # Percentile ordering
        mrr = mc["mrr_month_12"]
        assert mrr["p10"] <= mrr["p50"] <= mrr["p90"]

        net = mc["net_contribution_12"]
        assert net["p10"] <= net["p50"] <= net["p90"]

        runway = mc["runway_months_12"]
        assert runway["p10"] <= runway["p50"] <= runway["p90"]


def test_monte_carlo_degenerate_ranges():
    """Verify that low == high degenerate ranges are handled cleanly without divide by zero."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.025,
            base=0.025,
            high=0.025,
            unit="ratio",
            provenance="simulated_estimate",
        ),
        Assumption(
            name="monthly_free_signups",
            low=3000.0,
            base=3000.0,
            high=3000.0,
            unit="users/month",
            provenance="simulated_estimate",
        ),
    ]
    reconciled = reconcile_assumptions(assumptions)
    results = run_monte_carlo_suite(
        strategies=[STRATEGY_B],
        reconciled_params=reconciled,
        n_iterations=50,
        seed=42,
    )
    assert results[STRATEGY_B]["mrr_month_12"]["p10"] == results[STRATEGY_B]["mrr_month_12"]["p90"]


@pytest.mark.asyncio
async def test_supervisor_monte_carlo_end_to_end_and_report():
    """Verify that full supervisor workflow populates state.mc_summaries and report contains outcome ranges."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert state.mc_summaries is not None
    assert STRATEGY_B in state.mc_summaries
    assert "outcome_ranges" in state.report["sections"]

    outcome_ranges = state.report["sections"]["outcome_ranges"]
    assert len(outcome_ranges) == 3
    strat_b_range = next(r for r in outcome_ranges if r["strategy"] == STRATEGY_B)
    assert "p_best" in strat_b_range
    assert "p_feasible" in strat_b_range
    assert "mrr_month_12" in strat_b_range


def test_verifier_catches_corrupted_outcome_ranges():
    """Verify that corrupting a number in outcome_ranges causes verifier traceability to fail."""
    from state.company import load_company_snapshot
    from simulation.saas_model import simulate

    company = load_company_snapshot()
    sim_runs = [
        simulate(STRATEGY_B, "expected", {"free_to_paid_conversion": 0.025}, company=company),
    ]
    mc_summaries = {
        STRATEGY_B: {
            "strategy": STRATEGY_B,
            "seed": 42,
            "p_best": 0.75,
            "p_feasible": 0.95,
            "mrr_month_12": {"p10": 170000.0, "p50": 185000.0, "p90": 200000.0},
            "runway_months_12": {"p10": 11.0, "p50": 13.0, "p90": 15.0},
            "net_contribution_12": {"p10": 80000.0, "p50": 120000.0, "p90": 160000.0},
        }
    }

    report = {
        "sections": {
            "outcome_ranges": [
                {
                    "strategy": STRATEGY_B,
                    "p_best": 0.75,
                    "p_feasible": 0.95,
                    "mrr_month_12_p50": 185000.0,
                    "runway_months_12_p50": 13.0,
                    "net_contribution_12_p50": 999999.0,  # CORRUPTED fabricated number
                }
            ]
        }
    }

    all_passed, results = verify_workflow(
        assumptions=[],
        simulation_runs=sim_runs,
        company=company,
        report_to_check=report,
        mc_summaries=mc_summaries,
    )
    trace_check = next(r for r in results if r.check_name == "report_number_traceability")
    assert trace_check.status == "failed"
    assert "999999" in trace_check.detail

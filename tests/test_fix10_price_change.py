"""Tests for Fix 10: Price-change decision simulation, elasticity modeling, and pricing report generation."""

import pytest
from orchestrator.supervisor import Supervisor
from orchestrator.parser import parse_decision_query
from simulation.price_model import (
    PRICE_STRAT_A,
    PRICE_STRAT_B,
    PRICE_STRAT_C,
    simulate_price_change,
)
from state.company import load_company_snapshot


def test_simulate_price_change_elasticity_mechanics():
    """Verify simulate_price_change adjusts MRR, gross margin, and churn according to price elasticity."""
    company = load_company_snapshot()
    
    # Moderate elasticity: price increase yields higher MRR
    moderate_assumptions = {
        "price_elasticity_starter": 0.40,
        "price_elasticity_growth": 0.30,
        "expansion_revenue_rate": 0.10,
        "contraction_risk_rate": 0.02,
    }
    run_mod = simulate_price_change(
        strategy=PRICE_STRAT_B,
        scenario="expected",
        assumptions=moderate_assumptions,
        company=company,
    )
    # Raising all prices 20% with low elasticity should increase MRR above baseline ($144,005)
    assert run_mod.outputs["mrr_month_12"] > company.mrr
    assert run_mod.outputs["net_retention_12"] >= 0.90

    # Extreme elasticity: price increase causes customer contraction
    extreme_assumptions = {
        "price_elasticity_starter": 1.80,
        "price_elasticity_growth": 1.50,
        "expansion_revenue_rate": 0.01,
        "contraction_risk_rate": 0.15,
    }
    run_ext = simulate_price_change(
        strategy=PRICE_STRAT_B,
        scenario="expected",
        assumptions=extreme_assumptions,
        company=company,
    )
    # Severe churn reduces active customers and net retention
    assert run_ext.outputs["paying_customers_12"] < run_mod.outputs["paying_customers_12"]
    assert run_ext.outputs["net_retention_12"] < run_mod.outputs["net_retention_12"]


@pytest.mark.asyncio
async def test_full_price_change_workflow():
    """Verify end-to-end workflow for 'What if we raise prices 20%?' executes price-specific strategies and builds pricing report."""
    supervisor = Supervisor()
    decision, supported = parse_decision_query("What if we raise prices 20%?")
    assert supported is True
    assert decision.type == "price_change"

    state = await supervisor.run_workflow(decision=decision)
    assert state.status == "completed"
    assert len(state.simulation_runs) >= 3

    # Check strategies present in simulation runs
    sim_strats = {r.strategy for r in state.simulation_runs}
    assert PRICE_STRAT_A in sim_strats
    assert PRICE_STRAT_B in sim_strats
    assert PRICE_STRAT_C in sim_strats

    # Verify report is generated with price-change semantics
    assert state.report is not None
    assert "20%" in state.report["question"]
    assert state.report["sections"]["executive_summary"]["primary_strategy"] in (PRICE_STRAT_A, PRICE_STRAT_B, PRICE_STRAT_C)
    
    # Verify scenario table contains pricing strategies
    scenarios = state.report["sections"]["scenario_table"]
    reported_strats = {s["strategy"] for s in scenarios}
    assert PRICE_STRAT_B in reported_strats

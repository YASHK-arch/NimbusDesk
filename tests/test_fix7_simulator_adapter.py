"""Unit and integration tests for Fix 7: SimulatorAdapter and real price-change workflow."""

import json
import pytest
from orchestrator.decomposer import decompose_decision
from orchestrator.supervisor import Supervisor
from simulation.adapter import (
    FreePlanSimulatorAdapter,
    PriceChangeSimulatorAdapter,
    SimulatorAdapter,
    get_simulator_adapter,
)
from state.schemas import Decision, Finding
from state.shared_state import WorkflowState


def test_simulator_adapter_protocol():
    """Verify that both free-plan and price-change adapters satisfy the SimulatorAdapter protocol."""
    free_adapter = get_simulator_adapter("free_plan")
    price_adapter = get_simulator_adapter("price_change")

    assert isinstance(free_adapter, SimulatorAdapter)
    assert isinstance(price_adapter, SimulatorAdapter)

    assert free_adapter.decision_type == "free_plan"
    assert price_adapter.decision_type == "price_change"
    assert len(free_adapter.strategies) == 3
    assert len(price_adapter.strategies) == 3


@pytest.mark.asyncio
async def test_price_change_workflow_findings_conflicts_and_report():
    """Verify that price change workflow runs with price-specific findings, resolved conflict, and no free-plan wording."""
    supervisor = Supervisor()
    decision = Decision(
        id="dec_price_test",
        title="Price Change Evaluation",
        question="Should we adjust our tier pricing?",
        type="price_change",
        objective="Evaluate elasticity and churn impacts of pricing adjustments",
        constraints=["Preserve at least 10 months runway"],
    )

    state = await supervisor.run_workflow(decision)

    # 1. Findings are price-specific
    cfo_finding = state.findings.get("CFO")
    growth_finding = state.findings.get("Growth")
    customer_finding = state.findings.get("Customer")

    assert cfo_finding is not None
    assert growth_finding is not None
    assert customer_finding is not None

    cfo_params = {a.name for a in cfo_finding.assumptions}
    growth_params = {a.name for a in growth_finding.assumptions}
    assert "price_elasticity_starter" in cfo_params
    assert "price_elasticity_starter" in growth_params

    # 2. Conflict on price_elasticity_starter was detected and resolved
    price_conflicts = [
        c for c in state.conflicts
        if "price_elasticity_starter" in c.disputed_item or "elasticity" in c.disputed_item.lower()
    ]
    assert len(price_conflicts) > 0, "Expected a conflict on price elasticity to be detected"
    assert price_conflicts[0].resolved is True
    assert len(price_conflicts[0].simulation_ids) > 0

    # 3. Report contains zero occurrences of 'free plan', 'free users', or free-plan strategy names
    report = state.report
    assert report is not None
    report_json_str = json.dumps(report).lower()

    assert "free plan" not in report_json_str
    assert "free users" not in report_json_str
    assert "unmetered free" not in report_json_str


@pytest.mark.asyncio
async def test_price_sensitivity_changes_numbers():
    """Verify that changing price_elasticity_starter bounds changes the price simulation outcomes."""
    price_adapter = get_simulator_adapter("price_change")
    strat = price_adapter.strategies[0]

    # Low elasticity scenario
    low_run = price_adapter.simulate(
        strategy=strat,
        scenario="test",
        assumptions={"price_elasticity_starter": 0.20},
    )

    # High elasticity scenario
    high_run = price_adapter.simulate(
        strategy=strat,
        scenario="test",
        assumptions={"price_elasticity_starter": 1.20},
    )

    # Higher elasticity leads to higher churn and thus lower month 12 MRR and net contribution
    assert low_run.outputs["mrr_month_12"] != high_run.outputs["mrr_month_12"]
    assert low_run.outputs["net_contribution_12"] > high_run.outputs["net_contribution_12"]

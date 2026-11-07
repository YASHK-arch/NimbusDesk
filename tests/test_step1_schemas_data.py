"""Unit tests for Step 1: Schemas, synthetic company data, and seeded decisions."""

import pytest
from pydantic import ValidationError

from state.schemas import (
    Assumption,
    CompanySnapshot,
    Conflict,
    Decision,
    DecisionRecord,
    Evidence,
    Finding,
    SimulationRun,
    Task,
    VerificationResult,
    WorkflowEvent,
)
from state.company import load_company_snapshot, load_seeded_decisions


def test_load_company_snapshot():
    """Verify loading and schema validation of NimbusDesk synthetic dataset."""
    snapshot = load_company_snapshot(reload=True)
    assert isinstance(snapshot, CompanySnapshot)
    assert snapshot.name == "NimbusDesk"
    assert snapshot.is_synthetic is True
    assert snapshot.mrr == 144005.0
    assert snapshot.total_paying_customers == 995
    assert len(snapshot.plans) == 3

    # Check plans sum
    plan_mrr_sum = sum(p.mrr for p in snapshot.plans)
    assert plan_mrr_sum == snapshot.mrr

    # Check runway calculation
    assert snapshot.runway_months == pytest.approx(12.6, rel=1e-2)
    assert snapshot.support["headcount"] == 4
    assert snapshot.infra["free_user_marginal_cost_per_month"] == 1.20


def test_load_seeded_decisions():
    """Verify loading of seeded calibration decisions."""
    decisions = load_seeded_decisions()
    assert isinstance(decisions, list)
    assert len(decisions) >= 4
    for dec in decisions:
        assert "id" in dec
        assert "predicted_metrics" in dec
        assert "actual_metrics" in dec
        assert "error_analysis" in dec


def test_assumption_schema_validation():
    """Verify Assumption schema validation and constraints."""
    valid_assumption = Assumption(
        name="free_to_paid_conversion",
        low=0.015,
        base=0.035,
        high=0.055,
        unit="%",
        provenance="simulated_estimate",
        confidence=0.8,
        proposed_by="Growth",
    )
    assert valid_assumption.name == "free_to_paid_conversion"
    assert valid_assumption.confidence == 0.8
    assert valid_assumption.challenged_by_skeptic is False

    # Out of range confidence should fail
    with pytest.raises(ValidationError):
        Assumption(
            name="invalid_confidence",
            low=1.0,
            base=2.0,
            high=3.0,
            unit="USD",
            provenance="verified_data",
            confidence=1.5,  # Invalid: > 1.0
        )


def test_finding_schema_validation():
    """Verify Finding schema with nested assumptions and evidence."""
    ev = Evidence(
        source_type="company_data",
        source_ref="nimbusdesk_q3_financials",
        snippet="Current runway is 12.6 months with $115k monthly net burn.",
    )
    asm = Assumption(
        name="free_user_infra_cost",
        low=0.90,
        base=1.20,
        high=1.80,
        unit="USD/user/mo",
        provenance="verified_data",
        source_ref="infra_table",
    )
    finding = Finding(
        agent="CFO",
        task_id="task_cfo_cost_impact",
        claim="Launching free tier without usage caps creates dangerous runway compression.",
        recommendation="proceed_with_limits",
        assumptions=[asm],
        evidence=[ev],
        confidence=0.85,
        limitations=["Assumes AWS reserved instances cannot be terminated early."],
        status="ok",
    )
    assert finding.agent == "CFO"
    assert len(finding.assumptions) == 1
    assert finding.assumptions[0].low == 0.90
    assert len(finding.evidence) == 1


def test_conflict_and_simulation_schemas():
    """Verify Conflict and SimulationRun models."""
    conflict = Conflict(
        id="conf-001",
        type="contradictory_recommendation",
        agents=["CFO", "Growth"],
        disputed_item="free_to_paid_conversion",
        simulation_ids=["sim-001", "sim-002"],
    )
    assert conflict.resolved is False

    sim = SimulationRun(
        id="sim-001",
        strategy="Strategy B (Usage Caps)",
        scenario="expected",
        parameters={"free_to_paid_pct": 0.03},
        outputs={"mrr_month_12": 182000.0, "runway_months": 15.2},
        seed=42,
    )
    assert sim.outputs["runway_months"] == 15.2

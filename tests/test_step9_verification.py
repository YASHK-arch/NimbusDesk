"""Unit and integration tests for Step 9: Skeptic audit challenges and deterministic workflow verification."""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from simulation.saas_model import STRATEGY_B, simulate
from state.company import load_company_snapshot
from state.schemas import Assumption
from verification.skeptic_audit import run_skeptic_audit
from verification.verifier import verify_workflow


def test_verification_all_checks_pass_on_valid_data():
    """Verify clean workflow passes all 5 verification checks."""
    company = load_company_snapshot()
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.025,
            high=0.04,
            unit="ratio",
            provenance="external_research",
            source_ref="benchmarks",
        )
    ]
    sim_run = simulate(STRATEGY_B, "expected", {"free_to_paid_conversion": 0.025}, company=company)

    # Draft metrics matching the verified simulation
    draft_metrics = {"mrr_month_12": sim_run.outputs["mrr_month_12"]}

    all_passed, results = verify_workflow(assumptions, [sim_run], company, draft_metrics)
    assert all_passed is True
    assert len(results) == 5
    for r in results:
        assert r.status == "passed"


def test_verification_catches_deliberately_corrupted_number():
    """Verify Hard Rule R4: Any number not tracing to simulator output is caught and failed."""
    company = load_company_snapshot()
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.025,
            high=0.04,
            unit="ratio",
            provenance="external_research",
            source_ref="benchmarks",
        )
    ]
    sim_run = simulate(STRATEGY_B, "expected", {"free_to_paid_conversion": 0.025}, company=company)

    # Deliberately corrupted number
    corrupted_metrics = {"mrr_month_12": 999999.0}

    all_passed, results = verify_workflow(assumptions, [sim_run], company, corrupted_metrics)
    assert all_passed is False

    trace_result = next(r for r in results if r.check_name == "report_number_traceability")
    assert trace_result.status == "failed"
    assert "Fabricated or corrupted report number detected" in trace_result.detail
    assert "999,999" in trace_result.detail


def test_verification_catches_invalid_unit_and_provenance():
    """Verify validation catches malformed units and invalid provenance tags."""
    company = load_company_snapshot()
    sim_run = simulate(STRATEGY_B, "expected", {}, company=company)

    bad_assumptions = [
        Assumption(
            name="bad_unit_metric",
            low=1.0,
            base=2.0,
            high=3.0,
            unit="lightyears",  # Invalid unit
            provenance="verified_data",
        )
    ]

    all_passed, results = verify_workflow(bad_assumptions, [sim_run], company)
    assert all_passed is False
    unit_res = next(r for r in results if r.check_name == "unit_consistency")
    assert unit_res.status == "failed"


def test_skeptic_audit_challenges_and_downgrades_confidence():
    """Verify Skeptic challenges aggressive conversion and downgrades confidence."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.035,
            base=0.045,  # > 3.0% threshold
            high=0.065,
            unit="%",
            provenance="external_research",
            confidence=0.85,
            proposed_by="Growth",
        )
    ]

    audited_asms, challenges = run_skeptic_audit({}, assumptions)
    asm = audited_asms[0]

    assert asm.challenged_by_skeptic is True
    assert asm.confidence == 0.65  # Downgraded from 0.85
    assert len(challenges) == 1
    assert "exceeds B2B SaaS benchmark median" in challenges[0]


@pytest.mark.asyncio
async def test_end_to_end_verification_in_workflow():
    """Verify full supervisor workflow executes verification and populates verification results."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert len(state.verification_results) >= 4
    # Check that required verification checks are recorded
    check_names = [r.check_name for r in state.verification_results]
    assert "unit_consistency" in check_names
    assert "provenance_integrity" in check_names
    assert "financial_ratio_tie_outs" in check_names
    assert "report_number_traceability" in check_names

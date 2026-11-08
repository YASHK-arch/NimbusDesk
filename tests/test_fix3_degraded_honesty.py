"""Tests for Fix 3: Degraded-agent handling, verifier provenance acceptance, and report honesty."""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from state.company import load_company_snapshot
from state.schemas import Assumption
from verification.verifier import verify_workflow


def test_verifier_accepts_fallback_degraded_with_bounded_confidence():
    """Verify that verifier provenance check accepts fallback_degraded when confidence <= 0.30."""
    company = load_company_snapshot()
    valid_degraded = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.02,
            high=0.03,
            unit="ratio",
            provenance="fallback_degraded",
            source_ref="fallback: BackupAnalyst conservative default",
            confidence=0.25,
        )
    ]
    all_passed, results = verify_workflow(valid_degraded, [], company)
    prov_res = next(r for r in results if r.check_name == "provenance_integrity")
    assert prov_res.status == "passed"


def test_verifier_rejects_fallback_degraded_with_unbounded_confidence():
    """Verify that verifier rejects fallback_degraded when confidence > 0.30."""
    company = load_company_snapshot()
    invalid_degraded = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.02,
            high=0.03,
            unit="ratio",
            provenance="fallback_degraded",
            source_ref="fallback: BackupAnalyst conservative default",
            confidence=0.85,
        )
    ]
    all_passed, results = verify_workflow(invalid_degraded, [], company)
    prov_res = next(r for r in results if r.check_name == "provenance_integrity")
    assert prov_res.status == "failed"
    assert "confidence must be <= 0.3" in prov_res.detail


@pytest.mark.asyncio
async def test_end_to_end_degraded_workflow_verifies_and_displays_status():
    """Verify persistent agent failure results in verified degraded status and low confidence."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    injected = {"CTO": {"failure_type": "exception", "persist": True}}
    state = await supervisor.run_workflow(decision=decision, injected_failures=injected)

    assert state.status == "completed"
    # Verification passed despite degraded agent
    prov_res = next(r for r in state.verification_results if r.check_name == "provenance_integrity")
    assert prov_res.status == "passed"

    # Report honesty
    exec_summary = state.report["sections"]["executive_summary"]
    assert exec_summary["status"] == "Degraded (verified)"
    assert state.report["confidence"] == "Low"
    assert "Degraded (verified)" in exec_summary["degraded_agent_banner"]

"""Tests for Fix 6: NumberRegistry, prose scanner, strict non-vacuous verifier checks, and meaningful loop-back."""

import pytest
from state.company import load_company_snapshot
from state.schemas import Assumption, CompanySnapshot, Decision, SimulationRun, VerificationResult
from state.shared_state import WorkflowState
from orchestrator.supervisor import Supervisor
from report.report_builder import build_consolidated_report, NumberRegistry
from verification.verifier import verify_workflow


def test_no_report_fails_report_dependent_checks():
    company = load_company_snapshot()
    all_passed, results = verify_workflow(
        assumptions=[],
        simulation_runs=[],
        company=company,
        draft_report=None,
    )
    assert not all_passed
    res_map = {r.check_name: r for r in results}
    assert res_map["scenario_ordering"].status == "failed"
    assert "no draft report" in res_map["scenario_ordering"].detail.lower()
    assert res_map["required_sections_present"].status == "failed"
    assert "no draft report" in res_map["required_sections_present"].detail.lower()
    assert res_map["report_number_traceability"].status == "failed"
    assert "no draft report" in res_map["report_number_traceability"].detail.lower()


def test_required_sections_fails_on_empty_content():
    company = load_company_snapshot()
    # A report with empty scenario_table
    fake_report = {
        "sections": {
            "executive_summary": {"recommendation": "Proceed"},
            "company_position": {"mrr": 100000},
            "scenario_table": [], # Empty list!
            "outcome_ranges": [{"strategy": "A"}],
            "conflicts": [],
            "sensitivity_tornado": [{"param": "conversion"}],
            "flip_point": {"exists": False},
            "assumption_ledger": [{"name": "conv"}],
            "risks": [{"risk": "infra"}],
            "verification_summary": {},
            "execution_plan": [{"step": "launch"}],
            "run_log": [{"event": "start"}],
        }
    }
    all_passed, results = verify_workflow(
        assumptions=[],
        simulation_runs=[],
        company=company,
        draft_report=fake_report,
    )
    res_map = {r.check_name: r for r in results}
    assert res_map["required_sections_present"].status == "failed"
    assert "scenario_table" in res_map["required_sections_present"].detail


def test_number_registry_present_and_traces_all_sections():
    company = load_company_snapshot()
    state = WorkflowState(
        decision=Decision(id="d1", title="Free plan", question="Should we launch?", type="free_plan", objective="Evaluate feasibility"),
        simulation_runs=[
            SimulationRun(
                id="sim_a_exp",
                strategy="Strategy A (Free Tier as Acquisition Engine)",
                scenario="expected",
                parameters={},
                seed=42,
                outputs={"mrr_month_12": 160000.0, "net_contribution_12": 45000.0, "min_runway_months": 15.0}
            ),
            SimulationRun(
                id="sim_a_con",
                strategy="Strategy A (Free Tier as Acquisition Engine)",
                scenario="conservative",
                parameters={},
                seed=42,
                outputs={"mrr_month_12": 140000.0, "net_contribution_12": 25000.0, "min_runway_months": 12.0}
            ),
            SimulationRun(
                id="sim_a_opt",
                strategy="Strategy A (Free Tier as Acquisition Engine)",
                scenario="optimistic",
                parameters={},
                seed=42,
                outputs={"mrr_month_12": 180000.0, "net_contribution_12": 65000.0, "min_runway_months": 18.0}
            ),
        ]
    )
    report = build_consolidated_report(state, company)
    assert "number_registry" in report
    registry = report["number_registry"]
    assert len(registry) > 0

    # Tamper with a number in the scenario table
    tampered_report = dict(report)
    tampered_report["sections"]["scenario_table"][0]["mrr_month_12_expected"] = 999999.0

    all_passed, results = verify_workflow(
        state.assumptions,
        state.simulation_runs,
        company,
        draft_report=tampered_report,
    )
    res_map = {r.check_name: r for r in results}
    assert res_map["report_number_traceability"].status == "failed"


def test_prose_scan_detects_unregistered_fabricated_number():
    company = load_company_snapshot()
    state = WorkflowState(
        decision=Decision(id="d1", title="Free plan", question="Should we launch?", type="free_plan", objective="Evaluate feasibility"),
        simulation_runs=[
            SimulationRun(
                id="sim_a_exp",
                strategy="Strategy A (Free Tier as Acquisition Engine)",
                scenario="expected",
                parameters={},
                seed=42,
                outputs={"mrr_month_12": 160000.0, "net_contribution_12": 45000.0, "min_runway_months": 15.0}
            )
        ]
    )
    report = build_consolidated_report(state, company)
    # Inject fabricated percentage into headline thesis
    report["sections"]["executive_summary"]["headline_thesis"] = "We anticipate a fabricated 88.7% growth burst."

    all_passed, results = verify_workflow(
        state.assumptions,
        state.simulation_runs,
        company,
        draft_report=report,
    )
    res_map = {r.check_name: r for r in results}
    assert res_map["report_number_traceability"].status == "failed"
    assert "88.7" in res_map["report_number_traceability"].detail

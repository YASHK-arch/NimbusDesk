"""Unit and integration tests for Step 10: Consolidated decision report generation and Markdown export."""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from report.report_builder import build_consolidated_report, render_report_markdown


@pytest.mark.asyncio
async def test_end_to_end_report_builder_10_sections():
    """Verify an end-to-end workflow run builds a 10-section JSON report and Markdown deliverable."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert state.report is not None

    report = state.report
    assert report["decision_id"] == decision.id
    assert report["synthetic_badge"] is True
    assert "SIMULATION DISCLAIMER" in report["disclaimer"]

    # Verify all 10 required sections are present
    sections = report["sections"]
    required_sections = [
        "executive_summary",
        "company_position",
        "scenario_table",
        "conflicts",
        "sensitivity_tornado",
        "flip_point",
        "assumption_ledger",
        "risks",
        "verification_summary",
        "execution_plan",
        "run_log",
    ]
    for sec_name in required_sections:
        assert sec_name in sections, f"Missing section: {sec_name}"

    # Verify numbers in scenario table trace to simulation runs (Hard Rule R4)
    scenario_table = sections["scenario_table"]
    assert len(scenario_table) == 3  # Strategies A, B, C

    sim_mrrs = {round(r.outputs.get("mrr_month_12", 0), 2) for r in state.simulation_runs}
    for row in scenario_table:
        expected_mrr = round(row["mrr_month_12_expected"], 2)
        assert expected_mrr in sim_mrrs, f"Report number {expected_mrr} does not trace to any simulator run"

    # Verify Markdown rendering
    md = render_report_markdown(report)
    assert isinstance(md, str)
    assert "# VentureTwin Decision Stress-Test Report" in md
    assert "Strategy Scenario Comparison" in md
    assert "Disagreements & Simulation-Based Resolutions" in md
    assert "Sensitivity Analysis (Tornado) & Flip-Point" in md
    assert "Assumption Ledger & Provenance" in md
    assert "Verification Summary" in md
    assert "SIMULATION DISCLAIMER" in md

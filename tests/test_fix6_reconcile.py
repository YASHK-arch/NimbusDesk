"""Tests for Fix 6: Deterministic assumption reconciliation, order independence, and clean simulated parameter filtering in tornado."""

import random
import pytest
from simulation.reconcile import reconcile_assumptions, ReconciledParams
from simulation.sensitivity import compute_tornado_sensitivity
from simulation.params import SIM_PARAMS
from simulation.saas_model import STRATEGY_B
from state.schemas import Assumption, Conflict
from state.company import load_company_snapshot


def test_reconciliation_order_independence_under_20_shuffles():
    """Verify that shuffling the order of findings/assumptions 20 times produces bit-for-bit identical reconciled parameters."""
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.010, base=0.015, high=0.022, unit="ratio", provenance="ai_assumption", proposed_by="CFO", confidence=0.8),
        Assumption(name="free_to_paid_conversion", low=0.035, base=0.045, high=0.065, unit="ratio", provenance="ai_assumption", proposed_by="Growth", confidence=0.7),
        Assumption(name="monthly_free_signups", low=2500.0, base=3200.0, high=5000.0, unit="users", provenance="verified_data", proposed_by="Growth", confidence=0.9),
        Assumption(name="free_user_marginal_infra_cost", low=0.90, base=1.20, high=1.80, unit="USD", provenance="verified_data", proposed_by="CTO", confidence=0.85),
        Assumption(name="starter_cannibalization_rate", low=0.06, base=0.12, high=0.20, unit="ratio", provenance="ai_assumption", proposed_by="CFO", confidence=0.75),
        Assumption(name="free_user_monthly_tickets", low=0.03, base=0.05, high=0.08, unit="tickets/user/mo", provenance="verified_data", proposed_by="Customer", confidence=0.8),
        # Non-simulated context assumptions
        Assumption(name="min_acceptable_runway_months", low=10.0, base=12.6, high=15.0, unit="months", provenance="verified_data", proposed_by="CFO", confidence=0.95),
        Assumption(name="feature_gate_conversion_multiplier", low=1.1, base=1.35, high=1.6, unit="multiplier", provenance="ai_assumption", proposed_by="Product", confidence=0.7),
    ]

    base_reconciled = reconcile_assumptions(assumptions, conflicts=[])

    rng = random.Random(42)
    for _ in range(20):
        shuffled = list(assumptions)
        rng.shuffle(shuffled)
        reconciled = reconcile_assumptions(shuffled, conflicts=[])

        assert reconciled.simulated_params == base_reconciled.simulated_params
        assert [p.name for p in reconciled.parameters] == [p.name for p in base_reconciled.parameters]
        assert [p.base for p in reconciled.parameters] == [p.base for p in base_reconciled.parameters]


def test_tornado_contains_only_simulated_params_and_no_duplicates():
    """Verify compute_tornado_sensitivity only tests de-duplicated parameters in SIM_PARAMS."""
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.015, base=0.025, high=0.045, unit="ratio", provenance="ai_assumption", proposed_by="CFO"),
        Assumption(name="free_to_paid_conversion", low=0.020, base=0.030, high=0.050, unit="ratio", provenance="ai_assumption", proposed_by="Growth"),
        Assumption(name="monthly_free_signups", low=2500.0, base=3200.0, high=5000.0, unit="users", provenance="verified_data", proposed_by="Growth"),
        # Non-simulated params
        Assumption(name="min_acceptable_runway_months", low=10.0, base=12.6, high=15.0, unit="months", provenance="verified_data", proposed_by="CFO"),
        Assumption(name="feature_gate_conversion_multiplier", low=1.1, base=1.35, high=1.6, unit="multiplier", provenance="ai_assumption", proposed_by="Product"),
    ]
    company = load_company_snapshot()
    reconciled = reconcile_assumptions(assumptions, conflicts=[])

    tornado = compute_tornado_sensitivity(STRATEGY_B, reconciled=reconciled, company=company)
    tornado_names = [t["assumption_name"] for t in tornado]

    # No duplicates
    assert len(tornado_names) == len(set(tornado_names))

    # All items must be valid SIM_PARAMS
    for name in tornado_names:
        assert name in SIM_PARAMS, f"Tornado contains non-simulated parameter '{name}'"

    # Non-simulated parameters must not be present
    assert "min_acceptable_runway_months" not in tornado_names
    assert "feature_gate_conversion_multiplier" not in tornado_names


def test_report_builder_renders_contested_and_context_sections():
    """Verify report_builder correctly formats simulated parameters with contested badge and operational context sub-table."""
    from state.shared_state import WorkflowState
    from state.schemas import Decision, Finding
    from report.report_builder import build_consolidated_report, render_report_markdown
    from simulation.saas_model import simulate

    company = load_company_snapshot()
    decision = Decision(id="dec_test", question="Should we launch a free plan?", type="free_plan", objective="Evaluate free tier")
    state = WorkflowState(decision=decision)
    
    # 2 conflicting assumptions with no overlap -> contested
    a1 = Assumption(name="free_to_paid_conversion", low=0.010, base=0.015, high=0.020, unit="ratio", provenance="ai_assumption", proposed_by="CFO", confidence=0.8)
    a2 = Assumption(name="free_to_paid_conversion", low=0.035, base=0.045, high=0.065, unit="ratio", provenance="ai_assumption", proposed_by="Growth", confidence=0.7)
    ctx = Assumption(name="dev_time_months", low=2.0, base=3.0, high=4.0, unit="months", provenance="ai_assumption", proposed_by="CTO", confidence=0.9)
    state.assumptions = [a1, a2, ctx]
    
    # Add minimal sim run so report builds
    state.simulation_runs = [
        simulate(STRATEGY_B, scenario="expected", assumptions={"free_to_paid_conversion": 0.025}, company=company),
    ]

    report = build_consolidated_report(state, company=company)
    assert "context_assumptions" in report["sections"]
    assert any(ca["name"] == "dev_time_months" for ca in report["sections"]["context_assumptions"])
    
    # Verify contested parameter in ledger
    conv_entry = next(p for p in report["sections"]["assumption_ledger"] if p["name"] == "free_to_paid_conversion")
    assert conv_entry["contested"] is True
    assert set(conv_entry["contributing_agents"]) == {"CFO", "Growth"}

    # Check markdown rendering
    md = render_report_markdown(report)
    assert "## 5. Assumption Ledger & Provenance" in md
    assert "### Simulated Parameters" in md
    assert "`CONTESTED`" in md
    assert "### Operational Context" in md
    assert "`dev_time_months`" in md


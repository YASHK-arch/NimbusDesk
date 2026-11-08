"""Tests proving Fix 1: Simulation Workspace API endpoints, trajectory queries,

what-if resimulation, report-grounded Q&A assistant, and Monte Carlo histograms.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from api.app import app
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from simulation.monte_carlo import run_monte_carlo_suite
from simulation.reconcile import reconcile_assumptions
from simulation.saas_model import STRATEGY_B
from state.schemas import Assumption


@pytest.mark.asyncio
async def test_get_params_endpoint():
    """Verify GET /api/params returns the full SIM_PARAMS dictionary with metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/params")
        assert resp.status_code == 200
        data = resp.json()
        assert "params" in data
        params = data["params"]
        assert "free_to_paid_conversion" in params
        conv = params["free_to_paid_conversion"]
        assert conv["unit"] == "ratio"
        assert "min" in conv and "max" in conv and "default" in conv
        assert "favorable_direction" in conv
        assert "description" in conv


@pytest.mark.asyncio
async def test_get_decision_trajectory_endpoint():
    """Verify GET /api/decisions/{id}/trajectory returns monthly trajectory points from simulation runs."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)
    assert state.status == "completed"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/decisions/{decision.id}/trajectory",
            params={"strategy": STRATEGY_B, "scenario": "expected"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision_id"] == decision.id
        assert data["strategy"] == STRATEGY_B
        assert data["scenario"] == "expected"
        assert "history" in data
        assert len(data["history"]) >= 12
        m1 = data["history"][0]
        assert "month" in m1 and "mrr" in m1 and "cash_balance" in m1 and "runway_months" in m1


@pytest.mark.asyncio
async def test_post_resimulate_what_if_endpoint():
    """Verify POST /api/decisions/{id}/resimulate accepts parameter overrides and returns what-if scenarios without overwriting stored report."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)
    original_rec = state.report["recommendation"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "overrides": {
                "free_to_paid_conversion": 0.045,
                "monthly_free_signups": 4000.0,
            }
        }
        resp = await client.post(f"/api/decisions/{decision.id}/resimulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["what_if"] is True
        assert "scenario_table" in data
        assert "outcome_ranges" in data
        assert "overrides_applied" in data
        assert data["overrides_applied"]["free_to_paid_conversion"] == 0.045

        # Check stored report was NOT modified
        rep_resp = await client.get(f"/api/decisions/{decision.id}/report")
        assert rep_resp.status_code == 200
        assert rep_resp.json()["recommendation"] == original_rec


@pytest.mark.asyncio
async def test_post_ask_assistant_endpoint_grounded_in_report():
    """Verify POST /api/decisions/{id}/ask answers questions using existing report data only."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ask about recommendation
        resp = await client.post(
            f"/api/decisions/{decision.id}/ask",
            json={"question": "What is the primary recommendation and confidence?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert state.report["recommendation"] in data["answer"] or "Strategy" in data["answer"]

        # 2. Ask about scenarios
        resp2 = await client.post(
            f"/api/decisions/{decision.id}/ask",
            json={"question": "Compare the scenarios for the top strategy."},
        )
        assert resp2.status_code == 200
        assert "mrr" in resp2.json()["answer"].lower() or "runway" in resp2.json()["answer"].lower()


def test_monte_carlo_distribution_histograms():
    """Verify run_monte_carlo_suite calculates deterministic histogram bins and counts."""
    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.015,
            base=0.025,
            high=0.045,
            unit="ratio",
            provenance="simulated_estimate",
        )
    ]
    reconciled = reconcile_assumptions(assumptions)
    results = run_monte_carlo_suite(
        strategies=[STRATEGY_B],
        reconciled_params=reconciled,
        n_iterations=100,
        seed=42,
    )
    b_res = results[STRATEGY_B]
    assert "histograms" in b_res
    hist = b_res["histograms"]
    assert "mrr_month_12" in hist
    assert "net_contribution_12" in hist
    mrr_hist = hist["mrr_month_12"]
    assert "bins" in mrr_hist and "counts" in mrr_hist
    assert len(mrr_hist["counts"]) > 0
    assert sum(mrr_hist["counts"]) == 100

"""Integration tests for Step 11: Full end-to-end API lifecycle via HTTP calls alone."""

import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from api.app import app


@pytest.mark.asyncio
async def test_full_api_workflow_lifecycle():
    """Verify entire workflow end-to-end using only FastAPI endpoints:

    submit -> check status -> stream -> fetch report -> approve -> verify history.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/company
        comp_resp = await client.get("/api/company")
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        assert comp_data["name"] == "NimbusDesk"
        assert comp_data["is_synthetic"] is True

        # 2. GET /api/graph
        graph_resp = await client.get("/api/graph")
        assert graph_resp.status_code == 200
        graph_data = graph_resp.json()
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) >= 7

        # 3. POST /api/decisions with unsupported question
        bad_resp = await client.post("/api/decisions", json={"question": "Should we move office to Paris?"})
        assert bad_resp.status_code == 400
        bad_data = bad_resp.json()
        assert "unsupported_decision_type" in str(bad_data)

        # 4. POST /api/decisions with valid question
        submit_resp = await client.post(
            "/api/decisions",
            json={"question": "Should we launch a free plan?"},
        )
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        dec_id = submit_data["decision_id"]
        assert dec_id.startswith("dec-")
        assert "plan" in submit_data
        assert len(submit_data["plan"]["nodes"]) >= 9

        # 5. Wait for background task to complete (poll GET /api/decisions/{id})
        max_wait = 10
        completed = False
        for _ in range(max_wait):
            await asyncio.sleep(0.15)
            status_resp = await client.get(f"/api/decisions/{dec_id}")
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                if s_data["status"] == "completed" and s_data["has_report"]:
                    completed = True
                    break

        assert completed is True, "Workflow did not complete in background within timeout"

        # 6. GET /api/decisions/{id}/report (JSON)
        report_resp = await client.get(f"/api/decisions/{dec_id}/report")
        assert report_resp.status_code == 200
        report = report_resp.json()
        assert report["decision_id"] == dec_id
        assert "Strategy B (Usage Caps)" in report["recommendation"]
        assert "scenario_table" in report["sections"]

        # 7. GET /api/decisions/{id}/report?format=markdown
        md_resp = await client.get(f"/api/decisions/{dec_id}/report?format=markdown")
        assert md_resp.status_code == 200
        assert "# VentureTwin Decision Stress-Test Report" in md_resp.json()["markdown"]

        # 8. POST /api/decisions/{id}/approve
        approve_resp = await client.post(
            f"/api/decisions/{dec_id}/approve",
            json={"action": "approve", "chosen_strategy": "Strategy B (Usage Caps)"},
        )
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["status"] == "decision_recorded"
        assert approve_data["record"]["status"] == "awaiting_outcome"
        assert approve_data["record"]["chosen_strategy"] == "Strategy B (Usage Caps)"

        # 9. GET /api/history (seeded + newly approved)
        hist_resp = await client.get("/api/history")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert len(hist_data["seeded_decisions"]) >= 4
        assert len(hist_data["live_approved_decisions"]) >= 1
        live_dec_ids = [d["decision_id"] for d in hist_data["live_approved_decisions"]]
        assert dec_id in live_dec_ids
        assert hist_data["calibration"]["average_absolute_error_pct"] > 0

"""Tests for Fix 5: Real-mode readiness, cassette hardening, provider/model config, and analysis independence."""

import os
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from pydantic import BaseModel
from fastapi.testclient import TestClient

from api.app import app
from agents.llm import (
    get_llm_mode,
    get_llm_provider,
    get_llm_model,
    get_llm_badge,
    ConfigurationError,
    llm_call,
    compute_cassette_hash,
)
from orchestrator.supervisor import Supervisor
from state.shared_state import WorkflowState, Decision, Finding, Assumption


class DummyModel(BaseModel):
    message: str


def test_health_endpoints_return_mode_provider_model():
    client = TestClient(app)
    with patch.dict(os.environ, {"LLM_MODE": "mock", "LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-2.0-flash"}):
        resp1 = client.get("/health")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["llm_mode"] == "mock"
        assert data1["provider"] == "gemini"
        assert data1["model"] == "gemini-2.0-flash"

        resp2 = client.get("/api/health")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["llm_mode"] == "mock"
        assert data2["provider"] == "gemini"
        assert data2["model"] == "gemini-2.0-flash"


def test_real_mode_missing_model_raises_configuration_error():
    with patch.dict(os.environ, {
        "LLM_MODE": "real",
        "LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "fake_key",
        "GEMINI_MODEL": "",
    }, clear=False):
        # Removing GEMINI_MODEL
        os.environ.pop("GEMINI_MODEL", None)
        with pytest.raises(ConfigurationError) as exc_info:
            get_llm_model()
        assert "Set GEMINI_MODEL to a currently supported model ID" in str(exc_info.value)


def test_gemini_uses_header_not_query_param():
    from agents.llm import _call_gemini
    
    mock_post = AsyncMock()
    mock_response = httpx.Response(
        200,
        json={"candidates": [{"content": {"parts": [{"text": '{"message": "hello"}'}]}}]},
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/test-model:generateContent")
    )
    mock_post.return_value = mock_response

    with patch("httpx.AsyncClient.post", mock_post):
        import asyncio
        asyncio.run(_call_gemini("fake-api-key", "system", "prompt", 0.0, model="gemini-2.0-flash"))
        
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        call_headers = mock_post.call_args[1].get("headers", {})
        
        assert "key=" not in call_url
        assert call_headers.get("x-goog-api-key") == "fake-api-key"


def test_cassette_hash_strips_volatile_values():
    prompt_1 = "Decision id: 1234-abcd-5678-efgh. Timestamp: 2026-11-08T05:00:00Z. What is the conversion?"
    prompt_2 = "Decision id: 9999-ffff-0000-aaaa. Timestamp: 2026-11-08T06:30:00Z. What is the conversion?"
    
    hash1 = compute_cassette_hash(prompt_1, "DummyModel", "gemini", "gemini-2.0-flash")
    hash2 = compute_cassette_hash(prompt_2, "DummyModel", "gemini", "gemini-2.0-flash")
    assert hash1 == hash2


def test_analysis_stage_agents_do_not_see_peer_findings():
    state = WorkflowState(
        decision=Decision(id="d1", title="Free plan", question="Should we launch?", type="free_plan", objective="Evaluate feasibility"),
        findings={
            "CFO": Finding(
                task_id="t_cfo",
                agent="CFO",
                claim="CFO analysis",
                recommendation="reject",
                confidence=0.8,
                assumptions=[
                    Assumption(name="conversion_rate", low=0.01, base=0.015, high=0.02, unit="ratio", provenance="ai_assumption", source_ref="CFO", confidence=0.8)
                ]
            )
        }
    )
    supervisor = Supervisor()
    supervisor.state = state
    # The supervisor's analysis task payload should not contain peer findings
    payload = supervisor._build_analysis_context("Growth")
    assert "findings" not in payload or not payload.get("peer_findings")
    assert "CFO" not in str(payload.get("peer_findings", {}))


def test_parameter_whitelisting_and_clamping():
    from state.schemas import Task
    from agents.registry import AgentRegistry
    registry = AgentRegistry()
    supervisor = Supervisor(agent_registry=registry)
    state = WorkflowState(
        decision=Decision(id="d1", title="Free plan", question="Should we launch?", type="free_plan", objective="Evaluate feasibility"),
    )
    supervisor.state = state

    # Mock finding with out of bounds and unknown assumptions
    finding = Finding(
        task_id="task_growth_analysis",
        agent="Growth",
        claim="Growth hypothesis",
        recommendation="proceed",
        confidence=0.8,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion", # max is 0.20
                low=0.01,
                base=0.50,
                high=0.60,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="Growth",
                confidence=0.8
            ),
            Assumption(
                name="unmodeled_macro_factor",
                low=1.0,
                base=2.0,
                high=3.0,
                unit="multiplier",
                provenance="ai_assumption",
                source_ref="Growth",
                confidence=0.5
            )
        ]
    )

    class MockAgent:
        name = "Growth"
        async def run(self, *args, **kwargs):
            return finding

    registry._active_agents["growth"] = MockAgent()
    import asyncio
    task = Task(id="task_growth_analysis", name="Growth Analysis", kind="agent_analysis", owner_agent="Growth")
    asyncio.run(supervisor._execute_single_task(task, state))

    # Assert clamped assumption
    assert any(c["name"] == "free_to_paid_conversion" and c["clamped_base"] <= 0.20 for c in state.clamped_assumptions)
    # Assert ignored assumption
    assert any(i["name"] == "unmodeled_macro_factor" for i in state.ignored_assumptions)

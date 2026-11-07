"""Unit tests for Step 0: Project skeleton, FastAPI app, and llm_call wrapper."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from api.app import app
from agents.llm import llm_call, register_mock_generator


class SampleAnalysisModel(BaseModel):
    summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


@pytest.mark.asyncio
async def test_fastapi_health_routes():
    """Verify FastAPI hello and health routes operate properly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["app"] == "VentureTwin"

        resp_api = await client.get("/api/health")
        assert resp_api.status_code == 200
        data_api = resp_api.json()
        assert data_api["status"] == "ok"
        assert data_api["synthetic_data"] is True


@pytest.mark.asyncio
async def test_llm_call_default_mock_mode():
    """Verify llm_call returns a validated Pydantic model in mock mode."""
    res = await llm_call(
        prompt="Analyze the feasibility of launching a free tier.",
        response_model=SampleAnalysisModel,
        mock_mode=True,
    )
    assert isinstance(res, SampleAnalysisModel)
    assert isinstance(res.summary, str)
    assert 0.0 <= res.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_llm_call_registered_mock_generator():
    """Verify registered mock generators produce deterministic structured outputs."""
    class CustomResponse(BaseModel):
        recommendation: str
        score: int

    def custom_generator(prompt: str, system_prompt: str) -> CustomResponse:
        return CustomResponse(recommendation="proceed_with_limits", score=42)

    register_mock_generator(CustomResponse, custom_generator)

    res = await llm_call(
        prompt="Give custom recommendation",
        response_model=CustomResponse,
        mock_mode=True,
    )
    assert isinstance(res, CustomResponse)
    assert res.recommendation == "proceed_with_limits"
    assert res.score == 42


@pytest.mark.asyncio
async def test_llm_call_explicit_mock_response():
    """Verify explicit mock_response injection."""
    canned = SampleAnalysisModel(summary="Deterministic analysis", confidence_score=0.95, tags=["cfo", "risk"])
    res = await llm_call(
        prompt="Arbitrary prompt",
        response_model=SampleAnalysisModel,
        mock_mode=True,
        mock_response=canned,
    )
    assert res == canned
    assert res.confidence_score == 0.95

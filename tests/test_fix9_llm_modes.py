"""Tests for Fix 9: Explicit LLM modes, ConfigurationError on missing keys, parameter whitelisting, and agent communication protocol."""

import os
import pytest
from agents.llm import ConfigurationError, get_llm_mode, llm_call, get_llm_badge
from orchestrator.supervisor import Supervisor
from orchestrator.parser import parse_decision_query
from simulation.reconcile import reconcile_assumptions
from state.schemas import Assumption, Message
from pydantic import BaseModel


class SampleModel(BaseModel):
    summary: str


@pytest.mark.asyncio
async def test_real_mode_without_key_raises_configuration_error(monkeypatch):
    """Verify that when LLM_MODE=real and no valid API key is set, ConfigurationError is raised immediately."""
    monkeypatch.setenv("LLM_MODE", "real")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ConfigurationError) as exc_info:
        await llm_call(
            prompt="Analyze pricing",
            response_model=SampleModel,
        )
    assert "no api key was provided" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_record_and_replay_cassettes(monkeypatch, tmp_path):
    """Verify record mode saves cassette to disk and replay mode reads it identically."""
    cassette_path = tmp_path / "test_task.json"
    
    # Replay without cassette raises FileNotFoundError
    monkeypatch.setenv("LLM_MODE", "replay")
    with pytest.raises(FileNotFoundError):
        await llm_call(
            prompt="Test prompt",
            response_model=SampleModel,
            cassette_file=str(cassette_path),
        )

    # Seed cassette (as record mode would do)
    cassette_path.write_text('{"summary": "Verified Cassette Output"}')
    
    # Replay succeeds and matches
    result = await llm_call(
        prompt="Test prompt",
        response_model=SampleModel,
        cassette_file=str(cassette_path),
    )
    assert result.summary == "Verified Cassette Output"


def test_hallucinated_parameter_is_filtered_from_simulated_params():
    """Verify that any parameter not in SIM_PARAMS is excluded from simulated_params."""
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.015, base=0.025, high=0.045, unit="ratio", provenance="ai_assumption"),
        # Hallucinated non-whitelisted parameter
        Assumption(name="quantum_synergy_boost", low=1.0, base=2.5, high=5.0, unit="multiplier", provenance="ai_assumption"),
    ]
    reconciled = reconcile_assumptions(assumptions, conflicts=[])
    
    # Simulated params must strictly exclude hallucinated parameter
    assert "quantum_synergy_boost" not in reconciled.simulated_params
    assert "free_to_paid_conversion" in reconciled.simulated_params
    # Hallucinated parameter should be relegated to context or flagged
    sim_names = [p.name for p in reconciled.parameters if p.is_simulated]
    assert "quantum_synergy_boost" not in sim_names


@pytest.mark.asyncio
async def test_agent_communication_protocol_records_discussion_messages():
    """Verify that workflow executes the agent discussion step and records at least 3 messages (critique and rebuttals)."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    
    state = await supervisor.run_workflow(decision=decision)
    assert state.status == "completed"
    
    # state.messages must contain structured conversation
    assert hasattr(state, "messages")
    assert len(state.messages) >= 3
    
    kinds = {m.kind for m in state.messages}
    assert "critique" in kinds
    assert "rebuttal" in kinds
    
    senders = {m.sender for m in state.messages}
    assert "Skeptic" in senders
    assert "Growth" in senders or "CFO" in senders
    
    # Check that report includes discussion summary and LLM badge
    assert state.report is not None
    assert "llm_mode" in state.report
    assert "Mock" in state.report["llm_mode"]

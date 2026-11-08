"""Tests for Fix 4: Data-driven discussion, structured critiques, benchmarks grounding, and bounded rebuttals."""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor


@pytest.mark.asyncio
async def test_agent_discussion_generates_dynamic_critiques_from_benchmarks():
    """Verify that agent discussion dynamically identifies parameter deviations against benchmarks and issues critiques."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    messages = state.messages
    assert len(messages) >= 4  # Proposals + at least one critique + rebuttal

    critiques = [m for m in messages if m.kind == "critique"]
    rebuttals = [m for m in messages if m.kind == "rebuttal"]

    assert len(critiques) >= 1
    assert len(rebuttals) >= 1

    # Verify critique is data-driven
    for c in critiques:
        assert c.sender == "Skeptic"
        assert c.recipient in state.findings
        # Must target a real parameter
        assert c.parameter is not None
        assert c.parameter in [a.name for a in state.assumptions]
        # Content must explain the data/benchmark rationale
        assert len(c.content) > 10

    # Verify rebuttal links to the critique
    for r in rebuttals:
        assert r.recipient == "Skeptic"
        assert r.sender in state.findings
        assert r.rationale is not None
        assert "rebuttal" in r.content.lower()


@pytest.mark.asyncio
async def test_agent_discussion_works_for_pricing_decision_without_unrelated_agents():
    """Verify that in price_change decisions, discussion only targets participating specialists (no CTO or Product)."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we raise prices by 20% on the Starter tier?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    messages = state.messages
    critiques = [m for m in messages if m.kind == "critique"]

    participating_agents = set(state.findings.keys())
    assert "CTO" not in participating_agents
    assert "Product" not in participating_agents

    # Critiques must never target an agent not in participating_agents
    for c in critiques:
        assert c.recipient in participating_agents, f"Critique targeted absent agent {c.recipient}"

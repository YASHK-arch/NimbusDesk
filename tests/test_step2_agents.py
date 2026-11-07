"""Unit tests for Step 2: Agent Base Class, Specialist Agents, and Agent Registry."""

import pytest
from pydantic import ValidationError

from agents.base_agent import BaseAgent
from agents.registry import registry
from agents.specialists import (
    CFOAgent,
    CTOAgent,
    CustomerAgent,
    GrowthAgent,
    ProductAgent,
    SkepticAgent,
)
from state.schemas import Finding, Task


@pytest.mark.asyncio
async def test_specialist_agents_return_valid_findings():
    """Verify that every specialist agent returns a valid structured Finding with assumptions and provenance."""
    agents = [
        CFOAgent(),
        GrowthAgent(),
        CTOAgent(),
        CustomerAgent(),
        ProductAgent(),
        SkepticAgent(),
    ]

    for agent in agents:
        task = Task(id=f"task_{agent.name.lower()}_analysis", owner_agent=agent.name)
        finding = await agent.run(task=task)

        assert isinstance(finding, Finding)
        assert finding.agent == agent.name
        assert finding.task_id == task.id
        assert finding.recommendation in ["proceed", "proceed_with_limits", "reject", "needs_more_info"]
        assert len(finding.assumptions) > 0

        # Verify assumption provenance and confidence
        for asm in finding.assumptions:
            assert asm.provenance in ["verified_data", "external_research", "simulated_estimate", "ai_assumption"]
            assert 0.0 <= asm.confidence <= 1.0
            assert asm.low <= asm.base <= asm.high
            assert asm.proposed_by == agent.name

        # Verify evidence
        assert len(finding.evidence) > 0
        for ev in finding.evidence:
            assert ev.source_type in ["company_data", "external", "calculation", "benchmark"]
            assert len(ev.snippet) > 0


@pytest.mark.asyncio
async def test_cfo_and_growth_disagree_on_free_plan():
    """Verify core differentiator: CFO and Growth naturally produce divergent recommendations."""
    cfo = CFOAgent()
    growth = GrowthAgent()

    cfo_task = Task(id="task_cfo_analysis", owner_agent="CFO")
    growth_task = Task(id="task_growth_analysis", owner_agent="Growth")

    cfo_finding = await cfo.run(task=cfo_task)
    growth_finding = await growth.run(task=growth_task)

    # Recommendations must diverge
    assert cfo_finding.recommendation != growth_finding.recommendation
    assert growth_finding.recommendation == "proceed"
    assert cfo_finding.recommendation in ["proceed_with_limits", "reject"]

    # Assumption ranges for conversion must not overlap (creating authentic conflict)
    cfo_conv = next(a for a in cfo_finding.assumptions if a.name == "free_to_paid_conversion")
    growth_conv = next(a for a in growth_finding.assumptions if a.name == "free_to_paid_conversion")

    assert cfo_conv.high < growth_conv.low  # CFO optimistic (2.2%) < Growth pessimistic (3.5%)


@pytest.mark.asyncio
async def test_agent_registry():
    """Verify registry maintains active agents and extensible placeholders."""
    # Active agents
    assert registry.get_agent("CFO") is not None
    assert registry.get_agent("growth") is not None
    assert registry.get_agent("CTO") is not None
    assert registry.get_agent("skeptic") is not None

    active_list = registry.list_active_agents()
    active_names = [a["name"] for a in active_list]
    assert "CFO" in active_names
    assert "Growth" in active_names
    assert "CTO" in active_names

    # Placeholders marked extensible / not built
    all_entries = registry.list_all_entries()
    placeholders = [e for e in all_entries if not e.get("built")]
    placeholder_names = [p["name"] for p in placeholders]
    assert "Ops" in placeholder_names
    assert "Market" in placeholder_names
    assert "Risk" in placeholder_names


@pytest.mark.asyncio
async def test_base_agent_failure_injection_hooks():
    """Verify chaos/failure injection hooks required for Step 8 / Milestone 7."""
    agent = CFOAgent()
    task = Task(id="task_test_chaos", owner_agent="CFO")

    # 1. Timeout injection
    with pytest.raises(TimeoutError):
        await agent.run(task=task, failure_mode="timeout")

    # 2. Exception injection
    with pytest.raises(RuntimeError) as exc_info:
        await agent.run(task=task, failure_mode="exception")
    assert "Simulated crash" in str(exc_info.value)

    # 3. Bad output injection
    with pytest.raises(ValidationError):
        await agent.run(task=task, failure_mode="bad_output")

"""Tests for Fix 4: Removal of fake citations, snapshot tie-outs for verified_data, unit validation against SIM_PARAMS."""

import json
from pathlib import Path
import pytest
from agents.registry import registry
from agents.tools import get_infra_headroom
from simulation.params import SIM_PARAMS
from state.company import load_company_snapshot
from state.schemas import Assumption
from verification.verifier import verify_workflow

FORBIDDEN_SOURCES = [
    "OpenView 2024 SaaS Product Benchmarks",
    "ProductLed PLG Benchmark Report 2024",
    "SaaS Growth Index 2024",
    "Zendesk PLG Support Benchmark",
    "NimbusDesk AWS CloudWatch Breakdown",
    "NimbusDesk Board Mandate Q3",
    "B2B SaaS Benchmark Report 2024",
]


def test_no_mock_findings_use_forbidden_fabricated_sources():
    """Verify none of the specialist mock findings cite non-existent benchmark reports."""
    agents = ["CFO", "Growth", "CTO", "Customer", "Product", "Skeptic"]
    for agent_name in agents:
        agent = registry.get_agent(agent_name)
        finding = agent._generate_specialist_mock("task_mock_test")
        for asm in finding.assumptions:
            source = asm.source_ref or ""
            for forbidden in FORBIDDEN_SOURCES:
                assert forbidden.lower() not in source.lower(), f"Agent {agent_name} assumption {asm.name} cited forbidden source '{forbidden}'"
            if asm.provenance == "external_research":
                pytest.fail(f"Agent {agent_name} assumption {asm.name} uses external_research; mock findings must use ai_assumption or verified_data")


def test_verified_data_assumptions_match_company_snapshot():
    """Verify that any assumption tagged verified_data has a value matching synthetic_company.json."""
    company = load_company_snapshot()
    agents = ["CFO", "Growth", "CTO", "Customer", "Product", "Skeptic"]
    for agent_name in agents:
        agent = registry.get_agent(agent_name)
        finding = agent._generate_specialist_mock("task_mock_test")
        for asm in finding.assumptions:
            if asm.provenance == "verified_data":
                assert asm.source_ref is not None and "data/synthetic_company.json#" in asm.source_ref
                # Resolve field path
                field_path = asm.source_ref.split("#")[1]
                val = company
                for part in field_path.split("."):
                    if isinstance(val, dict):
                        val = val[part]
                    else:
                        val = getattr(val, part)
                assert float(val) == pytest.approx(asm.base), f"Mismatch for {asm.name}: snapshot has {val}, assumption has {asm.base}"


def test_verifier_rejects_unit_mismatch_with_sim_params():
    """Verify that verifier unit_consistency check rejects an assumption whose unit mismatches SIM_PARAMS."""
    company = load_company_snapshot()
    # free_to_paid_conversion must have unit 'ratio', not '%'
    bad_asm = Assumption(
        name="free_to_paid_conversion",
        low=0.01,
        base=0.02,
        high=0.03,
        unit="%",  # Invalid: 0.01 is a ratio, not 1%
        provenance="ai_assumption",
    )
    all_passed, results = verify_workflow([bad_asm], [], company)
    unit_check = next((r for r in results if r.check_name == "unit_consistency"), None)
    assert unit_check is not None
    assert unit_check.status == "failed"
    assert "free_to_paid_conversion" in unit_check.detail


def test_infra_headroom_reads_from_company_snapshot():
    """Verify get_infra_headroom reads max_safe_free_users_without_sharding from company snapshot."""
    company = load_company_snapshot()
    assert "max_safe_free_users_without_sharding" in company.infra
    result = get_infra_headroom(active_free_users=1000)
    assert result["max_safe_free_users_without_sharding"] == company.infra["max_safe_free_users_without_sharding"]

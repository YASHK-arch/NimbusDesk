#!/usr/bin/env python3
"""Run real LLM demo script for VentureTwin multi-agent decision stress-testing.

Sets LLM_MODE=real, runs the workflow against the live configured provider (Gemini, Anthropic, OpenAI),
validates the consolidated output, and displays the executive decision report.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.llm import ConfigurationError, get_llm_badge
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from report.report_builder import render_report_markdown


async def main() -> None:
    print("=" * 70)
    print(" VentureTwin: Real LLM Mode End-to-End Execution")
    print("=" * 70)

    # Ensure real mode is active
    os.environ["LLM_MODE"] = "real"
    badge = get_llm_badge()
    print(f"Status Badge: [{badge}]")

    has_key = any([
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GOOGLE_API_KEY"),
        os.getenv("OPENAI_API_KEY"),
        os.getenv("ANTHROPIC_API_KEY"),
    ])

    if not has_key:
        print("\n[ERROR] No LLM API key detected.")
        print("Please export one of:")
        print("  export GEMINI_API_KEY='your-key'")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("\nExiting with ConfigurationError as mandated by Rule R6 (honest outputs).")
        sys.exit(1)

    question = "Should we launch a free plan?"
    print(f"\n1. Submitting Strategic Question: '{question}'")
    decision, supported = parse_decision_query(question)
    if not supported:
        print(f"[ERROR] Unsupported decision: {question}")
        sys.exit(1)

    supervisor = Supervisor()
    print("2. Spawning Multi-Agent DAG with Real LLM Orchestration...")
    state = await supervisor.run_workflow(decision=decision)

    if state.status == "failed":
        print(f"\n[FAIL] Workflow failed. Checkpoints preserved.")
        sys.exit(1)

    print(f"\n3. Workflow Finished Successfully with Status: {state.status.upper()}")
    print(f"   - Messages Exchanged: {len(state.messages)}")
    print(f"   - Assumptions Formulated: {len(state.assumptions)}")
    print(f"   - Conflicts Detected & Resolved: {len(state.conflicts)}")
    print(f"   - Simulation Runs Executed: {len(state.simulation_runs)}")

    if state.report:
        print("\n4. Executive Decision Report Generated:")
        md = render_report_markdown(state.report, state=state)
        print("-" * 70)
        print(md[:1500])
        print("...\n[Report truncated for CLI preview]")
        print("-" * 70)
        print(f"\nVerified Recommendation: {state.report['recommendation']}")
        print(f"Confidence Level: {state.report['confidence']}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ConfigurationError as err:
        print(f"\n[CONFIGURATION ERROR] {err}")
        sys.exit(1)


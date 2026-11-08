"""Full-workflow replay test using recorded cassettes.

Excluded from default test runs unless pytest is run with `-m requires_cassettes`.
If cassettes are not recorded, reports 'RECORDING PENDING: run LLM_MODE=record python scripts/run_real_demo.py with a key'.
"""

import os
from pathlib import Path
import pytest

from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor


@pytest.mark.requires_cassettes
@pytest.mark.asyncio
async def test_replay_full_workflow():
    cassette_dir = Path("tests/cassettes")
    if not cassette_dir.exists() or not list(cassette_dir.glob("*.json")):
        pytest.fail(
            "RECORDING PENDING: run LLM_MODE=record python scripts/run_real_demo.py with a key, "
            "then commit tests/cassettes/ and data/known_good_run.json"
        )

    os.environ["LLM_MODE"] = "replay"
    decision, _ = parse_decision_query("Should we launch a free plan?")
    supervisor = Supervisor()
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert state.report is not None
    assert state.report["llm_mode"] in ("replay", "real")

"""Failure detection, retry backoff, and degraded fallback recovery engine."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional
from state.schemas import Assumption, Evidence, Finding, Task

logger = logging.getLogger(__name__)


class RecoveryPolicy:
    """Manages failure handling, backoff retries, and degraded fallback synthesis."""

    def __init__(self, max_retries: int = 2, backoff_base_sec: float = 0.05) -> None:
        self.max_retries = max_retries
        self.backoff_base_sec = backoff_base_sec

    async def apply_backoff(self, attempt: int) -> None:
        """Non-blocking exponential backoff."""
        delay = self.backoff_base_sec * (2 ** (attempt - 1))
        await asyncio.sleep(delay)

    def create_degraded_fallback_finding(self, task: Task, agent_name: str, error_msg: str) -> Finding:
        """Construct a safe, conservative degraded-mode Finding when an agent fails permanently."""
        logger.warning(f"Synthesizing degraded fallback finding for {agent_name} after permanent failure: {error_msg}")
        return Finding(
            agent=agent_name,
            task_id=task.id,
            claim=f"Degraded Mode: {agent_name} failed ({error_msg}). Standard conservative benchmarks applied.",
            recommendation="proceed_with_limits",
            confidence=0.40,  # Lower confidence reflecting degraded mode
            assumptions=[
                Assumption(
                    name="degraded_fallback_margin_safety",
                    low=0.70,
                    base=0.85,
                    high=0.95,
                    unit="safety_ratio",
                    provenance="simulated_estimate",
                    source_ref=f"Supervisor Degraded Mode Rulebook for {agent_name}",
                    confidence=0.40,
                    proposed_by="Supervisor_Recovery",
                )
            ],
            evidence=[
                Evidence(
                    source_type="calculation",
                    source_ref="recovery_subsystem",
                    snippet=f"Primary agent {agent_name} crashed; fallback parameters injected to ensure workflow completion.",
                )
            ],
            limitations=[f"Primary {agent_name} analysis was unavailable; run completed in fault-tolerant degraded mode."],
            status="ok",
        )

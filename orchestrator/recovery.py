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
        """Construct a safe, conservative degraded-mode Finding using BackupAnalyst when an agent fails permanently."""
        logger.warning(f"Synthesizing degraded fallback finding via BackupAnalyst for {agent_name} after permanent failure: {error_msg}")
        from agents.specialists import BackupAnalyst
        analyst = BackupAnalyst()
        return analyst.generate_fallback_finding(task.id, failed_agent_name=agent_name)

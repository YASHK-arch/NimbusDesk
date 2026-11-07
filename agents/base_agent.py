"""Base class for all specialist AI agents in VentureTwin."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from pydantic import ValidationError

from agents.llm import llm_call
from state.schemas import Finding, Task

logger = logging.getLogger(__name__)


class BaseAgent:
    """Abstract base agent providing tool execution, heartbeat hooks, failure injection,

    and Pydantic output validation.
    """

    def __init__(
        self,
        name: str,
        role_title: str,
        objective: str,
        system_prompt: str,
        allowed_tools: Optional[List[Callable[[], Dict[str, Any]]]] = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.name = name
        self.role_title = role_title
        self.objective = objective
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or []
        self.timeout_seconds = timeout_seconds

    def execute_tools(self) -> Dict[str, Any]:
        """Execute all assigned deterministic tools to gather factual domain inputs."""
        tool_results = {}
        for tool in self.allowed_tools:
            tool_name = tool.__name__
            try:
                tool_results[tool_name] = tool()
            except Exception as e:
                logger.error(f"Error executing tool {tool_name} for agent {self.name}: {e}")
                tool_results[tool_name] = {"error": str(e)}
        return tool_results

    async def run(
        self,
        task: Task,
        state: Optional[Dict[str, Any]] = None,
        failure_mode: Optional[str] = None,
    ) -> Finding:
        """Execute agent analysis with timeout control and failure injection hooks."""
        # 1. Chaos / Failure Injection Hooks for Milestone 7
        if failure_mode == "timeout":
            logger.warning(f"Injecting simulated TIMEOUT in agent: {self.name}")
            raise TimeoutError(f"Agent {self.name} timed out after {self.timeout_seconds}s (injected chaos)")

        if failure_mode == "exception":
            logger.warning(f"Injecting simulated EXCEPTION in agent: {self.name}")
            raise RuntimeError(f"Simulated crash in {self.name}: unhandled kernel exception")

        if failure_mode == "bad_output":
            logger.warning(f"Injecting simulated BAD_OUTPUT in agent: {self.name}")
            # Construct an intentionally broken finding violating schema constraints
            raise ValidationError.from_exception_data(
                title="CorruptedAgentOutput",
                line_errors=[{"type": "missing", "loc": ("recommendation",), "input": {}}],
            )

        # 2. Gather factual deterministic tool context
        tool_context = self.execute_tools()

        # 3. Build prompt for specialist analysis
        user_prompt = (
            f"You are the {self.role_title} ({self.name}).\n"
            f"Your Core Objective: {self.objective}\n\n"
            f"Current Task: {task.id}\n"
            f"Verified Company Tool Data:\n{tool_context}\n\n"
            f"Additional Workflow Context:\n{state or {}}\n\n"
            "Analyze the strategic decision based on your specific objective. "
            "Propose structured assumptions with explicit low, base, high bounds and provenance tags. "
            "Never generate final financial numbers directly; output assumption ranges and qualitative claims."
        )

        # 4. Invoke LLM with bounded retries and structured validation
        try:
            finding = await asyncio.wait_for(
                self._execute_llm(user_prompt, task.id),
                timeout=self.timeout_seconds,
            )
            return finding
        except asyncio.TimeoutError:
            logger.error(f"Agent {self.name} timed out during LLM execution.")
            raise TimeoutError(f"Agent {self.name} exceeded execution limit of {self.timeout_seconds}s")

    async def _execute_llm(self, user_prompt: str, task_id: str) -> Finding:
        """Internal call to llm_call with fallback to specialized mock finding."""
        canned_finding = self._generate_specialist_mock(task_id)
        finding = await llm_call(
            prompt=user_prompt,
            response_model=Finding,
            system_prompt=self.system_prompt,
            mock_response=canned_finding,
        )
        # Ensure mandatory metadata is aligned
        finding.agent = self.name
        finding.task_id = task_id
        for asm in finding.assumptions:
            if not asm.proposed_by:
                asm.proposed_by = self.name
        return finding

    def _generate_specialist_mock(self, task_id: str) -> Finding:
        """Generate a realistic, deterministic domain finding if LLM is in mock mode.

        Overridden by individual specialist agents.
        """
        raise NotImplementedError("Specialist agents must implement _generate_specialist_mock")

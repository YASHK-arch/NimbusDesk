"""Shared workflow state model tracking decisions, findings, assumptions, and execution metrics."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from state.schemas import (
    Assumption,
    Conflict,
    Decision,
    Finding,
    Message,
    SimulationRun,
    Task,
    VerificationResult,
    WorkflowEvent,
)


class WorkflowState(BaseModel):
    decision: Decision
    tasks: Dict[str, Task] = Field(default_factory=dict)
    findings: Dict[str, Finding] = Field(default_factory=dict)  # agent_name -> Finding
    messages: List[Message] = Field(default_factory=list)
    assumptions: List[Assumption] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    skeptic_challenges: List[str] = Field(default_factory=list)
    simulation_runs: List[SimulationRun] = Field(default_factory=list)
    reconciled: Optional[Any] = None
    mc_summaries: Optional[Dict[str, Any]] = None
    verification_results: List[VerificationResult] = Field(default_factory=list)
    report: Optional[Dict[str, Any]] = None
    event_log: List[WorkflowEvent] = Field(default_factory=list)
    execution_timeline: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # task_id -> {start, finish, duration}
    status: str = "pending"  # "pending", "running", "completed", "failed", "recovering"
    checkpoint_id: Optional[str] = None

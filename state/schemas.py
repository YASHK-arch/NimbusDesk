"""Pydantic schemas for VentureTwin multi-agent coordination, state, and simulation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Assumption(BaseModel):
    name: str = Field(..., description="Unique assumption key, e.g. 'free_to_paid_conversion'")
    low: float = Field(..., description="Pessimistic / conservative bound")
    base: float = Field(..., description="Expected / baseline estimate")
    high: float = Field(..., description="Optimistic bound")
    unit: str = Field(..., description="Unit of measurement, e.g. '%', 'USD/user', 'ratio'")
    provenance: Literal["verified_data", "external_research", "simulated_estimate", "ai_assumption"] = Field(
        ..., description="Provenance tag tracing source category"
    )
    source_ref: Optional[str] = Field(None, description="Identifier of dataset, document, or calculation reference")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    proposed_by: Optional[str] = Field(None, description="Agent identity that introduced the assumption")
    challenged_by_skeptic: bool = Field(False, description="Flag set if Skeptic challenged this assumption")


class Evidence(BaseModel):
    source_type: Literal["company_data", "external", "calculation", "benchmark"]
    source_ref: str
    snippet: str


class Finding(BaseModel):
    agent: str = Field(..., description="Name of the specialist agent (e.g. 'CFO', 'Growth')")
    task_id: str = Field(..., description="ID of the task being fulfilled")
    claim: str = Field(..., description="Primary analytical claim or summary")
    recommendation: Literal["proceed", "proceed_with_limits", "reject", "needs_more_info"]
    assumptions: List[Assumption] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)
    status: Literal["ok", "failed", "needs_more_info"] = "ok"


class Decision(BaseModel):
    id: str
    type: Literal["free_plan", "price_change", "unsupported"]
    question: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["pending", "processing", "completed", "failed", "approved", "rejected"] = "pending"


class Task(BaseModel):
    id: str
    owner_agent: str
    depends_on: List[str] = Field(default_factory=list)
    status: Literal["pending", "running", "done", "failed", "retrying", "blocked"] = "pending"
    input_ref: Optional[str] = None
    output_ref: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None


class Conflict(BaseModel):
    id: str
    type: Literal["contradictory_recommendation", "assumption_divergence", "missing_evidence", "dependency_block"]
    agents: List[str]
    disputed_item: str
    evidence: List[Evidence] = Field(default_factory=list)
    resolution: Optional[str] = None
    simulation_ids: List[str] = Field(default_factory=list)
    resolved: bool = False


class SimulationRun(BaseModel):
    id: str
    strategy: str
    scenario: str
    parameters: Dict[str, Any]
    outputs: Dict[str, Any]
    seed: int


class VerificationResult(BaseModel):
    check_name: str
    status: Literal["passed", "failed", "waived"]
    detail: str


class DecisionRecord(BaseModel):
    decision_id: str
    snapshot: Dict[str, Any]
    chosen_strategy: str
    predicted_metrics: Dict[str, Any]
    approved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["awaiting_outcome", "evaluated"] = "awaiting_outcome"
    actual_metrics: Optional[Dict[str, Any]] = None


class WorkflowEvent(BaseModel):
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    type: Literal[
        "task_created",
        "agent_started",
        "finding_posted",
        "conflict_detected",
        "simulation_run",
        "agent_failed",
        "recovery_started",
        "recovery_done",
        "verification_passed",
        "verification_failed",
        "report_ready",
        "decision_approved",
    ]
    agent: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class PlanMetrics(BaseModel):
    plan_name: str
    price_per_month: float
    active_customers: int
    mrr: float
    churn_monthly_pct: float


class CompanySnapshot(BaseModel):
    name: str = "NimbusDesk"
    tagline: str
    currency: str = "USD"
    mrr: float
    arr: float
    cash_balance: float
    monthly_gross_burn: float = 259005.0
    monthly_burn: float
    runway_months: float
    total_paying_customers: int
    blended_churn_monthly_pct: float
    cac_blended: float
    ltv_blended: float
    current_free_users: int = 0
    support: Dict[str, Any]
    infra: Dict[str, Any]
    funnel: Dict[str, Any]
    engineering_capacity: Dict[str, Any]
    plans: List[PlanMetrics]
    is_synthetic: bool = True

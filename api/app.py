"""FastAPI application entry point for VentureTwin SwarmFlow Engine."""

from __future__ import annotations

import os
from typing import Dict, Literal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="VentureTwin: SwarmFlow Multi-Agent Coordination Engine",
    description="Operational Digital Twin & Decision Stress-Test Platform for SaaS Pricing and Packaging Decisions",
    version="0.1.0",
)

# In-memory storage for runtime failure injections
_INJECTED_FAILURES: Dict[str, Dict[str, str]] = {}


class InjectFailureRequest(BaseModel):
    agent: str
    mode: Literal["timeout", "exception", "bad_output"]


@app.post("/api/decisions/{id}/inject-failure")
async def inject_failure(id: str, req: InjectFailureRequest):
    """Chaos hook: inject simulated timeout, exception, or bad output into target agent."""
    _INJECTED_FAILURES.setdefault(id, {})[req.agent] = req.mode
    return {
        "status": "failure_injected",
        "decision_id": id,
        "agent": req.agent,
        "mode": req.mode,
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "VentureTwin",
        "version": "0.1.0",
        "mock_mode": os.getenv("LLM_MOCK_MODE", "true").lower() in ("true", "1", "yes"),
    }


@app.get("/api/health")
async def api_health_check():
    return {
        "status": "ok",
        "service": "VentureTwin Multi-Agent Orchestration Platform",
        "synthetic_data": True,
    }

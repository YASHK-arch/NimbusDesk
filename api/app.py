"""FastAPI application entry point for VentureTwin SwarmFlow Engine."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="VentureTwin: SwarmFlow Multi-Agent Coordination Engine",
    description="Operational Digital Twin & Decision Stress-Test Platform for SaaS Pricing and Packaging Decisions",
    version="0.1.0",
)

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

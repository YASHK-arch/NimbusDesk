"""Agent Registry maintaining active specialist agents and extensible placeholder metadata."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent
from agents.specialists import (
    CFOAgent,
    CTOAgent,
    CustomerAgent,
    GrowthAgent,
    ProductAgent,
    SkepticAgent,
)


class AgentRegistry:
    def __init__(self) -> None:
        self._active_agents: Dict[str, BaseAgent] = {
            "cfo": CFOAgent(),
            "growth": GrowthAgent(),
            "cto": CTOAgent(),
            "customer": CustomerAgent(),
            "product": ProductAgent(),
            "skeptic": SkepticAgent(),
        }
        self._placeholders: Dict[str, Dict[str, Any]] = {
            "ops": {
                "name": "Ops",
                "role_title": "Head of Operations & Billing Logistics",
                "objective": "Payment gateway fee optimization, multi-currency VAT compliance, and provisioning workflows.",
                "built": False,
                "status": "extensible_placeholder",
            },
            "market": {
                "name": "Market",
                "role_title": "Competitive Market Intelligence Agent",
                "objective": "Real-time competitor pricing radar, feature parity scanning, and win-loss intelligence.",
                "built": False,
                "status": "extensible_placeholder",
            },
            "risk": {
                "name": "Risk",
                "role_title": "Enterprise Risk & Governance Agent",
                "objective": "SOC2 compliance, GDPR data residency audits, and enterprise procurement liability assessment.",
                "built": False,
                "status": "extensible_placeholder",
            },
        }

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        key = agent_name.lower().strip()
        return self._active_agents.get(key)

    def list_active_agents(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": agent.name,
                "role_title": agent.role_title,
                "objective": agent.objective,
                "built": True,
                "allowed_tools": [tool.__name__ for tool in agent.allowed_tools],
            }
            for agent in self._active_agents.values()
        ]

    def list_all_entries(self) -> List[Dict[str, Any]]:
        active = self.list_active_agents()
        placeholders = list(self._placeholders.values())
        return active + placeholders


registry = AgentRegistry()

"""Rule-based and heuristic conflict detector across multi-agent findings and assumptions."""

from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Tuple
from state.schemas import Conflict, Evidence, Finding, Task

logger = logging.getLogger(__name__)

ORDINAL_RECOMMENDATIONS: Dict[str, int] = {
    "reject": 0,
    "needs_more_info": 1,
    "proceed_with_limits": 2,
    "proceed": 3,
}


def detect_conflicts(
    findings: Dict[str, Finding],
    tasks: Optional[Dict[str, Task]] = None,
) -> List[Conflict]:
    """Execute all conflict detection checks across findings and tasks."""
    conflicts: List[Conflict] = []
    conflicts.extend(detect_contradictory_recommendations(findings))
    conflicts.extend(detect_assumption_divergence(findings))
    conflicts.extend(detect_missing_evidence(findings))
    if tasks:
        conflicts.extend(detect_unresolved_dependencies(tasks))
    return conflicts


def detect_contradictory_recommendations(findings: Dict[str, Finding]) -> List[Conflict]:
    """Check 1: Flag when agents issue opposing strategic recommendations.

    Uses an ordinal distance scale:
    reject (0) < needs_more_info (1) < proceed_with_limits (2) < proceed (3).
    A conflict is flagged only when distance >= 2 (e.g. proceed vs reject, or proceed vs needs_more_info).
    Proceed vs proceed_with_limits (distance = 1) is logged as an informational note, not a conflict.
    """
    conflicts = []
    finding_list = list(findings.values())

    for i in range(len(finding_list)):
        for j in range(i + 1, len(finding_list)):
            f1, f2 = finding_list[i], finding_list[j]
            score1 = ORDINAL_RECOMMENDATIONS.get(f1.recommendation, 1)
            score2 = ORDINAL_RECOMMENDATIONS.get(f2.recommendation, 1)
            dist = abs(score1 - score2)

            if dist >= 2:
                conflicts.append(
                    Conflict(
                        id=f"conf-rec-{uuid.uuid4().hex[:6]}",
                        type="contradictory_recommendation",
                        agents=[f1.agent, f2.agent],
                        disputed_item=f"Recommendation divergence: {f1.agent} recommends '{f1.recommendation}' vs {f2.agent} recommends '{f2.recommendation}'",
                        evidence=f1.evidence + f2.evidence,
                        resolved=False,
                        status="detected",
                    )
                )
            elif dist == 1:
                logger.info(
                    "Informational divergence (no conflict): %s recommends '%s' vs %s recommends '%s'",
                    f1.agent,
                    f1.recommendation,
                    f2.agent,
                    f2.recommendation,
                )
    return conflicts


def detect_assumption_divergence(findings: Dict[str, Finding]) -> List[Conflict]:
    """Check 2: Flag when agents propose non-overlapping ranges for the same assumption.

    Grouped by disputed parameter so each parameter yields at most ONE conflict listing all conflicting agents.
    """
    conflicts = []
    assumption_map: Dict[str, List[Tuple[str, Any, List[Evidence]]]] = {}
    for f in findings.values():
        for asm in f.assumptions:
            assumption_map.setdefault(asm.name, []).append((f.agent, asm, f.evidence))

    for name, entries in assumption_map.items():
        if len(entries) < 2:
            continue

        conflicting_agents: List[str] = []
        evidence_pool: List[Evidence] = []
        disputed_descriptions: List[str] = []

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                agent1, asm1, ev1 = entries[i]
                agent2, asm2, ev2 = entries[j]

                # Check for strictly non-overlapping bounds: [low1, high1] vs [low2, high2]
                if (asm1.high < asm2.low) or (asm2.high < asm1.low):
                    if agent1 not in conflicting_agents:
                        conflicting_agents.append(agent1)
                    if agent2 not in conflicting_agents:
                        conflicting_agents.append(agent2)
                    for e in ev1 + ev2:
                        if e not in evidence_pool:
                            evidence_pool.append(e)
                    disputed_descriptions.append(
                        f"{agent1} [{asm1.low}, {asm1.high}] vs {agent2} [{asm2.low}, {asm2.high}]"
                    )

        if conflicting_agents:
            conflicts.append(
                Conflict(
                    id=f"conf-asm-{uuid.uuid4().hex[:6]}",
                    type="assumption_divergence",
                    agents=conflicting_agents,
                    disputed_item=f"Non-overlapping bounds on '{name}': {'; '.join(disputed_descriptions)}",
                    evidence=evidence_pool,
                    resolved=False,
                    status="detected",
                )
            )
    return conflicts


def detect_missing_evidence(findings: Dict[str, Finding]) -> List[Conflict]:
    """Check 3: Flag key claims or assumptions lacking verifiable evidence."""
    conflicts = []
    for f in findings.values():
        if not f.evidence and f.recommendation in ("proceed", "reject"):
            conflicts.append(
                Conflict(
                    id=f"conf-evi-{uuid.uuid4().hex[:6]}",
                    type="missing_evidence",
                    agents=[f.agent],
                    disputed_item=f"Agent {f.agent} recommended '{f.recommendation}' without attaching factual evidence.",
                    evidence=[],
                    resolved=False,
                    status="detected",
                )
            )
    return conflicts


def detect_unresolved_dependencies(tasks: Dict[str, Task]) -> List[Conflict]:
    """Check 4: Flag unresolved task dependencies."""
    conflicts = []
    for t in tasks.values():
        for dep_id in t.depends_on:
            dep_task = tasks.get(dep_id)
            if dep_task and dep_task.status == "failed":
                conflicts.append(
                    Conflict(
                        id=f"conf-dep-{uuid.uuid4().hex[:6]}",
                        type="dependency_block",
                        agents=[t.owner_agent, dep_task.owner_agent],
                        disputed_item=f"Task {t.id} blocked by failed prerequisite {dep_id}",
                        evidence=[],
                        resolved=False,
                        status="detected",
                    )
                )
    return conflicts

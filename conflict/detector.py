"""Rule-based and heuristic conflict detector across multi-agent findings and assumptions."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional
from state.schemas import Conflict, Evidence, Finding, Task


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
    """Check 1: Flag when agents issue opposing strategic recommendations."""
    conflicts = []
    finding_list = list(findings.values())

    for i in range(len(finding_list)):
        for j in range(i + 1, len(finding_list)):
            f1, f2 = finding_list[i], finding_list[j]
            # Opposing pair: proceed vs reject, or proceed vs proceed_with_limits
            opposing = False
            if (f1.recommendation == "proceed" and f2.recommendation in ("reject", "proceed_with_limits")) or (
                f2.recommendation == "proceed" and f1.recommendation in ("reject", "proceed_with_limits")
            ):
                opposing = True

            if opposing:
                conflicts.append(
                    Conflict(
                        id=f"conf-rec-{uuid.uuid4().hex[:6]}",
                        type="contradictory_recommendation",
                        agents=[f1.agent, f2.agent],
                        disputed_item=f"Recommendation divergence: {f1.agent} recommends '{f1.recommendation}' vs {f2.agent} recommends '{f2.recommendation}'",
                        evidence=f1.evidence + f2.evidence,
                        resolved=False,
                    )
                )
    return conflicts


def detect_assumption_divergence(findings: Dict[str, Finding]) -> List[Conflict]:
    """Check 2: Flag when two agents propose non-overlapping ranges for the same assumption."""
    conflicts = []
    # Map assumption_name -> list of (agent_name, assumption)
    assumption_map: Dict[str, List] = {}
    for f in findings.values():
        for asm in f.assumptions:
            assumption_map.setdefault(asm.name, []).append((f.agent, asm))

    for name, entries in assumption_map.items():
        if len(entries) < 2:
            continue
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                agent1, asm1 = entries[i]
                agent2, asm2 = entries[j]

                # Check for non-overlapping bounds
                non_overlapping = (asm1.high < asm2.low) or (asm2.high < asm1.low)
                if non_overlapping:
                    conflicts.append(
                        Conflict(
                            id=f"conf-asm-{uuid.uuid4().hex[:6]}",
                            type="assumption_divergence",
                            agents=[agent1, agent2],
                            disputed_item=f"Non-overlapping bounds on '{name}': {agent1} [{asm1.low}, {asm1.high}] vs {agent2} [{asm2.low}, {asm2.high}]",
                            evidence=[],
                            resolved=False,
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
                    )
                )
    return conflicts

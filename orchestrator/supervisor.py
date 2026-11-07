"""Central Supervisor orchestrator managing parallel task dispatching, event streaming,

and dependency ordering.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, Optional, Set
from agents.registry import registry as default_registry
from conflict.detector import detect_conflicts
from conflict.resolver import resolve_conflicts_with_simulation
from orchestrator.checkpoint import CheckpointStore
from orchestrator.recovery import RecoveryPolicy
from report.report_builder import build_consolidated_report
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from state.company import load_company_snapshot
from verification.skeptic_audit import run_skeptic_audit
from verification.verifier import verify_workflow
from orchestrator.dag import TaskDAG
from orchestrator.decomposer import decompose_decision
from state.event_bus import event_bus as default_event_bus
from state.schemas import Decision, Finding, Task, WorkflowEvent
from state.shared_state import WorkflowState

logger = logging.getLogger(__name__)


class Supervisor:
    def __init__(self, agent_registry=None, bus=None, checkpoint_store=None, recovery_policy=None) -> None:
        self.registry = agent_registry or default_registry
        self.bus = bus or default_event_bus
        self.checkpoints = checkpoint_store or CheckpointStore()
        self.recovery = recovery_policy or RecoveryPolicy()

    async def run_workflow(
        self,
        decision: Decision,
        dag: Optional[TaskDAG] = None,
        injected_failures: Optional[Dict[str, str]] = None,
        resume_if_checkpoint_exists: bool = False,
    ) -> WorkflowState:
        """Execute or resume a multi-agent workflow DAG with task-level SQLite checkpointing."""
        injected_failures = injected_failures or {}
        if dag is None:
            dag = decompose_decision(decision)

        # Check for existing checkpoint if resume requested
        existing_checkpoint: Optional[WorkflowState] = None
        if resume_if_checkpoint_exists:
            existing_checkpoint = self.checkpoints.load_latest_checkpoint(decision.id)

        if existing_checkpoint:
            state = existing_checkpoint
            state.status = "recovering"
            await self.bus.emit(
                event_type="recovery_started",
                agent="Supervisor",
                payload={"decision_id": decision.id, "resuming_from_task": list(state.findings.keys())},
            )
            completed_ids: Set[str] = {tid for tid, t in state.tasks.items() if t.status == "done"}
            await self.bus.emit(
                event_type="recovery_done",
                agent="Supervisor",
                payload={"decision_id": decision.id, "skipped_completed_count": len(completed_ids)},
            )
        else:
            state = WorkflowState(
                decision=decision,
                tasks={t.id: t for t in dag.tasks.values()},
                status="running",
            )
            completed_ids = set()

            # Emit task_created events for the plan
            for t in dag.tasks.values():
                await self.bus.emit(
                    event_type="task_created",
                    agent="Supervisor",
                    payload={"task_id": t.id, "owner": t.owner_agent, "depends_on": t.depends_on},
                )

        active_tasks: Dict[str, asyncio.Task] = {}
        task_ref_map: Dict[str, Task] = {t.id: t for t in dag.tasks.values()}
        # Sync DAG task statuses with restored state
        for tid in completed_ids:
            if tid in task_ref_map:
                task_ref_map[tid].status = "done"

        # Execution loop: dynamically dispatch ready tasks in parallel
        while len(completed_ids) < len(dag.tasks):
            ready_tasks = dag.get_ready_tasks(
                completed_ids=completed_ids,
                active_ids=set(active_tasks.keys()),
            )

            # Spawn ready tasks concurrently
            for task in ready_tasks:
                task.status = "running"
                task_id = task.id
                failure_mode = injected_failures.get(task.owner_agent) or injected_failures.get(task_id)

                async_task = asyncio.create_task(
                    self._execute_single_task(
                        task=task,
                        state=state,
                        failure_mode=failure_mode,
                    )
                )
                active_tasks[task_id] = async_task

            if not active_tasks:
                if len(completed_ids) < len(dag.tasks):
                    failed_tasks = [t.id for t in dag.tasks.values() if t.status == "failed"]
                    state.status = "failed"
                    raise RuntimeError(f"Workflow deadlocked or stalled. Failed tasks: {failed_tasks}")
                break

            # Wait for at least one active task to complete
            done_set, _ = await asyncio.wait(
                active_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Process completed tasks
            finished_ids = []
            for tid, atask in active_tasks.items():
                if atask in done_set:
                    finished_ids.append(tid)
                    try:
                        result = atask.result()
                        task_obj = task_ref_map[tid]
                        task_obj.status = "done"
                        completed_ids.add(tid)
                        state.tasks[tid] = task_obj

                        # Save checkpoint to SQLite after each task
                        ckpt_id = self.checkpoints.save_checkpoint(state, tid)
                        state.checkpoint_id = str(ckpt_id)

                    except Exception as err:
                        logger.error(f"Task {tid} execution error: {err}")
                        task_obj = task_ref_map[tid]
                        task_obj.status = "failed"
                        task_obj.error_message = str(err)
                        state.tasks[tid] = task_obj
                        # Persist failed checkpoint
                        self.checkpoints.save_checkpoint(state, tid)
                        completed_ids.add(tid)

            for fid in finished_ids:
                del active_tasks[fid]

        state.status = "completed"
        return state

    async def _execute_single_task(
        self,
        task: Task,
        state: WorkflowState,
        failure_mode: Optional[str] = None,
    ) -> Any:
        """Execute an individual task, logging timestamps to prove concurrent parallelism."""
        start_ts = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()

        await self.bus.emit(
            event_type="agent_started",
            agent=task.owner_agent,
            payload={"task_id": task.id, "start_time": start_iso},
        )

        try:
            # Handle specialist agent execution
            agent = self.registry.get_agent(task.owner_agent)
            if agent:
                finding: Optional[Finding] = None
                task.attempts = 1
                try:
                    finding = await agent.run(task=task, state=state.model_dump(), failure_mode=failure_mode)
                except Exception as first_exc:
                    await self.bus.emit(
                        event_type="agent_failed",
                        agent=task.owner_agent,
                        payload={"task_id": task.id, "attempt": task.attempts, "error": str(first_exc)},
                    )
                    await self.bus.emit(
                        event_type="recovery_started",
                        agent="Supervisor",
                        payload={"task_id": task.id, "target_agent": task.owner_agent, "action": "retry_with_backoff"},
                    )
                    task.attempts += 1
                    await self.recovery.apply_backoff(task.attempts)

                    # Transient retry attempt without injected failure
                    try:
                        finding = await agent.run(task=task, state=state.model_dump(), failure_mode=None)
                        await self.bus.emit(
                            event_type="recovery_done",
                            agent="Supervisor",
                            payload={"task_id": task.id, "recovered_via": "retry_success"},
                        )
                    except Exception as retry_exc:
                        # Fallback to degraded recovery mode
                        finding = self.recovery.create_degraded_fallback_finding(
                            task=task,
                            agent_name=task.owner_agent,
                            error_msg=str(retry_exc),
                        )
                        await self.bus.emit(
                            event_type="recovery_done",
                            agent="Supervisor",
                            payload={"task_id": task.id, "recovered_via": "degraded_fallback"},
                        )

                state.findings[agent.name] = finding

                # Collect proposed assumptions
                for asm in finding.assumptions:
                    if not any(existing.name == asm.name and existing.proposed_by == asm.proposed_by for existing in state.assumptions):
                        state.assumptions.append(asm)

                finish_ts = time.time()
                finish_iso = datetime.now(timezone.utc).isoformat()

                state.execution_timeline[task.id] = {
                    "agent": task.owner_agent,
                    "start_time": start_ts,
                    "finish_time": finish_ts,
                    "duration_sec": round(finish_ts - start_ts, 4),
                    "start_iso": start_iso,
                    "finish_iso": finish_iso,
                }

                await self.bus.emit(
                    event_type="finding_posted",
                    agent=task.owner_agent,
                    payload={
                        "task_id": task.id,
                        "claim": finding.claim,
                        "recommendation": finding.recommendation,
                        "confidence": finding.confidence,
                        "assumptions_count": len(finding.assumptions),
                    },
                )
                return finding

            # Handle supervisor internal tasks (conflict, simulation, verification, report)
            result = await self._handle_supervisor_task(task, state)

            finish_ts = time.time()
            finish_iso = datetime.now(timezone.utc).isoformat()

            state.execution_timeline[task.id] = {
                "agent": task.owner_agent,
                "start_time": start_ts,
                "finish_time": finish_ts,
                "duration_sec": round(finish_ts - start_ts, 4),
                "start_iso": start_iso,
                "finish_iso": finish_iso,
            }
            return result

        except Exception as exc:
            await self.bus.emit(
                event_type="agent_failed",
                agent=task.owner_agent,
                payload={"task_id": task.id, "error": str(exc)},
            )
            raise

    async def _handle_supervisor_task(self, task: Task, state: WorkflowState) -> Any:
        """Internal handler for orchestrator synthesis, conflict resolution, and verification tasks."""
        if "conflict" in task.id:
            conflicts = detect_conflicts(state.findings, state.tasks)
            state.conflicts = conflicts
            for c in conflicts:
                await self.bus.emit(
                    event_type="conflict_detected",
                    agent="Supervisor",
                    payload={"conflict_id": c.id, "type": c.type, "agents": c.agents, "disputed_item": c.disputed_item},
                )
            return {"status": "conflicts_detected", "count": len(conflicts)}

        elif "simulation" in task.id:
            # 1. Resolve conflicts via simulation
            resolved_conflicts, conflict_sim_runs = resolve_conflicts_with_simulation(state.conflicts, state.findings)
            state.conflicts = resolved_conflicts
            state.simulation_runs.extend(conflict_sim_runs)

            # 2. Run standard 3 strategies x 3 scenarios matrix
            base_params = {asm.name: asm.base for asm in state.assumptions}
            strategies = [STRATEGY_A, STRATEGY_B, STRATEGY_C]
            scenarios = ["conservative", "expected", "optimistic"]
            for strat in strategies:
                for scen in scenarios:
                    run = simulate(strat, scen, base_params)
                    state.simulation_runs.append(run)
                    await self.bus.emit(
                        event_type="simulation_run",
                        agent="Supervisor",
                        payload={"simulation_id": run.id, "strategy": strat, "scenario": scen},
                    )

            return {"status": "simulations_completed", "total_runs": len(state.simulation_runs)}

        elif "verification" in task.id:
            company = load_company_snapshot()
            all_passed, results = verify_workflow(state.assumptions, state.simulation_runs, company)
            state.verification_results = results
            passed_count = sum(1 for r in results if r.status == "passed")

            if all_passed:
                await self.bus.emit(
                    event_type="verification_passed",
                    agent="Supervisor",
                    payload={"task_id": task.id, "checks_passed": passed_count, "total_checks": len(results)},
                )
                return {"status": "verification_passed", "results": [r.model_dump() for r in results]}
            else:
                await self.bus.emit(
                    event_type="verification_failed",
                    agent="Supervisor",
                    payload={"task_id": task.id, "failures": [r.detail for r in results if r.status == "failed"]},
                )
                return {"status": "verification_failed", "results": [r.model_dump() for r in results]}

        elif "report" in task.id:
            company = load_company_snapshot()
            report_dict = build_consolidated_report(state, company)
            state.report = report_dict
            await self.bus.emit(
                event_type="report_ready",
                agent="Supervisor",
                payload={
                    "task_id": task.id,
                    "report_id": f"rep-{state.decision.id}",
                    "recommendation": report_dict["recommendation"],
                    "confidence": report_dict["confidence"],
                },
            )
            return {"status": "report_ready", "report_id": f"rep-{state.decision.id}"}

        return {"status": "done"}

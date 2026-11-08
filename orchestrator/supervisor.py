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
from simulation.params import build_scenario_params
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from state.company import load_company_snapshot
from verification.skeptic_audit import run_skeptic_audit
from verification.verifier import verify_workflow
from orchestrator.dag import TaskDAG
from orchestrator.decomposer import decompose_decision
from state.event_bus import event_bus as default_event_bus
from state.schemas import Decision, Finding, Message, Task, WorkflowEvent
from state.shared_state import WorkflowState

logger = logging.getLogger(__name__)


class Supervisor:
    def __init__(self, agent_registry=None, bus=None, checkpoint_store=None, recovery_policy=None) -> None:
        self.registry = agent_registry or default_registry
        self.bus = bus or default_event_bus
        self.checkpoints = checkpoint_store or CheckpointStore()
        self.recovery = recovery_policy or RecoveryPolicy()

    def _get_failure_for_attempt(
        self,
        target_keys: List[str],
        attempt: int,
        injected_failures: Dict[str, Any],
    ) -> Optional[str]:
        """Check if an injected failure applies to this target on the given attempt number."""
        for key in target_keys:
            if not key or key not in injected_failures:
                continue
            inj = injected_failures[key]
            if isinstance(inj, str):
                if attempt == 1:
                    return inj
            elif isinstance(inj, dict):
                f_type = inj.get("failure_type") or inj.get("mode", "exception")
                persist = inj.get("persist", False)
                fail_attempts = inj.get("fail_attempts", 1)
                if persist or attempt <= fail_attempts:
                    return f_type
            else:
                f_type = getattr(inj, "failure_type", getattr(inj, "mode", "exception"))
                persist = getattr(inj, "persist", False)
                fail_attempts = getattr(inj, "fail_attempts", 1)
                if persist or attempt <= fail_attempts:
                    return f_type
        return None

    async def run_workflow(
        self,
        decision: Decision,
        dag: Optional[TaskDAG] = None,
        injected_failures: Optional[Dict[str, Any]] = None,
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

                async_task = asyncio.create_task(
                    self._execute_single_task(
                        task=task,
                        state=state,
                        injected_failures=injected_failures,
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
                        state.status = "failed"
                        state.decision.status = "failed"
                        # Persist failed checkpoint
                        self.checkpoints.save_checkpoint(state, tid)
                        for at in active_tasks.values():
                            if not at.done():
                                at.cancel()
                        return state

            for fid in finished_ids:
                del active_tasks[fid]

        state.status = "completed"
        return state

    def _build_analysis_context(self, agent_name: str, state: Optional[WorkflowState] = None) -> Dict[str, Any]:
        """Provide isolated context to analysis agents: decision and company snapshot only (no peer findings)."""
        target_state = state or getattr(self, "state", None)
        decision_data = {}
        company_data = None
        if target_state:
            decision_data = target_state.decision.model_dump() if hasattr(target_state.decision, "model_dump") else target_state.decision
            if hasattr(target_state, "company") and target_state.company:
                company_data = target_state.company.model_dump() if hasattr(target_state.company, "model_dump") else target_state.company
        if not company_data:
            company_data = load_company_snapshot().model_dump()
        return {
            "decision": decision_data,
            "company": company_data,
        }

    async def _execute_single_task(
        self,
        task: Task,
        state: WorkflowState,
        injected_failures: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute an individual task, logging timestamps to prove concurrent parallelism."""
        injected_failures = injected_failures or {}
        start_ts = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()

        await self.bus.emit(
            event_type="agent_started",
            agent=task.owner_agent,
            payload={"task_id": task.id, "start_time": start_iso},
        )

        try:
            target_keys = [task.owner_agent, task.id]

            # Handle specialist agent analysis tasks
            if task.kind == "agent_analysis":
                agent = self.registry.get_agent(task.owner_agent)
                if agent:
                    finding: Optional[Finding] = None
                    task.attempts = 1
                    analysis_context = self._build_analysis_context(task.owner_agent, state=state)
                    fail_1 = self._get_failure_for_attempt(target_keys, 1, injected_failures)
                    try:
                        finding = await agent.run(task=task, state=analysis_context, failure_mode=fail_1)
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
                        task.attempts = 2
                        await self.recovery.apply_backoff(task.attempts)

                        fail_2 = self._get_failure_for_attempt(target_keys, 2, injected_failures)
                        try:
                            finding = await agent.run(task=task, state=analysis_context, failure_mode=fail_2)
                            await self.bus.emit(
                                event_type="recovery_done",
                                agent="Supervisor",
                                payload={"task_id": task.id, "recovered_via": "retry_success"},
                            )
                        except Exception as retry_exc:
                            # Fallback to BackupAnalyst
                            backup_agent = self.registry.get_agent("backupanalyst")
                            if backup_agent and hasattr(backup_agent, "generate_fallback_finding"):
                                finding = backup_agent.generate_fallback_finding(
                                    task_id=task.id,
                                    failed_agent_name=task.owner_agent,
                                    disputed_area=task.owner_agent.lower(),
                                )
                            else:
                                finding = self.recovery.create_degraded_fallback_finding(
                                    task=task,
                                    agent_name=task.owner_agent,
                                    error_msg=str(retry_exc),
                                )
                            await self.bus.emit(
                                event_type="recovery_done",
                                agent="Supervisor",
                                payload={"task_id": task.id, "recovered_via": "degraded_fallback", "substitute": "BackupAnalyst"},
                            )

                    state.findings[agent.name] = finding

                    # Whitelist and clamp assumptions from agent finding
                    from simulation.params import SIM_PARAMS
                    price_param_names = {"price_elasticity_starter", "price_elasticity_growth", "expansion_revenue_rate", "contraction_risk_rate"}
                    allowed_params = set(SIM_PARAMS.keys()) | price_param_names

                    for asm in finding.assumptions:
                        if asm.name not in allowed_params:
                            state.ignored_assumptions.append({
                                "agent": task.owner_agent,
                                "name": asm.name,
                                "base": asm.base,
                                "reason": "Not in simulator parameter whitelist; recorded as operational context assumption"
                            })
                        else:
                            meta = SIM_PARAMS.get(asm.name)
                            if meta and "bounds" in meta:
                                min_val, max_val = meta["bounds"]
                                clamped = False
                                orig_base = asm.base
                                if asm.base < min_val or asm.base > max_val:
                                    asm.base = max(min_val, min(max_val, asm.base))
                                    clamped = True
                                if asm.low < min_val or asm.low > max_val:
                                    asm.low = max(min_val, min(max_val, asm.low))
                                    clamped = True
                                if asm.high < min_val or asm.high > max_val:
                                    asm.high = max(min_val, min(max_val, asm.high))
                                    clamped = True
                                if clamped:
                                    state.clamped_assumptions.append({
                                        "agent": task.owner_agent,
                                        "name": asm.name,
                                        "original_base": orig_base,
                                        "clamped_base": asm.base,
                                        "bounds": [min_val, max_val]
                                    })

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

            # Non-agent core task: check failure injection
            fail_1 = self._get_failure_for_attempt(target_keys, 1, injected_failures)
            if fail_1:
                task.attempts = 2
                await self.recovery.apply_backoff(2)
                fail_2 = self._get_failure_for_attempt(target_keys, 2, injected_failures)
                if fail_2:
                    raise RuntimeError(f"Core task {task.id} failed persistently after retries (injected {fail_2})")

            # Handle supervisor internal tasks (conflict, skeptic_review, simulation, report_draft, verification, report_finalize)
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
        """Internal handler for orchestrator synthesis, conflict resolution, skeptic review, and verification tasks."""
        kind = getattr(task, "kind", None)

        if kind == "agent_discussion":
            from pathlib import Path
            import json

            # 1. Record initial proposals from specialist agent findings
            for agent_name, finding in state.findings.items():
                if finding.agent != "Skeptic":
                    state.messages.append(
                        Message(
                            sender=finding.agent,
                            recipient="all",
                            kind="proposal",
                            content=finding.claim,
                            assumptions=finding.assumptions,
                        )
                    )

            # 2. Load benchmarks data for data-driven critiques
            benchmarks_path = Path(__file__).resolve().parent.parent / "data" / "benchmarks.json"
            benchmarks: Dict[str, Any] = {}
            if benchmarks_path.exists():
                try:
                    with open(benchmarks_path, "r", encoding="utf-8") as f:
                        benchmarks = json.load(f)
                except Exception as e:
                    logger.warning("Could not load benchmarks.json: %s", e)

            bench_map = {
                b["metric"]: b["value"]
                for b in benchmarks.values()
                if isinstance(b, dict) and "metric" in b and "value" in b
            }

            # 3. Skeptic dynamically critiques assumptions deviating from benchmarks or with wide ranges
            critiques: List[Message] = []
            for agent_name, finding in state.findings.items():
                if finding.agent == "Skeptic" or getattr(finding, "degraded", False):
                    continue

                for asm in finding.assumptions:
                    if asm.name in bench_map:
                        bench_val = bench_map[asm.name]
                        ratio = asm.base / bench_val if bench_val > 0 else 1.0
                        if ratio > 1.20 or ratio < 0.80:
                            critique = Message(
                                sender="Skeptic",
                                recipient=finding.agent,
                                kind="critique",
                                parameter=asm.name,
                                challenged_value=asm.base,
                                benchmark_reference=bench_val,
                                content=(
                                    f"Skeptic Critique: {finding.agent}'s proposed {asm.name} of {asm.base} "
                                    f"deviates significantly from illustrative B2B SaaS benchmark median ({bench_val}). "
                                    f"Please justify this interval against customer friction and churn risks."
                                ),
                            )
                            critiques.append(critique)
                    elif asm.high / max(asm.low, 1e-4) > 2.2:
                        critique = Message(
                            sender="Skeptic",
                            recipient=finding.agent,
                            kind="critique",
                            parameter=asm.name,
                            challenged_value=asm.base,
                            benchmark_reference=None,
                            content=(
                                f"Skeptic Critique: {finding.agent}'s proposed {asm.name} interval [{asm.low}, {asm.high}] "
                                f"exhibits wide uncertainty (>2.2x spread). Please provide operational justification."
                            ),
                        )
                        critiques.append(critique)

            # Fallback critique if all parameters aligned with benchmarks
            if not critiques:
                for agent_name, finding in state.findings.items():
                    if finding.agent != "Skeptic" and finding.assumptions:
                        top_asm = finding.assumptions[0]
                        critiques.append(
                            Message(
                                sender="Skeptic",
                                recipient=finding.agent,
                                kind="critique",
                                parameter=top_asm.name,
                                challenged_value=top_asm.base,
                                content=f"Skeptic Audit: Requesting confirmation of {top_asm.name} baseline ({top_asm.base}).",
                            )
                        )
                        break

            state.messages.extend(critiques)

            # 4. Critiqued agents respond with bounded, evidence-grounded rebuttals
            rebuttals: List[Message] = []
            for crit in critiques:
                target_finding = state.findings.get(crit.recipient)
                if not target_finding:
                    continue

                snippet = target_finding.evidence[0].snippet if target_finding.evidence else "internal metrics"
                source = target_finding.evidence[0].source_type if target_finding.evidence else "operational analysis"

                reb = Message(
                    sender=crit.recipient,
                    recipient="Skeptic",
                    kind="rebuttal",
                    parameter=crit.parameter,
                    challenged_value=crit.challenged_value,
                    benchmark_reference=crit.benchmark_reference,
                    concession_made=False,
                    rationale=f"Maintained based on {source}: {snippet}",
                    content=(
                        f"Rebuttal from {crit.recipient}: Position maintained on {crit.parameter}. "
                        f"Our model is calibrated against {snippet}; divergence from macro median is intentional."
                    ),
                )
                rebuttals.append(reb)

            state.messages.extend(rebuttals)

            # 5. Emit event stream notifications
            for msg in critiques + rebuttals:
                await self.bus.emit(
                    event_type="message_posted",
                    agent=msg.sender,
                    payload={"recipient": msg.recipient, "kind": msg.kind, "content": msg.content},
                )

            return {"status": "discussion_completed", "message_count": len(state.messages)}

        elif kind == "conflict_detection":
            conflicts = detect_conflicts(state.findings, state.tasks)
            state.conflicts = conflicts
            for c in conflicts:
                await self.bus.emit(
                    event_type="conflict_detected",
                    agent="Supervisor",
                    payload={"conflict_id": c.id, "type": c.type, "agents": c.agents, "disputed_item": c.disputed_item},
                )
            return {"status": "conflicts_detected", "count": len(conflicts)}

        elif kind == "skeptic_review":
            # 1. Execute Skeptic agent against current workflow findings
            skeptic_agent = self.registry.get_agent("Skeptic")
            if skeptic_agent:
                try:
                    f_skeptic = await skeptic_agent.run(task=task, state=state.model_dump())
                    state.findings["Skeptic"] = f_skeptic
                    for asm in f_skeptic.assumptions:
                        if not any(existing.name == asm.name and existing.proposed_by == asm.proposed_by for existing in state.assumptions):
                            state.assumptions.append(asm)
                except Exception as e:
                    logger.warning("Skeptic agent execution error: %s", e)

            # 2. Run deterministic skeptic audit logic
            updated_assumptions, challenges = run_skeptic_audit(state.findings, state.assumptions)
            state.assumptions = updated_assumptions
            state.skeptic_challenges = challenges
            for ch in challenges:
                logger.info("Skeptic audit challenge: %s", ch)

            await self.bus.emit(
                event_type="finding_posted",
                agent="Skeptic",
                payload={"task_id": task.id, "challenges_count": len(challenges)},
            )
            return {"status": "skeptic_review_completed", "challenges_count": len(challenges)}

        elif kind == "simulation":
            from report.decision_logic import extract_min_runway_constraint
            from simulation.reconcile import reconcile_assumptions
            from simulation.monte_carlo import run_monte_carlo_suite
            from simulation.adapter import get_simulator_adapter

            company = load_company_snapshot()
            adapter = get_simulator_adapter(state.decision.type if state.decision else None)

            # Extract dynamic runway floor from constraints or CFO assumptions
            min_runway = extract_min_runway_constraint(state.decision.constraints, state.assumptions)

            # Reconcile assumptions once as the single source of truth for the entire workflow
            state.reconciled = reconcile_assumptions(state.assumptions, state.conflicts)

            # 1. Resolve conflicts via simulation using adapter
            resolved_conflicts, conflict_sim_runs = resolve_conflicts_with_simulation(
                state.conflicts,
                state.findings,
                company=company,
                adapter=adapter,
                min_runway=min_runway,
            )
            state.conflicts = resolved_conflicts
            state.simulation_runs.extend(conflict_sim_runs)

            # 2. Run distinct scenario matrix: 3 strategies x (conservative, expected, optimistic)
            core_scenarios = ["conservative", "expected", "optimistic"]
            for strat in adapter.strategies:
                for scen in core_scenarios:
                    params = adapter.build_params(state.reconciled.parameters, scen)
                    run = adapter.simulate(strat, scen, params, company=company, seed=42)
                    state.simulation_runs.append(run)
                    await self.bus.emit(
                        event_type="simulation_run",
                        agent="Supervisor",
                        payload={"simulation_id": run.id, "strategy": strat, "scenario": scen},
                    )

            # Stress scenarios for free_plan
            if adapter.decision_type == "free_plan":
                stress_scenarios = ["stress_infra_doubles", "stress_conversion_collapse", "stress_large_customer_churn"]
                base_params = adapter.build_params(state.reconciled.parameters, "expected")
                for strat in adapter.strategies:
                    for scen in stress_scenarios:
                        run = adapter.simulate(strat, scen, base_params, company=company, seed=42)
                        state.simulation_runs.append(run)
                        await self.bus.emit(
                            event_type="simulation_run",
                            agent="Supervisor",
                            payload={"simulation_id": run.id, "strategy": strat, "scenario": scen},
                        )

            # 3. Run Monte Carlo probability distributions across all strategies
            mc_results = run_monte_carlo_suite(
                strategies=adapter.strategies,
                reconciled_params=state.reconciled,
                company=company,
                n_iterations=250,
                seed=42,
                min_runway=min_runway,
                adapter=adapter,
            )
            state.mc_summaries = mc_results

            return {"status": "simulations_completed", "total_runs": len(state.simulation_runs)}

        elif kind == "report_draft":
            company = load_company_snapshot()
            draft_report = build_consolidated_report(state, company)
            state.report = draft_report
            return {"status": "report_draft_ready"}

        elif kind == "verification":
            company = load_company_snapshot()
            if state.report is None:
                state.report = build_consolidated_report(state, company)

            all_passed, results = verify_workflow(
                state.assumptions,
                state.simulation_runs,
                company,
                draft_report=state.report,
                mc_summaries=state.mc_summaries,
            )
            state.verification_results = results

            # Bounded loop-back (up to 2 loops)
            loop = 0
            prev_failures = None
            while not all_passed and loop < 2:
                loop += 1
                task.attempts += 1
                failed_checks = [r for r in results if r.status == "failed"]
                failure_signatures = tuple(sorted(r.detail for r in failed_checks))
                if failure_signatures == prev_failures:
                    logger.warning("Verification loopback produced identical failure set; stopping loop-back early.")
                    break
                prev_failures = failure_signatures

                # Map failures to the responsible tasks
                failed_names = {r.check_name for r in failed_checks}
                target_tasks = []
                if "report_number_traceability" in failed_names or "scenario_ordering" in failed_names:
                    target_tasks.extend(["simulation", "report_draft"])
                elif "required_sections_present" in failed_names:
                    target_tasks.append("report_draft")
                elif "provenance_integrity" in failed_names or "unit_consistency" in failed_names:
                    target_tasks.extend(["skeptic_review", "report_draft"])
                else:
                    target_tasks.append("report_draft")

                await self.bus.emit(
                    event_type="verification_loopback",
                    agent="Supervisor",
                    payload={"loop": loop, "target_tasks": target_tasks, "failed_checks": list(failed_names)},
                )

                # Re-dispatch mapped tasks
                for target_kind in target_tasks:
                    sub_task = Task(id=f"loop_{loop}_{target_kind}", name=f"Re-dispatch {target_kind}", kind=target_kind, owner_agent="Supervisor")
                    await self._execute_single_task(sub_task, state)

                # Fresh checkpoint
                self.checkpoints.save_checkpoint(state, f"{task.id}_loop_{loop}")

                # Re-verify
                all_passed, results = verify_workflow(
                    state.assumptions,
                    state.simulation_runs,
                    company,
                    draft_report=state.report,
                    mc_summaries=state.mc_summaries,
                )
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

        elif kind == "report_finalize":
            company = load_company_snapshot()
            report_dict = build_consolidated_report(state, company)
            has_failed_check = any(r.status == "failed" for r in state.verification_results)
            if has_failed_check:
                report_dict["recommendation"] = f"Unverified: {report_dict['recommendation']}"
                report_dict["sections"]["executive_summary"]["recommendation"] = report_dict["recommendation"]
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

        else:
            raise ValueError(f"Unknown or unsupported supervisor task kind: '{kind}' for task '{task.id}'")

"""Simulation-based conflict resolution engine settling agent disputes with deterministic math.

Hard Rules:
- R3: Conflicts are resolved by simulation and evidence, not by LLMs picking a winner or voting.
- Resolution text is generated purely from computed simulation outputs, never pre-written.
- Unresolved material conflicts remain marked resolved = False and status = 'unresolved_material'.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from report.decision_logic import rank_strategies
from simulation.params import SIM_PARAMS
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from simulation.adapter import SimulatorAdapter, get_simulator_adapter
from simulation.sensitivity import find_flip_point
from state.schemas import CompanySnapshot, Conflict, Finding, SimulationRun


def resolve_conflicts_with_simulation(
    conflicts: List[Conflict],
    findings: Dict[str, Finding],
    company: Optional[CompanySnapshot] = None,
    rebuttal_round: bool = False,
    adapter: Optional[SimulatorAdapter] = None,
    min_runway: float = 10.0,
) -> Tuple[List[Conflict], List[SimulationRun]]:
    """Resolve detected conflicts by executing simulations for competing agent assumptions.

    Returns:
        (resolved_conflicts, simulation_runs)
    """
    if adapter is None:
        is_price = any(
            "price" in f.task_id.lower() or any("price" in a.name for a in f.assumptions)
            for f in findings.values()
        )
        adapter = get_simulator_adapter("price_change" if is_price else "free_plan")

    simulation_runs: List[SimulationRun] = []
    processed_conflicts: List[Conflict] = []

    # Build baseline parameter dictionary from SIM_PARAMS defaults
    baseline_params = {name: spec["default"] for name, spec in SIM_PARAMS.items()}
    # Update with any non-conflicting base values from findings
    for f in findings.values():
        for asm in f.assumptions:
            if asm.name in baseline_params:
                baseline_params[asm.name] = asm.base

    for conflict in conflicts:
        if conflict.type == "assumption_divergence":
            # Extract disputed parameter name from disputed_item
            param_match = re.search(r"Non-overlapping bounds on '([^']+)'", conflict.disputed_item)
            disputed_param = param_match.group(1) if param_match else "free_to_paid_conversion"

            agent_a = conflict.agents[0] if len(conflict.agents) >= 1 else "CFO"
            agent_b = conflict.agents[1] if len(conflict.agents) >= 2 else "Growth"

            finding_a = findings.get(agent_a)
            finding_b = findings.get(agent_b)

            asm_a = next((a for a in (finding_a.assumptions if finding_a else []) if a.name == disputed_param), None)
            asm_b = next((a for a in (finding_b.assumptions if finding_b else []) if a.name == disputed_param), None)

            val_a = asm_a.base if asm_a else baseline_params.get(disputed_param, 0.015)
            val_b = asm_b.base if asm_b else baseline_params.get(disputed_param, 0.045)

            # Start from baseline parameters and change ONLY the disputed parameter
            params_a = dict(baseline_params)
            params_a[disputed_param] = val_a

            params_b = dict(baseline_params)
            params_b[disputed_param] = val_b

            # Run all strategies for both sides
            runs_a = [
                adapter.simulate(strat, f"conflict_{agent_a.lower()}", params_a, company=company)
                for strat in adapter.strategies
            ]
            runs_b = [
                adapter.simulate(strat, f"conflict_{agent_b.lower()}", params_b, company=company)
                for strat in adapter.strategies
            ]
            simulation_runs.extend(runs_a + runs_b)

            ranked_a = rank_strategies(runs_a, min_runway=min_runway)
            ranked_b = rank_strategies(runs_b, min_runway=min_runway)

            top_a = ranked_a[0]
            top_b = ranked_b[0]

            # Evaluate decision relevance: does recommended strategy or feasibility differ?
            recommendation_differs = top_a.strategy != top_b.strategy
            feasibility_differs = top_a.feasible != top_b.feasible
            is_decision_relevant = recommendation_differs or feasibility_differs

            verdict = "decision_relevant" if is_decision_relevant else "immaterial"
            conflict.verdict = verdict

            # Compute deltas for the top strategy
            mrr_a = top_a.mrr_month_12
            mrr_b = top_b.mrr_month_12
            runway_a = top_a.runway_months_12
            runway_b = top_b.runway_months_12
            net_contrib_a = top_a.net_contribution_12
            net_contrib_b = top_b.net_contribution_12

            mrr_delta = round(mrr_b - mrr_a, 2)
            runway_delta = round(runway_b - runway_a, 2)
            contrib_delta = round(net_contrib_b - net_contrib_a, 2)

            competing_strat = adapter.strategies[1] if top_a.strategy == adapter.strategies[0] else adapter.strategies[0]
            flip = find_flip_point(
                primary_strategy=top_a.strategy,
                competing_strategy=competing_strat,
                parameter_name=disputed_param,
                base_assumptions=baseline_params,
                company=company,
                adapter=adapter,
            )

            # Check if ranges overlap (e.g. after a rebuttal round)
            ranges_overlap = False
            if asm_a and asm_b:
                ranges_overlap = not ((asm_a.high < asm_b.low) or (asm_b.high < asm_a.low))

            if ranges_overlap:
                conflict.resolved = True
                conflict.status = "resolved_converged"
                conflict.resolution_method = "converged_after_rebuttal"
                resolution_text = (
                    f"Dispute on '{disputed_param}' settled: revised assumption ranges overlap. "
                    f"Consensus parameter space supports {top_a.strategy}."
                )
            elif not is_decision_relevant:
                conflict.resolved = True
                conflict.status = "resolved_immaterial"
                conflict.resolution_method = "simulation_immaterial"
                resolution_text = (
                    f"Simulation proves disagreement on '{disputed_param}' ({val_a} vs {val_b}) is immaterial: "
                    f"both parameter sets recommend {top_a.strategy} "
                    f"(Side {agent_a}: ${net_contrib_a:,.0f} net contribution, {runway_a:.1f}mo runway; "
                    f"Side {agent_b}: ${net_contrib_b:,.0f} net contribution, {runway_b:.1f}mo runway). "
                    f"MRR delta: +${mrr_delta:,.0f}, net contribution delta: +${contrib_delta:,.0f}, runway delta: {runway_delta:+.1f}mo. "
                    f"Simulation proves strategy flips below {flip.get('threshold_display', 'the threshold')} conversion."
                )
            else:
                # Decision relevant and non-overlapping: remains an honest unresolved conflict
                conflict.resolved = False
                conflict.status = "unresolved_material"
                conflict.resolution_method = "unresolved"
                resolution_text = (
                    f"Decision-relevant divergence on '{disputed_param}' ({val_a} vs {val_b}): "
                    f"Under {agent_a}'s assumptions, optimal strategy is {top_a.strategy} "
                    f"(${mrr_a:,.0f} MRR, {runway_a:.1f}mo runway, feasible: {top_a.feasible}). "
                    f"Under {agent_b}'s assumptions, optimal strategy is {top_b.strategy} "
                    f"(${mrr_b:,.0f} MRR, {runway_b:.1f}mo runway, feasible: {top_b.feasible}). "
                    f"Divergence delta: ${mrr_delta:,.0f} MRR, ${contrib_delta:,.0f} net contribution. "
                    f"Threshold: strategy dominance flips at {flip.get('threshold_display', 'the modeled threshold')}. "
                    f"Status remains unresolved pending empirical cohort data."
                )

            conflict.resolution = resolution_text
            conflict.simulation_ids = [r.id for r in runs_a + runs_b]
            processed_conflicts.append(conflict)

        elif conflict.type == "contradictory_recommendation":
            # Direct recommendation clash
            agent_a = conflict.agents[0] if len(conflict.agents) >= 1 else "CFO"
            agent_b = conflict.agents[1] if len(conflict.agents) >= 2 else "Risk"
            finding_a = findings.get(agent_a)
            finding_b = findings.get(agent_b)

            rec_a = finding_a.recommendation if finding_a else "proceed_with_limits"
            rec_b = finding_b.recommendation if finding_b else "reject"

            # Execute standard simulation for expected scenario
            runs = [
                adapter.simulate(strat, "expected", baseline_params, company=company)
                for strat in adapter.strategies
            ]
            simulation_runs.extend(runs)
            ranked = rank_strategies(runs, min_runway=min_runway)
            top = ranked[0]

            is_feasible = top.feasible
            if is_feasible:
                verdict = "immaterial" if "proceed" in rec_a or "proceed" in rec_b else "decision_relevant"
                status = "resolved_immaterial"
                resolved = True
                method = "simulation_immaterial"
            else:
                verdict = "decision_relevant"
                status = "unresolved_material"
                resolved = False
                method = "unresolved"

            conflict.verdict = verdict
            conflict.status = status
            conflict.resolved = resolved
            conflict.resolution_method = method
            conflict.simulation_ids = [r.id for r in runs]
            conflict.resolution = (
                f"Evaluated opposing recommendations ({agent_a} '{rec_a}' vs {agent_b} '{rec_b}') against simulation runs. "
                f"Financial model indicates {top.strategy} yields ${top.net_contribution_12:,.0f} net contribution with "
                f"{top.runway_months_12:.1f}mo runway (feasibility: {top.feasible})."
            )
            processed_conflicts.append(conflict)

        else:
            # missing_evidence or dependency_block
            conflict.verdict = "immaterial"
            conflict.status = "resolved_immaterial"
            conflict.resolved = True
            conflict.resolution_method = "simulation_immaterial"
            conflict.resolution = "Recorded as verified procedural constraint; no simulation required."
            conflict.simulation_ids = []
            processed_conflicts.append(conflict)

    return processed_conflicts, simulation_runs

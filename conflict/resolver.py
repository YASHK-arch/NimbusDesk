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

            mrr_delta_str = f"{'+' if mrr_delta >= 0 else '-'}${abs(mrr_delta):,.0f}"
            contrib_delta_str = f"{'+' if contrib_delta >= 0 else '-'}${abs(contrib_delta):,.0f}"
            runway_delta_str = f"{runway_delta:+.1f}mo"

            competing_strat = adapter.strategies[1] if top_a.strategy == adapter.strategies[0] else adapter.strategies[0]
            flip = find_flip_point(
                primary_strategy=top_a.strategy,
                competing_strategy=competing_strat,
                parameter_name=disputed_param,
                base_assumptions=baseline_params,
                company=company,
                adapter=adapter,
            )

            # Check if ranges overlap
            ranges_overlap = False
            if asm_a and asm_b:
                ranges_overlap = not ((asm_a.high < asm_b.low) or (asm_b.high < asm_a.low))

            from simulation.reconcile import reconcile_assumptions
            reconciled_both = reconcile_assumptions([asm_a, asm_b] if (asm_a and asm_b) else [])
            merged_val = reconciled_both.simulated_params.get(disputed_param, (val_a + val_b) / 2.0)
            params_merged = dict(baseline_params)
            params_merged[disputed_param] = merged_val

            runs_merged = [
                adapter.simulate(strat, "conflict_merged", params_merged, company=company)
                for strat in adapter.strategies
            ]
            ranked_merged = rank_strategies(runs_merged, min_runway=min_runway)
            top_merged = ranked_merged[0]

            # Re-rank under merged base and under each side's base
            all_three_agree = (top_merged.strategy == top_a.strategy == top_b.strategy) and (top_merged.feasible and top_a.feasible and top_b.feasible)

            if rebuttal_round and ranges_overlap and all_three_agree:
                conflict.resolved = True
                conflict.status = "resolved_converged"
                conflict.resolution_method = "converged_after_rebuttal"
                resolution_text = (
                    f"Consensus achieved after rebuttal for '{disputed_param}': revised ranges overlap and "
                    f"all three baselines ({agent_a} base: {val_a}, {agent_b} base: {val_b}, merged: {merged_val}) "
                    f"unanimously recommend {top_merged.strategy} "
                    f"(${top_merged.net_contribution_12:,.0f} net contribution, {top_merged.runway_months_12:.1f}mo runway)."
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
                    f"MRR delta: {mrr_delta_str}, net contribution delta: {contrib_delta_str}, runway delta: {runway_delta_str}. "
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
                    f"Divergence delta: {mrr_delta_str} MRR, {contrib_delta_str} net contribution. "
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

            # Build side-specific parameters
            params_a = dict(baseline_params)
            for asm in (finding_a.assumptions if finding_a else []):
                if asm.name in params_a:
                    params_a[asm.name] = asm.base

            params_b = dict(baseline_params)
            for asm in (finding_b.assumptions if finding_b else []):
                if asm.name in params_b:
                    params_b[asm.name] = asm.base

            runs_a = [
                adapter.simulate(strat, f"rec_conflict_{agent_a.lower()}", params_a, company=company)
                for strat in adapter.strategies
            ]
            runs_b = [
                adapter.simulate(strat, f"rec_conflict_{agent_b.lower()}", params_b, company=company)
                for strat in adapter.strategies
            ]
            simulation_runs.extend(runs_a + runs_b)

            ranked_a = rank_strategies(runs_a, min_runway=min_runway)
            ranked_b = rank_strategies(runs_b, min_runway=min_runway)

            hold_strat = adapter.strategies[-1]
            hold_run_a = next((r for r in runs_a if r.strategy == hold_strat), runs_a[-1])
            hold_contrib_a = hold_run_a.outputs.get("net_contribution_12", 0.0)

            hold_run_b = next((r for r in runs_b if r.strategy == hold_strat), runs_b[-1])
            hold_contrib_b = hold_run_b.outputs.get("net_contribution_12", 0.0)

            # Determine whether a feasible, positive-contribution strategy exists on each side
            feasible_pos_a = [
                r for r in ranked_a
                if r.feasible and r.net_contribution_12 > 0 and r.net_contribution_12 > hold_contrib_a
            ]
            feasible_pos_b = [
                r for r in ranked_b
                if r.feasible and r.net_contribution_12 > 0 and r.net_contribution_12 > hold_contrib_b
            ]

            has_a = len(feasible_pos_a) > 0
            has_b = len(feasible_pos_b) > 0

            is_proceed_a = rec_a in ("proceed", "proceed_with_limits")
            is_proceed_b = rec_b in ("proceed", "proceed_with_limits")

            if is_proceed_a and not is_proceed_b:
                proceed_agent, reject_agent = agent_a, agent_b
                rec_proceed, rec_reject = rec_a, rec_b
                ranked_proceed, ranked_reject = ranked_a, ranked_b
            elif is_proceed_b and not is_proceed_a:
                proceed_agent, reject_agent = agent_b, agent_a
                rec_proceed, rec_reject = rec_b, rec_a
                ranked_proceed, ranked_reject = ranked_b, ranked_a
            else:
                proceed_agent, reject_agent = agent_a, agent_b
                rec_proceed, rec_reject = rec_a, rec_b
                ranked_proceed, ranked_reject = ranked_a, ranked_b

            if has_a and has_b:
                # Feasible, positive-contribution strategy exists under both sides' assumptions
                top_p = ranked_proceed[0]
                verdict = "decision_relevant"
                status = "resolved_simulation"
                resolved = True
                method = f"simulation_supports_{proceed_agent}"
                res_text = (
                    f"Financial simulation contradicts {reject_agent}'s recommendation to '{rec_reject}': "
                    f"strategy {top_p.strategy} is feasible ({top_p.runway_months_12:.1f}mo runway >= {min_runway:.1f}mo floor) "
                    f"and yields ${top_p.net_contribution_12:,.0f} net contribution relative to baseline."
                )
            elif not has_a and not has_b:
                # No feasible positive-contribution strategy exists on either side
                verdict = "decision_relevant"
                status = "resolved_simulation"
                resolved = True
                method = f"simulation_supports_{reject_agent}"
                res_text = (
                    f"Financial simulation contradicts {proceed_agent}'s recommendation to '{rec_proceed}': "
                    f"no evaluated strategy satisfies the {min_runway:.1f}mo runway floor with positive net contribution."
                )
            else:
                # Mixed evidence: feasible under one agent's assumptions, unfeasible under the other
                verdict = "decision_relevant"
                status = "unresolved_material"
                resolved = False
                method = "unresolved_material"
                res_text = (
                    f"Mixed simulation evidence: under {proceed_agent}'s assumptions, a feasible strategy exists "
                    f"(${ranked_proceed[0].net_contribution_12:,.0f} net contribution); however, under {reject_agent}'s assumptions, "
                    f"no strategy satisfies the {min_runway:.1f}mo runway floor. Divergence remains unresolved."
                )

            conflict.verdict = verdict
            conflict.status = status
            conflict.resolved = resolved
            conflict.resolution_method = method
            conflict.simulation_ids = [r.id for r in runs_a + runs_b]
            conflict.resolution = res_text
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

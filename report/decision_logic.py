"""Deterministic decision logic for strategy ranking, feasibility filtering, and dynamic confidence scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from state.schemas import Assumption, SimulationRun, VerificationResult


@dataclass
class RankedStrategy:
    strategy: str
    net_contribution_12: float
    runway_months_12: float
    mrr_month_12: float
    gross_margin_12: float
    feasible: bool
    unfeasibility_reason: Optional[str] = None


def extract_min_runway_constraint(
    constraints: Optional[List[str]] = None,
    assumptions: Optional[List[Assumption]] = None,
    default_min_runway: float = 10.0,
) -> float:
    """Extract minimum required runway floor from constraints or CFO assumptions."""
    # 1. Check constraints list
    if constraints:
        for c in constraints:
            match = re.search(r"(\d+(?:\.\d+)?)\s*months?", c, re.IGNORECASE)
            if match:
                return float(match.group(1))

    # 2. Check CFO assumptions
    if assumptions:
        for asm in assumptions:
            if asm.name in ("min_acceptable_runway_months", "min_runway_months"):
                return float(asm.base)

    return default_min_runway


def rank_strategies(
    sim_runs: List[SimulationRun],
    constraints: Optional[List[str]] = None,
    assumptions: Optional[List[Assumption]] = None,
    min_runway: Optional[float] = None,
) -> List[RankedStrategy]:
    """Rank strategies evaluated under the expected scenario by net contribution subject to runway feasibility.

    Feasibility condition: runway_months_12 >= min_runway.
    Feasible strategies are ranked by net_contribution_12 descending, tie-breaking by runway_months_12.
    Unfeasible strategies are sorted by runway_months_12 descending.
    """
    if min_runway is None:
        min_runway = extract_min_runway_constraint(constraints, assumptions, default_min_runway=10.0)

    # Collect expected scenario runs per strategy
    expected_runs: Dict[str, SimulationRun] = {}
    for r in sim_runs:
        if r.scenario == "expected":
            expected_runs[r.strategy] = r

    # Fallback to first available run per strategy if expected is missing
    if not expected_runs:
        for r in sim_runs:
            if r.strategy not in expected_runs:
                expected_runs[r.strategy] = r

    evaluated: List[RankedStrategy] = []
    for strat, run in expected_runs.items():
        out = run.outputs
        net_contrib = out.get("net_contribution_12", 0.0)
        runway = out.get("runway_months_12", 0.0)
        mrr = out.get("mrr_month_12", 0.0)
        gm = out.get("gross_margin_month_12", 0.0)

        # Check both month-12 runway and minimum runway experienced in history
        history = out.get("history", [])
        min_runway_in_history = min(h.get("runway_months", 0.0) for h in history) if history else runway

        feasible = (runway >= min_runway) and (min_runway_in_history > 0.0)
        if feasible:
            reason = None
        elif min_runway_in_history <= 0.0:
            reason = f"Company suffers cash depletion/insolvency during trajectory (min runway: {min_runway_in_history:.1f}mo)"
        else:
            reason = f"Projected runway {runway:.1f}mo violates {min_runway:.1f}mo minimum safety floor"

        evaluated.append(
            RankedStrategy(
                strategy=strat,
                net_contribution_12=net_contrib,
                runway_months_12=runway,
                mrr_month_12=mrr,
                gross_margin_12=gm,
                feasible=feasible,
                unfeasibility_reason=reason,
            )
        )

    feasible_list = [s for s in evaluated if s.feasible]
    unfeasible_list = [s for s in evaluated if not s.feasible]

    feasible_list.sort(key=lambda s: (s.net_contribution_12, s.runway_months_12), reverse=True)
    unfeasible_list.sort(key=lambda s: (s.runway_months_12, s.net_contribution_12), reverse=True)

    return feasible_list + unfeasible_list


def compute_confidence(
    ranked: List[RankedStrategy],
    mc_summaries: Optional[Dict[str, Any]] = None,
    assumptions: Optional[List[Assumption]] = None,
    degraded_agents: Optional[List[str]] = None,
    unresolved_conflicts: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Compute holistic recommendation confidence based on margin, Monte Carlo stability, assumption rigor, and penalties."""
    reasons: List[str] = []
    score = 0.50

    if not ranked:
        return {"level": "Low", "score": 0.0, "reasons": ["No strategies evaluated."]}

    # (a) Margin between first and second strategy
    top = ranked[0]
    if not top.feasible:
        score = 0.20
        reasons.append("Top-ranked strategy violates minimum runway constraint; no feasible option available.")
    elif len(ranked) >= 2 and ranked[1].feasible:
        second = ranked[1]
        margin = top.net_contribution_12 - second.net_contribution_12
        if margin > 50_000:
            score += 0.20
            reasons.append(f"Strong financial margin (+${margin:,.0f} net contribution advantage over {second.strategy}).")
        elif margin > 15_000:
            score += 0.10
            reasons.append(f"Moderate financial margin (+${margin:,.0f} net contribution advantage over {second.strategy}).")
        else:
            reasons.append(f"Narrow financial margin (+${margin:,.0f} advantage over {second.strategy}).")
    elif top.feasible:
        score += 0.15
        reasons.append("Top strategy is the only feasible option satisfying runway constraints.")

    # (b) Monte Carlo stability if available
    if mc_summaries and top.strategy in mc_summaries:
        strat_mc = mc_summaries[top.strategy]
        p_best = strat_mc.get("p_best", 0.5)
        p_feasible = strat_mc.get("p_feasible", 0.5)
        mc_contribution = (p_best * 0.15) + (p_feasible * 0.10)
        score += mc_contribution
        reasons.append(f"Monte Carlo stability: {p_best*100:.0f}% win probability across sampled scenarios ({p_feasible*100:.0f}% feasibility).")

    # (c) Average assumption confidence
    if assumptions:
        avg_asm_conf = sum(a.confidence for a in assumptions) / len(assumptions)
        score += (avg_asm_conf - 0.50) * 0.20
        reasons.append(f"Assumption rigor: average peer-reviewed assumption confidence is {avg_asm_conf*100:.1f}%.")

    # (d) Penalties for degraded execution or unresolved conflicts
    if degraded_agents:
        penalty = 0.15 * len(degraded_agents)
        score -= penalty
        reasons.append(f"Execution penalty: {len(degraded_agents)} agent(s) ran in degraded mode ({', '.join(degraded_agents)}).")

    if unresolved_conflicts:
        penalty = 0.10 * len(unresolved_conflicts)
        score -= penalty
        reasons.append(f"Conflict penalty: {len(unresolved_conflicts)} unresolved material disagreement(s) remain.")

    # Clamp score in 0.0 .. 1.0
    score = max(0.0, min(1.0, round(score, 2)))

    # Force low if top is unfeasible or any degraded agent
    if not top.feasible or (degraded_agents and len(degraded_agents) > 0):
        level = "Low"
    elif score >= 0.70:
        level = "High"
    elif score >= 0.45:
        level = "Medium"
    else:
        level = "Low"

    return {"level": level, "score": score, "reasons": reasons}

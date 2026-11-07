"""Deterministic assumption reconciliation engine ensuring order independence and de-duplication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from simulation.params import SIM_PARAMS
from state.schemas import Assumption, Conflict


@dataclass
class ReconciledParameter:
    name: str
    unit: str
    low: float
    base: float
    high: float
    is_simulated: bool
    contested: bool
    contributing_agents: List[str]
    provenance: str
    source_ref: Optional[str] = None


@dataclass
class ReconciledParams:
    parameters: List[ReconciledParameter]
    simulated_params: Dict[str, float] = field(default_factory=dict)
    context_params: List[ReconciledParameter] = field(default_factory=list)


def reconcile_assumptions(
    assumptions: List[Assumption],
    conflicts: Optional[List[Conflict]] = None,
) -> ReconciledParams:
    """Reconcile assumptions across multiple agents into a deterministic, order-independent parameter set.

    Rules:
    - Sort inputs deterministically by (agent, assumption_name).
    - Simulated parameters belong to SIM_PARAMS; non-simulated remain context parameters.
    - If ranges overlap, merge with confidence-weighted mean for base, and [min(low), max(high)].
    - If non-overlapping, mark contested=True and use confidence-weighted midpoint.
    """
    conflicts = conflicts or []

    # Sort deterministically so results never depend on task completion order
    sorted_assumptions = sorted(
        assumptions,
        key=lambda a: (a.proposed_by or "", a.name, a.base),
    )

    # Group by assumption name
    grouped: Dict[str, List[Assumption]] = {}
    for asm in sorted_assumptions:
        grouped.setdefault(asm.name, []).append(asm)

    # Identify parameters with unresolved conflicts
    contested_params = set()
    for c in conflicts:
        if c.type == "assumption_divergence" and not c.resolved:
            for p_name in SIM_PARAMS:
                if p_name in c.disputed_item:
                    contested_params.add(p_name)

    reconciled_list: List[ReconciledParameter] = []
    simulated_dict: Dict[str, float] = {}
    context_list: List[ReconciledParameter] = []

    # Process parameters in alphabetical order
    for name in sorted(grouped.keys()):
        asms = grouped[name]
        is_sim = name in SIM_PARAMS
        unit = asms[0].unit
        agents = sorted(list({a.proposed_by for a in asms if a.proposed_by}))
        prov = asms[0].provenance if len(asms) == 1 else "simulated_estimate"
        sref = asms[0].source_ref if len(asms) == 1 else "reconciled consensus"

        if len(asms) == 1:
            asm = asms[0]
            rec_param = ReconciledParameter(
                name=name,
                unit=asm.unit,
                low=round(asm.low, 4),
                base=round(asm.base, 4),
                high=round(asm.high, 4),
                is_simulated=is_sim,
                contested=False,
                contributing_agents=agents,
                provenance=asm.provenance,
                source_ref=asm.source_ref,
            )
        else:
            # Multiple agents proposed this parameter
            # Check for range overlap: min(highs) >= max(lows)
            min_high = min(a.high for a in asms)
            max_low = max(a.low for a in asms)
            ranges_overlap = min_high >= max_low
            is_contested = (not ranges_overlap) or (name in contested_params)

            # Confidence-weighted mean for base
            total_weight = sum(a.confidence for a in asms)
            if total_weight > 0:
                weighted_base = sum(a.base * a.confidence for a in asms) / total_weight
            else:
                weighted_base = sum(a.base for a in asms) / len(asms)

            # Union of bounds
            low_bound = min(a.low for a in asms)
            high_bound = max(a.high for a in asms)

            # Clamp to SIM_PARAMS valid bounds if applicable
            if is_sim:
                min_valid, max_valid = SIM_PARAMS[name]["bounds"]
                low_bound = max(min_valid, low_bound)
                high_bound = min(max_valid, high_bound)
                weighted_base = max(low_bound, min(high_bound, weighted_base))

            rec_param = ReconciledParameter(
                name=name,
                unit=unit,
                low=round(low_bound, 4),
                base=round(weighted_base, 4),
                high=round(high_bound, 4),
                is_simulated=is_sim,
                contested=is_contested,
                contributing_agents=agents,
                provenance="simulated_estimate" if ranges_overlap else "ai_assumption",
                source_ref="reconciled multi-agent consensus",
            )

        reconciled_list.append(rec_param)
        if is_sim:
            simulated_dict[rec_param.name] = rec_param.base
        else:
            context_list.append(rec_param)

    # Ensure all SIM_PARAMS have at least default values
    for sim_k, spec in SIM_PARAMS.items():
        if sim_k not in simulated_dict:
            simulated_dict[sim_k] = spec["default"]

    return ReconciledParams(
        parameters=reconciled_list,
        simulated_params=simulated_dict,
        context_params=context_list,
    )


"""Parameter definitions, directions, bounds, and scenario parameter builders.

Single source of truth for all parameters consumed by the deterministic SaaS simulator.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple
from state.schemas import Assumption

SIM_PARAMS: Dict[str, Dict[str, Any]] = {
    "free_to_paid_conversion": {
        "unit": "ratio",
        "favorable_direction": "higher",
        "bounds": (0.001, 0.20),
        "default": 0.025,
        "description": "Monthly conversion rate from active free cohort to paid Starter/Pro tiers.",
    },
    "monthly_free_signups": {
        "unit": "users",
        "favorable_direction": "higher",
        "bounds": (100.0, 50000.0),
        "default": 3200.0,
        "description": "Monthly new organic and viral signups joining the free tier.",
    },
    "free_user_marginal_infra_cost": {
        "unit": "USD",
        "favorable_direction": "lower",
        "bounds": (0.10, 15.0),
        "default": 1.20,
        "description": "Marginal compute, DB connections, and storage cost per free user per month.",
    },
    "starter_cannibalization_rate": {
        "unit": "ratio",
        "favorable_direction": "lower",
        "bounds": (0.0, 0.50),
        "default": 0.10,
        "description": "Share of existing paying Starter accounts that downgrade to free.",
    },
    "free_user_monthly_tickets": {
        "unit": "tickets/user/mo",
        "favorable_direction": "lower",
        "bounds": (0.001, 1.0),
        "default": 0.05,
        "description": "Average support ticket volume submitted per active free user per month.",
    },
    "price_elasticity_starter": {
        "unit": "ratio",
        "favorable_direction": "lower",
        "bounds": (0.05, 3.0),
        "default": 0.65,
        "description": "Price elasticity of demand for Starter plan subscribers.",
    },
    "price_elasticity_growth": {
        "unit": "ratio",
        "favorable_direction": "lower",
        "bounds": (0.05, 2.5),
        "default": 0.45,
        "description": "Price elasticity of demand for Growth plan subscribers.",
    },
    "expansion_revenue_rate": {
        "unit": "ratio",
        "favorable_direction": "higher",
        "bounds": (0.005, 0.40),
        "default": 0.08,
        "description": "Monthly expansion and upsell revenue rate from existing paid accounts.",
    },
    "contraction_risk_rate": {
        "unit": "ratio",
        "favorable_direction": "lower",
        "bounds": (0.001, 0.25),
        "default": 0.04,
        "description": "Monthly contraction risk or downgrade rate triggered by price increases.",
    },
}


def build_scenario_params(
    assumptions_input: Iterable[Assumption] | Dict[str, Any],
    scenario: str,
) -> Dict[str, float]:
    """Derive numerical parameter dictionary for a given scenario based on favorable directions.

    Scenarios:
    - conservative: each parameter at its unfavorable bound
    - expected: each parameter at its base value
    - optimistic: each parameter at its favorable bound
    - stress_*: base values (the stress perturbation is applied by the simulation engine)
    """
    # Normalize input to a dict: name -> (low, base, high)
    param_bounds: Dict[str, Tuple[float, float, float]] = {}

    if isinstance(assumptions_input, dict):
        for k, v in assumptions_input.items():
            if isinstance(v, Assumption):
                param_bounds[k] = (v.low, v.base, v.high)
            elif isinstance(v, dict) and "low" in v and "base" in v and "high" in v:
                param_bounds[k] = (float(v["low"]), float(v["base"]), float(v["high"]))
            elif isinstance(v, (int, float)):
                param_bounds[k] = (float(v), float(v), float(v))
    else:
        for asm in assumptions_input:
            if isinstance(asm, Assumption):
                param_bounds[asm.name] = (asm.low, asm.base, asm.high)

    resolved: Dict[str, float] = {}

    for name, spec in SIM_PARAMS.items():
        bounds = param_bounds.get(name)
        default_val = spec["default"]
        low, base, high = bounds if bounds is not None else (default_val, default_val, default_val)
        fav = spec["favorable_direction"]

        if scenario == "conservative":
            # Unfavorable bound
            resolved[name] = low if fav == "higher" else high
        elif scenario == "optimistic":
            # Favorable bound
            resolved[name] = high if fav == "higher" else low
        else:
            # expected or stress_*
            resolved[name] = base

    return resolved

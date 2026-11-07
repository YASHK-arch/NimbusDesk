"""Sensitivity analysis (tornado chart) and flip-point search algorithms."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from state.schemas import Assumption, CompanySnapshot


def compute_tornado_sensitivity(
    strategy: str,
    assumptions_list: List[Assumption],
    metric_key: str = "net_contribution_12",
    company: Optional[CompanySnapshot] = None,
) -> List[Dict[str, Any]]:
    """Compute one-at-a-time (OAT) sensitivity swings for each assumption (Tornado Chart).

    Returns assumptions ranked from largest swing to smallest swing.
    """
    # 1. Base parameter dictionary
    base_params = {asm.name: asm.base for asm in assumptions_list}
    base_run = simulate(strategy, "expected", base_params, company=company)
    baseline_value = base_run.outputs[metric_key]

    tornado_items: List[Dict[str, Any]] = []

    for asm in assumptions_list:
        # High run
        high_params = copy_and_set(base_params, asm.name, asm.high)
        high_run = simulate(strategy, "oat_high", high_params, company=company)
        high_val = high_run.outputs[metric_key]

        # Low run
        low_params = copy_and_set(base_params, asm.name, asm.low)
        low_run = simulate(strategy, "oat_low", low_params, company=company)
        low_val = low_run.outputs[metric_key]

        swing = abs(high_val - low_val)
        tornado_items.append({
            "assumption_name": asm.name,
            "unit": asm.unit,
            "provenance": asm.provenance,
            "low_param": asm.low,
            "base_param": asm.base,
            "high_param": asm.high,
            "low_outcome": round(low_val, 2),
            "base_outcome": round(baseline_value, 2),
            "high_outcome": round(high_val, 2),
            "swing": round(swing, 2),
        })

    # Sort descending by swing
    tornado_items.sort(key=lambda x: x["swing"], reverse=True)
    return tornado_items


def find_flip_point(
    primary_strategy: str = STRATEGY_B,
    competing_strategy: str = STRATEGY_C,
    parameter_name: str = "free_to_paid_conversion",
    param_min: float = 0.005,
    param_max: float = 0.060,
    steps: int = 110,
    base_assumptions: Optional[Dict[str, float]] = None,
    company: Optional[CompanySnapshot] = None,
) -> Dict[str, Any]:
    """Find the exact threshold where the winning strategy flips.

    Returns:
        threshold, winning_strategy_above, plain_language_statement.
    """
    if base_assumptions is None:
        base_assumptions = {
            "free_to_paid_conversion": 0.025,
            "monthly_free_signups": 3500.0,
            "free_user_marginal_infra_cost": 1.20,
            "starter_cannibalization_rate": 0.12,
            "free_user_monthly_tickets": 0.05,
        }

    # Evaluate competitor strategy outcome
    competitor_run = simulate(competing_strategy, "expected", base_assumptions, company=company)
    competitor_metric = competitor_run.outputs["net_contribution_12"]

    flip_threshold: Optional[float] = None
    step_size = (param_max - param_min) / steps

    # Scan parameter values
    previous_diff = None
    for i in range(steps + 1):
        param_val = param_min + (i * step_size)
        curr_params = copy_and_set(base_assumptions, parameter_name, param_val)
        primary_run = simulate(primary_strategy, "flip_search", curr_params, company=company)
        primary_metric = primary_run.outputs["net_contribution_12"]

        diff = primary_metric - competitor_metric
        if previous_diff is not None:
            if (previous_diff < 0 and diff >= 0) or (previous_diff >= 0 and diff < 0):
                flip_threshold = round(param_val, 4)
                break
        previous_diff = diff

    if flip_threshold is None:
        flip_threshold = round(param_min + (param_max - param_min) / 2.0, 4)

    pct_str = f"{flip_threshold * 100:.2f}%"
    statement = (
        f"{primary_strategy} generates superior 12-month net contribution over {competing_strategy} "
        f"only if {parameter_name.replace('_', ' ')} remains above {pct_str}."
    )

    return {
        "primary_strategy": primary_strategy,
        "competing_strategy": competing_strategy,
        "parameter_name": parameter_name,
        "threshold": flip_threshold,
        "threshold_display": pct_str,
        "statement": statement,
    }


def copy_and_set(d: Dict[str, float], key: str, value: float) -> Dict[str, float]:
    cp = dict(d)
    cp[key] = value
    return cp

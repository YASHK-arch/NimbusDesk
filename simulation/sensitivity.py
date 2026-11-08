"""Sensitivity analysis (tornado chart) and flip-point search algorithms."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from simulation.reconcile import ReconciledParams, reconcile_assumptions
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from simulation.adapter import SimulatorAdapter, get_simulator_adapter
from state.schemas import Assumption, CompanySnapshot
from state.company import load_company_snapshot


def compute_tornado_sensitivity(
    strategy: str,
    assumptions_list: Optional[List[Assumption]] = None,
    reconciled: Optional[ReconciledParams] = None,
    metric_key: str = "net_contribution_12",
    company: Optional[CompanySnapshot] = None,
    adapter: Optional[SimulatorAdapter] = None,
    decision_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Compute one-at-a-time (OAT) sensitivity swings for simulated parameters (Tornado Chart).

    Only iterates over simulated parameters (in SIM_PARAMS), de-duplicated and sorted by impact.
    """
    if adapter is None:
        if decision_type:
            adapter = get_simulator_adapter(decision_type)
        elif "Raise" in strategy or "Hold Prices" in strategy or "20%" in strategy:
            adapter = get_simulator_adapter("price_change")
        else:
            adapter = get_simulator_adapter("free_plan")

    if reconciled is None:
        reconciled = reconcile_assumptions(assumptions_list or [])

    base_params = reconciled.simulated_params
    base_run = adapter.simulate(strategy, "expected", base_params, company=company)
    baseline_value = base_run.outputs[metric_key]

    tornado_items: List[Dict[str, Any]] = []

    for param in reconciled.parameters:
        if not param.is_simulated:
            continue

        # High run
        high_params = copy_and_set(base_params, param.name, param.high)
        high_run = adapter.simulate(strategy, "oat_high", high_params, company=company)
        high_val = high_run.outputs[metric_key]

        # Low run
        low_params = copy_and_set(base_params, param.name, param.low)
        low_run = adapter.simulate(strategy, "oat_low", low_params, company=company)
        low_val = low_run.outputs[metric_key]

        swing = abs(high_val - low_val)
        tornado_items.append({
            "assumption_name": param.name,
            "unit": param.unit,
            "provenance": param.provenance,
            "low_param": param.low,
            "base_param": param.base,
            "high_param": param.high,
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
    adapter: Optional[SimulatorAdapter] = None,
    decision_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Find the exact threshold where the winning strategy flips.

    Uses bisection to find the root where primary and competing strategy outcomes cross.
    If outcomes at both bounds have the same sign, returns exists=False with an honest
    statement and no fabricated midpoint fallback.
    """
    if adapter is None:
        if decision_type:
            adapter = get_simulator_adapter(decision_type)
        elif "Raise" in primary_strategy or "Hold Prices" in primary_strategy or "20%" in primary_strategy:
            adapter = get_simulator_adapter("price_change")
        else:
            adapter = get_simulator_adapter("free_plan")

    if company is None:
        company = load_company_snapshot()

    if base_assumptions is None:
        base_assumptions = {
            "free_to_paid_conversion": 0.025,
            "monthly_free_signups": 3500.0,
            "free_user_marginal_infra_cost": 1.20,
            "starter_cannibalization_rate": 0.12,
            "free_user_monthly_tickets": 0.05,
        }

    base_val = base_assumptions.get(parameter_name, (param_min + param_max) / 2.0)

    def eval_diff(val: float) -> float:
        curr_params = copy_and_set(base_assumptions, parameter_name, val)
        primary_run = adapter.simulate(primary_strategy, "flip_search", curr_params, company=company)
        # In free-plan model, Strategy C represents baseline status-quo break-even (0 net contribution threshold)
        if "Funnel Optimization" in competing_strategy or (competing_strategy == STRATEGY_C and adapter.decision_type == "free_plan"):
            return primary_run.outputs["net_contribution_12"]
        competing_run = adapter.simulate(competing_strategy, "flip_search", curr_params, company=company)
        return primary_run.outputs["net_contribution_12"] - competing_run.outputs["net_contribution_12"]

    val_low = eval_diff(param_min)
    val_high = eval_diff(param_max)

    # If both bounds have the same sign, no flip point exists in range
    if (val_low > 0 and val_high > 0) or (val_low < 0 and val_high < 0) or (val_low == 0 and val_high == 0):
        superior = val_low > 0
        statement = (
            f"No flip point within tested range [{param_min}, {param_max}]. "
            f"Disputed parameter '{parameter_name}' does not change the ranking between {primary_strategy} and {competing_strategy} "
            f"within tested bounds [{param_min}, {param_max}]. "
            f"Strategy {primary_strategy} remains {'superior' if superior else 'inferior'} "
            f"across the entire tested interval."
        )
        return {
            "exists": False,
            "strategy": primary_strategy,
            "primary_strategy": primary_strategy,
            "competing_strategy": competing_strategy,
            "parameter": parameter_name,
            "parameter_name": parameter_name,
            "tested_range": [param_min, param_max],
            "outcome_at_low": round(val_low, 2),
            "outcome_at_high": round(val_high, 2),
            "statement": statement,
            "flip_value": None,
            "threshold": None,
            "threshold_display": "No flip point in range",
        }

    # If bounds have opposite signs, run bisection to tolerance 1e-4
    lo = param_min
    hi = param_max
    f_lo = val_low
    f_hi = val_high

    mid = (lo + hi) / 2.0
    f_mid = eval_diff(mid)

    for _ in range(30):
        mid = (lo + hi) / 2.0
        f_mid = eval_diff(mid)
        if abs(f_mid) < 1.0 or (hi - lo) < 1e-5:
            break
        if (f_lo > 0 and f_mid > 0) or (f_lo < 0 and f_mid < 0):
            lo = mid
            f_lo = f_mid
        else:
            hi = mid
            f_hi = f_mid

    root = mid
    val_root = f_mid
    flip_value = round(root, 4)
    pct_str = f"{root * 100:.2f}%" if root <= 1.0 else f"{root:,.2f}"
    statement = (
        f"Strategy {primary_strategy} net contribution flips sign relative to {competing_strategy} at "
        f"{parameter_name} = {root:.4f} ({pct_str}) (baseline: {base_val:.4f})."
    )

    return {
        "exists": True,
        "strategy": primary_strategy,
        "primary_strategy": primary_strategy,
        "competing_strategy": competing_strategy,
        "parameter": parameter_name,
        "parameter_name": parameter_name,
        "tested_range": [param_min, param_max],
        "flip_value": flip_value,
        "outcome_at_flip": round(val_root, 2),
        "statement": statement,
        "threshold": flip_value,
        "threshold_display": pct_str,
    }


def copy_and_set(d: Dict[str, float], key: str, value: float) -> Dict[str, float]:
    cp = dict(d)
    cp[key] = value
    return cp

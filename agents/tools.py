"""Deterministic analytical tools for agents to query company metrics and compute bounds.

No numbers originate from LLMs; all tools query the synthetic company dataset or compute deterministic bounds.
"""

from __future__ import annotations

from typing import Any, Dict
from state.company import load_company_snapshot


def get_financial_summary() -> Dict[str, Any]:
    """CFO Tool: Retrieve current financial health, runway, and plan contributions."""
    snapshot = load_company_snapshot()
    return {
        "mrr": snapshot.mrr,
        "arr": snapshot.arr,
        "cash_balance": snapshot.cash_balance,
        "monthly_burn": snapshot.monthly_burn,
        "runway_months": snapshot.runway_months,
        "starter_plan_mrr": next((p.mrr for p in snapshot.plans if p.plan_name == "Starter"), 0.0),
        "starter_plan_customers": next((p.active_customers for p in snapshot.plans if p.plan_name == "Starter"), 0),
        "blended_churn_monthly_pct": snapshot.blended_churn_monthly_pct,
    }


def calculate_runway_impact(additional_monthly_burn: float = 20000.0) -> Dict[str, Any]:
    """CFO Tool: Deterministically compute runway reduction from added burn."""
    snapshot = load_company_snapshot()
    new_burn = snapshot.monthly_burn + additional_monthly_burn
    new_runway = snapshot.cash_balance / new_burn if new_burn > 0 else 999.0
    return {
        "current_runway_months": snapshot.runway_months,
        "new_runway_months": round(new_runway, 2),
        "runway_delta_months": round(new_runway - snapshot.runway_months, 2),
        "additional_monthly_burn": additional_monthly_burn,
    }


def get_funnel_metrics() -> Dict[str, Any]:
    """Growth Tool: Retrieve top-of-funnel traffic, conversion benchmarks, and CAC."""
    snapshot = load_company_snapshot()
    return {
        "monthly_unique_visitors": snapshot.funnel["monthly_unique_visitors"],
        "visitor_to_trial_signup_pct": snapshot.funnel["visitor_to_trial_signup_pct"],
        "trial_to_paid_conversion_pct": snapshot.funnel["trial_to_paid_conversion_pct"],
        "cac_blended": snapshot.cac_blended,
        "ltv_blended": snapshot.ltv_blended,
        "estimated_free_tier_monthly_signups": snapshot.funnel["estimated_free_tier_monthly_signups"],
    }


def get_infra_headroom(active_free_users: int = 0) -> Dict[str, Any]:
    """CTO Tool: Retrieve compute headroom and marginal infra cost per free user."""
    snapshot = load_company_snapshot()
    max_safe = snapshot.infra.get("max_safe_free_users_without_sharding", 6000)
    return {
        "current_monthly_cost": snapshot.infra["current_monthly_cost"],
        "paid_user_cost_per_month": snapshot.infra["paid_user_cost_per_month"],
        "free_user_marginal_cost_per_month": snapshot.infra["free_user_marginal_cost_per_month"],
        "database_cluster_utilization_pct": snapshot.infra["database_cluster_utilization_pct"],
        "max_concurrent_connections_headroom_pct": snapshot.infra["max_concurrent_connections_headroom_pct"],
        "max_safe_free_users_without_sharding": max_safe,
        "active_free_users": active_free_users,
        "headroom_remaining": max_safe - active_free_users,
    }


def get_support_capacity() -> Dict[str, Any]:
    """Customer Tool: Retrieve support rep capacity and ticket cost data."""
    snapshot = load_company_snapshot()
    support = snapshot.support
    total_capacity = support["headcount"] * support["max_tickets_per_rep_month"]
    unused_capacity = total_capacity - support["total_monthly_tickets"]
    return {
        "support_headcount": support["headcount"],
        "total_ticket_capacity": total_capacity,
        "current_monthly_tickets": support["total_monthly_tickets"],
        "unused_ticket_capacity": unused_capacity,
        "cost_per_ticket": support["cost_per_ticket"],
        "free_user_ticket_rate_estimate": support["free_user_ticket_rate_estimate"],
    }


def get_engineering_capacity() -> Dict[str, Any]:
    """Product/CTO Tool: Engineering capacity and development sprint estimate."""
    snapshot = load_company_snapshot()
    return {
        "total_engineers": snapshot.engineering_capacity["total_engineers"],
        "dedicated_to_core_product": snapshot.engineering_capacity["dedicated_to_core_product"],
        "free_tier_dev_effort_weeks": snapshot.engineering_capacity["free_tier_dev_effort_weeks"],
    }

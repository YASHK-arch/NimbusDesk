"""Deterministic SaaS Pricing & Elasticity Simulation Engine.

Simulates 24 monthly steps under price increases and packaging adjustments:
- Strategy A: Raise Starter 20%, Hold Growth & Enterprise
- Strategy B: Raise All Tiers 20%
- Strategy C: Hold Prices, Introduce Usage Add-on
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np
from state.company import load_company_snapshot
from state.schemas import CompanySnapshot, SimulationRun

logger = logging.getLogger(__name__)

PRICE_STRAT_A = "Strategy A (Raise Starter 20%, Hold Others)"
PRICE_STRAT_B = "Strategy B (Raise All Tiers 20%)"
PRICE_STRAT_C = "Strategy C (Hold Prices, Introduce Usage Add-on)"


def simulate_price_change(
    strategy: str,
    scenario: str,
    assumptions: Dict[str, float],
    company: Optional[CompanySnapshot] = None,
    months: int = 24,
    seed: int = 42,
) -> SimulationRun:
    """Simulate 24-month financial trajectory under pricing adjustments and demand elasticity."""
    if company is None:
        company = load_company_snapshot()

    rng = np.random.RandomState(seed)

    # Extract elasticity and expansion parameters
    elasticity_starter = assumptions.get("price_elasticity_starter", 0.65)
    elasticity_growth = assumptions.get("price_elasticity_growth", 0.45)
    expansion_rate = assumptions.get("expansion_revenue_rate", 0.08)
    contraction_risk = assumptions.get("contraction_risk_rate", 0.04)

    # Baseline plans from synthetic company
    starter_plan = next((p for p in company.plans if "starter" in p.plan_name.lower()), None)
    growth_plan = next((p for p in company.plans if "growth" in p.plan_name.lower()), None)
    ent_plan = next((p for p in company.plans if "enterprise" in p.plan_name.lower()), None)

    starter_price_base = starter_plan.price_per_month if starter_plan else 49.0
    growth_price_base = growth_plan.price_per_month if growth_plan else 199.0
    ent_price_base = ent_plan.price_per_month if ent_plan else 999.0

    starter_cust = starter_plan.active_customers if starter_plan else 1200
    growth_cust = growth_plan.active_customers if growth_plan else 202
    ent_cust = ent_plan.active_customers if ent_plan else 45

    starter_churn_base = (starter_plan.churn_monthly_pct if starter_plan else 2.5) / 100.0
    growth_churn_base = (growth_plan.churn_monthly_pct if growth_plan else 1.5) / 100.0
    ent_churn_base = (ent_plan.churn_monthly_pct if ent_plan else 0.8) / 100.0

    # Pricing strategy adjustments
    if strategy == PRICE_STRAT_A:
        p_starter = starter_price_base * 1.20
        p_growth = growth_price_base
        p_ent = ent_price_base
        hike_starter = 0.20
        hike_growth = 0.0
        hike_ent = 0.0
        usage_addon_mrr_per_cust = 0.0
    elif strategy == PRICE_STRAT_B:
        p_starter = starter_price_base * 1.20
        p_growth = growth_price_base * 1.20
        p_ent = ent_price_base * 1.20
        hike_starter = 0.20
        hike_growth = 0.20
        hike_ent = 0.20
        usage_addon_mrr_per_cust = 0.0
    elif strategy == PRICE_STRAT_C:
        p_starter = starter_price_base
        p_growth = growth_price_base
        p_ent = ent_price_base
        hike_starter = 0.0
        hike_growth = 0.0
        hike_ent = 0.0
        usage_addon_mrr_per_cust = 35.0  # Optional metered add-on
    else:
        p_starter = starter_price_base
        p_growth = growth_price_base
        p_ent = ent_price_base
        hike_starter = 0.0
        hike_growth = 0.0
        hike_ent = 0.0
        usage_addon_mrr_per_cust = 0.0

    # Churn shifts based on price elasticity: churn_new = churn_base * (1 + hike * elasticity)
    churn_starter = starter_churn_base * (1.0 + (hike_starter * elasticity_starter))
    churn_growth = growth_churn_base * (1.0 + (hike_growth * elasticity_growth))
    churn_ent = ent_churn_base * (1.0 + (hike_ent * (elasticity_growth * 0.5)))

    # Initial state
    cash = company.cash_balance
    base_opex = company.monthly_gross_burn - company.infra["current_monthly_cost"] - company.support["team_cost_monthly"]
    fixed_infra_cost = company.infra["current_monthly_cost"]
    support_cost = company.support["team_cost_monthly"]

    curr_starter = float(starter_cust)
    curr_growth = float(growth_cust)
    curr_ent = float(ent_cust)

    history: List[Dict[str, Any]] = []
    initial_mrr = company.mrr
    cum_net_contrib = 0.0

    for m in range(1, months + 1):
        # Organic monthly customer additions at new pricing
        new_starter = 45.0 * (1.0 - (hike_starter * elasticity_starter * 0.5))
        new_growth = 12.0 * (1.0 - (hike_growth * elasticity_growth * 0.4))
        new_ent = 2.0 * (1.0 - (hike_ent * 0.1))

        # Monthly churn
        lost_starter = curr_starter * churn_starter
        lost_growth = curr_growth * churn_growth
        lost_ent = curr_ent * churn_ent

        curr_starter = max(10.0, curr_starter - lost_starter + new_starter)
        curr_growth = max(5.0, curr_growth - lost_growth + new_growth)
        curr_ent = max(2.0, curr_ent - lost_ent + new_ent)

        total_customers = curr_starter + curr_growth + curr_ent

        # Base plan revenue
        base_revenue = (curr_starter * p_starter) + (curr_growth * p_growth) + (curr_ent * p_ent)
        
        # Expansion revenue and contraction risk
        expansion_rev = base_revenue * expansion_rate
        contraction_loss = base_revenue * contraction_risk
        addon_rev = (curr_growth + curr_ent) * usage_addon_mrr_per_cust

        monthly_mrr = base_revenue + expansion_rev - contraction_loss + addon_rev

        # Operating costs
        infra_cost = fixed_infra_cost * (1.0 + (total_customers / 2000.0) * 0.15)
        total_opex = base_opex + infra_cost + support_cost

        monthly_net = monthly_mrr - total_opex
        cum_net_contrib += monthly_net
        cash += monthly_net

        burn = max(1000.0, total_opex - monthly_mrr)
        runway = (cash / burn) if burn > 0 else 999.0
        if cash <= 0:
            runway = 0.0

        gm = (monthly_mrr - (infra_cost + support_cost)) / monthly_mrr if monthly_mrr > 0 else 0.0

        history.append({
            "month": m,
            "mrr": round(monthly_mrr, 2),
            "total_customers": int(round(total_customers)),
            "cash_balance": round(cash, 2),
            "runway_months": round(runway, 2),
            "gross_margin": round(gm, 4),
            "net_contribution": round(cum_net_contrib, 2),
        })

    m12 = history[min(11, len(history) - 1)]
    m24 = history[min(23, len(history) - 1)]

    # Net Retention Rate at Month 12: baseline accounts retained value
    net_retention_12 = round((m12["mrr"] - (45.0 * p_starter * 12 * 0.3)) / initial_mrr, 4)

    outputs = {
        "mrr_month_12": m12["mrr"],
        "mrr_month_24": m24["mrr"],
        "arr_month_12": round(m12["mrr"] * 12, 2),
        "arr_month_24": round(m24["mrr"] * 12, 2),
        "paying_customers_12": m12["total_customers"],
        "paying_customers_24": m24["total_customers"],
        "runway_months_12": m12["runway_months"],
        "runway_months_24": m24["runway_months"],
        "gross_margin_month_12": m12["gross_margin"],
        "net_contribution_12": m12["net_contribution"],
        "net_contribution_24": m24["net_contribution"],
        "net_retention_12": net_retention_12,
        "history": history,
    }

    return SimulationRun(
        id=f"sim_price_{scenario}_{seed}_{strategy[:10].replace(' ', '_').lower()}",
        strategy=strategy,
        scenario=scenario,
        parameters=assumptions,
        outputs=outputs,
        seed=seed,
    )

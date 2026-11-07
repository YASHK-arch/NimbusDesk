"""Deterministic SaaS dynamics model for 12-24 month trajectory forecasting.

Rules:
- R2: LLMs never output numbers; this deterministic model computes all financial outcomes.
- Reproducible: Fixed seed for all probabilistic perturbations.
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional
from state.company import load_company_snapshot
from state.schemas import CompanySnapshot, SimulationRun

STRATEGY_A = "Strategy A (Limited Features)"
STRATEGY_B = "Strategy B (Usage Caps)"
STRATEGY_C = "Strategy C (Funnel Optimization Only)"


def simulate(
    strategy: str,
    scenario: str,
    assumptions: Dict[str, float],
    company: Optional[CompanySnapshot] = None,
    months: int = 24,
    seed: int = 42,
) -> SimulationRun:
    """Simulate SaaS financial trajectory over 12-24 monthly steps.

    Parameters:
        strategy: Strategy A, B, or C.
        scenario: 'conservative', 'expected', 'optimistic', 'stress_test'.
        assumptions: dictionary of key parameters (conversion, signups, infra, cannibalization).
        company: baseline company snapshot (defaults to NimbusDesk).
        months: number of monthly time steps (default 24).
        seed: stored random seed for determinism.
    """
    if company is None:
        company = load_company_snapshot()

    # Levers and default calibration
    free_conversion = assumptions.get("free_to_paid_conversion", 0.025)
    monthly_free_signups = assumptions.get("monthly_free_signups", 3200.0)
    free_infra_per_user = assumptions.get("free_user_marginal_infra_cost", 1.20)
    cannibalization_rate = assumptions.get("starter_cannibalization_rate", 0.10)
    free_ticket_rate = assumptions.get("free_user_monthly_tickets", 0.05)

    # Strategy modifiers
    if strategy == STRATEGY_A:
        # Limited features: high top of funnel, standard conversion, higher support burden
        effective_signups = monthly_free_signups * 1.15
        effective_conversion = free_conversion * 0.95
        effective_infra = free_infra_per_user * 1.10
        effective_cannibalization = cannibalization_rate * 1.20
        effective_support_tickets = free_ticket_rate * 1.25
        starter_growth_rate = 0.02
        pro_growth_rate = 0.025
    elif strategy == STRATEGY_B:
        # Usage caps: focused signups, higher conversion incentive, lower marginal infra
        effective_signups = monthly_free_signups * 0.90
        effective_conversion = free_conversion * 1.25
        effective_infra = free_infra_per_user * 0.85
        effective_cannibalization = cannibalization_rate * 0.60
        effective_support_tickets = free_ticket_rate * 0.40  # strict community deflection
        starter_growth_rate = 0.025
        pro_growth_rate = 0.035
    elif strategy == STRATEGY_C:
        # No free plan; improve trial conversion
        effective_signups = 0.0
        effective_conversion = 0.0
        effective_infra = 0.0
        effective_cannibalization = 0.0
        effective_support_tickets = 0.0
        # Increased paid conversion from funnel optimization
        starter_growth_rate = 0.035
        pro_growth_rate = 0.030
    else:
        effective_signups = monthly_free_signups
        effective_conversion = free_conversion
        effective_infra = free_infra_per_user
        effective_cannibalization = cannibalization_rate
        effective_support_tickets = free_ticket_rate
        starter_growth_rate = 0.02
        pro_growth_rate = 0.02

    # Stress test multipliers
    if scenario == "stress_test":
        effective_conversion *= 0.50
        effective_infra *= 2.0
        effective_cannibalization *= 1.50

    # Initial state initialization from company snapshot
    cash = company.cash_balance
    starter_users = next((p.active_customers for p in company.plans if p.plan_name == "Starter"), 600)
    pro_users = next((p.active_customers for p in company.plans if p.plan_name == "Pro"), 350)
    ent_users = next((p.active_customers for p in company.plans if p.plan_name == "Enterprise"), 45)

    starter_price = next((p.price_per_month for p in company.plans if p.plan_name == "Starter"), 49.0)
    pro_price = next((p.price_per_month for p in company.plans if p.plan_name == "Pro"), 199.0)
    ent_price = next((p.price_per_month for p in company.plans if p.plan_name == "Enterprise"), 999.0)

    starter_churn = next((p.churn_monthly_pct / 100.0 for p in company.plans if p.plan_name == "Starter"), 0.045)
    pro_churn = next((p.churn_monthly_pct / 100.0 for p in company.plans if p.plan_name == "Pro"), 0.021)
    ent_churn = next((p.churn_monthly_pct / 100.0 for p in company.plans if p.plan_name == "Enterprise"), 0.008)

    base_opex = company.monthly_gross_burn - company.infra["current_monthly_cost"] - company.support["team_cost_monthly"]
    free_users = 0
    support_reps = company.support["headcount"]
    max_tickets_per_rep = company.support["max_tickets_per_rep_month"]
    cost_per_rep = company.support["team_cost_monthly"] / support_reps

    history: List[Dict[str, Any]] = []
    cumulative_net_contribution = 0.0

    # Simulation monthly time-step loop
    for m in range(1, months + 1):
        # 1. Update Free Users cohort
        if effective_signups > 0:
            free_users += int(effective_signups)
            # Free user churn (~15% monthly inactive purge)
            free_users = int(free_users * 0.85)

        # 2. Conversion from Free to Paid (splits 75% to Starter, 25% to Pro)
        converted_users = int(free_users * effective_conversion)
        free_users = max(0, free_users - converted_users)
        new_starter_from_free = int(converted_users * 0.75)
        new_pro_from_free = int(converted_users * 0.25)

        # 3. Churn and Cannibalization
        cannibalized_starter = int(starter_users * effective_cannibalization / 12.0) if m <= 12 else 0
        starter_churned = int(starter_users * starter_churn) + cannibalized_starter
        pro_churned = int(pro_users * pro_churn)
        ent_churned = int(ent_users * ent_churn)

        # 4. Organic Paid Growth
        new_starter_organic = int(starter_users * starter_growth_rate)
        new_pro_organic = int(pro_users * pro_growth_rate)

        starter_users = max(0, starter_users - starter_churned + new_starter_organic + new_starter_from_free)
        pro_users = max(0, pro_users - pro_churned + new_pro_organic + new_pro_from_free)
        ent_users = max(0, ent_users - ent_churned)

        # 5. Financial metrics
        mrr = (starter_users * starter_price) + (pro_users * pro_price) + (ent_users * ent_price)
        total_paid_users = starter_users + pro_users + ent_users

        # 6. Infra cost calculation
        infra_paid = total_paid_users * company.infra["paid_user_cost_per_month"]
        infra_free = free_users * effective_infra
        total_infra = company.infra["current_monthly_cost"] + infra_free

        # 7. Support load & staffing
        paid_tickets = total_paid_users * company.support["paid_ticket_rate_per_user_month"]
        free_tickets = free_users * effective_support_tickets
        total_tickets = paid_tickets + free_tickets
        needed_reps = max(company.support["headcount"], int(total_tickets // max_tickets_per_rep) + 1)
        total_support_cost = needed_reps * cost_per_rep

        # 8. Monthly Burn and Cash Runway
        total_monthly_expenses = base_opex + total_infra + total_support_cost
        net_burn = total_monthly_expenses - mrr
        cash -= net_burn
        runway = (cash / net_burn) if net_burn > 0 else 999.0

        gross_margin = (mrr - total_infra - total_support_cost) / mrr if mrr > 0 else 0.0
        monthly_net_contribution = mrr - total_monthly_expenses
        cumulative_net_contribution += monthly_net_contribution

        history.append({
            "month": m,
            "mrr": round(mrr, 2),
            "paying_customers": total_paid_users,
            "free_users": free_users,
            "infra_cost": round(total_infra, 2),
            "support_headcount": needed_reps,
            "support_cost": round(total_support_cost, 2),
            "gross_margin_pct": round(gross_margin * 100, 2),
            "cash_balance": round(cash, 2),
            "runway_months": round(max(0.0, runway), 2),
            "cumulative_net_contribution": round(cumulative_net_contribution, 2),
        })

    # Milestone checkpoints: 6, 12, 24 months
    m6 = history[min(5, len(history) - 1)]
    m12 = history[min(11, len(history) - 1)]
    m24 = history[min(23, len(history) - 1)]

    outputs = {
        "mrr_month_6": m6["mrr"],
        "mrr_month_12": m12["mrr"],
        "mrr_month_24": m24["mrr"],
        "gross_margin_month_6": m6["gross_margin_pct"],
        "gross_margin_month_12": m12["gross_margin_pct"],
        "gross_margin_month_24": m24["gross_margin_pct"],
        "runway_months_6": m6["runway_months"],
        "runway_months_12": m12["runway_months"],
        "runway_months_24": m24["runway_months"],
        "support_headcount_12": m12["support_headcount"],
        "infra_cost_12": m12["infra_cost"],
        "net_contribution_12": m12["cumulative_net_contribution"],
        "net_contribution_24": m24["cumulative_net_contribution"],
        "history": history,
    }

    return SimulationRun(
        id=f"sim-{uuid.uuid4().hex[:8]}",
        strategy=strategy,
        scenario=scenario,
        parameters=copy.deepcopy(assumptions),
        outputs=outputs,
        seed=seed,
    )

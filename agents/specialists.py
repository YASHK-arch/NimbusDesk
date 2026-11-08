"""Specialist AI agent implementations with distinct objectives, tools, and mock findings.

Strict Provenance & Unit Rules:
- R4 / R7: No fabricated reports, benchmarks, or ungrounded external sources.
- verified_data: strictly read from data/synthetic_company.json#<path> with base matching snapshot.
- ai_assumption: mock assumptions tagged source_ref='mock: illustrative assumption'.
- Units: ratio for fractions (0..1), USD for currency, users for counts, tickets/user/mo for rates.
"""

from __future__ import annotations

from typing import List, Optional
from agents.base_agent import BaseAgent
from agents.tools import (
    calculate_runway_impact,
    get_engineering_capacity,
    get_financial_summary,
    get_funnel_metrics,
    get_infra_headroom,
    get_support_capacity,
)
from state.schemas import Assumption, Evidence, Finding


class CFOAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="CFO",
            role_title="Chief Financial Officer",
            objective="Protect runway, preserve gross margins, prevent unmetered burn, and guard against customer cannibalization.",
            system_prompt=(
                "You are the CFO. Your duty is capital preservation. Scrutinize all cost implications, "
                "runway decay, and revenue cannibalization. Be skeptical of unproven conversion rates."
            ),
            allowed_tools=[get_financial_summary, calculate_runway_impact],
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        if decision_type == "price_change":
            return Finding(
                agent=self.name,
                task_id=task_id,
                claim="Pricing adjustments improve gross margins but entry-tier elasticity above 0.70 risks contraction; cautious elasticity parameters required to protect runway.",
                recommendation="proceed_with_limits",
                confidence=0.85,
                assumptions=[
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.40,
                        base=0.60,
                        high=0.85,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.75,
                        proposed_by=self.name,
                    ),
                    Assumption(
                        name="contraction_risk_rate",
                        low=0.02,
                        base=0.04,
                        high=0.08,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.70,
                        proposed_by=self.name,
                    ),
                    Assumption(
                        name="expansion_revenue_rate",
                        low=0.05,
                        base=0.08,
                        high=0.12,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.70,
                        proposed_by=self.name,
                    ),
                ],
                evidence=[
                    Evidence(
                        source_type="company_data",
                        source_ref="data/synthetic_company.json#mrr",
                        snippet="Current MRR is $89.7k across 1,447 paying customers. Price increases must protect net retention.",
                    )
                ],
                limitations=["Assumes macroeconomic software spending remains flat."],
                status="ok",
            )

        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="Unconstrained free tier threatens runway; conversion is likely low (1.0%-2.2%) while Starter plan will experience 12% cannibalization.",
            recommendation="proceed_with_limits",
            confidence=0.82,
            assumptions=[
                Assumption(
                    name="free_to_paid_conversion",
                    low=0.010,
                    base=0.015,
                    high=0.022,
                    unit="ratio",
                    provenance="ai_assumption",
                    source_ref="mock: illustrative assumption",
                    confidence=0.65,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="starter_cannibalization_rate",
                    low=0.06,
                    base=0.12,
                    high=0.20,
                    unit="ratio",
                    provenance="ai_assumption",
                    source_ref="mock: illustrative assumption",
                    confidence=0.70,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="min_acceptable_runway_months",
                    low=10.0,
                    base=12.6,
                    high=15.0,
                    unit="months",
                    provenance="verified_data",
                    source_ref="data/synthetic_company.json#runway_months",
                    confidence=0.95,
                    proposed_by=self.name,
                ),
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="data/synthetic_company.json#runway_months",
                    snippet="Current runway is 12.6 months with $115k monthly net burn. Adding $20k/mo net burn reduces runway to under 10.7 months.",
                )
            ],
            limitations=["Does not account for enterprise network viral expansion."],
            status="ok",
        )


class GrowthAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Growth",
            role_title="Head of Growth / CMO",
            objective="Maximize top-of-funnel acquisition, organic virality, expansion velocity, and customer lifetime value.",
            system_prompt=(
                "You are the Head of Growth. Your duty is rapid market capture and product-led acquisition. "
                "Focus on viral coefficients, top-of-funnel volume, CAC reduction, and user expansion."
            ),
            allowed_tools=[get_funnel_metrics],
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        if decision_type == "price_change":
            return Finding(
                agent=self.name,
                task_id=task_id,
                claim="Market demand exhibits low elasticity; a 20% Starter hike will encounter minimal churn (elasticity 0.20-0.50) while expansion features accelerate net expansion to 14%.",
                recommendation="proceed",
                confidence=0.88,
                assumptions=[
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.20,
                        base=0.35,
                        high=0.50,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.80,
                        proposed_by=self.name,
                    ),
                    Assumption(
                        name="price_elasticity_growth",
                        low=0.15,
                        base=0.25,
                        high=0.40,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.75,
                        proposed_by=self.name,
                    ),
                    Assumption(
                        name="expansion_revenue_rate",
                        low=0.08,
                        base=0.14,
                        high=0.20,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.75,
                        proposed_by=self.name,
                    ),
                ],
                evidence=[
                    Evidence(
                        source_type="company_data",
                        source_ref="data/synthetic_company.json#plans",
                        snippet="Starter tier is priced at $49/mo; competitive willingness-to-pay benchmark indicates capacity up to $59/mo.",
                    )
                ],
                limitations=["Assumes core product quality and uptime remain high."],
                status="ok",
            )

        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="A free tier unlocks 3,200 monthly signups and creates a strong product-led upgrade funnel, converting at 3.5%-6.5% and reducing CAC by 40%.",
            recommendation="proceed",
            confidence=0.88,
            assumptions=[
                Assumption(
                    name="free_to_paid_conversion",
                    low=0.035,
                    base=0.045,
                    high=0.065,
                    unit="ratio",
                    provenance="ai_assumption",
                    source_ref="mock: illustrative assumption",
                    confidence=0.75,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="monthly_free_signups",
                    low=2500.0,
                    base=3200.0,
                    high=5000.0,
                    unit="users",
                    provenance="verified_data",
                    source_ref="data/synthetic_company.json#funnel.estimated_free_tier_monthly_signups",
                    confidence=0.80,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="blended_cac_reduction_pct",
                    low=0.25,
                    base=0.40,
                    high=0.60,
                    unit="ratio",
                    provenance="ai_assumption",
                    source_ref="mock: illustrative assumption",
                    confidence=0.70,
                    proposed_by=self.name,
                ),
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="data/synthetic_company.json#funnel.monthly_unique_visitors",
                    snippet="45,000 unique monthly visitors currently convert at only 1.2% to trial; free tier capture rate typically reaches 7-10% of visitors.",
                )
            ],
            limitations=["Assumes user onboarding friction is reduced to under 5 minutes."],
            status="ok",
        )


class CTOAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="CTO",
            role_title="Chief Technology Officer",
            objective="Assess cloud infrastructure capacity, marginal compute/database loads, and engineering feasibility.",
            system_prompt=(
                "You are the CTO. Ensure architectural headroom, evaluate database concurrency limits, "
                "and prevent cloud infrastructure overruns."
            ),
            allowed_tools=[get_infra_headroom, get_engineering_capacity],
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="Infra can support up to 6,000 active free users without architectural sharding; marginal cost is $1.20/user/mo.",
            recommendation="proceed_with_limits",
            confidence=0.85,
            assumptions=[
                Assumption(
                    name="free_user_marginal_infra_cost",
                    low=0.90,
                    base=1.20,
                    high=1.80,
                    unit="USD",
                    provenance="verified_data",
                    source_ref="data/synthetic_company.json#infra.free_user_marginal_cost_per_month",
                    confidence=0.90,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="max_free_tier_users_before_sharding",
                    low=4500.0,
                    base=6000.0,
                    high=8000.0,
                    unit="users",
                    provenance="verified_data",
                    source_ref="data/synthetic_company.json#infra.max_safe_free_users_without_sharding",
                    confidence=0.85,
                    proposed_by=self.name,
                ),
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="data/synthetic_company.json#infra.database_cluster_utilization_pct",
                    snippet="Database cluster operates at 58% utilization; 42% connection headroom remains before replica pool expansion.",
                )
            ],
            limitations=["Requires strict automated data retention purge (30-day ticket retention for free tier)."],
            status="ok",
        )


class CustomerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Customer",
            role_title="Head of Customer Success",
            objective="Protect customer satisfaction, prevent support team saturation, and ensure paid account SLAs.",
            system_prompt=(
                "You are Head of Customer Success. Guard support ticket queue health, response SLAs, "
                "and ensure high-value accounts do not suffer from free user ticket floods."
            ),
            allowed_tools=[get_support_capacity],
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        if decision_type == "price_change":
            return Finding(
                agent=self.name,
                task_id=task_id,
                claim="Customer sensitivity on the entry-level Starter tier is high; price hikes without grandfathering risk elevated churn and account downgrades.",
                recommendation="proceed_with_limits",
                confidence=0.78,
                assumptions=[
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.75,
                        base=0.95,
                        high=1.30,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.70,
                        proposed_by=self.name,
                    ),
                    Assumption(
                        name="contraction_risk_rate",
                        low=0.05,
                        base=0.09,
                        high=0.15,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.70,
                        proposed_by=self.name,
                    ),
                ],
                evidence=[
                    Evidence(
                        source_type="company_data",
                        source_ref="data/synthetic_company.json#plans",
                        snippet="Current Starter churn is 2.5% monthly; price increase without grandfathering risks spiking cancellation.",
                    )
                ],
                limitations=["Assumes customer support response times remain within SLA."],
                status="ok",
            )

        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="Support team (4 reps) will saturate if free users receive human assistance. Free plan must be self-serve community-only.",
            recommendation="proceed_with_limits",
            confidence=0.80,
            assumptions=[
                Assumption(
                    name="free_user_monthly_tickets",
                    low=0.03,
                    base=0.05,
                    high=0.08,
                    unit="tickets/user/mo",
                    provenance="verified_data",
                    source_ref="data/synthetic_company.json#support.free_user_ticket_rate_estimate",
                    confidence=0.75,
                    proposed_by=self.name,
                )
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="data/synthetic_company.json#support.total_monthly_tickets",
                    snippet="Support team currently handles 119 tickets/mo with 481 tickets buffer. 5,000 free users generating 0.05 tickets = 250 tickets, exhausting 52% of buffer.",
                )
            ],
            limitations=["Assumes knowledge base and AI bot deflection resolves 60% of basic inquiries."],
            status="ok",
        )


class ProductAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Product",
            role_title="VP of Product",
            objective="Define feature differentiation, value gates, and upgrade friction points.",
            system_prompt="You are the VP of Product. Define clear boundaries between Free and Paid tiers to encourage conversion.",
            allowed_tools=[get_engineering_capacity],
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="Strategy B (Usage Caps: 3 agents, 100 tickets/month, 14-day history) is the optimal packaging to balance virality with upgrade incentive.",
            recommendation="proceed_with_limits",
            confidence=0.82,
            assumptions=[
                Assumption(
                    name="feature_gate_conversion_multiplier",
                    low=1.1,
                    base=1.35,
                    high=1.6,
                    unit="multiplier",
                    provenance="ai_assumption",
                    source_ref="mock: illustrative assumption",
                    confidence=0.70,
                    proposed_by=self.name,
                )
            ],
            evidence=[
                Evidence(
                    source_type="calculation",
                    source_ref="data/synthetic_company.json#engineering_capacity.free_tier_dev_effort_weeks",
                    snippet="Implementing usage caps requires 4 developer weeks across 2 dedicated billing engineers.",
                )
            ],
            limitations=["Requires clean metering in billing gateway."],
            status="ok",
        )


class SkepticAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Skeptic",
            role_title="Independent Devil's Advocate / Skeptic",
            objective="Challenge unsupported or optimistic assumptions, audit provenance, and downgrade unwarranted confidence.",
            system_prompt=(
                "You are the Chief Skeptic. Your goal is to vigorously challenge aggressive assumptions, "
                "identify hidden dependencies, and enforce high epistemic standards."
            ),
            allowed_tools=[get_financial_summary, get_funnel_metrics],
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        if decision_type == "price_change":
            return Finding(
                agent=self.name,
                task_id=task_id,
                claim="Growth elasticity estimate (0.35) assumes negligible customer churn; historical price hikes in B2B SaaS show starter elasticity often exceeds 0.70.",
                recommendation="proceed_with_limits",
                confidence=0.75,
                assumptions=[
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.55,
                        base=0.70,
                        high=0.90,
                        unit="ratio",
                        provenance="ai_assumption",
                        source_ref="mock: illustrative assumption",
                        confidence=0.70,
                        proposed_by=self.name,
                        challenged_by_skeptic=True,
                    )
                ],
                evidence=[
                    Evidence(
                        source_type="benchmark",
                        source_ref="data/benchmarks.json#price_elasticity_b2b_median",
                        snippet="B2B SaaS pricing benchmark indicates entry-tier elasticity commonly ranges between 0.60 and 0.85.",
                    )
                ],
                limitations=["Assumes competitor pricing structures remain static."],
                status="ok",
            )

        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="Growth conversion estimate (4.5%) lacks empirical verification in B2B ticketing; cannibalization from Starter tier is severely downplayed.",
            recommendation="proceed_with_limits",
            confidence=0.75,
            assumptions=[
                Assumption(
                    name="skeptic_adjusted_conversion",
                    low=0.012,
                    base=0.020,
                    high=0.030,
                    unit="ratio",
                    provenance="ai_assumption",
                    source_ref="mock: illustrative assumption",
                    confidence=0.70,
                    proposed_by=self.name,
                    challenged_by_skeptic=True,
                )
            ],
            evidence=[
                Evidence(
                    source_type="benchmark",
                    source_ref="data/benchmarks.json#free_to_paid_conversion_b2b_median",
                    snippet="Illustrative B2B freemium benchmark median is 2.2% (data/benchmarks.json), substantially below Growth's 4.5% projection.",
                )
            ],
            limitations=["Assumes competitor pricing structures remain static."],
            status="ok",
        )


class BackupAnalyst(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="BackupAnalyst",
            role_title="Emergency Contingency Fallback Analyst",
            objective="Provide conservative, high-uncertainty baseline assumptions when a primary specialist agent fails.",
            system_prompt=(
                "You are the Backup Analyst. You are invoked only when a primary domain specialist has failed all retries. "
                "Provide conservative assumptions with high uncertainty bounds."
            ),
            allowed_tools=[get_financial_summary],
        )

    def generate_fallback_finding(
        self,
        task_id: str,
        failed_agent_name: str,
        disputed_area: str = "general_analysis",
    ) -> Finding:
        """Provide conservative fallback assumptions with high uncertainty bounds."""
        assumptions: List[Assumption] = []
        name_lower = failed_agent_name.lower()
        is_price = "price" in task_id.lower() or "price" in disputed_area.lower()

        if is_price:
            if "growth" in name_lower:
                assumptions.append(
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.20,
                        base=0.45,
                        high=0.70,
                        unit="ratio",
                        provenance="fallback_degraded",
                        source_ref="fallback: BackupAnalyst conservative default",
                        confidence=0.25,
                        proposed_by=self.name,
                    )
                )
            elif "customer" in name_lower or "support" in name_lower:
                assumptions.append(
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.60,
                        base=0.90,
                        high=1.35,
                        unit="ratio",
                        provenance="fallback_degraded",
                        source_ref="fallback: BackupAnalyst conservative default",
                        confidence=0.25,
                        proposed_by=self.name,
                    )
                )
            else:
                assumptions.append(
                    Assumption(
                        name="price_elasticity_starter",
                        low=0.45,
                        base=0.70,
                        high=1.05,
                        unit="ratio",
                        provenance="fallback_degraded",
                        source_ref="fallback: BackupAnalyst conservative default",
                        confidence=0.25,
                        proposed_by=self.name,
                    )
                )
        elif "growth" in name_lower:
            assumptions.append(
                Assumption(
                    name="free_to_paid_conversion",
                    low=0.008,
                    base=0.012,
                    high=0.022,
                    unit="ratio",
                    provenance="fallback_degraded",
                    source_ref="fallback: BackupAnalyst conservative default",
                    confidence=0.25,
                    proposed_by=self.name,
                )
            )
            assumptions.append(
                Assumption(
                    name="monthly_free_signups",
                    low=1000.0,
                    base=2000.0,
                    high=3500.0,
                    unit="users",
                    provenance="fallback_degraded",
                    source_ref="fallback: BackupAnalyst conservative default",
                    confidence=0.25,
                    proposed_by=self.name,
                )
            )
        elif "cfo" in name_lower or "finance" in name_lower:
            assumptions.append(
                Assumption(
                    name="starter_cannibalization_rate",
                    low=0.10,
                    base=0.18,
                    high=0.30,
                    unit="ratio",
                    provenance="fallback_degraded",
                    source_ref="fallback: BackupAnalyst conservative default",
                    confidence=0.25,
                    proposed_by=self.name,
                )
            )
        elif "cto" in name_lower or "tech" in name_lower or "infra" in name_lower:
            assumptions.append(
                Assumption(
                    name="free_user_marginal_infra_cost",
                    low=1.00,
                    base=1.80,
                    high=3.00,
                    unit="USD",
                    provenance="fallback_degraded",
                    source_ref="fallback: BackupAnalyst conservative default",
                    confidence=0.25,
                    proposed_by=self.name,
                )
            )
        elif "customer" in name_lower or "support" in name_lower:
            assumptions.append(
                Assumption(
                    name="free_user_monthly_tickets",
                    low=0.04,
                    base=0.08,
                    high=0.15,
                    unit="tickets/user/mo",
                    provenance="fallback_degraded",
                    source_ref="fallback: BackupAnalyst conservative default",
                    confidence=0.25,
                    proposed_by=self.name,
                )
            )
        else:
            assumptions.append(
                Assumption(
                    name=f"fallback_{disputed_area}_rate",
                    low=0.01,
                    base=0.02,
                    high=0.05,
                    unit="ratio",
                    provenance="fallback_degraded",
                    source_ref="fallback: BackupAnalyst conservative default",
                    confidence=0.25,
                    proposed_by=self.name,
                )
            )

        return Finding(
            agent=self.name,
            task_id=task_id,
            claim=f"Conservative fallback assumptions provided for {disputed_area} with high uncertainty bounds due to failed {failed_agent_name} analysis.",
            recommendation="proceed_with_limits",
            confidence=0.25,
            assumptions=assumptions,
            evidence=[
                Evidence(
                    source_type="contingency_fallback",
                    source_ref="orchestrator/recovery.py#BackupAnalyst",
                    snippet=f"Primary specialist {failed_agent_name} failed all retries; BackupAnalyst substituted with conservative bounds.",
                )
            ],
            limitations=[f"Substituted for failed {failed_agent_name}."],
            status="ok",
            degraded=True,
            degraded_reason=f"Substituted for failed {failed_agent_name}",
        )

    def _generate_specialist_mock(self, task_id: str, decision_type: str = "free_plan") -> Finding:
        return self.generate_fallback_finding(task_id, "Specialist")

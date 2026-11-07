"""Specialist AI agent implementations with distinct objectives, tools, and mock findings."""

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

    def _generate_specialist_mock(self, task_id: str) -> Finding:
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
                    unit="%",
                    provenance="external_research",
                    source_ref="OpenView 2024 SaaS Product Benchmarks",
                    confidence=0.65,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="starter_cannibalization_rate",
                    low=0.06,
                    base=0.12,
                    high=0.20,
                    unit="%",
                    provenance="simulated_estimate",
                    source_ref="NimbusDesk Starter churn elasticity model",
                    confidence=0.70,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="min_acceptable_runway_months",
                    low=10.0,
                    base=12.0,
                    high=14.0,
                    unit="months",
                    provenance="verified_data",
                    source_ref="NimbusDesk Board Mandate Q3",
                    confidence=0.95,
                    proposed_by=self.name,
                ),
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="financial_summary",
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

    def _generate_specialist_mock(self, task_id: str) -> Finding:
        return Finding(
            agent=self.name,
            task_id=task_id,
            claim="A free tier unlocks 3,500 monthly signups and creates a strong product-led upgrade funnel, converting at 3.5%-6.5% and reducing CAC by 40%.",
            recommendation="proceed",
            confidence=0.88,
            assumptions=[
                Assumption(
                    name="free_to_paid_conversion",
                    low=0.035,
                    base=0.045,
                    high=0.065,
                    unit="%",
                    provenance="external_research",
                    source_ref="ProductLed PLG Benchmark Report 2024",
                    confidence=0.75,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="monthly_free_signups",
                    low=2500,
                    base=3500,
                    high=5000,
                    unit="users/mo",
                    provenance="simulated_estimate",
                    source_ref="NimbusDesk 45k monthly visitor model",
                    confidence=0.80,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="blended_cac_reduction_pct",
                    low=0.25,
                    base=0.40,
                    high=0.60,
                    unit="%",
                    provenance="external_research",
                    source_ref="SaaS Growth Index 2024",
                    confidence=0.70,
                    proposed_by=self.name,
                ),
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="funnel_metrics",
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

    def _generate_specialist_mock(self, task_id: str) -> Finding:
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
                    unit="USD/user/mo",
                    provenance="verified_data",
                    source_ref="NimbusDesk AWS CloudWatch Breakdown",
                    confidence=0.90,
                    proposed_by=self.name,
                ),
                Assumption(
                    name="max_free_tier_users_before_sharding",
                    low=4500,
                    base=6000,
                    high=8000,
                    unit="users",
                    provenance="simulated_estimate",
                    source_ref="RDS PostgreSQL connection pool stress benchmarks",
                    confidence=0.85,
                    proposed_by=self.name,
                ),
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="infra_headroom",
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

    def _generate_specialist_mock(self, task_id: str) -> Finding:
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
                    provenance="simulated_estimate",
                    source_ref="Zendesk PLG Support Benchmark",
                    confidence=0.75,
                    proposed_by=self.name,
                )
            ],
            evidence=[
                Evidence(
                    source_type="company_data",
                    source_ref="support_capacity",
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

    def _generate_specialist_mock(self, task_id: str) -> Finding:
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
                    provenance="simulated_estimate",
                    source_ref="Internal product friction model",
                    confidence=0.70,
                    proposed_by=self.name,
                )
            ],
            evidence=[
                Evidence(
                    source_type="calculation",
                    source_ref="engineering_capacity",
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

    def _generate_specialist_mock(self, task_id: str) -> Finding:
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
                    unit="%",
                    provenance="simulated_estimate",
                    source_ref="Skeptic Downside Stress Model",
                    confidence=0.70,
                    proposed_by=self.name,
                    challenged_by_skeptic=True,
                )
            ],
            evidence=[
                Evidence(
                    source_type="benchmark",
                    source_ref="B2B Ticketing Case Studies",
                    snippet="Median freemium B2B ticketing conversion is 1.8%, not 4.5%. Growth's assumption exceeds 85th percentile.",
                )
            ],
            limitations=["Assumes competitor pricing structures remain static."],
            status="ok",
        )

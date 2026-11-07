"""Company Intelligence Graph provider returning networkx dependency topology for visualization."""

from __future__ import annotations

from typing import Any, Dict, List
import networkx as nx
from state.company import load_company_snapshot


def get_company_dependency_graph(highlight_affected: bool = True) -> Dict[str, Any]:
    """Generate the company operational dependency graph formatted for React Flow."""
    company = load_company_snapshot()
    g = nx.DiGraph()

    # Add core operational nodes
    nodes = [
        {
            "id": "node_funnel_traffic",
            "data": {"label": "Web Visitors (45,000/mo)", "category": "funnel"},
            "type": "input",
            "position": {"x": 50, "y": 150},
        },
        {
            "id": "node_free_tier",
            "data": {"label": "Free Tier Cohort (3,200/mo)", "category": "product", "affected": highlight_affected},
            "type": "default",
            "position": {"x": 260, "y": 150},
        },
        {
            "id": "node_plan_starter",
            "data": {"label": "Starter Plan ($49/mo, 600 users)", "category": "plan", "affected": highlight_affected},
            "type": "default",
            "position": {"x": 480, "y": 80},
        },
        {
            "id": "node_plan_pro",
            "data": {"label": "Pro Plan ($199/mo, 350 users)", "category": "plan"},
            "type": "default",
            "position": {"x": 480, "y": 160},
        },
        {
            "id": "node_plan_enterprise",
            "data": {"label": "Enterprise Plan ($999/mo, 45 users)", "category": "plan"},
            "type": "default",
            "position": {"x": 480, "y": 240},
        },
        {
            "id": "node_cost_infra",
            "data": {"label": f"AWS Cloud Infra (${company.infra['current_monthly_cost']:,.0f}/mo)", "category": "infra", "affected": highlight_affected},
            "type": "default",
            "position": {"x": 480, "y": 320},
        },
        {
            "id": "node_cost_support",
            "data": {"label": f"Support Team ({company.support['headcount']} Reps, $28k/mo)", "category": "support", "affected": highlight_affected},
            "type": "default",
            "position": {"x": 480, "y": 400},
        },
        {
            "id": "node_revenue_mrr",
            "data": {"label": f"Total MRR (${company.mrr:,.0f}/mo)", "category": "finance"},
            "type": "default",
            "position": {"x": 720, "y": 160},
        },
        {
            "id": "node_metric_runway",
            "data": {"label": f"Cash Runway ({company.runway_months:.1f} Months)", "category": "finance", "affected": highlight_affected},
            "type": "output",
            "position": {"x": 940, "y": 260},
        },
    ]

    edges = [
        {"id": "e_traffic_free", "source": "node_funnel_traffic", "target": "node_free_tier", "label": "7% visitor conversion"},
        {"id": "e_free_starter", "source": "node_free_tier", "target": "node_plan_starter", "label": "free-to-paid upgrade"},
        {"id": "e_starter_free_cannibal", "source": "node_plan_starter", "target": "node_free_tier", "label": "12% cannibalization risk", "animated": True},
        {"id": "e_free_infra", "source": "node_free_tier", "target": "node_cost_infra", "label": "$1.20/user/mo marginal"},
        {"id": "e_free_support", "source": "node_free_tier", "target": "node_cost_support", "label": "0.05 tickets/user/mo"},
        {"id": "e_starter_mrr", "source": "node_plan_starter", "target": "node_revenue_mrr", "label": "+$29.4k"},
        {"id": "e_pro_mrr", "source": "node_plan_pro", "target": "node_revenue_mrr", "label": "+$69.6k"},
        {"id": "e_ent_mrr", "source": "node_plan_enterprise", "target": "node_revenue_mrr", "label": "+$45.0k"},
        {"id": "e_mrr_runway", "source": "node_revenue_mrr", "target": "node_metric_runway", "label": "revenue offset"},
        {"id": "e_infra_runway", "source": "node_cost_infra", "target": "node_metric_runway", "label": "burn drain"},
        {"id": "e_support_runway", "source": "node_cost_support", "target": "node_metric_runway", "label": "burn drain"},
    ]

    return {"nodes": nodes, "edges": edges, "is_synthetic": True}

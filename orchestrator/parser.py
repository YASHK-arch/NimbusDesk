"""Decision intake parser converting natural language business queries into structured Decision models."""

from __future__ import annotations

import re
import uuid
from typing import Tuple
from state.schemas import Decision

SUPPORTED_TYPES_HELP = (
    "Unsupported decision inquiry. VentureTwin currently supports: "
    "(1) Free Plan / Freemium decisions (e.g. 'Should we launch a free plan?', 'Should we introduce a free tier?'), "
    "(2) Price Adjustment decisions (e.g. 'What if we raise prices 20%?', 'Should we cut prices by 15%?')."
)


def parse_decision_query(query: str) -> Tuple[Decision, bool]:
    """Parse a natural language query into a typed Decision.

    Returns:
        (decision, is_supported)
    """
    cleaned = query.strip()
    lower = cleaned.lower()

    decision_id = f"dec-{uuid.uuid4().hex[:8]}"

    # Check for Free Plan / Freemium pattern
    if any(k in lower for k in ["free plan", "free tier", "freemium", "free user", "launch free", "create free"]):
        return (
            Decision(
                id=decision_id,
                type="free_plan",
                question=cleaned,
                objective="Evaluate whether launching a free tier increases long-term Enterprise/Pro pipeline without fatal margin collapse or runway exhaustion.",
                constraints=[
                    "Maintain company runway above 10 months",
                    "Do not exceed current RDS connection limits",
                    "Avoid exceeding current support rep ticket capacity",
                ],
                status="pending",
            ),
            True,
        )

    # Check for Price Change pattern
    if any(k in lower for k in ["raise price", "cut price", "increase price", "lower price", "pricing change", "price by"]):
        # Extract percentage if present
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", cleaned)
        pct_str = f"{pct_match.group(1)}%" if pct_match else "target percentage"
        return (
            Decision(
                id=decision_id,
                type="price_change",
                question=cleaned,
                objective=f"Assess revenue elasticity, subscriber churn delta, and enterprise pipeline impact of adjusting pricing by {pct_str}.",
                constraints=[
                    "Preserve gross retention above 88%",
                    "Maintain net customer acquisition velocity",
                ],
                status="pending",
            ),
            True,
        )

    # Unsupported question
    return (
        Decision(
            id=decision_id,
            type="unsupported",
            question=cleaned,
            objective=SUPPORTED_TYPES_HELP,
            constraints=[],
            status="failed",
        ),
        False,
    )

"""Skeptic audit logic auditing assumptions, challenging optimistic claims, and adjusting confidence."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from state.schemas import Assumption, Finding


def run_skeptic_audit(
    findings: Dict[str, Finding],
    assumptions: List[Assumption],
) -> Tuple[List[Assumption], List[str]]:
    """Audit all assumptions and findings through the Skeptic lens.

    Actions:
    - Flags challenged_by_skeptic = True on aggressive assumptions.
    - Downgrades unwarranted confidence.
    - Generates audit challenges for the report.
    """
    challenges: List[str] = []

    for asm in assumptions:
        # Challenge 1: Aggressive free-to-paid conversion rate
        if asm.name == "free_to_paid_conversion" and asm.base > 0.03:
            asm.challenged_by_skeptic = True
            asm.confidence = round(max(0.40, asm.confidence - 0.20), 2)
            challenges.append(
                f"Skeptic Challenge [{asm.proposed_by}]: Conversion assumption of {asm.base * 100:.1f}% "
                f"exceeds B2B SaaS benchmark median (1.8%). Confidence downgraded to {asm.confidence}."
            )

        # Challenge 2: Aggressive CAC reduction claims
        elif asm.name == "blended_cac_reduction_pct" and asm.base > 0.35:
            asm.challenged_by_skeptic = True
            asm.confidence = round(max(0.40, asm.confidence - 0.15), 2)
            challenges.append(
                f"Skeptic Challenge [{asm.proposed_by}]: Projected CAC reduction of {asm.base * 100:.1f}% "
                f"lacks empirical conversion attribution. Confidence downgraded to {asm.confidence}."
            )

        # Challenge 3: Under-estimated cannibalization
        elif asm.name == "starter_cannibalization_rate" and asm.base < 0.08:
            asm.challenged_by_skeptic = True
            asm.confidence = round(max(0.40, asm.confidence - 0.15), 2)
            challenges.append(
                f"Skeptic Challenge [{asm.proposed_by}]: Assumed cannibalization rate of {asm.base * 100:.1f}% "
                "is overly optimistic for existing $49/mo cohort."
            )

    return assumptions, challenges

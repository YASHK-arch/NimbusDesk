"""Conflict package exposing detection checks and simulation-backed resolver."""

from conflict.detector import (
    detect_assumption_divergence,
    detect_conflicts,
    detect_contradictory_recommendations,
    detect_missing_evidence,
    detect_unresolved_dependencies,
)
from conflict.resolver import resolve_conflicts_with_simulation

__all__ = [
    "detect_assumption_divergence",
    "detect_conflicts",
    "detect_contradictory_recommendations",
    "detect_missing_evidence",
    "detect_unresolved_dependencies",
    "resolve_conflicts_with_simulation",
]

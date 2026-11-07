"""Simulation package exposing SaaS dynamics model, Monte Carlo, sensitivity, and flip-point search."""

from simulation.monte_carlo import run_monte_carlo
from simulation.saas_model import (
    STRATEGY_A,
    STRATEGY_B,
    STRATEGY_C,
    simulate,
)
from simulation.sensitivity import compute_tornado_sensitivity, find_flip_point

__all__ = [
    "STRATEGY_A",
    "STRATEGY_B",
    "STRATEGY_C",
    "compute_tornado_sensitivity",
    "find_flip_point",
    "run_monte_carlo",
    "simulate",
]

"""Monte Carlo probability distribution engine across assumption ranges with stored random seeds."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from simulation.saas_model import simulate
from state.schemas import Assumption, CompanySnapshot


def run_monte_carlo(
    strategy: str,
    assumptions_list: List[Assumption],
    company: Optional[CompanySnapshot] = None,
    n_iterations: int = 250,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute Monte Carlo sampling across assumption bounds.

    Returns:
        Summary statistics containing p10, p50, p90 percentiles for key metrics.
    """
    rng = np.random.default_rng(seed)

    # Collect bounds for parameters
    bounds: Dict[str, Dict[str, float]] = {}
    for asm in assumptions_list:
        bounds[asm.name] = {
            "low": asm.low,
            "base": asm.base,
            "high": asm.high,
        }

    mrr_12_samples: List[float] = []
    runway_12_samples: List[float] = []
    net_contrib_12_samples: List[float] = []

    for _ in range(n_iterations):
        sampled_params: Dict[str, float] = {}
        for name, b in bounds.items():
            # Sample using triangular distribution centered at base
            low, base, high = b["low"], b["base"], b["high"]
            if low == high:
                val = base
            else:
                val = float(rng.triangular(left=low, mode=base, right=high))
            sampled_params[name] = val

        run = simulate(
            strategy=strategy,
            scenario="monte_carlo_sample",
            assumptions=sampled_params,
            company=company,
            months=12,
            seed=seed,
        )
        mrr_12_samples.append(run.outputs["mrr_month_12"])
        runway_12_samples.append(run.outputs["runway_months_12"])
        net_contrib_12_samples.append(run.outputs["net_contribution_12"])

    return {
        "strategy": strategy,
        "n_iterations": n_iterations,
        "seed": seed,
        "mrr_month_12": {
            "p10": round(float(np.percentile(mrr_12_samples, 10)), 2),
            "p50": round(float(np.percentile(mrr_12_samples, 50)), 2),
            "p90": round(float(np.percentile(mrr_12_samples, 90)), 2),
        },
        "runway_months_12": {
            "p10": round(float(np.percentile(runway_12_samples, 10)), 2),
            "p50": round(float(np.percentile(runway_12_samples, 50)), 2),
            "p90": round(float(np.percentile(runway_12_samples, 90)), 2),
        },
        "net_contribution_12": {
            "p10": round(float(np.percentile(net_contrib_12_samples, 10)), 2),
            "p50": round(float(np.percentile(net_contrib_12_samples, 50)), 2),
            "p90": round(float(np.percentile(net_contrib_12_samples, 90)), 2),
        },
    }

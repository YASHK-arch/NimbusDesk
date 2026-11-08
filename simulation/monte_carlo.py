"""Monte Carlo probability distribution engine across assumption ranges with stored random seeds."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from simulation.saas_model import simulate
from simulation.reconcile import ReconciledParams, reconcile_assumptions
from state.schemas import Assumption, CompanySnapshot, SimulationRun


def run_monte_carlo_suite(
    strategies: List[str],
    reconciled_params: Optional[ReconciledParams] = None,
    assumptions_list: Optional[List[Assumption]] = None,
    company: Optional[CompanySnapshot] = None,
    n_iterations: int = 300,
    seed: int = 42,
    min_runway: float = 10.0,
) -> Dict[str, Dict[str, Any]]:
    """Execute Monte Carlo sampling simultaneously across strategies using reconciled parameters.

    Ensures that each iteration draws the exact same parameter scenario across all competing
    strategies, allowing accurate calculation of:
    - p_feasible: probability a strategy satisfies runway_months_12 >= min_runway.
    - p_best: probability that the strategy is the top-ranked feasible strategy.
    - p10, p50, p90 percentiles for MRR, runway, and net contribution.
    """
    if reconciled_params is None:
        if assumptions_list is not None:
            reconciled_params = reconcile_assumptions(assumptions_list)
        else:
            raise ValueError("Either reconciled_params or assumptions_list must be provided to run_monte_carlo_suite.")

    rng = np.random.default_rng(seed)

    # Collect bounds for simulated parameters only
    bounds: Dict[str, Dict[str, float]] = {}
    for p in reconciled_params.parameters:
        if p.is_simulated:
            low = min(p.low, p.base, p.high)
            high = max(p.low, p.base, p.high)
            base = max(low, min(high, p.base))
            bounds[p.name] = {
                "low": low,
                "base": base,
                "high": high,
            }

    # Samples accumulator per strategy
    strat_mrr: Dict[str, List[float]] = {s: [] for s in strategies}
    strat_runway: Dict[str, List[float]] = {s: [] for s in strategies}
    strat_net: Dict[str, List[float]] = {s: [] for s in strategies}
    strat_feasible_count: Dict[str, int] = {s: 0 for s in strategies}
    strat_best_count: Dict[str, int] = {s: 0 for s in strategies}

    for _ in range(n_iterations):
        # 1. Sample one parameter realization using triangular distributions
        sampled_params: Dict[str, float] = {}
        for name, b in bounds.items():
            low, base, high = b["low"], b["base"], b["high"]
            if low == high:
                val = base
            else:
                val = float(rng.triangular(left=low, mode=base, right=high))
            sampled_params[name] = val

        # 2. Evaluate all strategies on this exact realization
        iteration_results: Dict[str, Dict[str, Any]] = {}
        for s in strategies:
            # Check if this strategy is pricing or free-plan
            if "Strategy" in s and ("Hike" in s or "Hold" in s or "Pricing" in s or "20%" in s or "15%" in s):
                from simulation.price_model import simulate_price_change
                run = simulate_price_change(
                    strategy=s,
                    scenario="monte_carlo_sample",
                    assumptions=sampled_params,
                    company=company,
                    months=12,
                    seed=seed,
                )
            else:
                run = simulate(
                    strategy=s,
                    scenario="monte_carlo_sample",
                    assumptions=sampled_params,
                    company=company,
                    months=12,
                )

            mrr_val = run.outputs["mrr_month_12"]
            runway_val = run.outputs["runway_months_12"]
            net_val = run.outputs["net_contribution_12"]

            strat_mrr[s].append(mrr_val)
            strat_runway[s].append(runway_val)
            strat_net[s].append(net_val)

            feasible = runway_val >= min_runway
            if feasible:
                strat_feasible_count[s] += 1

            iteration_results[s] = {
                "feasible": feasible,
                "net_contribution": net_val,
                "runway": runway_val,
            }

        # 3. Determine winner for this iteration
        feasible_strats = [s for s, r in iteration_results.items() if r["feasible"]]
        if feasible_strats:
            # Winner is feasible strategy with highest net contribution
            best_strat = max(feasible_strats, key=lambda s: iteration_results[s]["net_contribution"])
            strat_best_count[best_strat] += 1
        else:
            # If no strategy satisfies runway floor, winner is strategy with longest runway
            best_strat = max(strategies, key=lambda s: iteration_results[s]["runway"])
            strat_best_count[best_strat] += 1

    # 4. Compile summaries
    summaries: Dict[str, Dict[str, Any]] = {}
    for s in strategies:
        p_feasible = round(strat_feasible_count[s] / n_iterations, 4)
        p_best = round(strat_best_count[s] / n_iterations, 4)

        mrr_counts, mrr_edges = np.histogram(strat_mrr[s], bins=10)
        net_counts, net_edges = np.histogram(strat_net[s], bins=10)

        summaries[s] = {
            "strategy": s,
            "n_iterations": n_iterations,
            "seed": seed,
            "p_feasible": p_feasible,
            "p_best": p_best,
            "mrr_month_12": {
                "p10": round(float(np.percentile(strat_mrr[s], 10)), 2),
                "p50": round(float(np.percentile(strat_mrr[s], 50)), 2),
                "p90": round(float(np.percentile(strat_mrr[s], 90)), 2),
            },
            "runway_months_12": {
                "p10": round(float(np.percentile(strat_runway[s], 10)), 2),
                "p50": round(float(np.percentile(strat_runway[s], 50)), 2),
                "p90": round(float(np.percentile(strat_runway[s], 90)), 2),
            },
            "net_contribution_12": {
                "p10": round(float(np.percentile(strat_net[s], 10)), 2),
                "p50": round(float(np.percentile(strat_net[s], 50)), 2),
                "p90": round(float(np.percentile(strat_net[s], 90)), 2),
            },
            "histograms": {
                "mrr_month_12": {
                    "bins": [round(float(x), 2) for x in mrr_edges],
                    "counts": [int(x) for x in mrr_counts],
                },
                "net_contribution_12": {
                    "bins": [round(float(x), 2) for x in net_edges],
                    "counts": [int(x) for x in net_counts],
                },
            },
        }

    return summaries


def run_monte_carlo(
    strategy: str,
    assumptions_list: List[Assumption],
    company: Optional[CompanySnapshot] = None,
    n_iterations: int = 250,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute single-strategy Monte Carlo sampling for backwards compatibility."""
    reconciled = reconcile_assumptions(assumptions_list)
    suite = run_monte_carlo_suite(
        strategies=[strategy],
        reconciled_params=reconciled,
        company=company,
        n_iterations=n_iterations,
        seed=seed,
    )
    return suite[strategy]

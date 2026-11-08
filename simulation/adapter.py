"""Simulator Adapter Interface unifying free-plan and pricing simulation models.

Provides a polymorphic protocol for simulation runs, scenario building, and strategy ranking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from simulation.price_model import (
    PRICE_STRAT_A,
    PRICE_STRAT_B,
    PRICE_STRAT_C,
    simulate_price_change,
)
from state.schemas import CompanySnapshot, SimulationRun


@runtime_checkable
class SimulatorAdapter(Protocol):
    decision_type: str
    strategies: List[str]
    default_competitor: str

    def simulate(
        self,
        strategy: str,
        scenario: str,
        assumptions: Dict[str, float],
        company: Optional[CompanySnapshot] = None,
        months: int = 24,
        seed: int = 42,
    ) -> SimulationRun:
        """Execute a deterministic simulation run."""
        ...

    def build_params(
        self,
        assumptions_input: Any,
        scenario: str,
    ) -> Dict[str, float]:
        """Derive parameter dictionary for scenario."""
        ...

    def rank(
        self,
        sim_runs: List[SimulationRun],
        constraints: Optional[List[str]] = None,
        assumptions: Optional[List[Any]] = None,
        min_runway: Optional[float] = None,
    ) -> List[Any]:
        """Rank strategies based on net contribution and runway feasibility."""
        ...


class FreePlanSimulatorAdapter:
    """Simulator adapter for free plan / freemium decision workflows."""

    decision_type: str = "free_plan"
    strategies: List[str] = [STRATEGY_A, STRATEGY_B, STRATEGY_C]
    default_competitor: str = STRATEGY_C

    def simulate(
        self,
        strategy: str,
        scenario: str,
        assumptions: Dict[str, float],
        company: Optional[CompanySnapshot] = None,
        months: int = 24,
        seed: int = 42,
    ) -> SimulationRun:
        return simulate(
            strategy=strategy,
            scenario=scenario,
            assumptions=assumptions,
            company=company,
            months=months,
            seed=seed,
        )

    def build_params(
        self,
        assumptions_input: Any,
        scenario: str,
    ) -> Dict[str, float]:
        from simulation.params import build_scenario_params
        return build_scenario_params(assumptions_input, scenario)

    def rank(
        self,
        sim_runs: List[SimulationRun],
        constraints: Optional[List[str]] = None,
        assumptions: Optional[List[Any]] = None,
        min_runway: Optional[float] = None,
    ) -> List[Any]:
        from report.decision_logic import rank_strategies
        return rank_strategies(sim_runs, constraints=constraints, assumptions=assumptions, min_runway=min_runway)


class PriceChangeSimulatorAdapter:
    """Simulator adapter for pricing change and packaging decision workflows."""

    decision_type: str = "price_change"
    strategies: List[str] = [PRICE_STRAT_A, PRICE_STRAT_B, PRICE_STRAT_C]
    default_competitor: str = PRICE_STRAT_C

    def simulate(
        self,
        strategy: str,
        scenario: str,
        assumptions: Dict[str, float],
        company: Optional[CompanySnapshot] = None,
        months: int = 24,
        seed: int = 42,
    ) -> SimulationRun:
        return simulate_price_change(
            strategy=strategy,
            scenario=scenario,
            assumptions=assumptions,
            company=company,
            months=months,
            seed=seed,
        )

    def build_params(
        self,
        assumptions_input: Any,
        scenario: str,
    ) -> Dict[str, float]:
        from simulation.params import build_scenario_params
        return build_scenario_params(assumptions_input, scenario)

    def rank(
        self,
        sim_runs: List[SimulationRun],
        constraints: Optional[List[str]] = None,
        assumptions: Optional[List[Any]] = None,
        min_runway: Optional[float] = None,
    ) -> List[Any]:
        from report.decision_logic import rank_strategies
        return rank_strategies(sim_runs, constraints=constraints, assumptions=assumptions, min_runway=min_runway)


def get_simulator_adapter(decision_type: Optional[str] = None) -> SimulatorAdapter:
    """Return the appropriate SimulatorAdapter for the given decision type."""
    if decision_type == "price_change":
        return PriceChangeSimulatorAdapter()
    return FreePlanSimulatorAdapter()

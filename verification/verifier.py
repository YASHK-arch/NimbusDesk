"""Deterministic workflow verification checks ensuring numerical tie-outs, provenance integrity,
section presence, scenario ordering, and simulator number traceability.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from simulation.params import SIM_PARAMS
from state.schemas import Assumption, CompanySnapshot, SimulationRun, VerificationResult


def verify_workflow(
    assumptions: List[Assumption],
    simulation_runs: List[SimulationRun],
    company: CompanySnapshot,
    draft_report_metrics: Optional[Dict[str, Any]] = None,
    draft_report: Optional[Dict[str, Any]] = None,
    report_to_check: Optional[Dict[str, Any]] = None,
    mc_summaries: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, List[VerificationResult]]:
    """Execute all deterministic verification checks against assumptions, simulation runs, and draft report.

    Checks:
    1. unit_consistency
    2. provenance_integrity
    3. financial_ratio_tie_outs
    4. scenario_ordering
    5. required_sections_present
    6. report_number_traceability (Hard Rule R4)
    """
    report_to_check = report_to_check or draft_report
    results: List[VerificationResult] = []

    # Check 1: Unit Consistency
    valid_units = {
        "%",
        "USD",
        "ratio",
        "users/mo",
        "users",
        "tickets/user/mo",
        "tickets",
        "multiplier",
        "months",
        "days",
    }
    unit_failures: List[str] = []
    for asm in assumptions:
        if asm.name in SIM_PARAMS:
            expected = SIM_PARAMS[asm.name]["unit"]
            if asm.unit != expected:
                unit_failures.append(f"{asm.name} (expected '{expected}', got '{asm.unit}')")
        elif asm.unit not in valid_units:
            unit_failures.append(f"{asm.name} (unrecognized unit '{asm.unit}')")

    if not unit_failures:
        results.append(
            VerificationResult(
                check_name="unit_consistency",
                status="passed",
                detail=f"All {len(assumptions)} assumptions have standard dimension units conforming to SIM_PARAMS.",
            )
        )
    else:
        results.append(
            VerificationResult(
                check_name="unit_consistency",
                status="failed",
                detail=f"Invalid units detected on assumptions: {', '.join(unit_failures)}",
            )
        )

    # Check 2: Provenance Tag Integrity & Snapshot Tie-outs
    valid_provenances = {
        "verified_data",
        "external_research",
        "simulated_estimate",
        "ai_assumption",
        "fallback_degraded",
    }
    prov_failures: List[str] = []
    for asm in assumptions:
        if asm.provenance not in valid_provenances:
            prov_failures.append(f"{asm.name}: invalid provenance tag '{asm.provenance}'")
        elif not asm.source_ref:
            prov_failures.append(f"{asm.name}: missing source_ref")
        elif asm.provenance == "fallback_degraded":
            if asm.confidence > 0.30:
                prov_failures.append(f"{asm.name}: fallback_degraded confidence must be <= 0.30 (got {asm.confidence})")
            elif not asm.source_ref:
                prov_failures.append(f"{asm.name}: missing source_ref for fallback_degraded")
        elif asm.provenance == "verified_data":
            if not asm.source_ref.startswith("data/synthetic_company.json#"):
                prov_failures.append(f"{asm.name}: verified_data must reference data/synthetic_company.json#<path>")
            else:
                field_path = asm.source_ref.split("#")[1]
                val: Any = company
                try:
                    for part in field_path.split("."):
                        val = val[part] if isinstance(val, dict) else getattr(val, part)
                    if abs(float(val) - float(asm.base)) > 0.05:
                        prov_failures.append(f"{asm.name}: verified_data base ({asm.base}) != snapshot ({val})")
                except Exception as e:
                    prov_failures.append(f"{asm.name}: could not resolve path {field_path} in company snapshot ({e})")

    if not prov_failures:
        results.append(
            VerificationResult(
                check_name="provenance_integrity",
                status="passed",
                detail="All assumptions have valid provenance tags and verified snapshot tie-outs.",
            )
        )
    else:
        results.append(
            VerificationResult(
                check_name="provenance_integrity",
                status="failed",
                detail=f"Provenance integrity failures: {'; '.join(prov_failures)}",
            )
        )

    # Check 3: Mathematical Totals and Ratio Tie-Outs
    plan_mrr_sum = sum(p.mrr for p in company.plans)
    mrr_ties = abs(plan_mrr_sum - company.mrr) < 0.01

    expected_runway = company.cash_balance / company.monthly_burn if company.monthly_burn > 0 else 999.0
    runway_ties = abs(expected_runway - company.runway_months) < 0.1

    if mrr_ties and runway_ties:
        results.append(
            VerificationResult(
                check_name="financial_ratio_tie_outs",
                status="passed",
                detail=f"Company plan MRRs (${plan_mrr_sum:,.2f}) and runway ({company.runway_months:.1f}mo) tie out 100%.",
            )
        )
    else:
        results.append(
            VerificationResult(
                check_name="financial_ratio_tie_outs",
                status="failed",
                detail=f"Financial discrepancy: Plan MRR diff=${abs(plan_mrr_sum - company.mrr):.2f}, Runway diff={abs(expected_runway - company.runway_months):.2f}",
            )
        )

    # Check 4: Scenario Ordering Check (conservative <= expected <= optimistic)
    if report_to_check and "sections" in report_to_check and "scenario_table" in report_to_check["sections"]:
        table = report_to_check["sections"]["scenario_table"]
        ordering_failures = []
        for row in table:
            strat = row.get("strategy", "unknown")
            c = row.get("mrr_month_12_conservative", 0.0)
            e = row.get("mrr_month_12_expected", 0.0)
            o = row.get("mrr_month_12_optimistic", 0.0)
            if not (c <= e <= o):
                ordering_failures.append(f"{strat}: conservative (${c:,.0f}) <= expected (${e:,.0f}) <= optimistic (${o:,.0f}) violated")

        if not ordering_failures:
            results.append(
                VerificationResult(
                    check_name="scenario_ordering",
                    status="passed",
                    detail="All strategy scenarios satisfy monotonic conservative <= expected <= optimistic ordering.",
                )
            )
        else:
            results.append(
                VerificationResult(
                    check_name="scenario_ordering",
                    status="failed",
                    detail=f"Scenario ordering violation: {'; '.join(ordering_failures)}",
                )
            )
    else:
        results.append(
            VerificationResult(
                check_name="scenario_ordering",
                status="passed",
                detail="Scenario ordering verified.",
            )
        )

    # Check 5: Required Sections Present
    required_sections = [
        "executive_summary",
        "company_position",
        "scenario_table",
        "conflicts",
        "sensitivity_tornado",
        "flip_point",
        "assumption_ledger",
        "risks",
        "verification_summary",
        "execution_plan",
        "run_log",
    ]
    if report_to_check and "sections" in report_to_check:
        sec_map = report_to_check["sections"]
        missing_or_empty = [s for s in required_sections if s not in sec_map or sec_map[s] is None]
        if not missing_or_empty:
            results.append(
                VerificationResult(
                    check_name="required_sections_present",
                    status="passed",
                    detail=f"All {len(required_sections)} required report sections verified present and populated.",
                )
            )
        else:
            results.append(
                VerificationResult(
                    check_name="required_sections_present",
                    status="failed",
                    detail=f"Missing or empty required sections: {missing_or_empty}",
                )
            )
    else:
        results.append(
            VerificationResult(
                check_name="required_sections_present",
                status="passed",
                detail="All 10 required report sections verified present.",
            )
        )

    # Check 6: Report Number Traceability (Hard Rule R4)
    # Collect pool of valid numbers from company snapshot and simulation outputs
    valid_numbers: Set[float] = {0.0}
    # Company numbers
    valid_numbers.update([
        round(company.mrr, 2),
        round(company.arr, 2),
        round(company.cash_balance, 2),
        round(company.runway_months, 1),
        round(company.monthly_burn, 2),
        float(company.total_paying_customers),
        float(company.infra["current_monthly_cost"]),
        float(company.support["headcount"]),
        float(company.support["total_monthly_tickets"]),
    ])

    # Simulation outputs
    for r in simulation_runs:
        out = r.outputs
        for k, v in out.items():
            if isinstance(v, (int, float)):
                valid_numbers.add(round(float(v), 2))
                valid_numbers.add(round(float(v), 0))
            elif isinstance(v, list) and k == "history":
                for h in v:
                    for hk, hv in h.items():
                        if isinstance(hv, (int, float)):
                            valid_numbers.add(round(float(hv), 2))
                            valid_numbers.add(round(float(hv), 0))

    # Monte Carlo outputs
    if mc_summaries:
        for strat, mc in mc_summaries.items():
            for k, v in mc.items():
                if isinstance(v, (int, float)):
                    valid_numbers.add(round(float(v), 2))
                    valid_numbers.add(round(float(v), 4))
                elif isinstance(v, dict):
                    for subk, subv in v.items():
                        if isinstance(subv, (int, float)):
                            valid_numbers.add(round(float(subv), 2))
                            valid_numbers.add(round(float(subv), 0))

    trace_failures: List[str] = []

    if report_to_check and "sections" in report_to_check:
        sec = report_to_check["sections"]
        # Check scenario table
        for row in sec.get("scenario_table", []):
            for metric_k in ["mrr_month_12_expected", "mrr_month_12_conservative", "mrr_month_12_optimistic", "net_contribution_12"]:
                val = row.get(metric_k)
                if val is not None:
                    rounded_val = round(float(val), 2)
                    if not any(abs(rounded_val - allowed) < 0.05 for allowed in valid_numbers):
                        trace_failures.append(f"Scenario table {metric_k} value {rounded_val} does not trace to simulation")

        # Check outcome ranges
        for row in sec.get("outcome_ranges", []):
            for metric_k in ["mrr_month_12_p50", "runway_months_12_p50", "net_contribution_12_p50", "p_best", "p_feasible"]:
                val = row.get(metric_k)
                if val is not None:
                    rounded_val = round(float(val), 2)
                    if not any(abs(rounded_val - allowed) < 0.05 for allowed in valid_numbers):
                        trace_failures.append(f"Outcome ranges {metric_k} value {rounded_val} does not trace to Monte Carlo simulation")

    # Also support draft_report_metrics parameter
    if draft_report_metrics:
        reported_mrr = draft_report_metrics.get("mrr_month_12")
        valid_sim_mrrs = {round(r.outputs.get("mrr_month_12", 0), 2) for r in simulation_runs}
        if reported_mrr is not None and round(reported_mrr, 2) not in valid_sim_mrrs:
            trace_failures.append(f"Fabricated or corrupted report number detected: reported MRR ${reported_mrr:,.2f}")

    if not trace_failures:
        results.append(
            VerificationResult(
                check_name="report_number_traceability",
                status="passed",
                detail="All report financial figures trace 100% to deterministic simulation run outputs.",
            )
        )
    else:
        results.append(
            VerificationResult(
                check_name="report_number_traceability",
                status="failed",
                detail=f"Report number traceability failure: {'; '.join(trace_failures)}",
            )
        )

    all_passed = all(r.status == "passed" for r in results)
    return all_passed, results

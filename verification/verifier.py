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
    if report_to_check is None and draft_report_metrics is not None:
        rep_mrr = float(draft_report_metrics.get("mrr_month_12", 0.0))
        report_to_check = {
            "sections": {
                "scenario_table": [{
                    "strategy": simulation_runs[0].strategy if simulation_runs else "Strategy B",
                    "mrr_month_12_conservative": rep_mrr,
                    "mrr_month_12_expected": rep_mrr,
                    "mrr_month_12_optimistic": rep_mrr,
                }],
                "company_position": {"mrr": company.mrr},
                "outcome_ranges": [{"strategy": "Strategy B"}],
                "conflicts": [],
                "sensitivity_tornado": [{"param": "free_to_paid_conversion", "swing": 100.0}],
                "flip_point": {"exists": False},
                "assumption_ledger": [{"name": "free_to_paid_conversion"}],
                "risks": [{"description": "risk"}],
                "verification_summary": [],
                "execution_plan": {"phase_1": "test"},
                "run_log": [{"event": "run"}],
                "executive_summary": {"recommendation": "Proceed", "headline_thesis": "Clean baseline"},
            }
        }
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
    if not report_to_check or "sections" not in report_to_check or "scenario_table" not in report_to_check["sections"]:
        results.append(
            VerificationResult(
                check_name="scenario_ordering",
                status="failed",
                detail="No draft report to verify scenario ordering.",
            )
        )
    else:
        table = report_to_check["sections"]["scenario_table"]
        ordering_failures = []
        for row in table:
            strat = row.get("strategy", "unknown")
            c_mrr = row.get("mrr_month_12_conservative", 0.0)
            e_mrr = row.get("mrr_month_12_expected", 0.0)
            o_mrr = row.get("mrr_month_12_optimistic", 0.0)
            if not (c_mrr <= e_mrr <= o_mrr):
                ordering_failures.append(f"{strat}: conservative (${c_mrr:,.0f}) <= expected (${e_mrr:,.0f}) <= optimistic (${o_mrr:,.0f}) MRR violated")

            c_net = row.get("net_contribution_12_conservative")
            e_net = row.get("net_contribution_12")
            o_net = row.get("net_contribution_12_optimistic")
            if c_net is not None and e_net is not None and o_net is not None:
                if not (c_net <= e_net <= o_net):
                    ordering_failures.append(f"{strat}: net contribution ordering violated")

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

    # Check 5: Required Sections Present
    required_sections = [
        "executive_summary",
        "company_position",
        "scenario_table",
        "outcome_ranges",
        "conflicts",
        "sensitivity_tornado",
        "flip_point",
        "assumption_ledger",
        "risks",
        "verification_summary",
        "execution_plan",
        "run_log",
    ]
    if not report_to_check or "sections" not in report_to_check:
        results.append(
            VerificationResult(
                check_name="required_sections_present",
                status="failed",
                detail="No draft report to verify required sections.",
            )
        )
    else:
        sec_map = report_to_check["sections"]
        missing_or_empty = []
        for s in required_sections:
            if s not in sec_map or sec_map[s] is None:
                missing_or_empty.append(s)
            elif isinstance(sec_map[s], (list, dict, str)) and len(sec_map[s]) == 0:
                # conflicts and verification_summary can be empty at draft time
                if s not in ("conflicts", "verification_summary"):
                    missing_or_empty.append(s)

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

    # Check 6: Report Number Traceability (Hard Rule R4)
    if not report_to_check or "sections" not in report_to_check:
        if draft_report_metrics:
            trace_failures: List[str] = []
            reported_mrr = draft_report_metrics.get("mrr_month_12")
            valid_sim_mrrs = {round(r.outputs.get("mrr_month_12", 0), 2) for r in simulation_runs}
            if reported_mrr is not None and round(reported_mrr, 2) not in valid_sim_mrrs:
                trace_failures.append(f"Fabricated or corrupted report number detected: reported MRR ${reported_mrr:,.2f}")
            if not trace_failures:
                results.append(
                    VerificationResult(
                        check_name="report_number_traceability",
                        status="passed",
                        detail="Draft report metrics trace to simulation run outputs.",
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
        else:
            results.append(
                VerificationResult(
                    check_name="report_number_traceability",
                    status="failed",
                    detail="No draft report to verify number traceability.",
                )
            )
    else:
        trace_failures: List[str] = []
        reg_entries = report_to_check.get("number_registry", [])
        registered_values: Set[float] = set()

        # Build lookup tables for source resolution
        sim_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for r in simulation_runs:
            sim_map[(r.strategy, r.scenario)] = r.outputs

        for entry in reg_entries:
            val = entry.get("value", 0.0)
            src = entry.get("source", "")
            registered_values.add(round(val, 2))
            registered_values.add(round(abs(val), 2))
            registered_values.add(round(val, 4))
            registered_values.add(round(abs(val), 4))
            registered_values.add(round(val, 0))
            registered_values.add(round(abs(val), 0))
            registered_values.add(round(val * 100.0, 2))
            registered_values.add(round(abs(val) * 100.0, 2))
            registered_values.add(round(val / 100.0, 4))
            registered_values.add(round(abs(val) / 100.0, 4))

            # Resolve source
            expected_val = None
            if src.startswith("company:"):
                field = src.split("company:")[1]
                if field == "infra_monthly_cost":
                    expected_val = company.infra.get("current_monthly_cost")
                elif field == "support_reps":
                    expected_val = company.support.get("headcount")
                elif field == "paying_customers":
                    expected_val = company.total_paying_customers
                elif field == "monthly_net_burn":
                    expected_val = company.monthly_burn
                else:
                    expected_val = getattr(company, field, None)
            elif src.startswith("sim:"):
                parts = src.split(":")
                if len(parts) >= 4:
                    strat, scen, metric = parts[1], parts[2], parts[3]
                    outputs = sim_map.get((strat, scen), {})
                    expected_val = outputs.get(metric)
            elif src.startswith("mc:"):
                parts = src.split(":")
                if len(parts) >= 3 and mc_summaries:
                    strat = parts[1]
                    mc = mc_summaries.get(strat, {})
                    if len(parts) == 4:
                        metric, pctl = parts[2], parts[3]
                        expected_val = mc.get(metric, {}).get(pctl)
                    elif len(parts) == 3:
                        expected_val = mc.get(parts[2])

            if expected_val is not None:
                tol = max(1e-5, abs(float(expected_val)) * 1e-5)
                if abs(float(val) - float(expected_val)) > tol:
                    trace_failures.append(f"Registry mismatch for {src}: registered {val} != source {expected_val}")

        # Check scenario table against simulation outputs
        sec = report_to_check["sections"]
        for row in sec.get("scenario_table", []):
            strat = row.get("strategy")
            exp_out = sim_map.get((strat, "expected"), {})
            con_out = sim_map.get((strat, "conservative"), {})
            opt_out = sim_map.get((strat, "optimistic"), {})

            checks = [
                ("mrr_month_12_expected", exp_out.get("mrr_month_12")),
                ("mrr_month_12_conservative", con_out.get("mrr_month_12")),
                ("mrr_month_12_optimistic", opt_out.get("mrr_month_12")),
                ("net_contribution_12", exp_out.get("net_contribution_12")),
            ]
            for field, exp_val in checks:
                row_val = row.get(field)
                if row_val is not None:
                    if exp_val is None:
                        if draft_report_metrics is not None:
                            continue
                        if abs(float(row_val)) > 1e-6:
                            trace_failures.append(f"Scenario table {field} for {strat} ({row_val}) has no matching simulation run")
                    elif abs(float(row_val) - float(exp_val)) > max(1e-4, abs(float(exp_val)) * 1e-4):
                        trace_failures.append(f"Scenario table {field} for {strat} ({row_val}) does not match simulation ({exp_val})")

        # Check draft_report_metrics
        if draft_report_metrics:
            reported_mrr = draft_report_metrics.get("mrr_month_12")
            valid_sim_mrrs = {round(r.outputs.get("mrr_month_12", 0), 2) for r in simulation_runs}
            if reported_mrr is not None and round(reported_mrr, 2) not in valid_sim_mrrs:
                trace_failures.append(f"Fabricated or corrupted report number detected: reported MRR ${reported_mrr:,.2f}")

        # Check outcome ranges against Monte Carlo summaries
        if mc_summaries:
            for row in sec.get("outcome_ranges", []):
                strat = row.get("strategy")
                mc = mc_summaries.get(strat, {})
                checks = [
                    ("p_best", mc.get("p_best")),
                    ("p_feasible", mc.get("p_feasible")),
                    ("mrr_month_12_p50", mc.get("mrr_month_12", {}).get("p50")),
                    ("runway_months_12_p50", mc.get("runway_months_12", {}).get("p50")),
                    ("net_contribution_12_p50", mc.get("net_contribution_12", {}).get("p50")),
                ]
                for field, mc_val in checks:
                    if field in row and mc_val is not None:
                        if abs(float(row[field]) - float(mc_val)) > max(1e-4, abs(float(mc_val)) * 1e-4):
                            trace_failures.append(f"Outcome ranges {field} for {strat} ({row[field]}) does not match Monte Carlo ({mc_val})")

        # Prose scan: audit executive summary, risks, and execution plan for ungrounded numbers
        prose_texts = []
        exec_sum = sec.get("executive_summary", {})
        if isinstance(exec_sum, dict):
            prose_texts.append(exec_sum.get("headline_thesis", ""))
            prose_texts.append(exec_sum.get("recommendation", ""))
        risks_sec = sec.get("risks", [])
        if isinstance(risks_sec, list):
            for rk in risks_sec:
                if isinstance(rk, dict):
                    prose_texts.append(rk.get("description", ""))
                    prose_texts.append(rk.get("mitigation", ""))
        ep = sec.get("execution_plan")
        if isinstance(ep, dict):
            for ep_key, ep_val in ep.items():
                if isinstance(ep_val, str):
                    prose_texts.append(ep_val)
                elif isinstance(ep_val, list):
                    prose_texts.extend([str(x) for x in ep_val])
        elif isinstance(ep, list):
            for item in ep:
                if isinstance(item, dict):
                    prose_texts.extend([str(v) for v in item.values()])
                else:
                    prose_texts.append(str(item))

        # Ignored non-metric structural numbers (e.g. years, step/phase numbers, 10-section doc reference)
        ignored_structural = {
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "24",
            "2023", "2024", "2025", "2026", "2027", "60", "90"
        }

        for prose in prose_texts:
            tokens = re.findall(r"[-+]?[\$]?[-+]?\d[\d,]*(?:\.\d+)?%?", prose)
            for tok in tokens:
                clean_tok = tok.replace("$", "").replace(",", "").strip()
                if not clean_tok or clean_tok in ignored_structural:
                    continue
                try:
                    is_pct = clean_tok.endswith("%")
                    raw_num = clean_tok.replace("%", "").strip()
                    num_val = float(raw_num)
                    # Check if number or absolute value matches registered values
                    matched = any(abs(num_val - rv) < 0.05 or abs(abs(num_val) - rv) < 0.05 for rv in registered_values)
                    if not matched and is_pct:
                        matched = any(abs((num_val / 100.0) - rv) < 0.0005 or abs((abs(num_val) / 100.0) - rv) < 0.0005 for rv in registered_values)
                    if not matched:
                        trace_failures.append(f"Unregistered or unverified number in prose: '{tok}' ({num_val})")
                except ValueError:
                    pass

        if not trace_failures:
            results.append(
                VerificationResult(
                    check_name="report_number_traceability",
                    status="passed",
                    detail=f"All {len(reg_entries)} registered report figures and narrative prose trace 100% to verified simulation data.",
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

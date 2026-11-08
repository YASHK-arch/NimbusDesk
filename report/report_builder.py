"""Consolidated decision report builder generating structured JSON and Markdown deliverables.

Rules:
- R2: Numbers are inserted strictly from deterministic simulator outputs or company baseline facts.
- R6: Honest outputs with synthetic data disclosure and simulation disclaimer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from agents.llm import get_llm_badge
from report.decision_logic import compute_confidence, extract_min_runway_constraint, rank_strategies
from simulation.reconcile import reconcile_assumptions
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C
from simulation.sensitivity import compute_tornado_sensitivity, find_flip_point
from state.company import load_company_snapshot
from state.schemas import CompanySnapshot
from state.shared_state import WorkflowState


def build_consolidated_report(
    state: WorkflowState,
    company: Optional[CompanySnapshot] = None,
) -> Dict[str, Any]:
    """Assemble the 10-section decision report dynamically from workflow state and simulation runs."""
    if company is None:
        company = load_company_snapshot()

    # 1. Evaluate minimum runway constraint and rank strategies
    min_runway = extract_min_runway_constraint(
        constraints=state.decision.constraints if state.decision else None,
        assumptions=state.assumptions,
        default_min_runway=10.0,
    )
    ranked = rank_strategies(state.simulation_runs, min_runway=min_runway)

    # Detect degraded agents and unresolved conflicts for honest confidence scoring
    degraded_agents = []
    for f in state.findings.values():
        if getattr(f, "degraded", False) or "degraded" in f.claim.lower():
            if getattr(f, "degraded_reason", None) and "for failed " in f.degraded_reason:
                degraded_agents.append(f.degraded_reason.split("for failed ")[-1].strip())
            else:
                degraded_agents.append(f.agent)

    degraded_agent_banner = None
    if degraded_agents:
        degraded_agent_banner = (
            f"WARNING: Analysis from {', '.join(degraded_agents)} failed; "
            "conservative fallback assumptions were used. Recommendation confidence is capped at Low."
        )
    unresolved_conflicts = [c for c in state.conflicts if not c.resolved]

    mc_summaries = getattr(state, "mc_summaries", None)
    confidence_data = compute_confidence(
        ranked=ranked,
        mc_summaries=mc_summaries,
        assumptions=state.assumptions,
        degraded_agents=degraded_agents,
        unresolved_conflicts=unresolved_conflicts,
    )
    confidence_level = confidence_data["level"]

    # 2. Company Baseline Snapshot
    company_position = {
        "company_name": company.name,
        "tagline": company.tagline,
        "mrr": company.mrr,
        "arr": company.arr,
        "runway_months": company.runway_months,
        "cash_balance": company.cash_balance,
        "paying_customers": company.total_paying_customers,
        "monthly_net_burn": company.monthly_burn,
        "infra_monthly_cost": company.infra["current_monthly_cost"],
        "support_reps": company.support["headcount"],
        "is_synthetic": True,
    }

    # 3. Strategy Comparison & Scenarios Table
    is_price_change = state.decision and state.decision.type == "price_change"
    if is_price_change:
        from simulation.price_model import PRICE_STRAT_A, PRICE_STRAT_B, PRICE_STRAT_C
        target_strategies = [PRICE_STRAT_A, PRICE_STRAT_B, PRICE_STRAT_C]
    else:
        target_strategies = [STRATEGY_A, STRATEGY_B, STRATEGY_C]

    strategy_runs: Dict[str, Dict[str, Any]] = {}
    for r in state.simulation_runs:
        strat = r.strategy
        scen = r.scenario
        strategy_runs.setdefault(strat, {})[scen] = r.outputs

    scenario_table = []
    for strat in target_strategies:
        strat_scenarios = strategy_runs.get(strat, {})
        expected = strat_scenarios.get("expected", {})
        conservative = strat_scenarios.get("conservative", {})
        optimistic = strat_scenarios.get("optimistic", {})

        scenario_table.append({
            "strategy": strat,
            "mrr_month_12_expected": expected.get("mrr_month_12", 0.0),
            "mrr_month_12_conservative": conservative.get("mrr_month_12", 0.0),
            "mrr_month_12_optimistic": optimistic.get("mrr_month_12", 0.0),
            "runway_months_12_expected": expected.get("runway_months_12", 0.0),
            "gross_margin_12_expected": expected.get("gross_margin_month_12", 0.0),
            "support_headcount_12": expected.get("support_headcount_12", company.support["headcount"]),
            "net_contribution_12": expected.get("net_contribution_12", 0.0),
            "net_contribution_24": expected.get("net_contribution_24", 0.0),
        })

    # 4. Conflict Resolution Summary
    conflict_panel = [
        {
            "id": c.id,
            "type": c.type,
            "agents": c.agents,
            "disputed_item": c.disputed_item,
            "resolved": c.resolved,
            "resolution": c.resolution,
            "simulation_ids": c.simulation_ids,
        }
        for c in state.conflicts
    ]

    # Determine primary strategy and competitor for flip point
    top_strat_candidate = ranked[0].strategy if ranked else STRATEGY_B
    competitor_candidate = STRATEGY_C if top_strat_candidate != STRATEGY_C else STRATEGY_B

    # 5. Sensitivity Tornado & Flip-Points
    reconciled = getattr(state, "reconciled", None) or reconcile_assumptions(state.assumptions, state.conflicts)
    tornado_data = compute_tornado_sensitivity(
        top_strat_candidate,
        reconciled=reconciled,
        company=company,
    )
    flip_point_data = find_flip_point(
        primary_strategy=top_strat_candidate,
        competing_strategy=competitor_candidate,
        company=company,
    )

    # Determine dynamic recommendation and headline thesis
    flip_display = flip_point_data.get("threshold_display", "the modeled threshold")
    if is_price_change and ranked and ranked[0].feasible:
        top_strat = ranked[0]
        primary_strategy = top_strat.strategy
        recommendation = f"Adopt {primary_strategy} based on Net Retention and Expansion Profile"
        headline_thesis = (
            f"Adopting {primary_strategy} projects Month 12 MRR of ${top_strat.mrr_month_12:,.0f} "
            f"(${top_strat.mrr_month_12 * 12:,.0f} ARR) with {top_strat.runway_months_12:.1f} months runway and "
            f"${top_strat.net_contribution_12:,.0f} net contribution, maintaining strong retention and gross margins."
        )
    elif ranked and ranked[0].feasible:
        top_strat = ranked[0]
        primary_strategy = top_strat.strategy
        recommendation = f"Proceed with {primary_strategy} under Stated Guardrails"
        if flip_point_data.get("exists", True) and flip_point_data.get("flip_value") is not None:
            flip_qualifier = f"The recommendation holds as long as conversion remains above {flip_display}."
        else:
            flip_qualifier = "The recommendation is robust across the entire tested parameter range (no flip point detected)."
        headline_thesis = (
            f"Launching {primary_strategy} delivers ${top_strat.mrr_month_12:,.0f} MRR with "
            f"{top_strat.runway_months_12:.1f} months runway and ${top_strat.net_contribution_12:,.0f} "
            f"net contribution at Month 12, satisfying the {min_runway:.1f}-month runway constraint. "
            f"{flip_qualifier}"
        )
    elif ranked:
        least_bad = ranked[0]
        primary_strategy = least_bad.strategy
        recommendation = f"Do not proceed with any free-plan strategy under current constraints; {least_bad.strategy} is least detrimental but violates the {min_runway:.1f}-month runway floor"
        headline_thesis = (
            f"Under current capital constraints (minimum runway >= {min_runway:.1f} months), "
            f"all evaluated free-plan strategies result in unacceptable runway depletion. "
            f"The least-negative strategy is {least_bad.strategy} with projected runway of "
            f"{least_bad.runway_months_12:.1f} months and net contribution of ${least_bad.net_contribution_12:,.0f}."
        )
    else:
        primary_strategy = STRATEGY_C
        recommendation = "Do not proceed: insufficient simulation data"
        headline_thesis = "Unable to verify financial feasibility due to missing simulation results."

    # 6. Reconciled Assumption Ledger (De-duplicated with contributing agents)
    ledger = [
        {
            "name": p.name,
            "low": p.low,
            "base": p.base,
            "high": p.high,
            "unit": p.unit,
            "provenance": p.provenance,
            "source_ref": p.source_ref,
            "is_simulated": p.is_simulated,
            "contested": p.contested,
            "contributing_agents": p.contributing_agents,
            "proposed_by": ", ".join(p.contributing_agents),
            "challenged_by_skeptic": any(
                a.challenged_by_skeptic for a in state.assumptions if a.name == p.name
            ),
        }
        for p in reconciled.parameters
    ]

    context_ledger = [
        {
            "name": p.name,
            "low": p.low,
            "base": p.base,
            "high": p.high,
            "unit": p.unit,
            "provenance": p.provenance,
            "contributing_agents": p.contributing_agents,
        }
        for p in reconciled.context_params
    ]

    # 7. Risks and Uncertainties (Templated from computed metrics)
    top_runway_disp = f"{ranked[0].runway_months_12:.1f}" if ranked else f"{company.runway_months:.1f}"
    risks = [
        {
            "category": "Runway Compression Risk",
            "description": (
                f"If conversion falls below {flip_display}, cash burn accelerates and "
                f"erodes projected runway from {top_runway_disp} months toward the {min_runway:.1f}-month floor."
            ),
            "mitigation": f"Establish strict monthly cohort milestones and abort if 60-day conversion remains below {flip_display}.",
        },
        {
            "category": "Starter Plan Cannibalization",
            "description": "Risk that existing paying customers downgrade to the unmetered free tier.",
            "mitigation": f"Enforce usage caps and limit support SLAs so paid tiers preserve clear enterprise value.",
        },
        {
            "category": "Support Saturation",
            "description": f"Customer support team ({company.support['headcount']} reps) risks queue saturation if unmetered free users submit tickets.",
            "mitigation": "Enforce community-only deflection and automated triage for non-paying users.",
        },
    ]

    # 8. Verification Summary
    verification_summary = [
        {
            "check_name": r.check_name,
            "status": r.status,
            "detail": r.detail,
        }
        for r in state.verification_results
    ]

    # 9. Suggested Execution Plan & Key Metrics to Monitor
    execution_plan = {
        "phase_1_rollout": f"Private beta rollout under {primary_strategy} with cohort tracking.",
        "phase_2_evaluation": "Audit conversion velocity and AWS infrastructure connection pool utilization across active cohorts.",
        "phase_3_decision_gate": f"Expand public rollout only if measured conversion exceeds {flip_display}; otherwise trigger rollback.",
        "metrics_to_monitor": [
            f"Free-to-Paid Conversion Rate (Threshold: >= {flip_display})",
            f"Runway Floor Maintenance (Threshold: >= {min_runway:.1f} months)",
            "Marginal Infrastructure Connection Headroom",
            "Monthly Starter Plan Net Downgrades",
        ],
    }

    # 10. Run Log & Telemetry
    run_log = [
        {
            "task_id": tid,
            "agent": meta.get("agent"),
            "duration_sec": meta.get("duration_sec"),
            "start_iso": meta.get("start_iso"),
            "finish_iso": meta.get("finish_iso"),
        }
        for tid, meta in state.execution_timeline.items()
    ]

    # 11. Outcome Ranges (Monte Carlo Distributions)
    outcome_ranges: List[Dict[str, Any]] = []
    if mc_summaries:
        for strat in target_strategies:
            if strat in mc_summaries:
                mc = mc_summaries[strat]
                mrr_dist = mc.get("mrr_month_12", {})
                runway_dist = mc.get("runway_months_12", {})
                net_dist = mc.get("net_contribution_12", {})
                outcome_ranges.append({
                    "strategy": strat,
                    "n_iterations": mc.get("n_iterations", 250),
                    "seed": mc.get("seed", 42),
                    "p_best": mc.get("p_best", 0.0),
                    "p_feasible": mc.get("p_feasible", 0.0),
                    "mrr_month_12": mrr_dist,
                    "mrr_month_12_p10": mrr_dist.get("p10", 0.0),
                    "mrr_month_12_p50": mrr_dist.get("p50", 0.0),
                    "mrr_month_12_p90": mrr_dist.get("p90", 0.0),
                    "runway_months_12": runway_dist,
                    "runway_months_12_p10": runway_dist.get("p10", 0.0),
                    "runway_months_12_p50": runway_dist.get("p50", 0.0),
                    "runway_months_12_p90": runway_dist.get("p90", 0.0),
                    "net_contribution_12": net_dist,
                    "net_contribution_12_p10": net_dist.get("p10", 0.0),
                    "net_contribution_12_p50": net_dist.get("p50", 0.0),
                    "net_contribution_12_p90": net_dist.get("p90", 0.0),
                    "histograms": mc.get("histograms", {}),
                })

    llm_badge = get_llm_badge()
    report = {
        "decision_id": state.decision.id,
        "question": state.decision.question,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommendation": recommendation,
        "confidence": confidence_level,
        "confidence_score": confidence_data["score"],
        "confidence_reasons": confidence_data["reasons"],
        "llm_mode": llm_badge,
        "disclaimer": (
            "SIMULATION DISCLAIMER: All outputs in this report are generated by deterministic multi-agent simulations "
            "based on explicitly stated parameter ranges. They do not constitute guaranteed financial outcomes. "
            "All company metrics originate from the synthetic NimbusDesk dataset."
        ),
        "synthetic_badge": True,
        "degraded_agent_banner": degraded_agent_banner,
        "sections": {
            "executive_summary": {
                "recommendation": recommendation,
                "confidence": confidence_level,
                "confidence_score": confidence_data["score"],
                "confidence_reasons": confidence_data["reasons"],
                "primary_strategy": primary_strategy,
                "headline_thesis": headline_thesis,
                "degraded_agent_banner": degraded_agent_banner,
                "llm_mode": llm_badge,
            },
            "company_position": company_position,
            "scenario_table": scenario_table,
            "outcome_ranges": outcome_ranges,
            "conflicts": conflict_panel,
            "discussion_messages": [m.model_dump() for m in state.messages],
            "sensitivity_tornado": tornado_data,
            "flip_point": flip_point_data,
            "assumption_ledger": ledger,
            "context_assumptions": context_ledger,
            "risks": risks,
            "verification_summary": verification_summary,
            "execution_plan": execution_plan,
            "run_log": run_log,
        },
    }

    return report


def render_report_markdown(report: Dict[str, Any], state: Optional[WorkflowState] = None) -> str:
    """Render the structured report dictionary into an executive GitHub Flavored Markdown document."""
    sec = report["sections"]
    exec_sum = sec["executive_summary"]
    comp = sec["company_position"]
    flip = sec["flip_point"]

    # Determine status dynamically from verification results and workflow state
    verif_items = sec.get("verification_summary", [])
    has_failed_check = any(v.get("status") == "failed" for v in verif_items)
    is_degraded = any("degraded" in r.lower() for r in exec_sum.get("confidence_reasons", []))

    if has_failed_check:
        status_label = "Verification Failed"
    elif is_degraded:
        status_label = "Degraded Mode"
    elif verif_items and all(v.get("status") == "passed" for v in verif_items):
        status_label = "Verified"
    elif state and state.status == "completed":
        status_label = "Verified"
    else:
        status_label = "Verified" if not has_failed_check else "Verification Failed"

    md = [
        f"# VentureTwin Decision Stress-Test Report: {report['question']}",
        f"**Decision ID:** `{report['decision_id']}` | **Status:** `{status_label}` | **Badge:** `[SYNTHETIC DATA: NimbusDesk]` | **Engine:** `{report.get('llm_mode', 'LLM Mode: Mock')}`",
        f"**Generated:** {report['generated_at']}",
        "",
    ]
    if report.get("degraded_agent_banner"):
        md.extend([
            "> [!WARNING]",
            f"> **DEGRADED AGENT EXECUTION:** {report['degraded_agent_banner']}",
            "",
        ])
    md.extend([
        "> [!IMPORTANT]",
        f"> **Recommendation:** {exec_sum['recommendation']}  ",
        f"> **Confidence Level:** {exec_sum['confidence']}  ",
        f"> **Core Finding:** {exec_sum['headline_thesis']}",
        "",
        "---",
        "",
        "## 1. Current Company Position (NimbusDesk Baseline)",
        f"- **Current MRR / ARR:** ${comp['mrr']:,.2f} / ${comp['arr']:,.2f}",
        f"- **Paying Customers:** {comp['paying_customers']:,}",
        f"- **Cash Balance & Net Burn:** ${comp['cash_balance']:,.2f} (${comp['monthly_net_burn']:,.2f}/mo net burn)",
        f"- **Runway:** **{comp['runway_months']:.1f} months** (Board Mandate: maintain >= 10.0 months)",
        f"- **Infrastructure Cloud Cost:** ${comp['infra_monthly_cost']:,.2f}/mo",
        f"- **Customer Support Team:** {comp['support_reps']} full-time representatives",
        "",
        "---",
        "",
        "## 2. Strategy Scenario Comparison (12-Month Forecast)",
        "| Strategy | MRR (Conservative) | MRR (Expected) | MRR (Optimistic) | Runway (Mo) | Gross Margin | Net Contribution (12mo) |",
        "|---|---|---|---|---|---|---|",
    ])

    for row in sec["scenario_table"]:
        md.append(
            f"| {row['strategy']} | "
            f"${row['mrr_month_12_conservative']:,.0f} | "
            f"${row['mrr_month_12_expected']:,.0f} | "
            f"${row['mrr_month_12_optimistic']:,.0f} | "
            f"{row['runway_months_12_expected']:.1f} mo | "
            f"{row['gross_margin_12_expected']*100:.1f}% | "
            f"${row['net_contribution_12']:,.0f} |"
        )

    if sec.get("outcome_ranges"):
        md.extend([
            "",
            "---",
            "",
            "## 3. Outcome Ranges (Monte Carlo Distributions)",
            "*Probabilistic simulation across 250 iterations with stored seed and triangular sampling over reconciled bounds.*",
            "",
            "| Strategy | Win Prob (p_best) | Feasibility (p_feasible) | MRR (p10 / p50 / p90) | Net Contribution 12 (p10 / p50 / p90) | Runway 12 (p10 / p50 / p90) |",
            "|---|---|---|---|---|---|",
        ])
        for mc in sec["outcome_ranges"]:
            mrr_str = f"${mc['mrr_month_12_p10']:,.0f} / ${mc['mrr_month_12_p50']:,.0f} / ${mc['mrr_month_12_p90']:,.0f}"
            net_str = f"${mc['net_contribution_12_p10']:,.0f} / ${mc['net_contribution_12_p50']:,.0f} / ${mc['net_contribution_12_p90']:,.0f}"
            runway_str = f"{mc['runway_months_12_p10']:.1f} / {mc['runway_months_12_p50']:.1f} / {mc['runway_months_12_p90']:.1f} mo"
            md.append(
                f"| {mc['strategy']} | {mc['p_best']*100:.1f}% | {mc['p_feasible']*100:.1f}% | {mrr_str} | {net_str} | {runway_str} |"
            )

    if sec.get("discussion_messages"):
        md.extend([
            "",
            "---",
            "",
            "## 3. Agent Discussion & Multi-Turn Deliberation",
        ])
        for msg in sec["discussion_messages"]:
            md.append(f"- **{msg['sender']}** `({msg['kind'].upper()} -> {msg['recipient']})`: {msg['content']}")

    md.extend([
        "",
        "---",
        "",
        "## 4. Disagreements & Simulation-Based Resolutions",
    ])
    if sec["conflicts"]:
        for c in sec["conflicts"]:
            status_tag = "RESOLVED" if c["resolved"] else "UNRESOLVED"
            md.append(f"### Conflict: {c['disputed_item']} `[{status_tag}]`")
            md.append(f"- **Contending Agents:** {', '.join(c['agents'])}")
            md.append(f"- **Resolution Evidence:** {c['resolution']}")
            if c["simulation_ids"]:
                md.append(f"- **Associated Simulation Runs:** {', '.join(c['simulation_ids'])}")
            md.append("")
    else:
        md.append("No active agent disagreements detected.\n")

    md.extend([
        "---",
        "",
        "## 4. Sensitivity Analysis (Tornado) & Flip-Point",
        f"**Decision Flip-Point Finding:** {flip['statement']}",
    ])
    if flip.get("exists") is False:
        md.append("> **Robust to Variation:** No decision flip point exists within the tested interval. The strategy maintains its relative position across tested parameter bounds.")
    md.extend([
        "",
        "| Rank | Parameter | Base | Low Swung Outcome | High Swung Outcome | Net Impact Swing |",
        "|---|---|---|---|---|---|",
    ])
    for idx, t in enumerate(sec["sensitivity_tornado"][:5], 1):
        md.append(
            f"| {idx} | `{t['assumption_name']}` | {t['base_param']} {t['unit']} | "
            f"${t['low_outcome']:,.0f} | ${t['high_outcome']:,.0f} | **${t['swing']:,.0f}** |"
        )

    md.extend([
        "",
        "---",
        "",
        "## 5. Assumption Ledger & Provenance",
        "### Simulated Parameters",
        "| Parameter | Base | Range (Low / High) | Unit | Source | Contributing Agents | Contested? |",
        "|---|---|---|---|---|---|---|",
    ])
    for a in sec["assumption_ledger"]:
        contested_badge = "`CONTESTED`" if a.get("contested") else "No"
        agents_str = ", ".join(a.get("contributing_agents", [])) or a.get("proposed_by", "N/A")
        md.append(
            f"| `{a['name']}` | {a['base']} | {a['low']} - {a['high']} | {a['unit']} | "
            f"`{a['provenance']}` ({a['source_ref'] or 'N/A'}) | {agents_str} | {contested_badge} |"
        )

    if sec.get("context_assumptions"):
        md.extend([
            "",
            "### Operational Context",
            "| Parameter | Base | Range (Low / High) | Unit | Source | Contributing Agents |",
            "|---|---|---|---|---|---|",
        ])
        for ca in sec["context_assumptions"]:
            agents_str = ", ".join(ca.get("contributing_agents", [])) or "N/A"
            md.append(
                f"| `{ca['name']}` | {ca['base']} | {ca['low']} - {ca['high']} | {ca['unit']} | "
                f"`{ca['provenance']}` | {agents_str} |"
            )

    md.extend([
        "",
        "---",
        "",
        "## 6. Verification Summary",
    ])
    for v in sec["verification_summary"]:
        icon = "[PASS]" if v["status"] == "passed" else "[FAIL]"
        md.append(f"- **{v['check_name']}**: `{icon}` — {v['detail']}")

    md.extend([
        "",
        "---",
        "",
        "## 7. Suggested Execution Plan & Guardrail Metrics",
        f"- **Phase 1 (Rollout):** {sec['execution_plan']['phase_1_rollout']}",
        f"- **Phase 2 (Evaluation):** {sec['execution_plan']['phase_2_evaluation']}",
        f"- **Phase 3 (Decision Gate):** {sec['execution_plan']['phase_3_decision_gate']}",
        "",
        "**Key Metrics to Monitor:**",
    ])
    for m in sec["execution_plan"]["metrics_to_monitor"]:
        md.append(f"- {m}")

    md.extend([
        "",
        "---",
        f"> {report['disclaimer']}",
    ])

    return "\n".join(md)

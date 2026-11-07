# FIX PROMPT: Make VentureTwin Data-Driven and Honest

> Paste this entire document as your message to the coding agent working in the existing VentureTwin repository (`Citadel-engine`). It is self-contained.

---

## 0. YOUR ROLE AND WORKING AGREEMENT

You are a senior Python engineer fixing an existing hackathon project. The repo already has a working skeleton (async DAG supervisor, agents, SQLite checkpoints, event bus, simulator, conflict detector, verifier, report builder, FastAPI API, React UI, per-step tests). A code review found that several of its headline claims are **not actually true in the code**: key outputs are hardcoded, scenarios are identical, verification is vacuous, and mock data cites sources that do not exist. Your job is to fix these in the order given below.

**How to work (follow strictly):**

1. **Start by reading the repo** (`orchestrator/`, `agents/`, `conflict/`, `simulation/`, `verification/`, `report/`, `api/`, `state/`, `tests/`, `README.md`, `docs/`). Then reply with a **short plan** listing the files you will change per fix. Ask at most one question, and only if you are blocked.
2. **Fix one item at a time, in order (Fix 1 to Fix 11, then Minor).** For each fix: (a) write or update a **failing test first** that proves the problem, (b) implement the fix, (c) run the whole test suite, (d) show evidence (test output, a before/after number), (e) append a short entry to `docs/PROGRESS.md`, then move on.
3. **Existing tests that assert hardcoded behaviour must be updated**, not deleted. If you change a test's expectation, say why.
4. **Do not break the demo flow:** submit "Should we launch a free plan?", watch the agent DAG, see conflicts, inject a failure, view the report, approve, open Calibration. After every fix this must still work end to end.
5. **Keep it simple.** No new infrastructure. No new frameworks. Prefer small, well-tested functions.
6. **Never fake it.** If something cannot be implemented in time, remove the claim from the README and UI rather than leaving a fake behind. Label anything not implemented as `planned`.
7. **UI changes only where a fix needs to show new data** (mock-mode banner, degraded-agent banner, unresolved conflicts, "no flip point", outcome ranges).

**Hard rules that must be true after your changes (the project's own rules, now enforced):**

- **R1.** Agents are separate nodes with distinct prompts, tools, and structured outputs.
- **R2.** No final number comes from an LLM or from a hardcoded string. Every number in the report comes from a `SimulationRun` output, a Monte Carlo summary, or the company snapshot.
- **R3.** Conflicts are resolved by simulation results computed at run time. The resolution text is generated from those results, never pre-written.
- **R4.** Every number in the report traces to a simulator run or input data, and this is **checked in code**, not just claimed.
- **R5.** Human approval only; no external actions.
- **R6.** Outputs are honest: the report and UI show whether the LLM ran in mock or real mode, whether any agent ran degraded, and which conflicts remain unresolved.
- **R7.** No invented sources, benchmarks, or company facts.

---

## 1. THE ONE-MINUTE TEST (your definition of "fixed")

After all fixes, these must all pass (turn them into automated tests in `tests/test_acceptance.py`):

1. **Data sensitivity:** change `cash_balance` (or churn, or infra cost) in a copy of `synthetic_company.json`; the recommendation, feasibility, flip-point, or confidence **changes accordingly**. With a tiny cash balance, the system must not recommend a strategy that violates the runway constraint.
2. **Scenario ordering:** for every strategy, `net_contribution_12` satisfies conservative <= expected <= optimistic, and the three are **not equal**.
3. **Order independence:** shuffling the order in which agent tasks finish yields **identical** report numbers.
4. **Real verification:** corrupting one number in the draft report makes verification **fail**, and the supervisor loops back (bounded) instead of publishing.
5. **Honest failure:** a persistent agent failure produces a report that **visibly flags the degraded agent** and caps confidence; a failed core task produces workflow status `failed`, not `completed`.
6. **No silent mock:** with `LLM_MODE=real` and no API key, startup/`/api/health` errors clearly. The report and UI always show the active LLM mode.
7. **No fabricated sources:** no assumption's `source_ref` names a benchmark/report that is not in the repo; every `verified_data` assumption's value equals the value in the company snapshot.

---

## FIX 1. The recommendation is hardcoded (CRITICAL)

**Problem.** `report/report_builder.py` hardcodes `recommendation = "Proceed with Strategy B..."`, `confidence = "Medium"`, the headline thesis ("3,200 users/mo", "runway above 10.8 months"), execution-plan thresholds ("1.8%", "1.85%", "8%"), and the Markdown renderer always prints "Status: Verified".

**Required changes.**

1. Create `report/decision_logic.py` with pure, tested functions:
   - `rank_strategies(sim_runs, constraints) -> list[RankedStrategy]`: use the `expected` scenario; a strategy is **feasible** only if `runway_months_12 >= min_runway` (read `min_runway` from the `Decision.constraints` / CFO's `min_acceptable_runway_months` base assumption; default 10). Rank feasible strategies by `net_contribution_12` (tie-break by `runway_months_12`). If no strategy is feasible, the recommendation is "Do not proceed with any free-plan strategy under the current constraints" and names the least-bad option.
   - `compute_confidence(ranked, mc_summaries, assumptions) -> {"level": "Low|Medium|High", "score": float, "reasons": [...]}`: base it on (a) the margin between the first and second ranked strategies, (b) the Monte Carlo probability that the top strategy stays top (Fix 11), (c) the average assumption confidence after Skeptic downgrades, (d) a penalty if any agent ran degraded (Fix 8) or any conflict is unresolved (Fix 3). Return the reasons so the report can show them.
2. Rewrite the executive summary, risks, and execution plan to be **generated from computed values** (templated f-strings using simulator outputs, the flip point, and the company snapshot). Remove every hardcoded number. Phase gates and monitored-metric thresholds come from the flip point and the constraints (for example "expand if measured conversion >= {flip_threshold}").
3. The Markdown header status comes from `verification_results` and the workflow status (`Verified`, `Verification failed`, `Degraded`), not a literal.

**Done when.** Test: with default data the report names a strategy derived from `rank_strategies`; with `cash_balance` set very low, the recommendation changes to "do not proceed" or a different strategy; grep finds no numeric literals in recommendation/thesis/execution-plan text in `report_builder.py`.

---

## FIX 2. Conservative / expected / optimistic scenarios are identical (CRITICAL)

**Problem.** `Supervisor._handle_supervisor_task` runs `simulate(strat, scen, base_params)` for three scenario names using the **same** `base_params`; `simulate()` only changes behaviour for `scenario == "stress_test"`. So the 3x3 matrix has three equal rows per strategy. The stress tests are never run in the pipeline.

**Required changes.**

1. Create `simulation/params.py` with a single source of truth, `SIM_PARAMS`, listing every parameter the simulator uses:
   `free_to_paid_conversion`, `monthly_free_signups`, `free_user_marginal_infra_cost`, `starter_cannibalization_rate`, `free_user_monthly_tickets`. For each: `unit`, `favorable_direction` (`"higher"` or `"lower"`), and valid bounds. (Conversion and signups: higher is favorable. Infra cost, cannibalization, tickets: lower is favorable.)
2. Add `build_scenario_params(reconciled_params, scenario)`:
   - `conservative` -> each parameter at its **unfavorable** bound (`low` if favorable is higher, else `high`),
   - `expected` -> `base`,
   - `optimistic` -> each parameter at its **favorable** bound.
3. Add stress scenarios to `simulate()` and to the supervisor matrix: `stress_infra_doubles`, `stress_conversion_collapse`, and `stress_large_customer_churn` (remove a configurable share of Enterprise users in month 1). Keep the existing `stress_test` behaviour for backward compatibility only if tests depend on it.
4. The supervisor must run the matrix: 3 strategies x (conservative, expected, optimistic) + 3 stress scenarios for each strategy.
5. Add a validator on `Assumption`: `low <= base <= high`, otherwise reject.

**Done when.** Tests: for each strategy, conservative < expected < optimistic on `net_contribution_12` (strict for Strategy A and B; Strategy C has no free-plan levers, so assert `<=` and document why); all stress scenarios are present in `state.simulation_runs`; the report scenario table shows three distinct values per strategy.

---

## FIX 3. Conflict resolution is scripted (CRITICAL)

**Problem.** `conflict/resolver.py`:
- writes a fixed conclusion ("Resolution: Adopt Strategy B... runway remains above the 10.0mo safety floor") without checking the runway it just computed;
- uses fallback conversions (`0.015` / `0.045`) regardless of which agents conflict, so CTO vs Growth gets the CFO's number;
- every agent pair involving Growth's `"proceed"` generates a separate near-duplicate conflict;
- always marks `resolved = True`.
Also, the CFO/Growth disagreement exists only because the mock findings hardcode non-overlapping conversion ranges.

**Required changes.**

1. **Detector (`conflict/detector.py`).**
   - Define an ordinal scale: `reject < needs_more_info < proceed_with_limits < proceed`. Flag `contradictory_recommendation` only when the distance is >= 2 steps (for example `proceed` vs `reject`), or when the agents' recommendations differ in kind. A `proceed` vs `proceed_with_limits` difference is **not** a conflict (log it as an informational note).
   - Group conflicts by disputed parameter so each disputed parameter yields **one** `assumption_divergence` conflict listing all disagreeing agents, not one per pair.
2. **Resolver (`conflict/resolver.py`).** For an `assumption_divergence` on parameter `P` between agent X and agent Y:
   - Start from the **reconciled** baseline parameters (Fix 6) and change **only** `P` (X's base vs Y's base). Do not substitute any other defaults.
   - Run **all three strategies** for both sides. Use `rank_strategies` (Fix 1) to determine the recommended strategy under each side's value.
   - Compute deltas for `net_contribution_12`, `mrr_month_12`, and `runway_months_12`, and whether each side's top strategy satisfies the runway constraint.
   - Verdict: `decision_relevant` if the recommended strategy or feasibility differs between the two sides; otherwise `immaterial`.
   - Generate `resolution` text from these computed values only. Include the flip point computed with the reconciled parameters.
3. **One rebuttal round (bounded).** When a conflict is `decision_relevant`, the supervisor sends each involved agent the other agent's finding plus the simulation evidence, and lets the agent revise its assumption range once (a single extra LLM call per agent, validated as a `Finding`). If the ranges now overlap, mark the conflict `resolved` with `resolution_method = "converged_after_rebuttal"`. If they still do not overlap, keep `resolved = False` and `status = "unresolved_material"`, with the simulation evidence attached. **Never mark a conflict resolved unless it is actually settled or shown immaterial.**
4. Add to the `Conflict` schema: `status` (`resolved_immaterial | resolved_converged | unresolved_material`), `verdict`, and `resolution_method`.
5. The report's conflict panel must show unresolved conflicts prominently, and the confidence logic (Fix 1) must penalize them.

**Done when.** Tests: (a) changing the disputed parameter's values so ranges overlap removes the conflict; (b) a conflict whose two sides yield the same recommended strategy is marked `resolved_immaterial`; (c) a conflict where the recommendation differs stays `unresolved_material` after the rebuttal round when ranges still do not overlap; (d) no resolution string contains a number that is not present in the referenced `SimulationRun` outputs; (e) the number of conflicts for the default scenario is small and each is meaningful.

---

## FIX 4. Mock findings cite sources that do not exist (CRITICAL for credibility)

**Problem.** `agents/specialists.py` mock findings use `provenance="external_research"` with made-up sources ("OpenView 2024 SaaS Product Benchmarks", "ProductLed PLG Benchmark Report 2024", "SaaS Growth Index 2024", "Zendesk PLG Support Benchmark"), tag "NimbusDesk AWS CloudWatch Breakdown" and "NimbusDesk Board Mandate Q3" as `verified_data` although the company is synthetic, and the skeptic hardcodes a "B2B SaaS benchmark median (1.8%)". Several assumptions also use unit `"%"` for fractional values like `0.015`.

**Required changes.**

1. Mock provenance rules:
   - A value read from the company snapshot -> `verified_data`, with `source_ref` like `data/synthetic_company.json#infra.free_user_marginal_cost_per_month`, and the **value must be read from the snapshot**, not typed in.
   - Any other value in a mock finding -> `ai_assumption` with `source_ref = "mock: illustrative assumption"`.
   - Remove all invented report/benchmark names. If you want benchmark references, add `data/benchmarks.json` where each entry is explicitly marked `"illustrative": true, "sourced": false` unless you have verified a real source and can put its URL in the file; the code may only cite entries from that file.
2. Remove the hardcoded 1.8% benchmark and the "85th percentile" claims from the Skeptic mock and `skeptic_audit.py`; make the Skeptic compare against the values in `data/benchmarks.json` (or against other agents' ranges and the company's own funnel metrics).
3. Units: use `"ratio"` for fractions in 0..1 (conversion, cannibalization) and keep `"%"` only for values that are truly stated in percent. Define the expected unit for each `SIM_PARAMS` entry and validate it in the verifier. Update the UI/report formatting accordingly (display ratios as percentages).
4. `agents/tools.py::get_infra_headroom` hardcodes `"max_safe_free_users_without_sharding": 6000`. Move it into `synthetic_company.json` and read it from there.

**Done when.** Tests: no `source_ref` in any mock finding matches a forbidden-names list (the strings above); every `verified_data` assumption equals the corresponding snapshot value; the verifier rejects an assumption whose unit does not match `SIM_PARAMS`.

---

## FIX 5. Verification is vacuous; the Skeptic never runs where it matters (CRITICAL)

**Problem.**
- `verify_workflow` only runs the traceability check if `draft_report_metrics` is passed. The supervisor never passes it, and verification runs **before** the report exists.
- `required_sections_present` returns "passed" unconditionally.
- A failed verification only emits an event; the report is still built.
- `run_skeptic_audit` is never called, and the Skeptic agent runs **after** the simulation, so it cannot influence results.

**Required changes.**

1. **Replace string-matching dispatch with explicit task kinds.** Add `kind` to `Task` (`agent_analysis | conflict_detection | skeptic_review | simulation | report_draft | verification | report_finalize`). Dispatch in `_handle_supervisor_task` on `task.kind`, not on substrings of `task.id`. Update `decomposer.py` and tests.
2. **New DAG order for `free_plan`:** agent analyses (parallel) -> `conflict_detection` -> `skeptic_review` -> `simulation` (matrix + conflict resolution + Monte Carlo) -> `report_draft` -> `verification` -> `report_finalize`.
3. **Skeptic review (before simulation).** Run both: the Skeptic **agent** (reads all peer findings through `state`, returns a `Finding` with challenges) and the deterministic `run_skeptic_audit`. Outputs: downgraded confidence, `challenged_by_skeptic` flags, and **Skeptic-adjusted bounds** that feed the conservative scenario (Fix 2). Record each challenge in `state.skeptic_challenges` and show them in the report.
4. **Real verification checks (`verification/verifier.py`),** run on the **draft report**:
   - `report_number_traceability`: extract every numeric field from the draft report's structured sections (scenario table, tornado, flip point, outcome ranges, execution thresholds, company position) and verify each exists in some `SimulationRun.outputs`, a Monte Carlo summary, or the company snapshot (tolerance 0.01). Also scan LLM-written prose for digits and fail on any number not in the allowed set.
   - `required_sections_present`: check that all 10 section keys exist and are non-empty.
   - `unit_consistency`: compare against `SIM_PARAMS` units (Fix 4), not a broad allowlist.
   - `provenance_integrity`: every assumption has a valid tag and a `source_ref`; `verified_data` values match the snapshot.
   - `scenario_ordering`: conservative <= expected <= optimistic for each strategy.
   - `financial_ratio_tie_outs`: keep, but compute from the data used.
5. **Loop back on failure (bounded to 2 loops).** If verification fails, route to the responsible task (`report_draft` for report issues, `simulation` for scenario issues), re-run, and re-verify. If still failing, finalize the report with status `Verification failed`, the recommendation downgraded to "unverified", and the failed checks listed. Never present a failed report as "Verified".

**Done when.** Tests: (a) tamper with one number in the draft report -> verification fails -> loop executes -> after a rebuild passes; (b) tamper persistently (monkeypatch) -> final status `Verification failed`; (c) `run_skeptic_audit` is executed in a normal run and its challenges appear in the report; (d) the Skeptic's adjusted bounds change the conservative scenario output.

---

## FIX 6. Same-named assumptions collide; results depend on completion order (IMPORTANT)

**Problem.** `base_params = {asm.name: asm.base for asm in state.assumptions}` lets whichever agent finished last win. The tornado list contains duplicate entries and zero-swing rows for parameters the simulator ignores (`min_acceptable_runway_months`, `skeptic_adjusted_conversion`, `feature_gate_conversion_multiplier`, `degraded_fallback_margin_safety`, and so on).

**Required changes.**

1. Add `simulation/reconcile.py::reconcile_assumptions(assumptions, conflicts) -> ReconciledParams`:
   - Only parameters in `SIM_PARAMS` are used by the simulator. Others stay in the ledger but are marked `non_simulated`.
   - For a parameter proposed by several agents: if ranges overlap, merge deterministically with a confidence-weighted mean for `base`, and the union of `[low, high]` clipped to the overlap policy you document; if they do not overlap, mark it `contested` and use the **conflict resolution's** chosen value (Fix 3) or, if unresolved, the confidence-weighted midpoint with a visible `contested=True` flag.
   - Sort inputs by `(agent_name, assumption_name)` so results never depend on task completion order.
2. `compute_tornado_sensitivity` and `run_monte_carlo` accept the reconciled parameters (not the raw list) and only iterate over simulated parameters, de-duplicated.
3. The assumption ledger in the report shows each parameter once with its contributing agents and a `contested` flag, and lists non-simulated assumptions in a separate "context assumptions" group.

**Done when.** Tests: shuffle the order of findings/assumptions 20 times -> identical reconciled params and identical report numbers; tornado has no duplicate names and no zero-swing rows for non-simulated assumptions.

---

## FIX 7. The flip point can be invented (IMPORTANT)

**Problem.** `find_flip_point` uses its own hardcoded base assumptions (ignoring the workflow's), scans 110 steps, and if no crossing is found silently returns the midpoint (3.25%) as the "threshold".

**Required changes.**

1. `find_flip_point(primary, competitor, parameter, reconciled_params, company, bounds)`:
   - Evaluate the difference `primary - competitor` at both bounds. If the sign is the same at both ends, return `{"exists": false, "reason": "...", "statement": "No flip point within the tested range [lo, hi]: <primary> remains better/worse across the range."}`.
   - Otherwise find the crossing with **bisection** (tolerance 1e-4) and describe the direction correctly ("above" or "below").
2. **Delete the midpoint fallback.**
3. The report, risks, execution-plan gates, and UI must handle `exists = false` without crashing and without inventing a threshold.
4. Use the reconciled parameters from the workflow, not defaults.

**Done when.** Tests: changing infra cost or cash moves the threshold; a configuration with no crossing returns `exists = false`; no code path returns a threshold that was not computed.

---

## FIX 8. Failure recovery cannot really fail (IMPORTANT)

**Problem.** In `Supervisor._execute_single_task` the injected failure only applies to the first attempt, so the retry always succeeds; the degraded path is never exercised from the UI; there is no reassignment; failed tasks are added to `completed_ids` and the run still ends `completed`; the degraded fallback finding is treated like a normal finding (including for conflict detection).

**Required changes.**

1. Failure injection spec: `{"agent": str, "mode": "timeout|exception|bad_output", "persist": bool, "fail_attempts": int}`. `persist=true` fails every attempt for that agent. Update `POST /api/decisions/{id}/inject-failure`, the UI control (add a "persistent" toggle), and tests.
2. `RecoveryPolicy` sequence: retry with exponential backoff up to `max_retries` -> **reassign** to a backup analyst (a generic `BackupAnalyst` agent using the failed agent's tools and objective but a different prompt) -> **degraded fallback** only if both fail. Emit an event at each step (`recovery_started` with `action`, `recovery_done` with `recovered_via`).
3. Add `degraded: bool` and `degraded_reason` to `Finding`. Degraded findings are **excluded** from conflict detection and from assumption reconciliation, cap the overall confidence at `Low` (Fix 1), and the report and UI show a visible "Degraded: <agent>" banner.
4. Core supervisor tasks (`conflict_detection`, `simulation`, `verification`, `report_*`) that fail after retries set `state.status = "failed"`, emit `workflow_failed`, persist a checkpoint, and **do not** produce a "completed" report. A failed agent-analysis task is allowed to degrade; a failed core task is not.
5. Do not add a failed task to `completed_ids` as if it were done; track `failed_ids` separately and make downstream behaviour explicit.
6. Make the checkpoint resume path testable: after a core-task failure, `resume_if_checkpoint_exists=True` continues from the last good checkpoint.

**Done when.** Tests (parametrized): 3 modes x each of the 5 specialist agents x `persist` true/false -> run completes; when `persist=false` the retry recovers; when `persist=true` the backup agent or degraded path is used and the report flags it; a forced failure in the simulation task yields workflow status `failed` with a resumable checkpoint.

---

## FIX 9. The LLM layer can silently run in mock mode; agents do not really communicate (IMPORTANT)

**Problem.** `agents/llm.py` falls back to mock mode when no API key is set **even if `LLM_MOCK_MODE=false`**; model IDs (`gemini-1.5-flash`, `claude-3-5-haiku-20241022`) are hardcoded and likely outdated; the Gemini key is in the URL query string; retries have no backoff; nothing restricts a real LLM to the parameter names the simulator understands (unknown names are silently ignored); agents never see each other's findings or rebut them.

**Required changes.**

1. Replace `LLM_MOCK_MODE` with `LLM_MODE = mock | real | record | replay` (keep `LLM_MOCK_MODE` as a deprecated alias that maps to mock/real).
   - `real` with no usable key -> raise a clear `ConfigError` (no silent fallback). `/api/health` and every report include `llm_mode` and the model name; the UI shows a visible banner "MOCK MODE: agent outputs are scripted" when mock.
   - `record`: call the real provider and save each response to `tests/cassettes/<sha256(prompt+schema)>.json`. `replay`: serve from cassettes and fail if a cassette is missing. Document the workflow in the README.
2. Model IDs come from env (`GEMINI_MODEL`, `OPENAI_MODEL`, `ANTHROPIC_MODEL`) with documented defaults. **Check the provider's current docs for non-retired model IDs before choosing defaults; do not guess.**
3. Send the Gemini key in the `x-goog-api-key` header, not the URL. Add exponential backoff with jitter on 429/5xx and on JSON/validation failures (bounded).
4. **Parameter whitelist.** The agent prompt must list the allowed simulator parameter names, units, and bounds from `SIM_PARAMS`. After validation, any assumption whose name is not in `SIM_PARAMS` is kept as a `context assumption` and logged; any simulator-relevant assumption outside bounds is clamped and flagged. Report `ignored_assumptions` in the run log.
5. **Real communication.** Agents in the parallel analysis stage stay independent (so disagreement is genuine). The Skeptic receives all peer findings. The rebuttal round (Fix 3) passes peer findings plus simulation evidence to the two conflicting agents. Record the exchange as structured `Message` objects in `state.messages` and show them in the agent inspector.
6. **Run once in real mode.** Add a script `scripts/run_real_demo.py` that runs the free-plan flow with a real provider, records cassettes, and writes the report to `data/known_good_run.json`. The mock-mode findings must **not** be what judges see in the primary demo.

**Done when.** Tests: `LLM_MODE=real` without a key raises `ConfigError`; replay mode runs the full flow from cassettes with no network; a response with an unknown assumption name is not fed to the simulator and appears in `ignored_assumptions`; backoff is exercised via a mocked 429.

---

## FIX 10. The price-change path is not real (IMPORTANT)

**Problem.** The `price_change` DAG has `task_pricing_simulation`, which matches the `"simulation"` branch and runs the **free-plan** strategies; there is no conflict step; the report is free-plan text.

**Required changes (choose ONE, in this order of preference):**

- **Option A (preferred if time allows, after Fixes 1 to 9):** implement it properly.
  - `simulate_price_change(...)` with parameters `price_change_pct`, `price_elasticity`, `churn_response`, `new_customer_conversion_effect` added to `SIM_PARAMS` (scoped to this decision type).
  - Strategies: Raise by X%, Hold, Cut by X%.
  - DAG with the same task kinds as `free_plan` (analysis, conflict detection, skeptic, simulation, report draft, verification, finalize).
  - A decision-type-specific report template; the rest of the engine stays shared.
- **Option B:** remove `price_change` from the parser, DAG, UI chips, and README, and list it as "planned". Do this if you do not have time for Option A.

**Done when.** Either a price-change run produces its own strategies, scenarios, conflicts, and report with no free-plan text, or no part of the repo claims to support it.

---

## FIX 11. Monte Carlo is never used; seed handling is misleading (IMPORTANT)

**Problem.** `simulation/monte_carlo.py` exists and the README advertises Monte Carlo distributions, but nothing in the pipeline calls it. `simulate()` accepts a `seed` that it never uses.

**Required changes.**

1. In the `simulation` task, run `run_monte_carlo` for each strategy using the **reconciled** parameters (simulated parameters only), 250 to 500 iterations, a stored seed, triangular sampling. Handle degenerate ranges (`low == high`) and enforce `low <= base <= high`.
2. Store the results in `state.mc_summaries` and the report: p10/p50/p90 for `mrr_month_12`, `runway_months_12`, `net_contribution_12`, plus `p_feasible` (probability the strategy keeps runway >= the minimum) and `p_best` (probability each strategy is the top-ranked feasible one across samples).
3. Feed `p_best` into `compute_confidence` (Fix 1).
4. `simulate()` is deterministic: remove the unused `seed` parameter from it. Record the seed only on Monte Carlo summaries and any `SimulationRun` created inside Monte Carlo.
5. Add an "Outcome ranges" section to the report and a simple range chart in the UI.

**Done when.** Tests: Monte Carlo output is identical for the same seed and differs for another; `p_best` values sum to ~1 across strategies; the report contains outcome ranges; the verifier's traceability check includes Monte Carlo summaries.

---

## MINOR (do after the fixes above)

1. **Repo hygiene.** Move the context/feature docs into `docs/` only (delete the root duplicates and `Antigravity_Master_Prompt_VentureTwin.md`). Confirm `data/checkpoints.sqlite` and `ui/node_modules` are not committed (`git rm --cached` if they are).
2. **CORS.** Replace `allow_origins=["*"]` with an env-configurable list (default `http://localhost:5173,http://localhost:8000`).
3. **CI.** Add `.github/workflows/ci.yml` that installs dependencies and runs the tests in replay/mock mode, so the README badge reflects a real run. Replace the static "46 Passed" badge with the workflow badge.
4. **Naming.** Rename the repo to `venturetwin`, add a description and topics, and make the README title consistent.
5. **README honesty.** Update the milestone table so each claim matches the code after these fixes. Add sections: "Limitations", "Why a custom executor instead of LangGraph", "LLM modes (mock / real / record / replay)", and "What is synthetic".
6. **Demo hardening.** Update `docs/DEMO_SCRIPT.md` for the real-mode demo, including the persistent-failure toggle and an unresolved-conflict example.

---

## FINAL CHECKLIST (report back with evidence for each)

- [ ] Fix 1: recommendation, confidence, and thesis derived from computed values; low-cash data changes the outcome
- [ ] Fix 2: three distinct scenarios per strategy plus stress runs; ordering test passes
- [ ] Fix 3: resolver computes verdicts; unresolved conflicts stay visible; rebuttal round bounded to one
- [ ] Fix 4: no invented sources; `verified_data` values match the snapshot; units consistent
- [ ] Fix 5: task kinds; Skeptic before simulation; real checks on the draft report; loop-back works
- [ ] Fix 6: deterministic reconciliation; tornado de-duplicated and limited to simulated parameters
- [ ] Fix 7: bisection flip point; `exists=false` handled; no midpoint fallback
- [ ] Fix 8: persistent failures, backup agent, degraded flagging, core-task failure is `failed`
- [ ] Fix 9: explicit LLM modes, no silent mock, banner, whitelist, record/replay, one real-mode run recorded
- [ ] Fix 10: price change implemented or removed
- [ ] Fix 11: Monte Carlo wired in; outcome ranges and `p_best` in the report
- [ ] Minor items done; README matches reality
- [ ] All tests pass; `tests/test_acceptance.py` covers the One-Minute Test

**Begin by reading the repo and posting your short plan. Then start with Fix 1.**

# FIX PROMPT 2: Remove the Remaining Fakes in VentureTwin

> Paste this entire document as your message to the coding agent working in the VentureTwin repository (`Citadel-engine`). It is self-contained. It follows an earlier fix round (Fixes 1 to 11 are already merged) and covers what a second code review found.

---

## 0. YOUR ROLE AND WORKING AGREEMENT

You are a senior full-stack engineer fixing an existing hackathon project. The first fix round made the backend much more honest: ranked recommendations, distinct scenarios, simulation-based conflict resolution, a flip-point by bisection, Monte Carlo, LLM modes, CI. A second review found that several **new** features and some older paths still show scripted or fabricated output. The most serious is the new "Simulation Workspace" screen, which is mostly a front-end mock.

**How to work (follow strictly):**

1. **Read the repo first** (`ui/src/components/**`, `orchestrator/supervisor.py`, `conflict/`, `simulation/`, `verification/`, `report/`, `agents/`, `api/app.py`, `tests/`). Then reply with a **short plan** listing the files you will change per fix. Ask at most one question, only if blocked.
2. **Fix one item at a time, in the order below (Fix 1 to Fix 9).** For each: (a) write or update a **failing test first** that proves the problem, (b) implement, (c) run the whole backend test suite and the UI build, (d) show evidence (test output, a before/after), (e) append an entry to `docs/PROGRESS.md`, then continue.
3. **Update existing tests that assert fake behaviour.** Do not delete them; say why each expectation changed.
4. **Do not break the demo flow:** submit "Should we launch a free plan?", watch the DAG, see conflicts, inject a failure, view the report, approve, open Calibration.
5. **Never fake it.** If something cannot be made real in time, **remove it from the UI and README** or label it clearly as a non-model preview. Do not leave plausible-looking fake numbers on screen.
6. **If you lack an API key** for a step that needs one (Fix 5), implement everything, do **not** fabricate cassettes or recorded runs, and finish with a clear note: `RECORDING PENDING: run <command> locally with a key`.
7. You cannot assume tests pass: **run them** and paste the summary line.

**Hard rules (must be true after your changes):**

- **R1.** Agents are separate nodes with distinct prompts, tools, and structured outputs.
- **R2.** No final number comes from an LLM, a hardcoded string, or a front-end formula. Every number on any screen or report comes from a `SimulationRun`, a Monte Carlo summary, a deterministic calculation, or the company snapshot.
- **R3.** Conflicts are resolved by simulation results computed at run time; resolution text is generated from those results.
- **R4.** Every number in the report is traced to a source **and this is verified in code** (Fix 6).
- **R5.** Human approval only; no external actions.
- **R6.** Honest outputs: the UI and report always show the LLM mode, degraded agents, unresolved conflicts, and the synthetic-data badge.
- **R7.** No invented data, sources, benchmarks, or "validated" statuses.

---

## 1. ACCEPTANCE TESTS (the definition of "fixed")

Automate these in `tests/test_acceptance_v2.py` (backend) and a UI check script (Fix 1). All must pass:

1. **No fake numbers in the UI:** a script `ui/scripts/check-no-fake-numbers.mjs` (run in CI before the build) fails if the source contains any of: `157200`, `144500`, `172800`, `18.8`, `59.6`, `20.9`, `1.16` (CAGR), `145 + i`, `GDP Growth`, `'Passed'` literal inside a validator list, or `getDemoResponse`.
2. **Full-workflow order independence:** run the free-plan workflow 10 times with random per-agent delays; the **entire report JSON** (excluding ids and timestamps) is identical.
3. **Degraded run verifies correctly:** a persistent failure in one agent yields a report with a degraded banner, `Low` confidence, and verification **not** failing because of the fallback provenance tag.
4. **Discussion is data-driven:** change the CFO's conversion assumption in the mock; the Skeptic critique text and the numbers inside it change accordingly. No numeric literals appear in the discussion code.
5. **Verification catches tampering** in every report section: scenario table, tornado, flip point, outcome ranges, executive-summary prose, and execution-plan thresholds. A missing report fails verification.
6. **Real-mode readiness:** `/api/health` returns `llm_mode`, provider, and model; `LLM_MODE=real` without a key or without an explicit model ID raises `ConfigurationError`; a full replay run from committed cassettes passes with no network (or the test reports `RECORDING PENDING` if none exist yet).
7. **Price change is real:** a price-change run has price-specific agent findings, a conflict on a price parameter resolved by the price simulator, and **no free-plan wording** anywhere in the report.
8. **Resolver correctness:** a `proceed` vs `reject` conflict is never auto-marked immaterial without a computed justification.

---

## FIX 1. The "Simulation Workspace" is largely a front-end mock (CRITICAL; review item 1)

**Problem (verified in code).**
- `SimulationWorkspace.tsx::scenariosFromReport` hardcodes probabilities `18.8 / 59.6 / 20.9`, invents ranges with `* 0.95` and `* 1.05`, and builds "Pessimistic / Realistic / Optimistic" by picking **different strategies'** MRR instead of one strategy's scenarios.
- `SimulationResultsPanel.tsx::BASE_DEMO_SCENARIOS` shows made-up values (144,500 / 157,200 / 172,800) before any run.
- `WorkspaceModal.tsx::ForecastingView` shows `145 + i * 2.2` as MRR.
- `SimulationContextBar.tsx` multiplies a hardcoded `157200` by `1.16 ^ years`.
- `ModelValidatorView` is a static list of five checks, all hardcoded "Passed", including "settled CFO vs Growth divergence at 1.85%".
- `DRIVER_DEFAULTS` includes Inflation, GDP Growth, Salary Increase, Discounts, which are not in `SIM_PARAMS` and affect nothing. `VERSION_SNAPSHOTS` and `PRESET_DECISIONS` are static.
- `DecisionAssistantPanel` / `handleSendMessage` submits **each chat message as a new decision**, then shows the report's headline thesis whatever the question was; otherwise it shows canned text.

**Required changes.**

1. **Principle: every number on every screen comes from the API.** Anything else is removed or visibly labelled "UI preview, not model output".
2. **Backend: add read endpoints** (and tests):
   - `GET /api/params` returns `SIM_PARAMS` (name, unit, bounds, default, favorable direction, description).
   - `GET /api/decisions/{id}/trajectory?strategy=&scenario=` returns the monthly `history` (MRR, customers, free users, cash, runway) from the matching `SimulationRun`.
   - Add a deterministic histogram (bins and counts, seeded) per strategy to the Monte Carlo summaries for MRR and net contribution; include it in the report's `outcome_ranges` and in the verifier's traceable set.
   - `POST /api/decisions/{id}/resimulate` accepts parameter overrides (within `SIM_PARAMS` bounds), re-runs the deterministic scenario matrix and Monte Carlo for that decision, and returns the new scenario table and outcome ranges. Mark the result `what_if: true`; it never overwrites the stored report.
   - `POST /api/decisions/{id}/ask` answers questions **about the existing report only** (see Assistant below). It never creates a new decision.
3. **Scenario cards.** For the **recommended strategy**, show conservative / expected / optimistic of that **same** strategy from the report's scenario table. Replace the invented probabilities with Monte Carlo **P10 / P50 / P90** and `p_feasible`, `p_best` from `outcome_ranges`. Delete `BASE_DEMO_SCENARIOS`; before any run show an empty state: "Run a decision to see results."
4. **Distribution chart.** Draw it from the API histogram. Remove any locally generated curve.
5. **Drivers panel.** Build drivers from `GET /api/params` and the report's assumption ledger (low / base / high per parameter, grouped by simulator parameter). Remove Inflation, GDP, Salary, Discounts, or show them disabled under a "Context only, not modelled" heading. Changing a driver and pressing **Re-run** calls `resimulate`. The distribution selector shows a read-only "Triangular" (what the engine samples).
6. **Forecast view** uses the trajectory endpoint. Remove the year/quarter/CAGR popover math; the horizon is the simulation horizon, labelled as such.
7. **Model Validator view** renders the report's real `verification_summary` (check name, status, detail) and the degraded and unresolved-conflict indicators. No static "Passed" list.
8. **Modals/menus.** Wire each to real data or delete it:
   - Version history = `/api/history`.
   - Break-even = report `flip_point`.
   - Scenario comparison = `scenario_table`.
   - What-if sandbox = `resimulate`.
   - Monte Carlo view = `outcome_ranges`.
   - Delete `PRESET_DECISIONS` and `VERSION_SNAPSHOTS` unless they come from the API.
9. **Assistant.** `ask` receives the question and the stored report JSON. In real/replay mode, call the LLM with a prompt that may use **only numbers present in the report JSON**; validate the answer by extracting its digits and rejecting any number not in the report (retry once, then return a safe templated answer). In mock mode, return answers templated from report fields ("Summarize results", "Explain cost drivers", "Compare scenarios", "Investigate risks"). Remove `getDemoResponse` canned replies.
10. **Honesty chrome.** The workspace header always shows the "Synthetic data" badge and an **LLM mode banner** (`/api/health`): "MOCK MODE: agent outputs are scripted" when mock.

**Done when.** `check-no-fake-numbers.mjs` passes and is added to CI before `npm run build`; backend tests cover each new endpoint; changing a driver and re-running changes the displayed numbers; with the backend stopped the workspace shows an error/empty state, **not** demo numbers.

---

## FIX 2. The scenario matrix is still order-dependent; runway floor is hardcoded (review item 3)

**Problem.** `Supervisor._handle_supervisor_task` calls `build_scenario_params(state.assumptions, scen)`, which overwrites by name, so the **last agent to finish wins** (completion order varies). Only the tornado and Monte Carlo use `reconcile_assumptions`, so the headline matrix and Monte Carlo can disagree. The resolver's `baseline_params` has the same last-writer problem, and `min_runway=10.0` is hardcoded in the resolver and in the Monte Carlo calls, ignoring the decision's constraints.

**Required changes.**

1. `build_scenario_params` must accept a `ReconciledParams` (low / base / high per simulated parameter) and use it. Update the supervisor (free-plan and price paths), the resolver baseline, the tornado, the flip-point, and Monte Carlo so **every** consumer uses the same reconciled object. Compute it once after the Skeptic review and store it on state (`state.reconciled`).
2. Contested parameters keep their union range and a `contested` flag; show the flag in the scenario table footnote and the assumption ledger.
3. Compute `min_runway` once with `extract_min_runway_constraint(decision.constraints, assumptions)` and pass it to `rank_strategies`, the resolver, and `run_monte_carlo_suite`. Remove the literal `10.0` from those call sites.
4. Exclude degraded findings' assumptions (provenance `fallback_degraded`) from reconciliation and conflict detection (see Fix 3).

**Done when.** Test: run the workflow 10 times with randomized agent delays; full report JSON identical (Acceptance test 2). Test: changing `constraints` to "minimum 14 months runway" changes feasibility in the ranking, the resolver verdicts, and Monte Carlo `p_feasible`.

---

## FIX 3. Degraded runs likely fail verification (review item 4)

**Problem.** `fallback_degraded` is allowed by the `Assumption` schema but is missing from `verifier.valid_provenances`. After a persistent failure, the BackupAnalyst's assumptions fail `provenance_integrity`, so the report is stamped "Unverified" for a failure the system handled correctly.

**Required changes.**

1. Add `fallback_degraded` to the valid provenance set, with the rule: it requires a `source_ref` and `confidence <= 0.3`.
2. Degraded assumptions are excluded from reconciliation and scenario parameters (Fix 2) but **remain visible** in the assumption ledger under a "Degraded fallback" group.
3. The report's degraded banner, `Low` confidence cap, and verification status must be consistent: a degraded-but-otherwise-valid run shows `Status: Degraded (verified)`, not `Unverified`.

**Done when.** Acceptance test 3, parametrized over all five specialist agents and all three failure modes with `persist=true`.

---

## FIX 4. The agent "discussion" is scripted (review item 2)

**Problem.** In `supervisor.py` the `agent_discussion` handler appends fixed message strings with hardcoded numbers ("4.5%", "3.5%-6.5%", "2.2%", "12%", "1.5%") and fixed rebuttals. It never reads the findings, never changes an assumption, and the one bounded rebuttal round that was specified is not implemented.

**Required changes.**

1. Define schemas: `Critique(target_agent, parameter, challenge, requested_evidence, benchmark_ref, suggested_low?, suggested_high?)` and `Rebuttal(agent, parameter, position: hold|revise, rationale, revised_low?, revised_base?, revised_high?)`.
2. **Skeptic critiques are generated from data.** In real/replay mode the Skeptic agent makes an LLM call over the peer findings and `data/benchmarks.json`, returning `Critique` objects. In mock mode a deterministic generator compares each agent's assumption to `benchmarks.json` and to the other agents' ranges and composes the text from those values. **No numeric literals in the discussion code.**
3. **One bounded rebuttal round.** Each critiqued agent receives its own finding, the critique, and (if available) the relevant conflict simulation evidence, and returns a `Rebuttal`. In real/replay mode agents may revise; validate revisions (within `SIM_PARAMS` bounds, `low <= base <= high`) and record `revision_of` plus the rationale. In mock mode agents **hold their position** with a rationale composed from their own finding's evidence (do not script concessions).
4. After the rebuttal round, **re-run conflict detection** on the revised findings. The resolver's `ranges_overlap` / "converged" path should therefore be reachable only when revised ranges truly overlap.
5. Store every `Message` in `state.messages`, stream `message_posted` events, and show the thread in the agent inspector.

**Done when.** Acceptance test 4; a test where a mocked rebuttal revises the CFO range into overlap with Growth's, after which the conflict becomes `resolved_converged`; a test where agents hold and the conflict stays `unresolved_material`.

---

## FIX 5. Real mode has never been exercised (review item 6)

**Problem.**
- `tests/cassettes/` does not exist; `data/known_good_run.json` is an old summary with no `llm_mode`.
- `/health` reads only the legacy `LLM_MOCK_MODE`; `/api/health` does not report the mode.
- `get_llm_badge()` always claims "Claude 3.5 Sonnet / GPT-4o / Gemini 1.5 Flash" regardless of the model actually called; the Gemini model is hardcoded, and the Anthropic/OpenAI defaults are old.
- The Gemini key is sent in the URL; retries have no backoff; there is a dead duplicate `raise` after the retry loop.
- The agent prompt does not list the simulator parameter names, so a real LLM will invent names that are silently ignored; there is no `ignored_assumptions` record.
- Analysis agents run in parallel but receive `state.model_dump()`, so what they see of each other's findings depends on timing.

**Required changes.**

1. **Mode reporting.** Both `/health` and `/api/health` return `llm_mode` (`mock|real|record|replay`), `provider`, and `model`. Replace every `LLM_MOCK_MODE` mention in `.env.example`, `Dockerfile`, `docker-compose.yml`, and the README with `LLM_MODE`.
2. **Explicit provider and model.** Add `LLM_PROVIDER` (`gemini|openai|anthropic`); do not guess from whichever key is set. Models come from `GEMINI_MODEL`, `OPENAI_MODEL`, `ANTHROPIC_MODEL` with **no baked-in defaults**; in `real`/`record` mode a missing model raises `ConfigurationError("Set <X>_MODEL to a currently supported model ID from the provider's docs")`. Document in `.env.example`. The badge is built from the actual provider and model.
3. **Transport hygiene.** Gemini key via the `x-goog-api-key` header. Exponential backoff with jitter on 429/5xx (honour `Retry-After`) and on JSON/validation failures, bounded. Remove the dead `raise`.
4. **Parameter whitelist.** The agent prompt lists the allowed simulator parameters (name, unit, bounds, favorable direction) from `SIM_PARAMS` and the exact JSON schema. After validation: unknown names become **context assumptions** and are recorded in `state.ignored_assumptions`; out-of-bounds values are clamped and flagged. Show `ignored_assumptions` and clamps in the run log.
5. **Independence in the analysis stage.** Analysis-stage agents receive only the decision, their own tool data, and the company snapshot, **not** peer findings or the full state. Peer findings are visible only in the discussion, Skeptic, and rebuttal stages (Fix 4). Add a test asserting the analysis prompts contain no peer content.
6. **Cassettes.** Key cassettes by `sha256(prompt + response_model name + provider + model)`, and strip volatile values (decision ids, timestamps) from prompts before hashing so replay is stable. Update `scripts/run_real_demo.py` to run with `LLM_MODE=record`, write cassettes to `tests/cassettes/`, and write the **full report JSON** (including `llm_mode`, provider, model, timestamp) to `data/known_good_run.json`.
7. **Replay test.** Add `tests/test_replay_full_run.py` that runs the whole free-plan workflow in `replay` mode with no network. If no cassettes exist yet, the test should fail with the message `RECORDING PENDING` only in a dedicated marker (`@pytest.mark.requires_cassettes`) and be excluded from the default run until cassettes are committed.
8. **If you have no API key,** complete items 1 to 5 and 7, and finish with: `RECORDING PENDING: run LLM_MODE=record python scripts/run_real_demo.py with a key, then commit tests/cassettes/ and data/known_good_run.json`.

**Done when.** Acceptance test 6.

---

## FIX 6. Verification is better but still weak (review item 5)

**Problem.**
- `report_number_traceability` only inspects the scenario table and outcome ranges, not the flip point, tornado, executive-summary and risks text, execution plan, or company position.
- It compares each value against a large pool (including integers rounded to 0 decimals, tolerance 0.05), which is easy to pass by accident.
- With no report supplied, `scenario_ordering` and `required_sections_present` return "passed" by default.
- The loop-back rebuilds the report from the same state with the same code, so it can never change the outcome.
- `scenario_ordering` checks MRR only.

**Required changes.**

1. **Number registry.** In `report_builder.py`, every number placed in the report goes through a `NumberRegistry` call such as `reg.n(value, source="sim:<run_id>.mrr_month_12")` (or `mc:<strategy>.p50`, `company:mrr`, `flip:<id>.threshold`, `tornado:<param>.swing`). The registry is attached to the report. The verifier then, for **each** registry entry, resolves the source against the real `SimulationRun`/Monte Carlo/company/flip/tornado data and checks equality (relative tolerance 1e-6). Report numbers not in the registry fail.
2. **Prose scan.** Extract every number from LLM-written or templated prose fields (executive summary, risks, execution plan) and require each to match a registry entry after formatting (percent, currency, months). Any unmatched digit fails.
3. **Stronger checks.** `scenario_ordering` for MRR **and** net contribution **and** runway, per strategy (Strategy C may be `<=`; document). `required_sections_present` fails on missing **or empty** content (empty list / dict / blank string), and includes `outcome_ranges`.
4. **No report = fail.** `verify_workflow` without a report returns `failed` for the report-dependent checks with the detail "no draft report to verify". Remove all vacuous `passed` defaults.
5. **Meaningful loop-back.** Map failures to the responsible task (trace or scenario failures: re-run `simulation` then `report_draft`; section failures: `report_draft`; provenance or unit failures: `skeptic_review`). Re-dispatch those tasks through the supervisor with fresh checkpoints, emit `verification_loopback` events, bounded to 2 loops. If a loop produces an identical failure set, stop early and finalize as `Verification failed`.

**Done when.** Acceptance test 5, with a separate tamper test for each section; a test that a run with a deliberately broken simulation function triggers a loop-back that re-runs the simulation task.

---

## FIX 7. Price change is not really implemented (review item 7)

**Problem.** The price-change DAG runs, but the agents are free-plan agents (nothing in `agents/specialists.py` is price-aware), the price simulator runs on default elasticities because no agent proposes price parameters, and conflicts are not resolved in that path.

**Required changes (Option A; if you are short on time, do Option B).**

- **Option A.**
  1. Pass `decision.type` into agent prompts and mock generators. Add price-specific findings for CFO (revenue lift vs runway), Growth (new-customer conversion effect), Customer (churn/contraction response), and Skeptic, with assumptions in the price parameters (`price_elasticity_starter`, `price_elasticity_growth`, `expansion_revenue_rate`, `contraction_risk_rate`). Do not activate the CTO and Product agents for price change unless they add value.
  2. Introduce a `SimulatorAdapter` interface (`strategies`, `simulate`, `build_params`, `rank`), implemented for the free-plan and price models. The resolver, scenario matrix, Monte Carlo, tornado, and flip-point use the adapter so **one** code path serves both decision types.
  3. Price conflicts (for example elasticity ranges that do not overlap) are detected and resolved by the price simulator.
  4. Report templates are decision-type specific; add a test that fails if the price report contains "free plan", "free users", or free-plan strategy names.
- **Option B.** Remove price change from the parser, DAG, UI chips, workspace presets, and README, and list it as planned.

**Done when.** Acceptance test 7, plus a data-sensitivity test: changing `price_elasticity_starter` bounds changes the price report's ranking or numbers.

---

## FIX 8. Conflict resolver bugs (review item 8)

**Problem (verified in `conflict/resolver.py`).**
- For `contradictory_recommendation`, `verdict = "immaterial" if "proceed" in rec_a or "proceed" in rec_b`, so **`proceed` vs `reject` is marked resolved whenever the top strategy is feasible**.
- The "resolved_converged" text claims "consensus" without computing it.
- `find_flip_point` always compares against a fixed competitor (Strategy C, or B).
- Deltas print "+$" even when negative.
- `rebuttal_round` is an unused parameter.

**Required changes.**

1. **Recommendation conflicts.** Determine from the simulation whether a **feasible, positive-contribution** strategy exists relative to Strategy C. If one exists, the "reject" side is contradicted: record `resolution_method = "simulation_supports_<agent>"` with the numbers. If none exists, the "proceed" side is contradicted. If the evidence is mixed (for example feasible only under one side's assumptions), mark `unresolved_material`. Never use string matching on recommendation labels to decide materiality.
2. **Converged status.** Only after rebuttal: merge the revised ranges with `reconcile_assumptions`, re-rank under the merged base **and** under each side's base; mark `resolved_converged` only if the recommended strategy is the same under all three, and generate the text from those numbers.
3. **Flip competitor.** Use the second-ranked strategy under the reconciled baseline as the competitor. If the disputed parameter does not change the ranking within its bounds, return `exists: false`.
4. Signed deltas via `{:+,.0f}`; remove or use `rebuttal_round`.
5. Use the reconciled baseline and constraint-derived `min_runway` (Fix 2).

**Done when.** Acceptance test 8; unit tests for each branch including negative deltas.

---

## FIX 9. Minor items and documentation honesty (review item 9)

1. **Dispatch on `task.kind` only.** Remove the substring fallbacks (`"conflict" in task.id`, `"report" in task.id`, and so on). A task without a valid `kind` raises a clear error. Update tests.
2. **README and docs.** Replace the static "94 Passed" badge with the GitHub Actions badge. Fix the stale "Current Step 0 Details" section in `docs/PROGRESS.md`. Update the milestone and status tables so each claim matches the code after these fixes; mark anything still mocked as `[MVP-MOCK]` (for example the seeded calibration history) and anything removed as `planned`.
3. **README sections.** Add "LLM modes (mock / real / record / replay)", "What is synthetic", and "Known limitations". State plainly that the primary demo should be run in `replay` or `real` mode, not `mock`.
4. **Docs folder.** Keep the specification and prompt files under `docs/` only. Do not reference them from the UI.
5. **CI.** Add the `check-no-fake-numbers.mjs` step before the frontend build; add a job that runs the acceptance tests in `mock` mode.

---

## FINAL CHECKLIST (report back with evidence for each)

- [ ] Fix 1: no fake numbers in the UI; new endpoints; workspace driven by API data; assistant answers from the report; `check-no-fake-numbers.mjs` in CI
- [ ] Fix 2: one reconciled parameter set everywhere; constraint-derived runway floor; order-independent full report
- [ ] Fix 3: degraded runs verify correctly; degraded assumptions excluded from simulation, visible in the ledger
- [ ] Fix 4: data-driven critiques; one real rebuttal round; re-detection after revisions
- [ ] Fix 5: mode/provider/model in `/health`; explicit model config; header key; backoff; whitelist and `ignored_assumptions`; independent analysis stage; cassette workflow (or `RECORDING PENDING` note)
- [ ] Fix 6: number registry; prose scan; no vacuous passes; meaningful loop-back
- [ ] Fix 7: price change implemented via a simulator adapter, or removed
- [ ] Fix 8: recommendation conflicts decided by simulation; converged status computed; flip competitor chosen from the ranking; signed deltas
- [ ] Fix 9: dispatch by kind only; README/docs/CI honest and current
- [ ] All backend tests pass (paste the summary line); UI builds; acceptance tests in `tests/test_acceptance_v2.py` pass

**Begin by reading the repo and posting your short plan. Then start with Fix 1.**

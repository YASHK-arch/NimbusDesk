# VentureTwin Build Progress & Verification Tracker

> **Project:** VentureTwin (SwarmFlow: Multi-Agent Task Coordination Engine)  
> **Repository:** [https://github.com/YASHK-arch/Citadel-engine](https://github.com/YASHK-arch/Citadel-engine)  
> **Status Badges:** `[MVP-REAL]` Built & Validated | `[MVP-MOCK]` Seeded/Simulated | `[STRETCH]` Deferred | `[FUTURE]` Roadmap Only

---

## Architecture Decision & Framework Choice

- **Executor Choice:** Custom Async DAG Executor with explicit topological task dispatcher, async worker pool, SQLite checkpointing, and live failure injection hooks.
- **Justification:** Guarantees 100% deterministic control over live chaos injection (timeouts, exceptions, schema corruption mid-flight), instant pause/resume, fine-grained event streaming (SSE/WebSocket), and zero black-box graph compilation overhead. It makes every state mutation, retry policy, and simulation-based conflict resolution loop explicitly traceable and testable without framework abstractions getting in the way.
- **LLM Strategy:** Provider-agnostic `llm_call()` with Pydantic v2 structured output validation, bounded retries, low temperature ($0.0$), and deterministic mock fallback for offline and fast unit testing.
- **Core Principle:** LLMs never output numbers; numbers come strictly from deterministic Python models (`NumPy`, `SciPy`, `Pandas`). Conflicts are resolved by simulation and evidence, never by voting or LLM preference.

---

## Step-by-Step Implementation & Milestone Status

| Step | Milestone & Focus | Status | Evidence / Done When |
|---|---|---|---|
| **Step 0** | Project Skeleton, Environment, `llm_call()`, FastAPI | **COMPLETED** | Pytest passes (4/4), API starts, mock LLM returns validated Pydantic model |
| **Step 1** | Schemas & Synthetic Data (`data/synthetic_company.json`, seeded decisions) | **COMPLETED** | Schemas validate (9/9 tests pass), NimbusDesk loaded with 12.6mo runway & tension |
| **Step 2** | Agent Base Class & Specialists (CFO, Growth, CTO, Customer, Skeptic, Registry) | **COMPLETED** | Distinct objectives, tools, non-overlapping conversion ranges (CFO 1.0-2.2% vs Growth 3.5-6.5%), chaos hooks verified |
| **Step 3** | Task Decomposition Engine (NLP -> Decision -> Task DAG) | **COMPLETED** | Natural language parsing, cycle detection, 10-node DAG decomposition with 5 parallel analysis roots |
| **Step 4** | Supervisor Architecture & Parallel Execution | **COMPLETED** | Async parallel dispatcher with timestamp tracking (<0.05s spread), dependency barriers, and full event bus |
| **Step 5** | Communication Protocol & Shared State (SQLite Checkpoints) | **COMPLETED** | Typed state with Pydantic, SQLite task-level checkpoints, resume without redoing finished work, malformed outputs rejected |
| **Step 6** | Deterministic SaaS Simulation Engine (Monte Carlo, Tornado, Flip-Points) | **COMPLETED** | 24-month SaaS dynamics, 3 strategies, reproducible seeds, Monte Carlo p10/p50/p90, tornado swings, flip-point search |
| **Step 7** | Conflict Detection & Simulation-Based Resolution | **COMPLETED** | Rule-based detectors (opposing recs, non-overlapping bounds, missing evidence), CFO vs Growth conflict resolved via dual simulation delta & flip-point |
| **Step 8** | Failure Injection & Recovery (Timeout, Exception, Corrupt Output) | **COMPLETED** | Fault detection, retry backoff, degraded fallback finding, POST /api/decisions/{id}/inject-failure endpoint |
| **Step 9** | Skeptic & Deterministic Workflow Verification | **COMPLETED** | Skeptic challenges aggressive assumptions & downgrades confidence; 5 deterministic checks (units, ratios, R4 traceability caught fabricated numbers) |
| **Step 10** | Consolidated Decision Report Builder (JSON + Markdown) | **COMPLETED** | 10-section report (scenarios, tornado, flip-point, provenance ledger, conflicts, verification summary, run log, disclaimer), 100% R4 traced |
| **Step 11** | API Endpoints & SSE Streaming | **COMPLETED** | Complete REST suite (company, submit, status, stream, chaos injection, report JSON/MD, approve, history, graph) |
| **Step 12** | Frontend: 3 Screens (Console, Report, Calibration) | **COMPLETED** | React+TS+Tailwind SPA: Live execution DAG, SSE feed, node inspector, failure injection, scenario tables, tornado charts |
| **Step 13** | Human Approval Gate, History & Calibration Screen | **COMPLETED** | POST /approve gate stores DecisionRecord in history, calibration stats computed with average error & most-wrong assumptions |
| **Step 14** | Hardening, Demo Fallback Cache & Documentation | **COMPLETED** | All 46 tests passing, demo script in DEMO_SCRIPT.md, known-good run cached in data/known_good_run.json, comprehensive README |
| **Fix 1** | Dynamic Strategy Ranking & Removal of Hardcoded Literals | **COMPLETED** | Pure functions in `report/decision_logic.py` (`rank_strategies`, `compute_confidence`). Dynamic recommendations based on runway floor; low cash triggers honest "Do not proceed"; all hardcoded numbers removed from report builder. (52/52 tests pass). |
| **Fix 2** | Scenario Variation, Stress Matrix & Assumption Bounds Validation | **COMPLETED** | Single source of truth in `simulation/params.py` (`SIM_PARAMS`, `build_scenario_params`). Strict `conservative < expected < optimistic` ordering, 3 stress scenarios (`stress_infra_doubles`, `stress_conversion_collapse`, `stress_large_customer_churn`), and `Assumption` `low <= base <= high` validator. (57/57 tests pass). |
| **Fix 3** | Conflict Resolution by Simulation, Ordinal Distance & Grouping | **COMPLETED** | Ordinal scale in `conflict/detector.py` (reject 0 to proceed 3, min distance 2), parameter-grouped assumption divergences. In `conflict/resolver.py`: 6-run dual strategy matrix, pure computed resolution text, verdict evaluation (`decision_relevant` vs `immaterial`), honest `unresolved_material` marking for persistent divergences. (61/61 tests pass). |
| **Fix 4** | Grounded Provenance, Unit Sanity & No Fabricated Benchmark Citations | **COMPLETED** | Created `data/benchmarks.json` (explicitly flagged illustrative). Removed all fabricated reports/benchmarks from specialist mocks and tools; `verified_data` strictly references and ties out to `data/synthetic_company.json#...`; `SIM_PARAMS` expected units strictly validated by verifier. (65/65 tests pass). |
| **Fix 5** | Explicit Task Kinds, Skeptic-Before-Simulation DAG & Real Verification | **COMPLETED** | Added `Task.kind` (7 explicit kinds) with DAG order: analyses -> conflict -> skeptic -> simulation -> draft -> verify -> finalize. Skeptic runs before simulation generating adjustments and challenges; verifier executes 6 rigorous checks including `scenario_ordering`, non-empty section presence, and strict draft number traceability with bounded loop-back on failure. (68/68 tests pass). |
| **Fix 6** | Order-Independent Assumption Reconciliation & Tornado Parameter Whitelist | **COMPLETED** | Created `simulation/reconcile.py` (`reconcile_assumptions`, `ReconciledParams`). Deterministic sorting by `(agent, assumption_name)` ensures execution-order invariance (verified under 20 random shuffles). Merges ranges with confidence-weighted base, flags non-overlapping ranges as `contested = True`, separates operational context parameters, filters tornado sensitivity strictly to `SIM_PARAMS` with no duplicates, and renders contested badges and operational context table in reports. (71/71 tests pass). |
| **Fix 7** | Honest Bisection Flip-Point & No Midpoint Fallback | **COMPLETED** | Rewrote `simulation/sensitivity.py::find_flip_point` with bisection search down to tolerance `< 1.0` when bounds have opposite signs. Completely removed midpoint fallback: when both bounds share the same sign, returns `exists=False`, `flip_value=None`, and honest statement (`"No flip point within tested range..."`). Updated `report/report_builder.py`, `ui/src/types.ts`, and created `ui/src/components/FlipPointCard.tsx` to render dedicated "Robust to Variation" panels. (73/73 tests pass). |
| **Fix 8** | Persistent Failure Injection, BackupAnalyst Fallback & Honest Workflow Failure Status | **COMPLETED** | Added `FailureInjection` schema with `persist` and `fail_attempts`. Implemented `BackupAnalyst` in `agents/specialists.py` providing conservative fallback assumptions (`fallback_degraded` provenance). Persistent specialist failure invokes `BackupAnalyst`, visibly displays `degraded_agent_banner` in report and markdown, and caps recommendation confidence at `Low`. Core task failure marks `state.status = 'failed'`, halts execution, persists SQLite checkpoint, and blocks report generation with HTTP 409. (76/76 tests pass). |
| **Fix 9** | Explicit LLM Modes, Cassette Record/Replay, Parameter Whitelisting & Agent Discussion | **COMPLETED** | Implemented `LLM_MODE in {'mock', 'real', 'record', 'replay'}`. `real`/`record` without API key immediately raises `ConfigurationError`. Added deterministic cassette recording/replaying in `tests/cassettes/`. Added `scripts/run_real_demo.py`. Enforced parameter whitelisting against `SIM_PARAMS` (hallucinations filtered from simulated execution). Added multi-turn `Message` schema (`proposal`, `critique`, `rebuttal`) and a dedicated `agent_discussion` DAG layer where Skeptic critiques Growth/CFO bounds and agents rebut before conflict detection. (80/80 tests pass). |
| **Fix 10** | Pricing-Change Simulation Path, Elasticity Mechanics & Pricing Report Generation | **COMPLETED** | Implemented Option A: `simulation/price_model.py` with 3 distinct pricing strategies (Strategy A: Selective 20% Starter hike, Strategy B: Flat 15% hike across all tiers, Strategy C: Hold prices + introduce metered usage add-on). Integrated price elasticity parameters into `SIM_PARAMS`, topological `price_change` DAG (analysis, discussion, skeptic, simulation, draft, verify, finalize), and decision-type-specific report generation without free-plan text contamination. (82/82 tests pass). |
| **Fix 11** | Monte Carlo Distributions, Triangular Sampling, Stored Seeds & Verifier Traceability | **COMPLETED** | Implemented `run_monte_carlo_suite` in `simulation/monte_carlo.py` using triangular sampling over reconciled simulated parameters. Samples identical realizations across competing strategies, computes `p_feasible` and `p_best` (summing to ~1.0), p10/p50/p90 percentiles for MRR, runway, and net contribution. Wired `p_best` into confidence scoring, removed unused `seed` from `simulate()`, added "Outcome ranges" section to report and markdown, built UI range distribution table, and verified full R4 verifier traceability. (87/87 tests pass). |
| **Minor Polish** | Repo Hygiene, Environment CORS, CI Workflow & Acceptance Auditing | **COMPLETED** | Cleaned root directory markdown duplicates, consolidated all specification and fix prompts into `docs/`. Configured CORS in `api/app.py` with `ALLOWED_ORIGINS` environment variable and safe localhost defaults. Added GitHub Actions CI workflow `.github/workflows/ci.yml` running pytest and npm build. Created `tests/test_acceptance.py` automating all 7 pillars of "The One-Minute Test" (data sensitivity, scenario ordering, order independence, real verification, honest failure, no silent mock, and no fabricated sources). All 94 tests passing. |
| **Step 15** | Simulation Workspace Dashboard & Production Database Layer | **COMPLETED** | Built enterprise SAP-style financial modelling workspace matching docs/dashboard.jpeg; functional File, Edit, Tools, Display menus; Recharts probability distribution curve; 3 scenario cards with donut rings; dual-engine PostgreSQL & SQLite persistence; Docker containerization |
| **Step 16** | Interactive Date & Forecast Horizon Popover, Deep Navigation Tools, & Toast System | **COMPLETED** | Interactive Date popover (FY2023-FY2027, quarters, custom date, compound projection preview); full wiring of File, Edit, Tools, Display actions with modal views (New Simulation, Version History, Monte Carlo engine, What-if Sandbox, Scenario Comparison, Break-even flip point, 12M Forecasting, Driver Properties, Model Validator); reactive toast feedback. |

---

## Current Step 0 Details

- **What is Implemented:**
  - Repository structure matching Section 5 (`orchestrator`, `agents`, `state`, `conflict`, `simulation`, `verification`, `report`, `data`, `api`, `ui`, `tests`, `docs`).
  - Python 3.13 venv with `fastapi`, `uvicorn`, `pydantic v2`, `numpy`, `pandas`, `scipy`, `networkx`, `pytest`, `pytest-asyncio`, `aiosqlite`.
  - Provider-agnostic `llm_call()` in `agents/llm.py` with structured Pydantic v2 validation, bounded retries, low temperature, and mock mode.
  - FastAPI app with `/health` and `/api/health` endpoints.
- **What is Mocked / Seeded:**
  - LLM call defaults to deterministic mock mode for offline testing.
- **How to Run Step 0 Tests:**
  ```bash
  .venv/bin/pytest tests/test_step0_skeleton.py -v
  ```
- **Known Gaps:**
  - Full domain schemas (Step 1) and agents (Step 2) are pending.

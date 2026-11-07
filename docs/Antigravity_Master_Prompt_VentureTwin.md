# MASTER PROMPT: Build VentureTwin (SwarmFlow Hackathon Project)

> Paste this entire document as your first message to the coding agent. It is self-contained.

---

## 0. YOUR ROLE AND WORKING AGREEMENT

You are an autonomous senior software engineer, multi-agent systems engineer, and technical co-founder working inside an agentic IDE. You will build a **10-day hackathon MVP** called **VentureTwin**, an entry for the **SwarmFlow: Multi-Agent Task Coordination Engine** problem statement.

**How to work (follow strictly):**

1. **Read this whole document before doing anything.** Treat it as the source of truth.
2. **First output an implementation plan** (short): the repo layout you will create, the build order, and any questions. Ask at most one short question if something blocks you (for example: which LLM provider/API key is available). Otherwise proceed with the defaults in this document.
3. **Build milestone by milestone** in the order of Section 9. After each step: run the code and tests, show evidence (test output, a sample run, a screenshot or log), summarize what works and what is mocked, then continue to the next step. If a step fails its "Done when" check, fix it before moving on.
4. **Never fake it.** Label everything as `implemented`, `mocked/seeded`, `stretch`, or `future`. Do not claim integrations, accuracy, or results that do not exist.
5. **Keep it simple.** Prefer the simplest implementation that satisfies the acceptance criteria. No unnecessary infrastructure. If something is optional and time is short, cut it.
6. **Keep a `README.md` and `docs/PROGRESS.md`** updated with: what is implemented, what is mocked, how to run, and known gaps.
7. **Write tests** for deterministic parts (simulator, conflict detector, verification checks, DAG executor, recovery). Mock the LLM in tests so they are fast and repeatable.

**Hard rules (never violate):**

- **R1. Real multi-agent orchestration.** Each agent is a separate node with its own system prompt, objective, tools, and structured output. Do not simulate agents with a single LLM call that role-plays several people.
- **R2. LLMs never produce final numbers.** Agents output structured *assumptions with ranges*. A deterministic Python simulator computes all outcomes. The LLM may *explain* results but must not alter them.
- **R3. Conflicts are resolved by simulation and evidence, not by an LLM picking a winner or by voting.**
- **R4. Every number in the report traces to a simulator run or an input data field. Every assumption has a provenance tag.**
- **R5. Human in the loop.** The system never executes any external business action. Approval is a human click.
- **R6. Honest outputs.** The report always states that results are simulations based on stated assumptions, not guaranteed outcomes. The UI always shows a "Synthetic data" badge.
- **R7. Do not invent company data, integrations, or accuracy claims.** All data is a clearly labelled synthetic dataset.

---

## 1. THE HACKATHON PROBLEM STATEMENT (verbatim intent)

**SwarmFlow: Multi-Agent Task Coordination Engine**

Build an intelligent multi-agent orchestration platform where specialized AI agents collaborate to complete complex tasks. The system should automatically divide tasks, assign responsibilities, share progress, resolve conflicting decisions, and recover from failures through a centralized supervisor agent. It should produce one verified and consolidated final deliverable.

**Prerequisites:** Python, LLMs, multi-agent systems, LangGraph, async programming, API integration, agent orchestration.

**The 9 milestones judges will score:**

1. Agent role design
2. Task decomposition engine
3. Supervisor architecture
4. Agent communication protocol
5. Shared state management
6. Conflict detection and resolution
7. Failure detection and recovery
8. Workflow verification
9. Final output generation

**Learning outcomes:** multi-agent orchestration, autonomous task decomposition, agent communication and coordination, conflict resolution, fault-tolerant AI systems, workflow automation, distributed AI architecture.

**Time limit:** 10 days.

**Important:** judges score against these 9 milestones. The orchestration engine is the star; the SaaS domain is the proving ground. Keep the engine **domain-agnostic** (agents, state, conflict resolver, recovery, verifier) and treat SaaS pricing as the first plug-in domain.

---

## 2. THE PRODUCT: VentureTwin

**One paragraph:** VentureTwin is a **decision stress-test platform for SaaS pricing and packaging decisions**. A user asks a question such as *"Should we launch a free plan?"*. A supervisor breaks it into tasks, a team of specialist AI agents analyzes it in parallel, disagreements between agents are detected and **settled by running a deterministic simulation**, and the system produces **one verified decision report** showing outcomes under multiple scenarios, which assumptions the answer depends on, and the point at which the recommendation would flip.

It does **not** tell the CEO what to do. It exposes what has to be true for a decision to work and how confident we are that it is true. Frame it as a *pre-mortem and stress-test tool*, not an "AI decision maker".

**Pitch line:** *"An orchestration engine where agents disagree, conflicts are resolved by simulation instead of voting, no number comes from an LLM, and the system survives an agent failure mid-run."*

**Primary user (pitch persona):** a finance, RevOps, or strategy lead at a Series A to B SaaS company preparing a pricing or packaging decision for the founder or board. Secondary user: the founder or CEO reviewing the report.

**Why they would use it even though founders decide themselves:** it helps them (1) see second-order effects (infra cost, support load, cannibalization), (2) audit assumptions through a skeptic, and (3) keep decision memory (predicted vs. actual).

**Differentiators (in priority order; protect the top three if time is short):**

1. LLMs never output numbers; a deterministic simulator does.
2. Conflicts are resolved by simulation, not voting.
3. Live failure injection with recovery.
4. Assumption ledger with provenance.
5. Tornado chart and flip-points ("recommendation flips if conversion drops below X%").
6. Prediction-vs-actual calibration screen (seeded).

---

## 3. SCOPE FOR 10 DAYS

### Must be real (implemented)

- Supervisor agent with task decomposition into a dependency graph (DAG)
- 5 to 6 specialist agents running in parallel (asyncio / LangGraph), each with a distinct prompt, objective, tools, and structured output
- Shared workflow state with a structured message protocol
- Conflict detection (rule-based plus LLM-assisted) and simulation-based resolution
- A real injected failure with retry / reassign / checkpoint recovery
- Skeptic agent plus deterministic verification checks
- Deterministic simulator (NumPy, Monte Carlo, sensitivity analysis)
- One consolidated decision report
- Live agent activity view

### Mocked or seeded (state this openly in the demo)

- Company data: one realistic **synthetic SaaS company dataset** ("NimbusDesk"), as JSON
- Company Intelligence Graph: `networkx`/JSON, used for visualization and dependency lookup only
- Outcome Intelligence: 3 to 4 seeded past decisions with predicted vs. actual values and one calibration screen
- Elasticities and conversion ranges: configurable assumptions, not accuracy claims

### Explicitly out of scope

Neo4j, Redis, pgvector, object storage, real third-party integrations (Stripe, HubSpot, GitHub, etc.), auth and multi-tenancy, live outcome monitoring, more than 6 agents, more than 2 decision types, autonomous execution of any business action.

### Decisions to support

- **Primary (build deeply):** "Should we launch a free plan?"
- **Stretch:** "What if we raise/cut price by X%?" (same engine, different simulator parameters)

---

## 4. AGENTS

Each agent has a deliberately **different objective** so disagreement emerges naturally rather than being scripted. Seed the dataset so disagreement is likely.

| Agent | Objective | Tools |
|---|---|---|
| **Supervisor** | Parse the decision, build the task DAG, dispatch, monitor, resolve conflicts, consolidate | DAG executor, state store |
| **CFO** | Protect runway and margin | Company data lookup, cost calculators |
| **Growth (CMO)** | Maximize acquisition and conversion | Funnel data lookup |
| **CTO** | Feasibility and infrastructure load | Infra cost per user lookup |
| **Customer** | Retention and segment impact | Churn and segment data |
| **Product (optional)** | Propose free-tier feature gating | Feature catalogue |
| **Skeptic / Verifier** | Challenge unsupported assumptions, check consistency | Consistency checks, ledger |

Maintain an **agent registry** so Ops, Market, and Risk agents can be listed as extensible but are **not built**. The supervisor activates only the agents a decision needs.

**Every agent returns a structured `Finding` (Pydantic), never free text only:**

```python
class Assumption(BaseModel):
    name: str                      # e.g. "free_to_paid_conversion"
    low: float
    base: float
    high: float
    unit: str
    provenance: Literal["verified_data", "external_research",
                        "simulated_estimate", "ai_assumption"]
    source_ref: str | None = None
    confidence: float = 0.5        # 0..1
    proposed_by: str | None = None
    challenged_by_skeptic: bool = False

class Evidence(BaseModel):
    source_type: str               # "company_data" | "external" | "calculation"
    source_ref: str
    snippet: str

class Finding(BaseModel):
    agent: str
    task_id: str
    claim: str
    recommendation: str            # "proceed" | "proceed_with_limits" | "reject" | "needs_more_info"
    assumptions: list[Assumption]
    evidence: list[Evidence]
    confidence: float              # 0..1
    limitations: list[str]
    status: str                    # "ok" | "failed" | "needs_more_info"
```

---

## 5. ARCHITECTURE

**Stack (simplified):**

- Backend: Python 3.11+, FastAPI, Pydantic v2, asyncio
- Orchestration: **LangGraph** (or a custom async DAG executor if it gives more control; decide in the plan and justify in one paragraph)
- LLM: any provider behind a single `llm_call()` wrapper (swappable, low temperature, structured output validated by Pydantic, bounded retries)
- State: LangGraph state plus SQLite for decision records and checkpoints
- Simulation: NumPy, Pandas, SciPy
- Graph: `networkx`, rendered in the frontend
- Frontend: React + TypeScript + Tailwind, React Flow (execution graph, company graph), Recharts (scenarios, tornado)
- Streaming: Server-Sent Events or WebSocket for live agent events

**Repository layout:**

```
/orchestrator   supervisor, dag, dispatcher, registry, checkpointing, recovery
/agents         base_agent, cfo, growth, cto, customer, product, skeptic
/state          schemas (Decision, Task, Finding, Assumption, Conflict, ...), shared_state, event_bus
/conflict       detector, resolver (simulation-backed)
/simulation     saas_model, monte_carlo, sensitivity, scenarios, flip_points
/verification   consistency_checks, provenance, confidence
/report         report_builder
/data           synthetic_company.json, seeded_decisions.json
/api            FastAPI routes, SSE/WebSocket
/ui             React app
/tests          unit and integration tests (LLM mocked)
/docs           PROGRESS.md, architecture notes
```

**Event types streamed to the UI:** `task_created`, `agent_started`, `finding_posted`, `conflict_detected`, `simulation_run`, `agent_failed`, `recovery_started`, `recovery_done`, `verification_passed`, `report_ready`.

---

## 6. SIMULATION DESIGN

A simple, explainable SaaS dynamics model over 12 to 24 monthly steps. Deterministic and reproducible (store the random seed for Monte Carlo).

- **State:** paying customers, free users, MRR, churn, infra cost, support load, cash and runway.
- **Free-plan levers:** free sign-ups per month, activation rate, free-to-paid conversion, cannibalization of existing paid users, infra cost per free user, support tickets per free user, support cost per ticket, churn change.
- **Strategies compared:**
  - **A.** Free plan with limited features
  - **B.** Free plan with usage caps
  - **C.** No free plan; improve the paid conversion funnel
- **Scenarios:** conservative / expected / optimistic (from assumption low/base/high), plus stress tests (infra cost doubles, conversion collapses, a large customer churns).
- **Outputs per scenario:** MRR, gross margin, runway, support headcount needed, infra cost, net contribution at 6, 12, and 24 months.
- **Techniques:** deterministic base calculation, Monte Carlo sampling across assumption ranges, one-at-a-time sensitivity (tornado data), and **flip-point search** (the value at which the best strategy changes).

---

## 7. FEATURE SPECIFICATION

Status labels: `[MVP-REAL]` build it, `[MVP-MOCK]` seeded/simulated, `[STRETCH]` only if time remains, `[FUTURE]` never claim as built.

**F1. Company workspace and synthetic data `[MVP-MOCK]`.** One preloaded demo company, "NimbusDesk" (fictional B2B SaaS), from `data/synthetic_company.json`: customers by plan, MRR, churn, CAC, LTV, infra cost, support headcount and ticket rates, funnel conversion, cash and runway, engineering capacity. A company overview card shows headline metrics. A "Synthetic data" badge is always visible. Data is editable JSON so disagreement between agents can be tuned.

**F2. Decision intake `[MVP-REAL]`.** Natural-language input with example chips. Parse into a structured `Decision` (type, target change, objective, constraints). Unsupported questions get a clear message listing supported decision types.

**F3. Supervisor and task decomposition `[MVP-REAL]`.** Turn the `Decision` into a task DAG (id, owner agent, inputs, dependencies, expected output schema). Activate only needed agents. Show the plan as a graph. Track status (`pending`, `running`, `done`, `failed`, `retrying`, `blocked`). Loop back on unresolved conflict or failed verification, with bounded rounds.

**F4. Specialist agent team `[MVP-REAL]`.** As in Section 4.

**F5. Shared state and agent messaging `[MVP-REAL]`.** One typed workflow state: decision, plan, findings, assumptions, conflicts, simulation runs, verification results, report draft, event log. Agents exchange structured `Finding` objects only. Checkpoint after each task so runs can resume.

**F6. Live agent activity view `[MVP-REAL]`.** Real-time DAG graph (idle, running, done, failed, recovering), streamed event feed, click-a-node to inspect that agent's finding, and an **Inject failure** control.

**F7. Conflict detection and simulation-based resolution `[MVP-REAL]`.**
Detection checks: (1) contradictory recommendations, (2) non-overlapping assumption ranges, (3) missing evidence for a key claim, (4) unresolved task dependencies.
Resolution: isolate the disputed assumption; run the simulator under each side's assumptions; compute outcome differences and which assumption drives them; if material, run a bounded rebuttal round or request more analysis; record the conflict, evidence, and resolution in the report. Unresolved disagreements stay visible.

**F8. Scenario simulation engine `[MVP-REAL]`.** As in Section 6. No LLM numbers.

**F9. Sensitivity analysis and flip-points `[MVP-REAL]`.** Tornado chart data and a plain-language flip-point statement such as "Strategy A beats C only if free-to-paid conversion stays above X%."

**F10. Assumption ledger with provenance `[MVP-REAL]`.** Table of every assumption: name, low/base/high, unit, provenance tag, source, confidence, proposing agent, whether the Skeptic challenged it. Visual cue per provenance type.

**F11. Skeptic and verification layer `[MVP-REAL]`.** Skeptic challenges unsupported or optimistic assumptions, requests evidence, downgrades confidence. Deterministic checks: unit consistency, totals and ratios tie out, every report number traces to a simulator run, every key claim has provenance, required sections present. Failure routes tasks back (bounded loops). Report includes a verification summary (passed / failed / waived with reasons).

**F12. Failure injection and recovery `[MVP-REAL]`.** Button/toggle to kill or corrupt a chosen agent mid-run (timeout, exception, invalid output). Detect via heartbeat, timeout, or schema-validation failure. Recovery: retry with backoff, then reassign to a fallback agent or degraded mode, resuming from the last checkpoint. UI shows failure, recovery, and success. The run log records every failure and recovery.

**F13. Consolidated decision report `[MVP-REAL]`.** One report with sections: (1) executive summary and recommendation with confidence, (2) current company position, (3) strategies compared with scenario table and charts, (4) conflicts and how they were resolved, (5) sensitivity tornado and flip-points, (6) assumption ledger, (7) risks, uncertainties, and what evidence would change the recommendation, (8) verification summary, (9) suggested execution plan and metrics to monitor, (10) run log. Includes the simulation disclaimer.

**F14. Human approval gate `[MVP-REAL]`.** Approve / Request changes / Reject. Approval stores a decision record (question, company snapshot, chosen strategy, assumptions, predicted metrics, date). No external action is ever triggered.

**F15. Decision history and calibration `[MVP-MOCK]`.** 3 to 4 seeded past decisions with predicted vs. actual metrics; calibration screen with per-metric error and most-wrong assumptions; new approved decisions appear as "awaiting outcome". Clearly labelled seeded demo data.

**F16. Company Intelligence Graph view `[MVP-MOCK]` / `[STRETCH]`.** `networkx`/JSON graph rendered with React Flow; nodes: plans, segments, revenue, infra, support, engineering capacity; edges are dependencies; optionally highlight nodes affected by the current decision.

**F17. Second decision type: price change `[STRETCH]`.** Same engine; parameters: price elasticity, churn response, new-customer conversion effect.

**F18. Report export (Markdown/PDF) `[STRETCH]`.**

**F19 to F21 `[FUTURE]`.** Real integrations, live outcome monitoring, auth/multi-tenancy/audit logs. Do not describe as built.

---

## 8. DATA OBJECTS AND API

**Core objects:**

```text
Decision        id, type, question, objective, constraints, created_at
Task            id, owner_agent, depends_on[], status, input_ref, output_ref, attempts
Finding         agent, task_id, claim, recommendation, assumptions[], evidence[],
                confidence, limitations[], status
Assumption      name, low, base, high, unit, provenance, source_ref, confidence,
                proposed_by, challenged_by_skeptic
Conflict        id, type, agents[], disputed_item, evidence[], resolution, simulation_ids[]
SimulationRun   id, strategy, scenario, parameters, outputs, seed
VerificationResult  check_name, status (passed|failed|waived), detail
Report          decision_id, sections, recommendation, confidence, disclaimers
DecisionRecord  decision_id, snapshot, chosen_strategy, predicted_metrics, approved_at,
                actual_metrics (nullable)
Event           ts, type, agent, payload
```

**API:**

```text
GET  /api/company                          company snapshot (synthetic)
POST /api/decisions                        submit decision, start workflow
GET  /api/decisions/{id}                   status, plan, findings
GET  /api/decisions/{id}/stream            SSE/WebSocket event stream
POST /api/decisions/{id}/inject-failure    {agent, mode: timeout|exception|bad_output}
GET  /api/decisions/{id}/report            consolidated report
POST /api/decisions/{id}/approve           approve | reject | request_changes
GET  /api/history                          decision history and calibration data
GET  /api/graph                            company dependency graph
```

**Non-functional:** reproducible simulations via stored seeds; bounded loops so every run terminates; resumable via checkpoints; full traceability of report numbers; target a full run in a few minutes at most; record a known-good run as a demo fallback; low LLM temperature.

---

## 9. STEP-BY-STEP BUILD PLAN (BUILD IN THIS ORDER)

For **every step**: implement, test, show evidence, update `docs/PROGRESS.md`, then continue. Do not skip "Done when".

### Mapping to the 9 hackathon milestones

| Hackathon milestone | Build steps |
|---|---|
| 1. Agent role design | Steps 1, 2 |
| 2. Task decomposition engine | Step 3 |
| 3. Supervisor architecture | Step 4 |
| 4. Agent communication protocol | Step 5 |
| 5. Shared state management | Step 5 |
| 6. Conflict detection and resolution | Steps 6, 7 |
| 7. Failure detection and recovery | Step 8 |
| 8. Workflow verification | Step 9 |
| 9. Final output generation | Steps 10 to 13 |

---

### Step 0. Project skeleton and environment (Day 1)

- Create the repo layout from Section 5, Python virtualenv/`pyproject.toml`, FastAPI "hello" route, test runner, lint config, `.env.example` (LLM key placeholder), `README.md`, `docs/PROGRESS.md`.
- Implement the `llm_call()` wrapper: provider-agnostic, structured output validated with Pydantic, bounded retries, low temperature, and a **mock mode** returning canned structured responses for tests.
- **Done when:** `pytest` runs, the API starts, and a mock `llm_call()` returns a validated Pydantic object.

### Step 1. Schemas and synthetic data (Day 1 to 2) *[Milestone 1: role design]*

- Define all Pydantic schemas from Sections 4 and 8 in `/state`.
- Create `data/synthetic_company.json` for NimbusDesk with realistic, internally consistent numbers (customers by plan, MRR, churn, CAC, LTV, infra cost, support staff and ticket rates, funnel conversion, cash/runway, engineering capacity). Tune it so the **CFO and Growth agents are likely to disagree** on the free-plan decision.
- Create `data/seeded_decisions.json` with 3 to 4 past decisions (predicted vs. actual).
- Write a data loader and a company-snapshot function.
- **Done when:** schemas validate sample objects, the loader returns the snapshot, and unit tests cover schema validation.

### Step 2. Agent base class and specialist agents (Day 2 to 3) *[Milestone 1]*

- Implement `BaseAgent` with: name, objective, system prompt, allowed tools, `run(task, state) -> Finding`, output validation, and a heartbeat/timeout hook.
- Implement CFO, Growth, CTO, Customer, (optional) Product, and Skeptic agents with **distinct prompts and objectives**. Tools are plain Python functions reading company data (no LLM numbers).
- Implement the **agent registry** (including placeholder entries for Ops, Market, Risk marked "not built").
- **Done when:** each agent, with the LLM mocked and with a real LLM, returns a valid `Finding` with assumptions carrying provenance tags; CFO and Growth produce different recommendations on the demo data.

### Step 3. Task decomposition engine (Day 2 to 3) *[Milestone 2]*

- Implement the decision parser (natural language to `Decision`) with a clear message for unsupported types.
- Implement the Supervisor's decomposition: `Decision` to a task DAG (ids, owners, dependencies, expected output schema), activating only the needed agents.
- Validate the DAG (no cycles, all dependencies exist).
- **Done when:** "Should we launch a free plan?" produces a valid DAG with parallelizable analysis tasks plus downstream simulation, verification, and report tasks; tests cover cycle detection.

### Step 4. Supervisor architecture and parallel execution (Day 3 to 4) *[Milestone 3]*

- Build the orchestrator (LangGraph or custom async executor): dispatch ready tasks concurrently, respect dependencies, track status, loop back with bounded rounds.
- Implement the event bus and emit all event types from Section 5.
- **Done when:** a run executes independent agent tasks **in parallel** (demonstrate with timestamps), downstream tasks wait for dependencies, and events are emitted in order.

### Step 5. Communication protocol and shared state (Day 3 to 4) *[Milestones 4 and 5]*

- Implement the typed shared workflow state (decision, plan, findings, assumptions, conflicts, simulation runs, verification results, report draft, event log).
- Enforce that agents post only validated `Finding` objects; reject malformed outputs.
- Implement **checkpointing** after each task (SQLite) and resume-from-checkpoint.
- **Done when:** killing the process mid-run and resuming continues from the last checkpoint without redoing completed tasks; invalid agent output is rejected and logged.

### Step 6. Simulation engine (Day 5) *[supports Milestone 6]*

- Implement the SaaS dynamics model, the three strategies, the three scenarios plus stress tests, Monte Carlo (stored seeds), tornado-chart sensitivity, and flip-point search.
- Function signature idea: `simulate(strategy, scenario, assumptions, company) -> SimulationRun`.
- **Done when:** results are deterministic for a fixed seed, outputs include all metrics at 6/12/24 months, the tornado data ranks assumptions by impact, and the flip-point finder returns a threshold; unit tests verify monotonicity (for example, higher conversion never lowers MRR) and reproducibility.

### Step 7. Conflict detection and simulation-based resolution (Day 5 to 6) *[Milestone 6]*

- Implement detectors: contradictory recommendations, non-overlapping assumption ranges, missing evidence, unresolved dependencies.
- Implement the resolver: isolate the disputed assumption, run the simulator for each side, compute outcome deltas and driver, trigger a bounded rebuttal round if material, record the resolution with simulation ids.
- **Done when:** on the demo data, a CFO vs. Growth conflict is **detected (not hardcoded)** and resolved with simulator evidence; the conflict record lists the disputed item, both runs, and the outcome difference; tests cover each detector.

### Step 8. Failure injection and recovery (Day 7) *[Milestone 7]*

- Implement failure detection: timeout, exception, schema-invalid output, heartbeat loss.
- Implement the recovery policy: retry with backoff, then reassign to a fallback agent or degraded mode, resume from the last checkpoint, with bounded attempts.
- Add the failure-injection hook and the `POST /inject-failure` endpoint.
- **Done when:** injecting each failure mode into any agent mid-run still yields a completed workflow; the event log shows `agent_failed`, `recovery_started`, `recovery_done`; tests cover each mode.

### Step 9. Skeptic and workflow verification (Day 7) *[Milestone 8]*

- Skeptic challenges assumptions (flag `challenged_by_skeptic`, request evidence, downgrade confidence).
- Implement deterministic verification checks: units, ratio and total tie-outs, every report number traces to a simulator run, every key claim has provenance, required sections present.
- Failed verification routes tasks back (bounded).
- **Done when:** a deliberately corrupted number in a draft report is caught by verification and routed back; the verification summary lists passed/failed/waived checks.

### Step 10. Report builder (Day 8) *[Milestone 9]*

- Build the consolidated report with all 10 sections (F13), including scenario tables, tornado data, flip-point statement, assumption ledger, conflict panel data, verification summary, risks, execution plan, metrics to monitor, and run log, plus the simulation disclaimer.
- The LLM may write explanatory prose; numbers are inserted from simulator outputs only.
- **Done when:** one end-to-end run produces a single JSON report (and a Markdown rendering) where every number traces to a simulator run or input data.

### Step 11. API and streaming (Day 8)

- Implement all endpoints from Section 8, including SSE/WebSocket event streaming, approval, history, graph.
- **Done when:** the full flow works via API calls alone (submit, stream events, fetch report, approve, fetch history).

### Step 12. Frontend: three screens (Day 8 to 10)

Keep UI effort to roughly two days. Build only:

1. **Decision Console:** company snapshot, "Synthetic data" badge, decision input with chips, live execution graph (React Flow) with node states, event feed, click-a-node inspector, **Inject failure** control.
2. **Decision Report:** recommendation with confidence, scenario table and charts (Recharts), conflict panel, tornado chart, flip-point statement, assumption ledger with provenance icons, risks, verification summary, run log, and **Approve / Request changes / Reject**.
3. **Calibration and History:** seeded predicted-vs-actual, per-metric error, most-wrong assumptions, "awaiting outcome" for new approvals, "seeded demo data" label.

Optional (stretch): company dependency graph panel with affected nodes highlighted.

- **Done when:** the whole demo flow in Section 10 runs in the browser.

### Step 13. Approval, history, and calibration (Day 8 to 9)

- Persist decision records on approval; show them in history as "awaiting outcome"; compute calibration stats from seeded data.
- **Done when:** approving a report adds a record visible on the Calibration screen.

### Step 14. Hardening, demo, and docs (Day 9 to 10)

- Record/cache a known-good run as a demo fallback; set LLM temperature low; add retries and clear error messages.
- Write the final `README.md` (setup, run, architecture diagram, what is real vs. mocked), and `docs/DEMO_SCRIPT.md`.
- Optional stretch if time: price-change decision type (F17), Markdown/PDF export (F18).
- **Done when:** all acceptance criteria in Section 11 pass on a fresh clone following the README.

**Cut order if behind schedule:** UI polish, optional agents (Product), company graph, stretch features. **Never cut:** simulation-based conflict resolution, failure recovery, or the deterministic simulator.

---

## 10. DEMO SCRIPT (about 3 minutes)

1. Open the app; show the NimbusDesk snapshot and the "Synthetic data" badge.
2. Ask: **"Should we launch a free plan?"** The supervisor's task graph appears and agents run in parallel.
3. A conflict (CFO vs. Growth) is flagged and **resolved by running both assumption sets through the simulator**.
4. Click **Inject failure** (for example, the CTO agent crashes). The supervisor detects it, retries or reassigns, and the run completes.
5. The Skeptic challenges an assumption; verification checks pass.
6. The report appears with three strategies, three scenarios, the tornado chart, and a flip-point.
7. Click **Approve**; open the Calibration screen to show seeded predicted-vs-actual results.
8. State openly: data is synthetic, assumptions are configurable, and the value is the **method** (assumption audit, conflict resolution by simulation, decision memory).

---

## 11. ACCEPTANCE CRITERIA (MVP is "done" when all are true)

1. A user can submit the free-plan question and get a final report with no manual steps.
2. At least 4 specialist agents plus a Skeptic run as separate nodes, with parallel execution visible.
3. A genuine conflict between two agents is detected and resolved using simulator runs.
4. Injecting a failure into any agent mid-run still ends in a completed report.
5. No number in the report originates from LLM text; all come from simulator outputs or input data.
6. The report contains an assumption ledger with provenance tags and a tornado chart with at least one flip-point statement.
7. Verification checks run and their results appear in the report.
8. Approval stores a decision record shown in history.
9. The Calibration screen displays seeded decisions, clearly labelled as seeded.

---

## 12. RISKS AND HOW TO HANDLE THEM

- **"Where do the numbers come from?"** They come from labelled, configurable assumptions with ranges; emphasize sensitivity analysis over accuracy claims.
- **Over-investing in UI.** Cap UI at about 2 days.
- **Fake agents.** Keep separate agent nodes with distinct prompts, tools, and structured outputs.
- **Conflict does not occur.** Give agents genuinely different objectives and seed the dataset so disagreement is likely. Never hardcode the outcome.
- **LLM flakiness during the demo.** Cache a known-good run, use low temperature, validate every output.
- **Scope creep.** Anything not in Sections 3 and 7 as MVP is a stretch goal.

---

## 13. WHAT TO DO FIRST

1. Reply with your **short implementation plan**: repo layout, whether you chose LangGraph or a custom executor (with one-paragraph justification), and the LLM provider you will assume (ask me only if you cannot proceed without it).
2. Then start **Step 0** and proceed step by step, reporting evidence after each step.

Begin.

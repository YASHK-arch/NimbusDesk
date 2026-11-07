# VentureTwin: Features and MVP Specification

> **Purpose:** Give any AI tool a complete picture of what VentureTwin does, which features exist at each stage, and what the hackathon MVP looks like on screen.
> **Companion file:** `SwarmFlow_x_VentureTwin_Hackathon_Project_Context.md` (problem statement, architecture, 10-day plan). Read that first if available; this file focuses on **features and product experience**.
> **Status labels used throughout:** `[MVP-REAL]` built and working, `[MVP-MOCK]` seeded or simulated for the demo, `[STRETCH]` only if time remains, `[FUTURE]` roadmap only, never claim as built.

---

## 1. Product in one paragraph

VentureTwin is a **decision stress-test platform for SaaS pricing and packaging decisions**. A user asks a question such as *"Should we launch a free plan?"*. A supervisor breaks it into tasks, a team of specialist AI agents analyzes it in parallel, disagreements between agents are detected and **settled by running a deterministic simulation**, and the system produces **one verified decision report** showing outcomes under multiple scenarios, which assumptions the answer depends on, and the point at which the recommendation would flip.

**It does not tell the CEO what to do.** It exposes what has to be true for a decision to work, and how confident we are that it is true.

**Pitch line:** *"An orchestration engine where agents disagree, conflicts are resolved by simulation instead of voting, no number comes from an LLM, and the system survives an agent failure mid-run."*

---

## 2. Who it is for and why they would use it

**Primary user (pitch persona):** a finance, RevOps, or strategy lead at a Series A to B SaaS company preparing a pricing or packaging decision for the founder or board.

**Secondary user:** the founder or CEO reviewing the report.

**Why not just decide alone?** The founder still decides. The product helps with three things founders do poorly alone:

1. **See second-order effects** (infra cost, support load, cannibalization) that spreadsheets usually miss.
2. **Audit assumptions** (a skeptic challenges optimistic inputs).
3. **Keep decision memory** (predicted vs. actual is recorded and compared).

**Framing to use:** a *pre-mortem and stress-test tool*, not an "AI decision maker".

**Honest limitation to state in the pitch:** the demo uses synthetic data. The value shown is the *method*: assumption audit, conflict resolution by simulation, and decision memory.

---

## 3. Feature map overview

| # | Feature area | MVP status |
|---|---|---|
| F1 | Company workspace and synthetic data | `[MVP-MOCK]` |
| F2 | Decision intake | `[MVP-REAL]` |
| F3 | Supervisor and task decomposition | `[MVP-REAL]` |
| F4 | Specialist agent team | `[MVP-REAL]` |
| F5 | Shared state and agent messaging | `[MVP-REAL]` |
| F6 | Live agent activity view | `[MVP-REAL]` |
| F7 | Conflict detection and simulation-based resolution | `[MVP-REAL]` |
| F8 | Scenario simulation engine | `[MVP-REAL]` |
| F9 | Sensitivity analysis and flip-points | `[MVP-REAL]` |
| F10 | Assumption ledger with provenance | `[MVP-REAL]` |
| F11 | Skeptic and verification layer | `[MVP-REAL]` |
| F12 | Failure injection and recovery | `[MVP-REAL]` |
| F13 | Consolidated decision report | `[MVP-REAL]` |
| F14 | Human approval gate | `[MVP-REAL]` |
| F15 | Decision history and calibration | `[MVP-MOCK]` (seeded) |
| F16 | Company Intelligence Graph view | `[MVP-MOCK]` / `[STRETCH]` |
| F17 | Second decision type (price change) | `[STRETCH]` |
| F18 | Report export (PDF/Markdown) | `[STRETCH]` |
| F19 | Real integrations (Stripe, HubSpot, GitHub, etc.) | `[FUTURE]` |
| F20 | Real outcome monitoring from live data | `[FUTURE]` |
| F21 | Auth, multi-tenancy, roles, audit logs | `[FUTURE]` |

---

## 4. Feature specifications

### F1. Company workspace and synthetic data `[MVP-MOCK]`

- One preloaded **demo company** ("NimbusDesk", a fictional B2B SaaS) loaded from `data/synthetic_company.json`.
- Contains: customers by plan, MRR, churn, CAC, LTV, infra cost, support headcount and ticket rates, funnel conversion numbers, cash and runway, engineering capacity.
- A "Company overview" card shows the headline metrics.
- A clear **"Synthetic data" badge** is visible at all times.
- Data is configurable (JSON edit) so the demo can be adjusted to create genuine disagreement between agents.

*Out of scope:* real data connectors, CSV upload (stretch only).

### F2. Decision intake `[MVP-REAL]`

- Natural-language input box with example chips: "Should we launch a free plan?", "What if we raise prices 20%?" (stretch).
- The system parses the request into a structured `Decision` object: decision type, target change, objective, constraints.
- Unsupported questions get a clear message listing supported decision types rather than a guess.

### F3. Supervisor and task decomposition `[MVP-REAL]`

- Supervisor turns the `Decision` into a **task DAG**: each task has an id, owner agent, inputs, dependencies, expected output schema.
- Only the agents required for the decision are activated.
- The plan is shown to the user as a graph before and during execution.
- Supervisor tracks task status: `pending`, `running`, `done`, `failed`, `retrying`, `blocked`.
- Supervisor decides when to loop back (conflict unresolved, verification failed), with bounded rounds.

### F4. Specialist agent team `[MVP-REAL]`

Each agent is a separate node with its own system prompt, objective, tools, and structured output.

| Agent | Objective | Tools it may use |
|---|---|---|
| Supervisor | Plan, dispatch, resolve, consolidate | DAG executor, state store |
| CFO | Protect runway and margin | Company data lookup, cost calculators |
| Growth | Maximize acquisition and conversion | Funnel data lookup |
| CTO | Feasibility and infrastructure load | Infra cost per user lookup |
| Customer | Retention and segment impact | Churn and segment data |
| Product (optional) | Define free-tier feature gating | Feature catalogue |
| Skeptic / Verifier | Challenge assumptions, check consistency | Consistency checks, ledger |

Registry lists extra agents (Ops, Market, Risk) as extensible but **not built**.

Agents deliberately have **different objectives** so disagreement emerges naturally, rather than being scripted.

### F5. Shared state and agent messaging `[MVP-REAL]`

- One typed workflow state holds: decision, plan, findings, assumptions, conflicts, simulation runs, verification results, report draft, event log.
- Agents exchange **structured `Finding` objects** (claim, recommendation, assumptions with low/base/high, evidence, confidence, limitations, status). No free-text-only messages.
- Checkpoints are saved after each task so the run can resume.

### F6. Live agent activity view `[MVP-REAL]`

- Graph of the task DAG where nodes change state in real time (idle, running, done, failed, recovering).
- Event feed streamed over WebSocket or SSE: `task_created`, `agent_started`, `finding_posted`, `conflict_detected`, `simulation_run`, `agent_failed`, `recovery_started`, `recovery_done`, `verification_passed`, `report_ready`.
- Clicking a node shows that agent's finding, assumptions, and evidence.
- Visible **"Inject failure"** control (see F12).

### F7. Conflict detection and simulation-based resolution `[MVP-REAL]`

**Detection checks:**
1. Contradictory recommendations (for example CFO "reject" vs. Growth "proceed").
2. Non-overlapping assumption ranges (for example conversion 1% to 2% vs. 4% to 6%).
3. Missing evidence for a key claim.
4. Unresolved dependency between tasks.

**Resolution flow:**
1. Isolate the specific disputed assumption or recommendation.
2. Run the simulator once with each side's assumptions.
3. Compute outcome differences and which assumption drives them.
4. If the disagreement matters, trigger a bounded rebuttal round or request more analysis.
5. Record the conflict, evidence, and resolution in the report.

**Rule:** the system never "picks a winner" by LLM preference. Resolution is based on simulation results and explicit evidence. Unresolved disagreements stay visible in the report.

### F8. Scenario simulation engine `[MVP-REAL]`

Deterministic Python (NumPy, Pandas, SciPy). No LLM-generated numbers.

- Monthly model over 12 to 24 months.
- State: paying customers, free users, MRR, churn, infra cost, support load, cash and runway.
- Free-plan levers: sign-ups per month, activation rate, free-to-paid conversion, cannibalization of existing paid users, infra cost per free user, tickets per free user, support cost per ticket, churn change.
- **Strategies compared:**
  - A. Free plan with limited features
  - B. Free plan with usage caps
  - C. No free plan, improve the paid conversion funnel
- **Scenarios:** conservative, expected, optimistic (from assumption low/base/high), plus stress tests (infra cost doubles, conversion collapses, large customer churns).
- Monte Carlo sampling across assumption ranges for outcome distributions.
- Outputs per scenario: MRR, gross margin, runway, support headcount needed, infra cost, net contribution at 6, 12, 24 months.

### F9. Sensitivity analysis and flip-points `[MVP-REAL]`

- **Tornado chart:** one-at-a-time sensitivity showing which assumptions move the outcome most.
- **Flip-point finder:** the value at which the best strategy changes, shown as a plain statement such as *"Strategy A beats C only if free-to-paid conversion stays above X%."*
- LLM may explain the result in words but cannot alter it.

### F10. Assumption ledger with provenance `[MVP-REAL]`

A table of every assumption used, with:

- name, low / base / high, unit
- **provenance tag:** `verified_data`, `external_research`, `simulated_estimate`, `ai_assumption`
- source reference
- confidence (0 to 1)
- which agent proposed it and whether the Skeptic challenged it

Visual cue: color or icon per provenance type. The ledger answers "where did this number come from?" for every figure in the report.

### F11. Skeptic and verification layer `[MVP-REAL]`

**Skeptic agent:** challenges unsupported or optimistic assumptions, requests evidence, downgrades confidence, flags missing analysis.

**Deterministic verification checks:**
- Units are consistent.
- Totals and ratios tie out.
- Every number in the report traces to a simulator run.
- Every key claim has provenance.
- Required sections are present.

If verification fails, the supervisor routes the relevant tasks back (bounded loops). The report shows a **verification summary** (passed, failed, waived, with reasons).

### F12. Failure injection and recovery `[MVP-REAL]`

- Button or toggle to **kill or corrupt a chosen agent mid-run** (timeout, exception, invalid output).
- Supervisor detects via heartbeat, timeout, or schema validation failure.
- Recovery policy: retry with backoff, then reassign to a fallback agent or degraded mode, resuming from the last checkpoint.
- The UI shows the failure, the recovery steps, and the final success.
- The run log in the report records every failure and recovery.

### F13. Consolidated decision report `[MVP-REAL]`

One page, not a collection of agent outputs. Sections:

1. Executive summary and recommendation (with confidence)
2. Current company position
3. Strategies compared (scenario table and charts)
4. Conflicts detected and how they were resolved
5. Sensitivity tornado and flip-points
6. Assumption ledger
7. Risks, uncertainties, and what evidence would change the recommendation
8. Verification summary
9. Suggested execution plan and metrics to monitor
10. Run log (agents used, failures, recoveries)

Always includes: *"Simulation outputs depend on stated assumptions and are not guaranteed outcomes."*

### F14. Human approval gate `[MVP-REAL]`

- The report ends with **Approve / Request changes / Reject**.
- Approval stores the decision record: question, company snapshot, chosen strategy, assumptions, predicted metrics, date.
- The system never triggers any external action. Execution is a suggested plan only.

### F15. Decision history and calibration `[MVP-MOCK]`

- 3 to 4 **seeded** past decisions with predicted vs. actual metrics.
- Calibration screen: prediction error per metric, which assumptions were repeatedly wrong, and a simple note on how this would adjust future priors.
- Newly approved decisions appear in the history as "awaiting outcome".
- Clearly labelled as seeded demo data. Do not present it as proof the system learns from real outcomes.

### F16. Company Intelligence Graph view `[MVP-MOCK]` / `[STRETCH]`

- `networkx` or JSON graph, rendered with React Flow.
- Nodes: plans, customers/segments, revenue, infra, support, engineering capacity. Edges: dependencies ("free users increase infra cost").
- Used for visual explanation and dependency lookup. No graph database.
- Optional: highlight the nodes affected by the current decision.

### F17. Second decision type: price change `[STRETCH]`

Same engine, different simulator parameters: price elasticity, churn response, new-customer conversion effect. Demonstrates that the engine is domain-agnostic.

### F18. Report export `[STRETCH]`

Markdown or PDF export of the final report.

### F19 to F21. Future roadmap `[FUTURE]`

Real integrations (Stripe, HubSpot, GitHub, Intercom, accounting tools), live outcome monitoring, auth and multi-tenancy, role-based access, encryption and audit logs, more decision types, learned forecast calibration with causal validation. **Do not describe these as implemented.**

---

## 5. What the MVP looks like (screens)

Three screens plus an optional graph panel. Keep UI effort to roughly two days.

### Screen 1: Decision Console

```
+--------------------------------------------------------------+
| VentureTwin      [Synthetic data: NimbusDesk]                |
+--------------------------------------------------------------+
| Company snapshot: MRR | Customers | Churn | Infra | Runway   |
+--------------------------------------------------------------+
| Ask a decision:  [ Should we launch a free plan?      ] [Run]|
|   chips: ( Free plan ) ( Price change* )   *stretch          |
+--------------------------------------------------------------+
| LIVE EXECUTION GRAPH                  | EVENT FEED           |
|                                       | 10:01 plan created   |
|   [Supervisor]                        | 10:01 CFO started    |
|     |-- [CFO] --\                     | 10:02 CTO started    |
|     |-- [Growth]-+-> [Conflict?]      | 10:03 conflict: CFO  |
|     |-- [CTO] --/      |              |       vs Growth      |
|     |-- [Customer]     v              | 10:03 simulating...  |
|                   [Simulator]         | 10:04 CTO FAILED     |
|                        |              | 10:04 retrying...    |
|                   [Skeptic/Verify]    | 10:05 verified       |
|                        |              |                      |
|                   [Report]            | [ Inject failure ]   |
+--------------------------------------------------------------+
```

Behaviors: agents light up as they run, edges show dependencies, conflicts are marked in a warning color, failures show red then recovering then green, node click opens that agent's finding.

### Screen 2: Decision Report

```
+--------------------------------------------------------------+
| Decision Report: Launch a free plan?      Status: Verified   |
+--------------------------------------------------------------+
| Recommendation: Start with Strategy B (usage caps) as a      |
| controlled experiment.       Confidence: Medium              |
+--------------------------------------------------------------+
| Scenario table:  A / B / C  x  Conservative/Expected/Optim.  |
| Chart: MRR and runway over time per strategy                 |
+--------------------------------------------------------------+
| Conflict panel: CFO vs Growth                                |
|   disputed assumption: free-to-paid conversion               |
|   resolved by simulation: outcome flips below X%             |
+--------------------------------------------------------------+
| Tornado chart: which assumptions matter most                 |
+--------------------------------------------------------------+
| Assumption ledger (provenance icons, confidence, challenged?)|
+--------------------------------------------------------------+
| Risks | What would change this | Verification summary | Log  |
+--------------------------------------------------------------+
| [ Approve ]  [ Request changes ]  [ Reject ]                 |
+--------------------------------------------------------------+
```

### Screen 3: Calibration and History

```
+--------------------------------------------------------------+
| Decision history                                             |
| 1. Raised Pro plan price  predicted +6% MRR  actual +3%      |
| 2. Hired 2 support staff  predicted -10% tickets  actual -4% |
| 3. Marketing +30%         predicted +12% leads  actual +9%   |
| 4. Free plan (this run)   status: awaiting outcome           |
+--------------------------------------------------------------+
| Calibration: avg error per metric | most-wrong assumptions   |
| Note: seeded demo data                                       |
+--------------------------------------------------------------+
```

### Optional panel: Company graph

Interactive dependency graph; affected nodes highlighted when a decision runs.

---

## 6. End-to-end user flow (MVP)

1. Open app, see the demo company snapshot.
2. Type "Should we launch a free plan?" and press Run.
3. See the supervisor's task DAG appear; agents run in parallel.
4. See a conflict flagged (CFO vs. Growth) and resolved by running the simulator.
5. Optionally click **Inject failure**; watch detection, retry or reassign, and completion.
6. Skeptic challenges an assumption; verification checks pass or loop back.
7. Report opens with scenarios, tornado chart, flip-point, assumption ledger.
8. User clicks **Approve**; the decision is saved to history as "awaiting outcome".
9. Open Calibration to see seeded predicted-vs-actual results.

---

## 7. Suggested core data objects

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

---

## 8. Suggested API surface

```text
GET  /api/company                      company snapshot (synthetic)
POST /api/decisions                    submit decision, start workflow
GET  /api/decisions/{id}               status, plan, findings
GET  /api/decisions/{id}/stream        SSE or WebSocket event stream
POST /api/decisions/{id}/inject-failure   {agent, mode: timeout|exception|bad_output}
GET  /api/decisions/{id}/report        consolidated report
POST /api/decisions/{id}/approve       approve, reject, or request changes
GET  /api/history                      decision history and calibration data
GET  /api/graph                        company dependency graph
```

---

## 9. Non-functional requirements (MVP level)

- **Determinism:** simulator runs are reproducible via stored seeds.
- **Bounded loops:** maximum rebuttal and verification rounds so a run always terminates.
- **Resumability:** checkpoint after each task; failure must not discard completed work.
- **Traceability:** every report number links to a simulation run and every assumption to provenance.
- **Latency target:** full run in a few minutes at most; cache or record a known-good run as demo fallback.
- **Model abstraction:** one `llm_call()` wrapper so the provider is swappable; low temperature for agents.
- **Honesty:** UI and report state that outputs are simulations on stated assumptions.

---

## 10. Acceptance criteria for the MVP

The MVP is "done" when all of these are demonstrably true:

1. A user can submit the free-plan question and get a final report with no manual steps.
2. At least 4 specialist agents plus a Skeptic run as separate nodes, with parallel execution visible.
3. A genuine conflict between two agents is detected and resolved using simulator runs.
4. Injecting a failure into any agent mid-run still ends in a completed report.
5. No number in the report originates from LLM text; all come from simulator outputs or the input data.
6. The report contains an assumption ledger with provenance tags and a tornado chart with at least one flip-point statement.
7. Verification checks run and their results appear in the report.
8. Approval stores a decision record shown in history.
9. Calibration screen displays seeded decisions, clearly labelled as seeded.

---

## 11. Explicit non-goals for the MVP

- Real third-party integrations or live data
- Authentication, multi-user, roles
- Neo4j, Redis, pgvector, or object storage
- More than 6 agents or more than 2 decision types
- Autonomous execution of any business action
- Claims of forecast accuracy or guaranteed outcomes
- Real monitoring of live post-decision metrics

---

## 12. Differentiators to keep visible in the demo

1. LLMs never output numbers; a deterministic simulator does.
2. Conflicts are resolved by simulation, not voting.
3. Live failure injection with recovery.
4. Assumption ledger with provenance.
5. Tornado chart and flip-points.
6. Prediction-vs-actual calibration (seeded).

If time is short, protect 1, 2, and 3. Cut UI polish and optional agents first.

---

## 13. Instructions for an AI assistant using this file

1. Treat the status labels as binding: never describe `[STRETCH]` or `[FUTURE]` items as implemented.
2. Keep orchestration real: separate agent nodes with distinct prompts, tools, and structured outputs.
3. Never let an LLM generate numerical outcomes; route all numbers through the simulator.
4. Do not invent company data, results, or integrations; label synthetic data clearly.
5. Prefer the simplest implementation that satisfies the acceptance criteria in Section 10.
6. When something is ambiguous (team size, LLM provider, framework choice), ask one short question before proceeding.
7. Suggested first tasks: define the Pydantic schemas (Section 7), the supervisor DAG, the parallel dispatcher with failure hooks, the simulator, the conflict detector and resolver, then the synthetic dataset, report builder, and UI.

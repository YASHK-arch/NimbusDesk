# SwarmFlow x VentureTwin: Hackathon Project Context

*Paste this whole document into any AI tool as the first message. It contains everything needed to continue the project without the earlier chat.*

---

## 0. How to use this document (instructions for the AI assistant)

You are helping a team build a 10-day hackathon project. Act as a product architect, senior Python engineer, and multi-agent systems engineer.

Rules:

1. Treat this document as the source of truth. Do not drift from the scope in Section 4.
2. Real multi-agent orchestration is mandatory. Do not simulate agents with a single LLM call.
3. LLMs never produce final numbers. Numbers come from deterministic code (NumPy / Monte Carlo).
4. Do not invent data, capabilities, or results. Label everything as *implemented*, *mocked*, or *planned*.
5. Prefer the simplest thing that makes the demo work. Avoid unnecessary infrastructure.
6. When giving code, make it runnable, async where relevant, and modular (one file or module per concern).
7. If something is unclear (team size, LLM provider, deadlines), ask one short question before proceeding.

---

## 1. The hackathon problem statement (SwarmFlow)

**SwarmFlow: Multi-Agent Task Coordination Engine.** Build an intelligent multi-agent orchestration platform where specialized AI agents collaborate on complex tasks. The system must automatically divide tasks, assign responsibilities, share progress, resolve conflicting decisions, and recover from failures through a centralized supervisor agent. It must produce one verified, consolidated final deliverable.

**Prerequisites:** Python, LLMs, multi-agent systems, LangGraph, async programming, API integration, agent orchestration.

**The 9 milestones judges will score against:**

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

**Time limit: 10 days.**

---

## 2. Our chosen idea: VentureTwin

**VentureTwin is an operational digital twin and AI flight simulator for SaaS CEOs.** A CEO asks a business question such as *"Should we launch a free plan?"* A supervisor decomposes it, a virtual executive board of specialized agents analyzes it in parallel, conflicts are detected and resolved, a deterministic simulator models the consequences, and one verified decision report is produced.

VentureTwin is the **use case**. SwarmFlow's orchestration engine is the **star**. In the pitch, lead with the orchestration engine and show SaaS decision-making as the proving ground.

**One-line pitch:** *"An orchestration engine where agents disagree, conflicts are settled by simulation instead of voting, nothing numeric comes from an LLM, and the system survives agent failure mid-run."*

---

## 3. What makes it unique (the differentiators)

The concept "virtual C-suite of AI agents" is common. The mechanisms below are what set us apart. Priority is in order; if time is short, the top three are non-negotiable.

1. **LLMs never output numbers.** Agents output structured *assumptions with ranges* (for example, free-to-paid conversion 2% to 5%). A deterministic simulator computes outcomes.
2. **Conflicts are resolved by simulation, not voting.** When agents disagree (for example, CFO vs. Growth), the conflict detector identifies the specific differing assumption or recommendation. Both parameter sets are run through the simulator, and sensitivity analysis shows which assumption drives the outcome.
3. **Live chaos / failure injection.** A demo button kills or breaks an agent mid-run. The supervisor detects it, retries or reassigns from a checkpoint, and the workflow still completes.
4. **Assumption ledger with provenance.** Every claim is tagged: `verified_data`, `external_research`, `simulated_estimate`, or `ai_assumption`, with a confidence level.
5. **Sensitivity (tornado) chart and flip-points.** Example: "the recommendation flips if conversion falls below 1.8%."
6. **Prediction-vs-actual calibration screen** (seeded with past decisions) to show the system learns.

---

## 4. Scope for 10 days

### Must be real (implemented)

- Supervisor agent with task decomposition into a dependency graph (DAG)
- 5 to 6 specialist agents running in parallel (asyncio / LangGraph), each with a distinct prompt, objective, tools, and structured output
- Shared workflow state with a structured message protocol
- Conflict detection (rule-based plus LLM-assisted) and simulation-based resolution
- Real injected failure with retry / reassign / checkpoint recovery
- Skeptic / verifier agent plus numerical consistency checks
- Deterministic simulator (NumPy, Monte Carlo, sensitivity analysis)
- One consolidated decision report
- Live agent activity view

### Mocked or seeded (state this openly in the demo)

- Company data: one realistic **synthetic SaaS company dataset** (CSV/JSON). No Stripe, HubSpot, GitHub, etc.
- Company Intelligence Graph: `networkx` or JSON graph, used for visualization and dependency lookup only
- Outcome Intelligence: 3 to 4 seeded past decisions with predicted vs. actual values, one calibration screen
- Elasticities and conversion ranges: configurable assumptions, not claims of accuracy

### Explicitly out of scope

Neo4j, Redis, pgvector, object storage, real third-party integrations, auth and multi-tenancy, real-time monitoring of live metrics, more than 6 agents, more than 2 decision types.

### Decisions to support

- **Primary (deep):** "Should we launch a free plan?"
- **Optional if time permits:** "What if we cut/raise price by X%?"

---

## 5. Agents

| Agent | Objective (deliberately different so real disagreement emerges) | Typical output |
| --- | --- | --- |
| **Supervisor** | Decompose request, build DAG, dispatch, monitor, resolve conflicts, consolidate | Task plan, final report |
| **CFO** | Protect runway and margin | Cost/revenue assumptions, risk flags |
| **Growth (CMO)** | Maximize acquisition and conversion | Funnel assumptions, upside estimates |
| **CTO** | Feasibility and infrastructure load | Capacity limits, infra cost per free user |
| **Customer** | Retention and segment impact | Churn/cannibalization assumptions |
| **Product (optional)** | Feature gating for the free tier | Feature split proposal |
| **Skeptic / Verifier** | Challenge unsupported assumptions, check consistency | Challenges, missing evidence, confidence downgrades |

Keep an **agent registry** so extra agents (Ops, Market, Risk) can be listed as extensible but not built.

**Every agent returns a structured `Finding`** (Pydantic), never free text only:

```python
class Finding(BaseModel):
    agent: str
    task_id: str
    claim: str
    recommendation: str            # e.g. "proceed", "proceed_with_limits", "reject"
    assumptions: list[Assumption]  # name, low, base, high, unit
    evidence: list[Evidence]       # source_type, source_ref, snippet
    confidence: float              # 0..1
    limitations: list[str]
    status: str                    # ok | failed | needs_more_info
```

```python
class Assumption(BaseModel):
    name: str                      # e.g. "free_to_paid_conversion"
    low: float
    base: float
    high: float
    unit: str
    provenance: Literal["verified_data","external_research","simulated_estimate","ai_assumption"]
```

---

## 6. Architecture

**Stack (simplified):**

- Backend: Python, FastAPI, Pydantic, asyncio
- Orchestration: LangGraph (or custom async DAG executor if faster to control)
- LLM: any provider; wrap behind one `llm_call()` interface so it is swappable
- State: LangGraph state plus SQLite (or Postgres) for decision records and checkpoints
- Simulation: NumPy, Pandas, SciPy
- Graph: networkx, rendered in the frontend
- Frontend: React plus Tailwind, React Flow (agent/task graph), Recharts (scenarios, tornado chart). Keep it to two or three screens.
- Streaming: WebSocket or SSE for live agent events

**Modules (one folder each):**

```
/orchestrator   supervisor, dag, dispatcher, registry, checkpointing, recovery
/agents         base_agent, cfo, growth, cto, customer, product, skeptic
/state          schemas (Finding, Assumption, Task, Conflict), shared_state, event_bus
/conflict       detector, resolver (simulation-backed)
/simulation     saas_model, monte_carlo, sensitivity, scenarios
/verification   consistency_checks, provenance, confidence
/report         report_builder
/data           synthetic_company.json, seeded_decisions.json
/api            FastAPI routes, websocket
/ui             React app
```

**Event types streamed to the UI:** `task_created`, `agent_started`, `finding_posted`, `conflict_detected`, `simulation_run`, `agent_failed`, `recovery_started`, `recovery_done`, `verification_passed`, `report_ready`.

---

## 7. Workflow (maps to the 9 milestones)

1. **Intake:** CEO submits a natural-language decision.
2. **Decomposition (M2, M3):** Supervisor produces a DAG of tasks with dependencies and required agents.
3. **Parallel execution (M1, M4):** Independent tasks run concurrently, each agent posting a structured `Finding` to shared state (M5).
4. **Conflict detection (M6):** Detector flags (a) contradictory recommendations, (b) assumption ranges that do not overlap, (c) missing evidence, (d) unresolved dependencies.
5. **Simulation-based resolution (M6):** For each conflict, run the simulator under each side's assumptions. Compute outcome differences and sensitivity. If still ambiguous, request additional analysis or a targeted agent rebuttal round (capped at N rounds).
6. **Failure handling (M7):** Heartbeat / timeout / invalid-output detection. Policy: retry with backoff, then reassign to a fallback agent or degraded mode, resuming from the last checkpoint. Failures are logged and shown.
7. **Verification (M8):** Skeptic challenges conclusions. Deterministic checks: unit consistency, sums and ratios tie out, every number in the report traces to simulator output, every claim has provenance. If verification fails, send back to the relevant tasks (bounded loop).
8. **Final output (M9):** One consolidated decision report.
9. **Approval and learning:** CEO approves (human in the loop). The decision and predictions are stored. A calibration view compares predicted vs. actual for seeded past decisions.

---

## 8. Simulation design

A simple, explainable SaaS dynamics model over about 12 to 24 months, monthly steps.

**State:** paying customers, free users, MRR, churn, infra cost, support load, cash/runway.

**Free-plan levers (examples):** free sign-ups per month, activation rate, free-to-paid conversion, cannibalization of existing paid users, infra cost per free user, support tickets per free user, support cost per ticket, churn change.

**Outputs per scenario:** MRR, gross margin, runway, support headcount needed, infra cost, net contribution at 6/12/24 months.

**Scenarios:** Conservative / Expected / Optimistic (from assumption low/base/high), plus stress tests (infra cost doubles, conversion collapses, a large customer churns).

**Strategies compared (free-plan case):**

A. Free plan with limited features B. Free plan with usage caps C. No free plan; improve the paid conversion funnel

**Techniques:** deterministic base calculation, Monte Carlo sampling across assumption ranges, one-at-a-time sensitivity (tornado), and flip-point search (the value at which the best strategy changes).

The LLM may *explain* results but must not alter them.

---

## 9. Consolidated decision report (final deliverable)

1. Executive summary and recommendation
2. Current company position (from synthetic data)
3. Strategies compared with scenario table and charts
4. Conflicts detected and how they were resolved (with simulation evidence)
5. Sensitivity tornado and flip-points
6. Assumption ledger (provenance and confidence)
7. Risks, uncertainties, and what evidence would change the recommendation
8. Verification summary (checks passed, issues, Skeptic's challenges)
9. Suggested execution plan and metrics to monitor
10. Run log: agents used, failures and recoveries

Always include the disclaimer that outputs are simulations based on stated assumptions, not guaranteed outcomes.

---

## 10. UI (keep minimal)

Three screens only:

1. **Decision console:** input box, live DAG / agent graph (agents light up, edges show dependencies), event feed, **"Inject failure" button**.
2. **Report page:** scenarios, tornado chart, conflict resolution panel, assumption ledger, verification status.
3. **Calibration page:** seeded past decisions, predicted vs. actual, assumption accuracy.

Optional small panel: company graph visualization.

---

## 11. Demo script (about 3 minutes)

1. Ask: "Should we launch a free plan?" The supervisor's task graph appears; agents run in parallel.
2. A conflict is flagged (CFO vs. Growth). It is resolved by running both assumption sets through the simulator.
3. Click **Inject failure** (for example, the CTO agent crashes). The supervisor detects it, retries or reassigns, and the run completes.
4. The Skeptic challenges an assumption; the verifier checks pass.
5. The final report appears with three scenarios, a tornado chart, and a flip-point.
6. Show the calibration screen for past decisions. State clearly that data is synthetic and assumptions are configurable.

---

## 12. 10-day plan

| Days | Focus |
| --- | --- |
| 1-2 | Schemas, shared state, supervisor and DAG, synthetic dataset, LLM wrapper |
| 3-4 | Agents, parallel execution, event streaming |
| 5-6 | Simulator (deterministic, Monte Carlo, sensitivity), conflict detection and resolution |
| 7 | Failure injection and recovery, Skeptic, verification checks |
| 8 | Report builder, calibration screen with seeded data |
| 9-10 | UI polish, demo rehearsal, README, buffer |

**Rule:** if behind schedule, cut UI polish and optional agents first; never cut conflict resolution, failure recovery, or the simulator.

---

## 13. Risks and mitigations

- **"Where do the numbers come from?"** They come from labeled, configurable assumptions with ranges. Emphasize sensitivity analysis over accuracy claims.
- **Over-investing in UI.** Cap UI effort at about 2 days total.
- **Fake agents.** Keep separate agent nodes with distinct prompts, tools, and structured outputs.
- **Conflict not actually occurring.** Give agents genuinely different objectives and seed the dataset so disagreement is likely. Do not hardcode the outcome.
- **LLM flakiness during the demo.** Cache or record a known-good run as a fallback, and use temperature 0 where possible.
- **Scope creep.** Anything not in Section 4 is a stretch goal.

---

## 14. Open questions (answer these to the assistant when relevant)

- Team size and who is stronger at frontend vs. backend
- Chosen LLM provider and API budget
- Whether judges weigh technical depth or demo polish more
- LangGraph vs. a custom async executor

---

## 15. Suggested first prompts to the AI assistant

- "Generate the Pydantic schemas for Finding, Assumption, Task, Conflict, and WorkflowState."
- "Design the supervisor's decomposition prompt and the DAG data structure for the free-plan decision."
- "Write the async parallel dispatcher with timeout, retry, checkpoint, and failure-injection hooks."
- "Write the SaaS simulator with Monte Carlo and a tornado-chart sensitivity function."
- "Implement the conflict detector and simulation-backed resolver."
- "Create the synthetic company dataset JSON and the 4 seeded past decisions."

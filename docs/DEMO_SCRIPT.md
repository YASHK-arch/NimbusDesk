# VentureTwin Hackathon Live Demo Script (3-Minute Walkthrough)

> **Hackathon:** SwarmFlow: Multi-Agent Task Coordination Engine  
> **Pitch Line:** *"An orchestration engine where agents disagree, conflicts are resolved by simulation instead of voting, no number comes from an LLM, and the system survives an agent failure mid-run."*  
> **Judge Persona:** Finance/RevOps/Strategy Lead stress-testing pricing decisions for the Board/CEO.

---

## Act 1: The Intake & The Problem (0:00 - 0:40)

1. **Open Application:** Navigate to `http://localhost:8000/` (or launch via `uvicorn api.app:app`).
2. **Point to Header Badge:**
   - *"Notice our prominent amber badge: `Synthetic Data: NimbusDesk`. We are honest about our proving ground: this is a realistic Series A B2B support SaaS with $144k MRR, 995 customers, and 12.6 months of runway."*
3. **The Executive Dilemma:**
   - *"The CEO asks: 'Should we launch a free plan?' The Growth team wants virality. The CFO fears runway collapse and margin destruction. Spreadsheets miss second-order effects like AWS connection limits and support saturation."*
4. **Click Submit:** Click the quick chip **"Should we launch a free plan?"** and press **Stress-Test**.

---

## Act 2: Multi-Agent Parallelism & Chaos Injection (0:40 - 1:20)

1. **DAG Graph Lights Up:**
   - *"The Supervisor autonomously decomposes the decision into a 10-node task DAG. Notice the 5 specialist agents (CFO, Growth, CTO, Customer, Product) running in parallel with overlapping timestamps."*
2. **Inject Live Chaos (Milestone 7):**
   - Click the **💥 Crash** button under Chaos Injection targeting the **CTO Agent**.
   - *"Watch the live event feed on the right: `agent_failed` is detected immediately by the supervisor. Instead of crashing the workflow, the engine triggers exponential backoff and activates our degraded fallback policy, resuming from our SQLite checkpoint."*
   - *"The CTO node turns amber, then green as recovery completes."*
3. **Inspect an Agent Finding:**
   - Click the **Growth** node to open the inspector drawer:
   - *"Each agent returns a typed Pydantic Finding with explicit low/base/high bounds and provenance tags. Notice: no agent outputs final financial figures; they output structured assumptions."*

---

## Act 3: Conflict Resolution by Simulation (1:20 - 2:05)

1. **Conflict Detected:**
   - *"The conflict detector flags an authentic disagreement: Growth predicts 3.5%-6.5% conversion, while the CFO estimates only 1.0%-2.2%, warning of Starter tier cannibalization."*
2. **Hard Rule R3 Adherence:**
   - *"How do most agent systems resolve this? They ask an LLM to vote or pick a winner. VentureTwin never votes. We run both sets of assumptions through a deterministic 24-month SaaS dynamics model."*
   - Point to `conflict_detected` and `simulation_run` events in the stream.

---

## Act 4: The Verified Decision Report (2:05 - 2:40)

1. **Open Decision Report:** Click **View Final Report**.
2. **Recommendation & Scenario Matrix:**
   - *"The system recommends Strategy B (Usage Caps) as a controlled 90-day experiment. The scenario table compares Strategy A, B, and C under conservative, expected, and optimistic scenarios."*
3. **The Flip-Point (The 'Aha!' Moment):**
   - Read the amber flip-point card:
   - *"Strategy B beats Strategy C only if free-to-paid conversion stays above 1.85%."*
   - *"This tells the CEO exactly what has to be true for the decision to work."*
4. **Tornado Sensitivity & Assumption Ledger:**
   - Show the Tornado chart ranking conversion as the top swing driver (±$38k swing).
   - Point to the Assumption Ledger:
   - *"Every number traces to a simulator run (Rule R4). Notice the Skeptic challenged Growth's 4.5% conversion and downgraded confidence."*

---

## Act 5: Human in the Loop & Calibration Memory (2:40 - 3:00)

1. **Human Approval Gate (Rule R5):**
   - *"The system never triggers external actions autonomously. We click **Approve Decision**."*
2. **Calibration Screen:** Switch to the **Calibration & History** tab:
   - *"Our approved decision is now saved as 'Awaiting Outcome'. Below it, our seeded historical decisions compare predicted vs. actual metrics, calculating an average model error of ±6.6% and exposing repeatedly wrong assumptions."*
3. **Closing Punchline:**
   - *"That is VentureTwin: An orchestration engine where agents disagree, conflicts are resolved by simulation instead of voting, no number comes from an LLM, and the system survives an agent crash mid-run."*

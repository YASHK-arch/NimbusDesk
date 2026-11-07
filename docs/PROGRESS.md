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
| **Step 1** | Schemas & Synthetic Data (`data/synthetic_company.json`, seeded decisions) | PENDING | Schemas validate, data loader snapshots NimbusDesk |
| **Step 2** | Agent Base Class & Specialists (CFO, Growth, CTO, Customer, Skeptic, Registry) | PENDING | Distinct prompts, tools, structured findings with provenance |
| **Step 3** | Task Decomposition Engine (NLP -> Decision -> Task DAG) | PENDING | Cycle detection, parallelizable tasks for free-plan question |
| **Step 4** | Supervisor Architecture & Parallel Execution | PENDING | Concurrent execution with timestamps, dependencies respected |
| **Step 5** | Communication Protocol & Shared State (SQLite Checkpoints) | PENDING | Kill/resume mid-run without redoing work, malformed outputs rejected |
| **Step 6** | Deterministic SaaS Simulation Engine (Monte Carlo, Tornado, Flip-Points) | PENDING | Reproducible seeds, 6/12/24mo metrics, flip-point search |
| **Step 7** | Conflict Detection & Simulation-Based Resolution | PENDING | CFO vs Growth conflict detected, resolved with simulation delta |
| **Step 8** | Failure Injection & Recovery (Timeout, Exception, Corrupt Output) | PENDING | Inject failure mid-run, checkpoint recovery, run completes |
| **Step 9** | Skeptic & Deterministic Workflow Verification | PENDING | Corrupted numbers caught and routed back, verification summary |
| **Step 10** | Consolidated Decision Report Builder (JSON + Markdown) | PENDING | 10 sections, all numbers traced to simulator or synthetic data |
| **Step 11** | API Endpoints & SSE Streaming | PENDING | Full API flow works (submit, stream, report, approve, history) |
| **Step 12** | Frontend: 3 Screens (Console, Report, Calibration) | PENDING | Live DAG execution, failure injection button, tornado charts |
| **Step 13** | Human Approval Gate, History & Calibration Screen | PENDING | Human approval persists record, calibration stats computed |
| **Step 14** | Hardening, Demo Fallback Cache & Documentation | PENDING | All acceptance criteria pass on clean clone |

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

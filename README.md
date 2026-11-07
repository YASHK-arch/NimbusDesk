# VentureTwin 🚀
### SwarmFlow: Multi-Agent Task Coordination Engine for SaaS Decision Stress-Testing

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg?style=flat)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Hackathon Track:** SwarmFlow: Multi-Agent Task Coordination Engine  
> **Pitch Persona:** Finance, RevOps, or Strategy leads at Series A/B SaaS companies stress-testing pricing & packaging decisions before board meetings.  
> **Pitch Line:** *"An orchestration engine where agents disagree, conflicts are resolved by simulation instead of voting, no number comes from an LLM, and the system survives an agent failure mid-run."*

---

## 🌟 Core Differentiators

1. **LLMs Never Output Numbers:** Agents output structured qualitative claims and assumption ranges (`low`, `base`, `high`). All financial outcomes, MRR projections, runway, and churn figures are computed by a deterministic Python simulator (`NumPy`, `SciPy`, Monte Carlo).
2. **Simulation-Based Conflict Resolution:** When agents disagree (e.g. CFO warns of margin collapse vs. Growth projects virality), conflicts are detected and resolved by running both sides through the dynamics simulator—never by arbitrary voting or LLM preference.
3. **Live Chaos & Fault Recovery:** Mid-run chaos injection (timeout, unhandled exception, corrupt schema). The supervisor detects the fault, activates backoff retry or reassigns to fallback, resuming from SQLite checkpoints without losing completed tasks.
4. **Assumption Ledger & Provenance:** Every assumption traces back to a verified provenance tag (`verified_data`, `external_research`, `simulated_estimate`, `ai_assumption`).
5. **Sensitivity Analysis & Flip-Points:** Tornado sensitivity rankings and plain-language threshold conditions (e.g. *"Strategy A beats C only if free-to-paid conversion stays above 1.8%"*).
6. **Decision Memory & Calibration:** Decision records persist upon human approval, tracking predicted vs. actual outcomes on seeded calibration datasets.

---

## 🏗 Repository Layout

```text
├── orchestrator/   # Supervisor, Task DAG, Dispatcher, Agent Registry, Checkpoints, Recovery
├── agents/         # BaseAgent, CFO, Growth, CTO, Customer, Product, Skeptic, LLM wrapper
├── state/          # Pydantic v2 schemas (Decision, Task, Finding, Assumption, Conflict, State)
├── conflict/       # Rule-based & LLM conflict detector, simulation-backed resolver
├── simulation/     # SaaS dynamics model, Monte Carlo, Tornado sensitivity, Flip-point search
├── verification/   # Deterministic unit/ratio checks, provenance validation, Skeptic challenges
├── report/         # Consolidated decision report generator (JSON & Markdown)
├── data/           # Synthetic company dataset (NimbusDesk), seeded past decisions
├── api/            # FastAPI routes, SSE / WebSocket live event streaming
├── ui/             # React + TypeScript + Tailwind + React Flow + Recharts console
├── tests/          # Pytest unit and integration test suite (deterministic LLM mocks)
└── docs/           # PROGRESS.md, architecture notes, DEMO_SCRIPT.md
```

---

## 🚀 Quickstart & Verification

### 1. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# or pip install -r pyproject.toml
```

### 2. Configure Environment
```bash
cp .env.example .env
# By default, LLM_MOCK_MODE=true runs 100% deterministically and offline without API keys.
```

### 3. Run Test Suite
```bash
.venv/bin/pytest tests/ -v
```

### 4. Launch Backend API
```bash
.venv/bin/uvicorn api.app:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for the interactive OpenAPI documentation.

---

## 📜 Working Agreement & Hard Rules
- **R1. Real Orchestration:** Every agent is a separate node with independent system prompts, tools, and Pydantic outputs.
- **R2. Deterministic Numbers:** LLMs never emit final numbers. The simulator computes all financial metrics.
- **R3. Evidence-Driven Conflicts:** Disagreements are settled by parametric simulation.
- **R4. Complete Provenance:** All report metrics trace to simulator runs or synthetic company inputs.
- **R5. Human In The Loop:** Never executes external business actions; approval requires explicit human action.
- **R6. Honest Disclaimers:** All results state they are simulations on stated assumptions; synthetic data badge is always visible.

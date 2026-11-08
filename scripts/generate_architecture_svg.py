import os

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 960" width="100%" height="100%" style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="blueCard" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#172554"/>
    </linearGradient>
    <linearGradient id="tealCard" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#134e4a"/>
      <stop offset="100%" stop-color="#042f2e"/>
    </linearGradient>
    <linearGradient id="purpleCard" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b0764"/>
      <stop offset="100%" stop-color="#2e1065"/>
    </linearGradient>
    <linearGradient id="emeraldCard" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#064e3b"/>
      <stop offset="100%" stop-color="#022c22"/>
    </linearGradient>
    <linearGradient id="amberCard" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#78350f"/>
      <stop offset="100%" stop-color="#451a03"/>
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000000" flood-opacity="0.4"/>
    </filter>
    <marker id="arrowBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8"/>
    </marker>
    <marker id="arrowTeal" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2dd4bf"/>
    </marker>
    <marker id="arrowPurple" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#c084fc"/>
    </marker>
  </defs>

  <!-- Canvas Border -->
  <rect x="15" y="15" width="1370" height="930" rx="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>

  <!-- Top Header Title Block -->
  <g transform="translate(40, 35)">
    <rect x="0" y="0" width="1320" height="85" rx="14" fill="url(#headerGrad)" stroke="#334155" stroke-width="1.5" filter="url(#cardShadow)"/>
    
    <circle cx="45" cy="42" r="22" fill="#2563eb" opacity="0.9"/>
    <path d="M 35 48 L 45 32 L 55 48 Z" fill="#ffffff"/>
    <path d="M 40 44 L 50 44" stroke="#2563eb" stroke-width="2"/>

    <text x="80" y="38" fill="#f8fafc" font-size="22" font-weight="800" letter-spacing="-0.5">VentureTwin : SwarmFlow System Architecture</text>
    <text x="80" y="62" fill="#94a3b8" font-size="13" font-weight="400">Autonomous Multi-Agent Coordination Engine for SaaS Pricing &amp; Freemium Stress-Testing</text>

    <!-- Badges on Header -->
    <rect x="860" y="26" width="140" height="32" rx="16" fill="#1e293b" stroke="#38bdf8" stroke-width="1.2"/>
    <text x="930" y="47" fill="#38bdf8" font-size="11" font-weight="700" text-anchor="middle">Single Port: 8000</text>

    <rect x="1015" y="26" width="145" height="32" rx="16" fill="#1e293b" stroke="#2dd4bf" stroke-width="1.2"/>
    <text x="1087" y="47" fill="#2dd4bf" font-size="11" font-weight="700" text-anchor="middle">No LLM Numbers (R2)</text>

    <rect x="1175" y="26" width="130" height="32" rx="16" fill="#1e293b" stroke="#f59e0b" stroke-width="1.2"/>
    <text x="1240" y="47" fill="#f59e0b" font-size="11" font-weight="700" text-anchor="middle">Human Gate (R5)</text>
  </g>

  <!-- LAYER 1: Frontend Presentation Layer (React 18 + TS) -->
  <g transform="translate(40, 140)">
    <rect x="0" y="0" width="1320" height="150" rx="14" fill="#1e293b" stroke="#3b82f6" stroke-width="1.5" filter="url(#cardShadow)"/>
    <rect x="0" y="0" width="1320" height="32" rx="14" fill="#2563eb" fill-opacity="0.25"/>
    <text x="20" y="22" fill="#60a5fa" font-size="12" font-weight="700" letter-spacing="1">LAYER 1: USER PRESENTATION &amp; WORKSPACE (REACT 18 + TAILWIND CSS)</text>

    <!-- Sub-box 1: 3-Column Simulation Workspace -->
    <g transform="translate(20, 44)">
      <rect x="0" y="0" width="460" height="90" rx="10" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="16" y="24" fill="#f1f5f9" font-size="13" font-weight="700">Interactive Simulation Workspace</text>
      <text x="16" y="46" fill="#94a3b8" font-size="11">• Left: Drivers Panel (12 parameters, dynamic bounds, distributions)</text>
      <text x="16" y="64" fill="#94a3b8" font-size="11">• Center: Simulation Curves, Scenario Groups, Horizon Selector</text>
      <text x="16" y="82" fill="#94a3b8" font-size="11">• Right: Grounded AI Analyst Chat + Synthetic Intel Feed</text>
    </g>

    <!-- Sub-box 2: Single-Purpose Deep Modals -->
    <g transform="translate(500, 44)">
      <rect x="0" y="0" width="520" height="90" rx="10" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="16" y="24" fill="#f1f5f9" font-size="13" font-weight="700">Dedicated Focused Tool Modals (No Toolbar Reduplication)</text>
      <text x="16" y="46" fill="#94a3b8" font-size="11">• New Simulation Dialog (4 Pre-calibrated Presets &amp; Inquiry Prompt)</text>
      <text x="16" y="64" fill="#94a3b8" font-size="11">• Monte Carlo Engine (150–1,000 Iterations, Histograms, Percentiles)</text>
      <text x="16" y="82" fill="#94a3b8" font-size="11">• What-If Sandbox (Real-Time Driver Overrides &amp; Instant Re-Sim)</text>
    </g>

    <!-- Sub-box 3: Executive Gates & Audits -->
    <g transform="translate(1040, 44)">
      <rect x="0" y="0" width="260" height="90" rx="10" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="16" y="24" fill="#f1f5f9" font-size="13" font-weight="700">Governance &amp; Review</text>
      <text x="16" y="46" fill="#94a3b8" font-size="11">• Executive Report &amp; Approval Gate</text>
      <text x="16" y="64" fill="#94a3b8" font-size="11">• Live DAG &amp; Chaos Injection</text>
      <text x="16" y="82" fill="#94a3b8" font-size="11">• 6 Deterministic Verifier Checks</text>
    </g>
  </g>

  <!-- Arrow L1 -> L2 -->
  <line x1="700" y1="290" x2="700" y2="310" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4 4" marker-end="url(#arrowBlue)"/>

  <!-- LAYER 2: API Gateway & Static Mounting (FastAPI / Uvicorn) -->
  <g transform="translate(40, 310)">
    <rect x="0" y="0" width="1320" height="100" rx="14" fill="#1e293b" stroke="#0d9488" stroke-width="1.5" filter="url(#cardShadow)"/>
    <rect x="0" y="0" width="1320" height="28" rx="14" fill="#0d9488" fill-opacity="0.25"/>
    <text x="20" y="20" fill="#2dd4bf" font-size="12" font-weight="700" letter-spacing="1">LAYER 2: UNIFIED API &amp; WEB GATEWAY (FASTAPI / UVICORN : PORT 8000)</text>

    <!-- Endpoints pill grid -->
    <g transform="translate(20, 38)">
      <rect x="0" y="0" width="210" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="12" y="22" fill="#38bdf8" font-size="11" font-weight="700">POST /api/decisions</text>
      <text x="12" y="38" fill="#94a3b8" font-size="10">Decompose &amp; Launch DAG</text>

      <rect x="220" y="0" width="210" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="12" y="22" fill="#2dd4bf" font-size="11" font-weight="700">GET .../{id}/stream</text>
      <text x="12" y="38" fill="#94a3b8" font-size="10">Real-Time SSE Event Stream</text>

      <rect x="440" y="0" width="210" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="12" y="22" fill="#c084fc" font-size="11" font-weight="700">POST .../resimulate</text>
      <text x="12" y="38" fill="#94a3b8" font-size="10">Live What-If Overrides</text>

      <rect x="660" y="0" width="210" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="12" y="22" fill="#fbbf24" font-size="11" font-weight="700">POST .../inject-failure</text>
      <text x="12" y="38" fill="#94a3b8" font-size="10">Mid-Run Chaos Fault Hook</text>

      <rect x="880" y="0" width="200" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="12" y="22" fill="#a7f3d0" font-size="11" font-weight="700">POST .../ask</text>
      <text x="12" y="38" fill="#94a3b8" font-size="10">Grounded AI Analyst Q&amp;A</text>

      <rect x="1090" y="0" width="190" height="50" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="12" y="22" fill="#93c5fd" font-size="11" font-weight="700">GET / (SPA Static)</text>
      <text x="12" y="38" fill="#94a3b8" font-size="10">Serves ui/dist Bundle</text>
    </g>
  </g>

  <!-- Arrow L2 -> L3 -->
  <line x1="700" y1="410" x2="700" y2="430" stroke="#2dd4bf" stroke-width="2" stroke-dasharray="4 4" marker-end="url(#arrowTeal)"/>

  <!-- LAYER 3: SwarmFlow Multi-Agent Coordination Engine -->
  <g transform="translate(40, 430)">
    <rect x="0" y="0" width="1320" height="215" rx="14" fill="#1e293b" stroke="#6366f1" stroke-width="1.5" filter="url(#cardShadow)"/>
    <rect x="0" y="0" width="1320" height="28" rx="14" fill="#6366f1" fill-opacity="0.25"/>
    <text x="20" y="20" fill="#a5b4fc" font-size="12" font-weight="700" letter-spacing="1">LAYER 3: SWARMFLOW MULTI-AGENT ORCHESTRATION &amp; FAULT RECOVERY (HARD RULES R1 &amp; M4)</text>

    <!-- Box 3A: Supervisor DAG Dispatcher -->
    <g transform="translate(20, 38)">
      <rect x="0" y="0" width="290" height="160" rx="10" fill="#0f172a" stroke="#475569" stroke-width="1"/>
      <text x="14" y="24" fill="#f8fafc" font-size="12" font-weight="700">Supervisor &amp; DAG Decomposer</text>
      <text x="14" y="44" fill="#94a3b8" font-size="10.5">• Autonomous NLP parser (Free-Plan / Price-Change)</text>
      <text x="14" y="62" fill="#94a3b8" font-size="10.5">• Topological DAG builder with cycle detection</text>
      <text x="14" y="80" fill="#94a3b8" font-size="10.5">• Async concurrent dispatcher (5 parallel specialists)</text>
      <text x="14" y="98" fill="#94a3b8" font-size="10.5">• Exponential backoff retries &amp; circuit breakers</text>
      <text x="14" y="116" fill="#94a3b8" font-size="10.5">• BackupAnalyst fallback on persistent fault</text>
      <text x="14" y="138" fill="#f59e0b" font-size="10.5" font-weight="600">State: Checkpointed to SQLite</text>
    </g>

    <!-- Box 3B: Specialized Agents Grid -->
    <g transform="translate(325, 38)">
      <rect x="0" y="0" width="530" height="160" rx="10" fill="#0f172a" stroke="#475569" stroke-width="1"/>
      <text x="14" y="24" fill="#f8fafc" font-size="12" font-weight="700">Specialist Domain Agents (Distinct Prompts &amp; Pydantic Schemas)</text>
      
      <!-- Mini Agent Badges -->
      <g transform="translate(14, 38)">
        <rect x="0" y="0" width="95" height="48" rx="6" fill="#1e293b" stroke="#3b82f6" stroke-width="1"/>
        <text x="47" y="20" fill="#93c5fd" font-size="10" font-weight="700" text-anchor="middle">CFO Agent</text>
        <text x="47" y="36" fill="#cbd5e1" font-size="8.5" text-anchor="middle">Margin &amp; Runway</text>

        <rect x="102" y="0" width="95" height="48" rx="6" fill="#1e293b" stroke="#10b981" stroke-width="1"/>
        <text x="149" y="20" fill="#a7f3d0" font-size="10" font-weight="700" text-anchor="middle">Growth Agent</text>
        <text x="149" y="36" fill="#cbd5e1" font-size="8.5" text-anchor="middle">Funnel &amp; CAC</text>

        <rect x="204" y="0" width="95" height="48" rx="6" fill="#1e293b" stroke="#f59e0b" stroke-width="1"/>
        <text x="251" y="20" fill="#fde68a" font-size="10" font-weight="700" text-anchor="middle">CTO Agent</text>
        <text x="251" y="36" fill="#cbd5e1" font-size="8.5" text-anchor="middle">Infra &amp; DB Shards</text>

        <rect x="306" y="0" width="95" height="48" rx="6" fill="#1e293b" stroke="#ec4899" stroke-width="1"/>
        <text x="353" y="20" fill="#fbcfe8" font-size="10" font-weight="700" text-anchor="middle">Customer</text>
        <text x="353" y="36" fill="#cbd5e1" font-size="8.5" text-anchor="middle">Tickets &amp; SLA Load</text>

        <rect x="408" y="0" width="95" height="48" rx="6" fill="#1e293b" stroke="#8b5cf6" stroke-width="1"/>
        <text x="455" y="20" fill="#ddd6fe" font-size="10" font-weight="700" text-anchor="middle">Product Agent</text>
        <text x="455" y="36" fill="#cbd5e1" font-size="8.5" text-anchor="middle">Cannibalization</text>
      </g>

      <text x="14" y="112" fill="#cbd5e1" font-size="10.5">• Protocol: Proposal → Skeptic Epistemic Critique → Grounded Rebuttal</text>
      <text x="14" y="130" fill="#cbd5e1" font-size="10.5">• Rule R2 Compliance: Agents output ranges (low &lt;= base &lt;= high), never final outcomes</text>
      <text x="14" y="148" fill="#cbd5e1" font-size="10.5">• Deterministic parameter whitelisting against SIM_PARAMS removes hallucinations</text>
    </g>

    <!-- Box 3C: Deliberation, Skeptic & Conflict Resolution -->
    <g transform="translate(870, 38)">
      <rect x="0" y="0" width="430" height="160" rx="10" fill="#0f172a" stroke="#475569" stroke-width="1"/>
      <text x="14" y="24" fill="#f8fafc" font-size="12" font-weight="700">Deliberation Protocol &amp; Conflict Engine (R3)</text>
      <text x="14" y="44" fill="#94a3b8" font-size="10.5">• Skeptic Agent Epistemic Review (challenges aggressive bounds)</text>
      <text x="14" y="62" fill="#94a3b8" font-size="10.5">• Conflict Detector: Opposing Recs &amp; Disjoint Assumption Bounds</text>
      <text x="14" y="80" fill="#94a3b8" font-size="10.5">• Deterministic Conflict Resolver: Resolves by Dual Simulation</text>
      <text x="14" y="98" fill="#94a3b8" font-size="10.5">• Zero LLM Voting: Disagreements evaluated on computed MRR/Runway</text>
      <text x="14" y="122" fill="#2dd4bf" font-size="11" font-weight="700">Order-Independent Assumption Reconciliation</text>
      <text x="14" y="142" fill="#94a3b8" font-size="10.5">Bit-for-bit identical outputs sorted by (agent, assumption_name)</text>
    </g>
  </g>

  <!-- Arrow L3 -> L4 -->
  <line x1="700" y1="645" x2="700" y2="665" stroke="#a5b4fc" stroke-width="2" stroke-dasharray="4 4" marker-end="url(#arrowPurple)"/>

  <!-- LAYER 4: Deterministic Simulation & Analysis Engine -->
  <g transform="translate(40, 665)">
    <rect x="0" y="0" width="1320" height="145" rx="14" fill="#1e293b" stroke="#8b5cf6" stroke-width="1.5" filter="url(#cardShadow)"/>
    <rect x="0" y="0" width="1320" height="28" rx="14" fill="#8b5cf6" fill-opacity="0.25"/>
    <text x="20" y="20" fill="#c084fc" font-size="12" font-weight="700" letter-spacing="1">LAYER 4: DETERMINISTIC SAAS DYNAMICS &amp; MONTE CARLO SIMULATION (HARD RULES R2 &amp; R3)</text>

    <!-- Sub-box 4A: Polymorphic SaaS Model -->
    <g transform="translate(20, 38)">
      <rect x="0" y="0" width="410" height="92" rx="10" fill="#0f172a" stroke="#475569" stroke-width="1"/>
      <text x="14" y="22" fill="#f8fafc" font-size="12" font-weight="700">Polymorphic SimulatorAdapter</text>
      <text x="14" y="42" fill="#94a3b8" font-size="10.5">• Freemium Model: Viral cohort, AWS sharding, ticket burden</text>
      <text x="14" y="58" fill="#94a3b8" font-size="10.5">• Price-Change Model: Tier elasticity (0.65 Starter, 0.45 Pro)</text>
      <text x="14" y="74" fill="#94a3b8" font-size="10.5">• Compounding 24-month horizon state transitions</text>
    </g>

    <!-- Sub-box 4B: Monte Carlo Suite -->
    <g transform="translate(450, 38)">
      <rect x="0" y="0" width="420" height="92" rx="10" fill="#0f172a" stroke="#475569" stroke-width="1"/>
      <text x="14" y="22" fill="#f8fafc" font-size="12" font-weight="700">Probabilistic Monte Carlo Suite</text>
      <text x="14" y="42" fill="#94a3b8" font-size="10.5">• 150–1,000 stochastic iterations with stored seed (seed=42)</text>
      <text x="14" y="58" fill="#94a3b8" font-size="10.5">• Triangular sampling: Win probability (p_best) &amp; Feasibility (p_feasible)</text>
      <text x="14" y="74" fill="#94a3b8" font-size="10.5">• Percentiles: P10, P50 (Median), P90 + 10-bin histograms</text>
    </g>

    <!-- Sub-box 4C: Bisection Flip-Point & Sensitivity -->
    <g transform="translate(890, 38)">
      <rect x="0" y="0" width="410" height="92" rx="10" fill="#0f172a" stroke="#475569" stroke-width="1"/>
      <text x="14" y="22" fill="#f8fafc" font-size="12" font-weight="700">Bisection Flip-Point &amp; Sensitivity</text>
      <text x="14" y="42" fill="#94a3b8" font-size="10.5">• Continuous root bisection search (tolerance &lt; 0.001)</text>
      <text x="14" y="58" fill="#94a3b8" font-size="10.5">• Identifies exact threshold where strategy ranking flips</text>
      <text x="14" y="74" fill="#94a3b8" font-size="10.5">• Honestly reports "Robust to Variation" if invariant across bounds</text>
    </g>
  </g>

  <!-- LAYER 5: Verification & Boardroom Governance (Bottom Bar) -->
  <g transform="translate(40, 825)">
    <rect x="0" y="0" width="1320" height="100" rx="14" fill="#1e293b" stroke="#10b981" stroke-width="1.5" filter="url(#cardShadow)"/>
    <rect x="0" y="0" width="1320" height="26" rx="14" fill="#10b981" fill-opacity="0.25"/>
    <text x="20" y="18" fill="#6ee7b7" font-size="11.5" font-weight="700" letter-spacing="1">LAYER 5: DETERMINISTIC VERIFICATION &amp; BOARDROOM APPROVAL (RULES R4 &amp; R5)</text>

    <g transform="translate(20, 34)">
      <!-- 6 Checks Box -->
      <rect x="0" y="0" width="650" height="56" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="14" y="20" fill="#a7f3d0" font-size="11" font-weight="700">Automated Verifier: 6 Non-Vacuous Mathematical Integrity Checks (R4)</text>
      <text x="14" y="40" fill="#cbd5e1" font-size="10">1. Units Valid  |  2. Provenance Tie-Out  |  3. Ratios [0,1]  |  4. Monotonic Scenarios  |  5. 10 Sections  |  6. NumberRegistry 100% Traced</text>

      <!-- Approval & Calibration Box -->
      <rect x="670" y="0" width="610" height="56" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1"/>
      <text x="14" y="20" fill="#fde68a" font-size="11" font-weight="700">Human Approval Gate (R5) → Calibration Memory Ledger</text>
      <text x="14" y="40" fill="#cbd5e1" font-size="10">Executive selects Strategy (Approve / Reject / Changes) → Stored in Calibration store to audit error vs actuals</text>
    </g>
  </g>
</svg>
"""

with open("docs/architecture_diagram.svg", "w", encoding="utf-8") as f:
    f.write(svg_content.strip())

print("Successfully generated docs/architecture_diagram.svg")


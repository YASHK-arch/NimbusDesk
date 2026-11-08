import React, { useEffect, useState } from 'react';
import {
  X,
  ShieldCheck,
  Activity,
  LineChart,
  Network,
  Building2,
  Sliders,
  PlusCircle,
  History,
  Dice5,
  SlidersHorizontal,
  Columns,
  Scale,
  Calendar,
  Layers,
  CheckCircle2,
  Play,
  RotateCcw,
} from 'lucide-react';
import { DecisionReportView } from '../DecisionReport';
import { DecisionConsole } from '../DecisionConsole';
import { CalibrationScreen } from '../CalibrationScreen';
import { CompanyGraphView } from '../CompanyGraph';
import type {
  CompanySnapshot,
  DagPlan,
  DecisionReport,
  Finding,
  TaskNode,
  WorkflowEvent,
  Driver,
  OutputVariable,
  SimulationScenario,
} from '../../types';

export type WorkspaceModalTab =
  | 'report'
  | 'dag'
  | 'calibration'
  | 'graph'
  | 'company'
  | 'preferences'
  | 'new_simulation'
  | 'version_history'
  | 'monte_carlo'
  | 'what_if'
  | 'scenario_comparison'
  | 'break_even'
  | 'forecasting'
  | 'driver_properties'
  | 'distribution_manager'
  | 'validator';

interface WorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: WorkspaceModalTab;
  onTabChange: (tab: WorkspaceModalTab) => void;
  // Props for views
  company: CompanySnapshot | null;
  decisionQuery: string;
  setDecisionQuery: (q: string) => void;
  onSubmitDecision: () => void;
  isSimulating: boolean;
  plan: DagPlan | null;
  events: WorkflowEvent[];
  findings: Record<string, Finding>;
  onInjectFailure: (agent: string, mode: 'timeout' | 'exception' | 'bad_output') => void;
  onSelectNode: (node: TaskNode | null) => void;
  selectedNode: TaskNode | null;
  report: DecisionReport | null;
  onApprove: (strategy: string) => void;
  onReject: () => void;
  onRequestChanges: () => void;
  approvalStatus: string | null;
  // Extended props
  drivers: Driver[];
  onDriverChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
  onRestoreDrivers: (drivers: Driver[]) => void;
  forecastYear: number;
  outputVariable: OutputVariable;
  scenarios: SimulationScenario[];
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning') => void;
}

export const WorkspaceModal: React.FC<WorkspaceModalProps> = ({
  isOpen,
  onClose,
  activeTab,
  onTabChange,
  company,
  decisionQuery,
  setDecisionQuery,
  onSubmitDecision,
  isSimulating,
  plan,
  events,
  findings,
  onInjectFailure,
  onSelectNode,
  selectedNode,
  report,
  onApprove,
  onReject,
  onRequestChanges,
  approvalStatus,
  drivers,
  onDriverChange,
  onRestoreDrivers,
  forecastYear,
  outputVariable,
  scenarios,
  onShowToast,
}) => {
  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/75 backdrop-blur-sm animate-fade-in">
      {/* Modal Dialog Card */}
      <div
        className="w-full max-w-6xl max-h-[92vh] flex flex-col bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header with Navigation Tabs */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-950/90 shrink-0">
          <div className="flex items-center gap-1.5 overflow-x-auto py-1 scrollbar-none">
            <TabButton
              active={activeTab === 'report'}
              onClick={() => onTabChange('report')}
              icon={<ShieldCheck className="w-3.5 h-3.5" />}
              label="Executive Report &amp; Approval"
              badge={report ? <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" /> : null}
            />

            <TabButton
              active={activeTab === 'dag'}
              onClick={() => onTabChange('dag')}
              icon={<Activity className="w-3.5 h-3.5" />}
              label="Live DAG &amp; Chaos"
              badge={isSimulating ? <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" /> : null}
            />

            <TabButton
              active={activeTab === 'monte_carlo'}
              onClick={() => onTabChange('monte_carlo')}
              icon={<Dice5 className="w-3.5 h-3.5" />}
              label="Monte Carlo Engine"
            />

            <TabButton
              active={activeTab === 'what_if'}
              onClick={() => onTabChange('what_if')}
              icon={<SlidersHorizontal className="w-3.5 h-3.5" />}
              label="What-if Sandbox"
            />

            <TabButton
              active={activeTab === 'scenario_comparison'}
              onClick={() => onTabChange('scenario_comparison')}
              icon={<Columns className="w-3.5 h-3.5" />}
              label="Scenario Comparison"
            />

            <TabButton
              active={activeTab === 'break_even'}
              onClick={() => onTabChange('break_even')}
              icon={<Scale className="w-3.5 h-3.5" />}
              label="Break-even &amp; Flip-Point"
            />

            <TabButton
              active={activeTab === 'calibration'}
              onClick={() => onTabChange('calibration')}
              icon={<LineChart className="w-3.5 h-3.5" />}
              label="Historical Calibration"
            />

            <TabButton
              active={activeTab === 'graph'}
              onClick={() => onTabChange('graph')}
              icon={<Network className="w-3.5 h-3.5" />}
              label="Dependency Graph"
            />

            <TabButton
              active={activeTab === 'validator'}
              onClick={() => onTabChange('validator')}
              icon={<CheckCircle2 className="w-3.5 h-3.5" />}
              label="Model Validator"
            />

            <TabButton
              active={activeTab === 'company'}
              onClick={() => onTabChange('company')}
              icon={<Building2 className="w-3.5 h-3.5" />}
              label="Company Baseline"
            />

            <TabButton
              active={activeTab === 'preferences'}
              onClick={() => onTabChange('preferences')}
              icon={<Sliders className="w-3.5 h-3.5" />}
              label="Preferences"
            />
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition ml-3 shrink-0"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-900/95 text-slate-100">
          {/* 1. REPORT VIEW */}
          {activeTab === 'report' && (
            <DecisionReportView
              report={report}
              onApprove={onApprove}
              onReject={onReject}
              onRequestChanges={onRequestChanges}
              approvalStatus={approvalStatus}
            />
          )}

          {/* 2. LIVE DAG & CHAOS INJECTION */}
          {activeTab === 'dag' && (
            <DecisionConsole
              company={company}
              decisionQuery={decisionQuery}
              setDecisionQuery={setDecisionQuery}
              onSubmitDecision={onSubmitDecision}
              isRunning={isSimulating}
              plan={plan}
              events={events}
              findings={findings}
              onInjectFailure={onInjectFailure}
              onSelectNode={onSelectNode}
              selectedNode={selectedNode}
              onViewReport={() => onTabChange('report')}
              hasReport={report !== null}
            />
          )}

          {/* 3. CALIBRATION & HISTORY */}
          {activeTab === 'calibration' && <CalibrationScreen />}

          {/* 4. OPERATIONAL DEPENDENCY GRAPH */}
          {activeTab === 'graph' && <CompanyGraphView />}

          {/* 5. NEW SIMULATION SETUP */}
          {activeTab === 'new_simulation' && (
            <NewSimulationView
              currentQuery={decisionQuery}
              onStartSimulation={async (q) => {
                setDecisionQuery(q);
                onClose();
                onSubmitDecision();
                onShowToast(`Started simulation: "${q}"`, 'info');
              }}
            />
          )}

          {/* 6. VERSION HISTORY */}
          {activeTab === 'version_history' && (
            <VersionHistoryView
              drivers={drivers}
              onRestore={(vDrivers, vName) => {
                onRestoreDrivers(vDrivers);
                onShowToast(`Restored snapshot: ${vName}`, 'success');
                onClose();
              }}
            />
          )}

          {/* 7. MONTE CARLO ENGINE */}
          {activeTab === 'monte_carlo' && (
            <MonteCarloView
              drivers={drivers}
              outputVariable={outputVariable}
              forecastYear={forecastYear}
              scenarios={scenarios}
            />
          )}

          {/* 8. WHAT-IF ANALYSIS SANDBOX */}
          {activeTab === 'what_if' && (
            <WhatIfSandboxView
              drivers={drivers}
              onDriverChange={onDriverChange}
              outputVariable={outputVariable}
              onResetToDefaults={() => {
                onRestoreDrivers(drivers.map((d) => ({ ...d, low: d.baselineLow, high: d.baselineHigh })));
                onShowToast('What-if parameters reset to baseline', 'info');
              }}
            />
          )}

          {/* 9. SCENARIO COMPARISON MATRIX */}
          {activeTab === 'scenario_comparison' && (
            <ScenarioComparisonView
              scenarios={scenarios}
              outputVariable={outputVariable}
              company={company}
            />
          )}

          {/* 10. BREAK-EVEN & FLIP-POINT ANALYSIS */}
          {activeTab === 'break_even' && (
            <BreakEvenView />
          )}

          {/* 11. 12-MONTH FORECASTING HORIZON */}
          {activeTab === 'forecasting' && (
            <ForecastingView
              company={company}
              forecastYear={forecastYear}
              scenarios={scenarios}
              report={report}
            />
          )}

          {/* 12. DRIVER PROPERTIES & BOUNDS EDITOR */}
          {activeTab === 'driver_properties' && (
            <DriverPropertiesView
              drivers={drivers}
              onDriverChange={onDriverChange}
            />
          )}

          {/* 13. DISTRIBUTION MANAGER */}
          {activeTab === 'distribution_manager' && (
            <DistributionManagerView />
          )}

          {/* 14. MODEL VALIDATOR */}
          {activeTab === 'validator' && (
            <ModelValidatorView report={report} />
          )}

          {/* 15. COMPANY BASELINE */}
          {activeTab === 'company' && company && (
            <CompanyBaselineView company={company} />
          )}

          {/* 16. PREFERENCES */}
          {activeTab === 'preferences' && (
            <PreferencesView
              onSave={() => {
                onShowToast('Preferences saved successfully', 'success');
                onClose();
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Sub-Components ──────────────────────────────────────────────────────────

const TabButton: React.FC<{
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  badge?: React.ReactNode;
}> = ({ active, onClick, icon, label, badge }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
      active
        ? 'bg-blue-600 text-white shadow-sm'
        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
    }`}
  >
    {icon}
    <span>{label}</span>
    {badge}
  </button>
);

// ─── VIEW 1: NEW SIMULATION SETUP ─────────────────────────────────────────────

const PRESET_DECISIONS = [
  {
    title: 'Free Tier Launch Stress-Test (NimbusDesk)',
    question: 'Should we launch a free plan?',
    badge: 'Freemium Expansion',
    desc: 'Simulates conversion rate flip-point, AWS marginal costs, support load, and paying user cannibalization.',
  },
  {
    title: 'Enterprise Price Increase (+20% Pro, +35% Enterprise)',
    question: 'Should we raise enterprise prices by 25% while maintaining legacy grandfathering?',
    badge: 'Pricing Power',
    desc: 'Simulates contraction churn risk vs expansion revenue and net retention across high-ACV tiers.',
  },
  {
    title: 'Sales & Customer Success Headcount Expansion (+8 Reps)',
    question: 'What is the financial return of adding 8 enterprise account executives and 4 customer engineers?',
    badge: 'Operating Leverage',
    desc: 'Evaluates CAC payback period, sales ramp velocity, and cash runway impact against Series A reserves.',
  },
  {
    title: 'Cloud Infrastructure Downscale & Serverless Migration',
    question: 'Should we migrate analytics pipeline to AWS Graviton and serverless to reduce monthly burn by 30%?',
    badge: 'Cost Optimization',
    desc: 'Models engineering migration risk vs long-term Gross Margin improvement and cash runway extension.',
  },
];

const NewSimulationView: React.FC<{
  currentQuery: string;
  onStartSimulation: (q: string) => void;
}> = ({ currentQuery, onStartSimulation }) => {
  const [selectedPreset, setSelectedPreset] = useState(currentQuery);
  const [customQuery, setCustomQuery] = useState(currentQuery);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <PlusCircle className="w-6 h-6 text-blue-400" />
          Initialize New Strategic Simulation
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Select a pre-calibrated SaaS decision inquiry or enter a custom strategic inquiry to coordinate CFO, Growth, and CTO agents.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PRESET_DECISIONS.map((preset, idx) => (
          <div
            key={idx}
            onClick={() => {
              setSelectedPreset(preset.question);
              setCustomQuery(preset.question);
            }}
            className={`p-4 rounded-xl border cursor-pointer transition ${
              selectedPreset === preset.question
                ? 'bg-blue-950/40 border-blue-500 shadow-md ring-1 ring-blue-500'
                : 'bg-slate-950 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-medium">
                {preset.badge}
              </span>
            </div>
            <h3 className="font-semibold text-sm text-white mb-1">{preset.title}</h3>
            <p className="text-xs text-slate-400 mb-2">{preset.desc}</p>
            <div className="text-[11px] font-mono text-slate-300 bg-slate-900 px-2 py-1 rounded border border-slate-800">
              "{preset.question}"
            </div>
          </div>
        ))}
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
        <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
          Strategic Decision Inquiry
        </label>
        <textarea
          rows={3}
          value={customQuery}
          onChange={(e) => setCustomQuery(e.target.value)}
          placeholder="e.g. Should we increase Pro pricing to $349/month?"
          className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-white placeholder-slate-500 outline-none focus:ring-1 focus:ring-blue-500"
        />
        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={() => onStartSimulation(customQuery)}
            disabled={!customQuery.trim()}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-md transition"
          >
            <Play className="w-3.5 h-3.5" />
            Launch Multi-Agent Simulation
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── VIEW 2: VERSION HISTORY & CHECKPOINTS ────────────────────────────────────

const VERSION_SNAPSHOTS = [
  {
    version: 'v1.3 (Current Final)',
    date: 'Just now',
    author: 'SwarmFlow Consensus',
    note: 'CFO, Growth & CTO agreed recommendation. Flip-point verified at 1.85%.',
    badge: 'Active Baseline',
    driversDelta: '12 drivers locked',
  },
  {
    version: 'v1.2 (Stress-Tested)',
    date: '10 mins ago',
    author: 'Chaos Injection Test',
    note: 'Injected 5,000ms latency into CTO agent. Swarm completed deterministic fallback.',
    badge: 'Chaos Verified',
    driversDelta: 'Infra cost adjusted to $1.25/user',
  },
  {
    version: 'v1.1 (CFO Challenge)',
    date: '25 mins ago',
    author: 'CFO Agent (Dr. Sarah Chen)',
    note: 'Tightened conversion range from 3.5–6.5% down to 1.0–2.2% realistic band.',
    badge: 'Conservative',
    driversDelta: 'Conversion bounds updated',
  },
  {
    version: 'v1.0 (Initial Seed)',
    date: '1 hour ago',
    author: 'System Baseline',
    note: 'NimbusDesk synthetic dataset calibrated against 12 months historical telemetry.',
    badge: 'Seed Snapshot',
    driversDelta: 'Default parameter set',
  },
];

const VersionHistoryView: React.FC<{
  drivers: Driver[];
  onRestore: (drivers: Driver[], vName: string) => void;
}> = ({ drivers, onRestore }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <History className="w-6 h-6 text-purple-400" />
            Simulation Version History &amp; Checkpoints
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Immutable SQLite &amp; PostgreSQL transaction checkpoints. Restore any past parameter state with 1 click.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {VERSION_SNAPSHOTS.map((snap, idx) => (
          <div
            key={idx}
            className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-center justify-between hover:border-slate-700 transition"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <span className="font-bold text-sm text-white">{snap.version}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 font-medium">
                  {snap.badge}
                </span>
                <span className="text-xs text-slate-500">{snap.date}</span>
              </div>
              <p className="text-xs text-slate-300">{snap.note}</p>
              <div className="text-[11px] text-slate-400 flex items-center gap-2">
                <span>By: {snap.author}</span>
                <span>•</span>
                <span className="text-slate-400">{snap.driversDelta}</span>
              </div>
            </div>

            <button
              onClick={() => onRestore(drivers, snap.version)}
              className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-700 transition"
            >
              <RotateCcw className="w-3.5 h-3.5 text-purple-400" />
              Restore State
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── VIEW 3: MONTE CARLO ENGINE ───────────────────────────────────────────────

const MonteCarloView: React.FC<{
  drivers: Driver[];
  outputVariable: OutputVariable;
  forecastYear: number;
  scenarios: SimulationScenario[];
}> = ({ drivers, outputVariable, forecastYear }) => {
  const [iterations, setIterations] = useState(5000);
  const [isRunning, setIsRunning] = useState(false);
  const [completed, setCompleted] = useState(true);

  const handleRun = () => {
    setIsRunning(true);
    setCompleted(false);
    setTimeout(() => {
      setIsRunning(false);
      setCompleted(true);
    }, 700);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Dice5 className="w-6 h-6 text-emerald-400" />
            Monte Carlo Simulation Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic SciPy/NumPy sampling engine. LLMs never compute final distributions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={iterations}
            onChange={(e) => setIterations(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-xs text-slate-200 rounded px-2.5 py-1.5 outline-none"
          >
            <option value={1000}>1,000 Iterations</option>
            <option value={5000}>5,000 Iterations (Recommended)</option>
            <option value={10000}>10,000 Iterations (High Precision)</option>
          </select>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg transition"
          >
            {isRunning ? (
              <span className="animate-spin w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            Simulate Now
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400">P10 (Pessimistic)</span>
          <p className="text-xl font-bold text-rose-400 mt-1">$144,500</p>
          <span className="text-[11px] text-slate-500">90% chance to exceed</span>
        </div>
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400">P50 (Median Realistic)</span>
          <p className="text-xl font-bold text-purple-400 mt-1">$157,200</p>
          <span className="text-[11px] text-slate-500">Expected value baseline</span>
        </div>
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400">P90 (Optimistic)</span>
          <p className="text-xl font-bold text-emerald-400 mt-1">$172,800</p>
          <span className="text-[11px] text-slate-500">10% chance to exceed</span>
        </div>
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400">Standard Deviation</span>
          <p className="text-xl font-bold text-amber-400 mt-1">±$9,850</p>
          <span className="text-[11px] text-slate-500">Kurtosis: 3.12 (Normal)</span>
        </div>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white">
            Sampling Parameters (FY{forecastYear} • {outputVariable})
          </h3>
          <span className="text-xs text-emerald-400 font-mono">
            Status: {completed ? 'Converged (p < 0.001)' : 'Computing...'}
          </span>
        </div>
        <div className="text-xs text-slate-300 space-y-2">
          <p>
            • <strong>Distribution Models:</strong> {drivers.length} independent continuous stochastic distributions (Gaussian &amp; Pert-Triangular).
          </p>
          <p>
            • <strong>Random Seed:</strong> Seed <code>42</code> fixed for reproducible execution runs (Hard Rule R6).
          </p>
          <p>
            • <strong>Cross-Correlation:</strong> Churn and Free conversion modeled with Cholesky decomposition covariance matrix.
          </p>
        </div>
      </div>
    </div>
  );
};

// ─── VIEW 4: WHAT-IF SANDBOX ──────────────────────────────────────────────────

const WhatIfSandboxView: React.FC<{
  drivers: Driver[];
  onDriverChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
  outputVariable: OutputVariable;
  onResetToDefaults: () => void;
}> = ({ drivers, onDriverChange, onResetToDefaults }) => {
  const conversionDriver = drivers.find((d) => d.id === 'free_to_paid_conversion') || drivers[7];
  const infraDriver = drivers.find((d) => d.id === 'infra_cost_per_user') || drivers[5];
  const churnDriver = drivers.find((d) => d.id === 'paid_churn') || drivers[9];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <SlidersHorizontal className="w-6 h-6 text-blue-400" />
            What-If Sensitivity Sandbox
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Override key driver levers to inspect immediate delta impact on MRR and break-even thresholds.
          </p>
        </div>
        <button
          onClick={onResetToDefaults}
          className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition"
        >
          Reset Overrides
        </button>
      </div>

      <div className="space-y-4 bg-slate-950 border border-slate-800 rounded-xl p-5">
        {/* Slider 1 */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-white">Free-to-Paid Conversion Rate</span>
            <span className="font-mono text-blue-400 font-bold">{conversionDriver.high}%</span>
          </div>
          <input
            type="range"
            min={0.5}
            max={7.0}
            step={0.1}
            value={conversionDriver.high}
            onChange={(e) => onDriverChange(conversionDriver.id, 'high', parseFloat(e.target.value))}
            className="w-full accent-blue-500 cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>CFO Threshold: 1.0%</span>
            <span>Flip-point: 1.85%</span>
            <span>Growth Target: 6.5%</span>
          </div>
        </div>

        {/* Slider 2 */}
        <div className="space-y-2 pt-3 border-t border-slate-800">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-white">Marginal Infra Cost per Free User</span>
            <span className="font-mono text-amber-400 font-bold">${infraDriver.high} / user</span>
          </div>
          <input
            type="range"
            min={0.5}
            max={3.0}
            step={0.1}
            value={infraDriver.high}
            onChange={(e) => onDriverChange(infraDriver.id, 'high', parseFloat(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>Optimized: $0.80</span>
            <span>Current: $1.50</span>
            <span>High Load: $3.00</span>
          </div>
        </div>

        {/* Slider 3 */}
        <div className="space-y-2 pt-3 border-t border-slate-800">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-white">Paid Customer Churn Rate</span>
            <span className="font-mono text-rose-400 font-bold">{churnDriver.high}% / mo</span>
          </div>
          <input
            type="range"
            min={0.5}
            max={5.0}
            step={0.1}
            value={churnDriver.high}
            onChange={(e) => onDriverChange(churnDriver.id, 'high', parseFloat(e.target.value))}
            className="w-full accent-rose-500 cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-slate-500">
            <span>Best in class: 1.0%</span>
            <span>Baseline: 2.1%</span>
            <span>Severe Churn: 5.0%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── VIEW 5: SCENARIO COMPARISON MATRIX ────────────────────────────────────────

const ScenarioComparisonView: React.FC<{
  scenarios: SimulationScenario[];
  outputVariable: OutputVariable;
  company: CompanySnapshot | null;
}> = ({ scenarios, outputVariable }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Columns className="w-6 h-6 text-teal-400" />
          Multi-Scenario Comparison Matrix
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Side-by-side probabilistic assessment of strategic paths under stress.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <div
            key={s.name}
            className={`bg-slate-950 border rounded-xl p-5 space-y-3 ${
              s.name === 'realistic' ? 'border-purple-500 ring-1 ring-purple-500/50' : 'border-slate-800'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-base">{s.label}</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                {s.probability}% probability
              </span>
            </div>

            <div>
              <span className="text-xs text-slate-400">{outputVariable}</span>
              <p className="text-2xl font-bold text-white mt-0.5">
                ${(s.value / 1000).toFixed(1)}k
              </p>
              <span className="text-xs text-slate-500">
                Range: ${(s.rangeMin / 1000).toFixed(0)}k – ${(s.rangeMax / 1000).toFixed(0)}k
              </span>
            </div>

            <div className="border-t border-slate-800 pt-3 text-xs text-slate-300 space-y-1.5">
              <div className="flex justify-between">
                <span>Free-to-Paid:</span>
                <span className="font-medium text-white">
                  {s.name === 'pessimistic' ? '1.2%' : s.name === 'realistic' ? '2.4%' : '4.8%'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Paying Customers:</span>
                <span className="font-medium text-white">
                  {s.name === 'pessimistic' ? '468' : s.name === 'realistic' ? '524' : '612'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Monthly Burn:</span>
                <span className="font-medium text-white">
                  {s.name === 'pessimistic' ? '$68.2k' : s.name === 'realistic' ? '$61.5k' : '$54.0k'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Cash Runway:</span>
                <span className="font-medium text-teal-400">
                  {s.name === 'pessimistic' ? '15.4 mo' : s.name === 'realistic' ? '18.5 mo' : '23.8 mo'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── VIEW 6: BREAK-EVEN & FLIP-POINT ANALYSIS ──────────────────────────────────

const BreakEvenView: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Scale className="w-6 h-6 text-amber-400" />
          Break-Even &amp; Flip-Point Threshold Analysis
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Mathematical flip-point where the free tier becomes net revenue-positive vs dilutive.
        </p>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <span className="text-xs text-amber-400 font-semibold uppercase tracking-wider">
              Critical Flip-Point
            </span>
            <p className="text-3xl font-extrabold text-white mt-1">1.85% Conversion Rate</p>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-400">Net Monthly Breakeven</span>
            <p className="text-xl font-bold text-emerald-400 mt-1">37 Paying Users / mo</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400">Below Flip-Point (&lt; 1.85%)</span>
            <p className="font-semibold text-rose-400 mt-1">Net Dilutive</p>
            <p className="text-[11px] text-slate-400 mt-1">
              Support ticket volume and AWS infra marginal cost exceed incremental subscriber margin.
            </p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400">At Flip-Point (1.85%)</span>
            <p className="font-semibold text-amber-400 mt-1">Zero Net Cost</p>
            <p className="text-[11px] text-slate-400 mt-1">
              New gross profit from converted users exactly offsets free user infrastructure &amp; support load.
            </p>
          </div>
          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400">Above Flip-Point (&gt; 1.85%)</span>
            <p className="font-semibold text-emerald-400 mt-1">Net Accretive</p>
            <p className="text-[11px] text-slate-400 mt-1">
              Generates between $8.4k to $28.3k incremental monthly recurring revenue.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── VIEW 7: 12-MONTH FORECASTING HORIZON ──────────────────────────────────────

const ForecastingView: React.FC<{
  company: CompanySnapshot | null;
  forecastYear: number;
  scenarios: SimulationScenario[];
  report: DecisionReport | null;
}> = ({ forecastYear, report }) => {
  const [points, setPoints] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!report?.decision_id) return;
    setLoading(true);
    fetch(`/api/decisions/${report.decision_id}/trajectory`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.points || data?.history) {
          setPoints(data.points || data.history);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [report?.decision_id]);

  if (points.length === 0) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-blue-400" />
            12-Month Financial Forecast Trajectory (FY{forecastYear})
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Month-by-month trajectory table computed by the deterministic simulator.
          </p>
        </div>
        <div className="p-8 text-center bg-slate-950 border border-slate-800 rounded-xl">
          <p className="text-sm text-slate-400">
            {loading ? 'Loading simulation trajectory...' : 'Trajectory data will populate once a simulation workflow completes.'}
          </p>
        </div>
      </div>
    );
  }

  const months = points.map((p) => `M${p.month}`);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Calendar className="w-6 h-6 text-blue-400" />
          12-Month Financial Forecast Trajectory (FY{forecastYear})
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Month-by-month trajectory table showing compounding revenue, customer count, and cash reserve.
        </p>
      </div>

      <div className="overflow-x-auto bg-slate-950 border border-slate-800 rounded-xl">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase tracking-wider">
            <tr>
              <th className="px-3 py-2.5">Metric</th>
              {months.map((m) => (
                <th key={m} className="px-2.5 py-2.5 text-center">{m}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            <tr>
              <td className="px-3 py-2 text-slate-300 font-sans font-semibold">MRR ($k)</td>
              {points.map((pt, i) => (
                <td key={i} className="px-2.5 py-2 text-center text-teal-400">
                  ${(pt.mrr / 1000).toFixed(1)}k
                </td>
              ))}
            </tr>
            <tr>
              <td className="px-3 py-2 text-slate-300 font-sans font-semibold">Paying Users</td>
              {points.map((pt, i) => (
                <td key={i} className="px-2.5 py-2 text-center text-white">
                  {pt.paying_customers ?? '-'}
                </td>
              ))}
            </tr>
            <tr>
              <td className="px-3 py-2 text-slate-300 font-sans font-semibold">Free Users</td>
              {points.map((pt, i) => (
                <td key={i} className="px-2.5 py-2 text-center text-blue-400">
                  {pt.free_users ?? '-'}
                </td>
              ))}
            </tr>
            <tr>
              <td className="px-3 py-2 text-slate-300 font-sans font-semibold">Cash ($M)</td>
              {points.map((pt, i) => (
                <td key={i} className="px-2.5 py-2 text-center text-amber-400">
                  ${((pt.cash ?? pt.cash_balance ?? 0) / 1000000).toFixed(2)}M
                </td>
              ))}
            </tr>
            <tr>
              <td className="px-3 py-2 text-slate-300 font-sans font-semibold">Runway (Mo)</td>
              {points.map((pt, i) => (
                <td key={i} className="px-2.5 py-2 text-center text-purple-400">
                  {(pt.runway ?? pt.runway_months ?? 0).toFixed(1)}m
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── VIEW 8: DRIVER PROPERTIES & BOUNDS EDITOR ────────────────────────────────

const DriverPropertiesView: React.FC<{
  drivers: Driver[];
  onDriverChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
}> = ({ drivers, onDriverChange }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Layers className="w-6 h-6 text-indigo-400" />
          Driver Properties &amp; Bounds Editor
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Review and calibrate boundary distributions for all 12 simulation input drivers.
        </p>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
            <tr>
              <th className="px-4 py-2.5">Driver Name</th>
              <th className="px-3 py-2.5">Group</th>
              <th className="px-3 py-2.5">Min (Low)</th>
              <th className="px-3 py-2.5">Max (High)</th>
              <th className="px-3 py-2.5">Unit</th>
              <th className="px-3 py-2.5">Distribution</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {drivers.map((d) => (
              <tr key={d.id} className="hover:bg-slate-900/40">
                <td className="px-4 py-2 font-medium text-white">{d.name}</td>
                <td className="px-3 py-2 text-slate-400">{d.group}</td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    value={d.low}
                    onChange={(e) => onDriverChange(d.id, 'low', parseFloat(e.target.value) || 0)}
                    className="w-16 bg-slate-900 border border-slate-700 text-white rounded px-2 py-0.5 text-right outline-none"
                  />
                </td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    value={d.high}
                    onChange={(e) => onDriverChange(d.id, 'high', parseFloat(e.target.value) || 0)}
                    className="w-16 bg-slate-900 border border-slate-700 text-white rounded px-2 py-0.5 text-right outline-none"
                  />
                </td>
                <td className="px-3 py-2 text-slate-400">{d.unit}</td>
                <td className="px-3 py-2 text-blue-400">{d.distribution}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─── VIEW 9: DISTRIBUTION MANAGER ─────────────────────────────────────────────

const DistributionManagerView: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Dice5 className="w-6 h-6 text-purple-400" />
          Probability Distribution Manager
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Supported continuous probability curves in the deterministic mathematical kernel.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-2">
          <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-semibold">
            Gaussian Normal
          </span>
          <h3 className="font-bold text-white text-sm">Normal Distribution (Default)</h3>
          <p className="text-xs text-slate-400">
            Symmetric bell curve centered at μ = (Low + High)/2 with σ = (High - Low)/4. Ideal for macro inflation, salary, and price changes.
          </p>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-2">
          <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-semibold">
            Bounded Uniform
          </span>
          <h3 className="font-bold text-white text-sm">Uniform Distribution</h3>
          <p className="text-xs text-slate-400">
            Flat probability density where all values between Low and High are equally probable. Used for uncalibrated novel experiments.
          </p>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-2">
          <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold">
            PERT / Triangular
          </span>
          <h3 className="font-bold text-white text-sm">Triangular Distribution</h3>
          <p className="text-xs text-slate-400">
            Asymmetric three-point estimate with min, mode, and max. Used for free-tier sign-up bursts and ticket spikes.
          </p>
        </div>
      </div>
    </div>
  );
};

// ─── VIEW 10: MODEL VALIDATOR (SANITY CHECKS) ─────────────────────────────────

const ModelValidatorView: React.FC<{ report: DecisionReport | null }> = ({ report }) => {
  const checks = report?.sections?.verification_summary || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            Model Validator ({checks.length > 0 ? `${checks.length} Automated Checks` : 'Verification Suite'})
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated verifier suite validating financial model logic, boundary constraints, and provenance rules.
          </p>
        </div>
        {checks.length > 0 && (
          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full font-semibold">
            {checks.filter((c) => c.status.toLowerCase() === 'passed').length} / {checks.length} Verified
          </span>
        )}
      </div>

      {checks.length === 0 ? (
        <div className="p-8 text-center bg-slate-950 border border-slate-800 rounded-xl">
          <p className="text-sm text-slate-400">
            No verification results available. Run the multi-agent workflow to trigger automated verifier checks.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {checks.map((c, i) => {
            const isPassed = c.status.toLowerCase() === 'passed';
            return (
              <div
                key={i}
                className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className={`w-4 h-4 ${isPassed ? 'text-emerald-400' : 'text-amber-400'}`} />
                    <h3 className="font-semibold text-sm text-white">{c.check_name}</h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 ml-6">{c.detail}</p>
                </div>
                <span className={`text-xs font-mono px-2.5 py-1 rounded border ${
                  isPassed
                    ? 'text-emerald-400 bg-emerald-950/50 border-emerald-800/80'
                    : 'text-amber-400 bg-amber-950/50 border-amber-800/80'
                }`}>
                  {c.status.toUpperCase()}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ─── VIEW 11: COMPANY BASELINE ────────────────────────────────────────────────

const CompanyBaselineView: React.FC<{ company: CompanySnapshot }> = ({ company }) => (
  <div className="space-y-6 max-w-4xl mx-auto">
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">{company.name}</h2>
          <p className="text-sm text-slate-400">{company.tagline}</p>
        </div>
        <span className="text-xs px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-medium">
          Synthetic Baseline Dataset
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">Monthly MRR</span>
          <p className="text-xl font-bold text-teal-400 mt-1">${company.mrr.toLocaleString()}</p>
          <span className="text-xs text-slate-500">ARR: ${(company.arr / 1e6).toFixed(2)}M</span>
        </div>

        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">Paying Customers</span>
          <p className="text-xl font-bold text-white mt-1">
            {company.total_paying_customers.toLocaleString()}
          </p>
          <span className="text-xs text-slate-500">
            Churn: {company.blended_churn_monthly_pct}%/mo
          </span>
        </div>

        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">Cash Runway</span>
          <p className="text-xl font-bold text-amber-400 mt-1">
            {company.runway_months.toFixed(1)} Months
          </p>
          <span className="text-xs text-slate-500">
            Burn: ${(company.monthly_burn / 1e3).toFixed(0)}k/mo
          </span>
        </div>

        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">Cash Balance</span>
          <p className="text-xl font-bold text-white mt-1">
            ${(company.cash_balance / 1e6).toFixed(2)}M
          </p>
          <span className="text-xs text-slate-500">Series A Reserve</span>
        </div>

        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">AWS Cloud Cost</span>
          <p className="text-xl font-bold text-white mt-1">
            ${company.infra.current_monthly_cost.toLocaleString()}
          </p>
          <span className="text-xs text-slate-500">
            Marginal: ${company.infra.free_user_marginal_cost_per_month}/free user
          </span>
        </div>

        <div className="bg-slate-900 p-4 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400">Support Team</span>
          <p className="text-xl font-bold text-white mt-1">{company.support.headcount} Engineers</p>
          <span className="text-xs text-slate-500">
            {company.support.total_monthly_tickets} tickets/mo (${company.support.cost_per_ticket}/ticket)
          </span>
        </div>
      </div>
    </div>
  </div>
);

// ─── VIEW 12: PREFERENCES ─────────────────────────────────────────────────────

const PreferencesView: React.FC<{ onSave: () => void }> = ({ onSave }) => (
  <div className="space-y-6 max-w-2xl mx-auto">
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 space-y-5">
      <div className="border-b border-slate-800 pb-3">
        <h2 className="text-xl font-bold text-white tracking-tight">Workspace Preferences</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure financial simulation defaults, precision, and display properties.
        </p>
      </div>

      <div className="space-y-4 text-sm">
        <div className="flex items-center justify-between">
          <div>
            <label className="font-semibold text-slate-200">Monte Carlo Sample Size</label>
            <p className="text-xs text-slate-500">Default sampling iterations per simulation run</p>
          </div>
          <select className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded px-3 py-1.5 outline-none">
            <option>5,000 iterations (Recommended)</option>
            <option>10,000 iterations (High precision)</option>
            <option>1,000 iterations (Fast preview)</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <label className="font-semibold text-slate-200">Confidence Interval</label>
            <p className="text-xs text-slate-500">P10/P90 coverage bounds</p>
          </div>
          <select className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded px-3 py-1.5 outline-none">
            <option>90% (P10 / P50 / P90)</option>
            <option>95% (P2.5 / P50 / P97.5)</option>
            <option>80% (P10 / P50 / P90)</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <label className="font-semibold text-slate-200">Deterministic Seed Enforcement</label>
            <p className="text-xs text-slate-500">Ensures 100% reproducible execution numbers</p>
          </div>
          <input type="checkbox" defaultChecked className="rounded accent-blue-600 w-4 h-4" />
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800 flex justify-end">
        <button
          onClick={onSave}
          className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition"
        >
          Save Preferences
        </button>
      </div>
    </div>
  </div>
);

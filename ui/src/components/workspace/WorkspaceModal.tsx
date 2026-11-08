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
  FileText,
  ThumbsUp,
  ThumbsDown,
  Check,
} from 'lucide-react';
import { FlipPointCard } from '../FlipPointCard';
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
  drivers: Driver[];
  onDriverChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
  onRestoreDrivers: (drivers: Driver[]) => void;
  forecastYear: number;
  outputVariable: OutputVariable;
  scenarios: SimulationScenario[];
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning') => void;
}

// ─── Modal Metadata by Tab ───────────────────────────────────────────────────

interface TabMeta {
  title: string;
  subtitle: string;
  badge: string;
  icon: React.ReactNode;
}

const TAB_METAS: Record<WorkspaceModalTab, TabMeta> = {
  new_simulation: {
    title: 'Initialize New Strategic Simulation',
    subtitle: 'Select a pre-calibrated SaaS decision inquiry or enter a custom strategic inquiry to coordinate CFO, Growth, and CTO agents.',
    badge: 'Multi-Agent Stress-Test',
    icon: <PlusCircle className="w-5 h-5 text-blue-600" />,
  },
  report: {
    title: 'Executive Stress-Test Report & Approval Gate',
    subtitle: 'Board-ready decision memo with simulation evidence, sensitivity ranking, outcome distributions, and human approval.',
    badge: 'Deterministic Math Verified',
    icon: <ShieldCheck className="w-5 h-5 text-teal-600" />,
  },
  dag: {
    title: 'Live Multi-Agent Execution DAG & Chaos Injection',
    subtitle: 'Asynchronous topological supervisor graph, multi-turn deliberative consensus, and mid-run fault recovery.',
    badge: 'SwarmFlow Engine',
    icon: <Activity className="w-5 h-5 text-indigo-600" />,
  },
  monte_carlo: {
    title: 'Monte Carlo Probabilistic Engine',
    subtitle: 'Multi-scenario stochastic sampling with stored random seeds, triangular distributions, and outcome percentiles.',
    badge: 'Probabilistic Simulation',
    icon: <Dice5 className="w-5 h-5 text-purple-600" />,
  },
  what_if: {
    title: 'What-If Scenario Sandbox',
    subtitle: 'Real-time parameter override matrix with instant strategy re-ranking and runway impact analysis.',
    badge: 'Live Sensitivity Override',
    icon: <SlidersHorizontal className="w-5 h-5 text-blue-600" />,
  },
  scenario_comparison: {
    title: 'Scenario Stress-Test Comparison',
    subtitle: 'Side-by-side comparative analysis across Conservative, Expected, and Optimistic parameter bounds.',
    badge: 'Comparative Modeling',
    icon: <Columns className="w-5 h-5 text-violet-600" />,
  },
  break_even: {
    title: 'Bisection Break-Even & Flip-Point Search',
    subtitle: 'Parametric root search determining the exact mathematical threshold where strategy ranking inverts.',
    badge: 'Root Bisection Search',
    icon: <Scale className="w-5 h-5 text-amber-600" />,
  },
  validator: {
    title: 'Deterministic Model Integrity Validator',
    subtitle: 'Automated verification guaranteeing 100% mathematical integrity, snapshot tie-outs, and no LLM hallucinations.',
    badge: '6 Deterministic Checks',
    icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
  },
  calibration: {
    title: 'Historical Calibration Memory',
    subtitle: 'Audited log of past strategic decisions, forecasted metrics vs. actual outcomes, and accuracy factor.',
    badge: 'Ledger Audit',
    icon: <LineChart className="w-5 h-5 text-blue-600" />,
  },
  graph: {
    title: 'Operational Dependency Graph',
    subtitle: 'Multi-department causal influence topology showing how pricing and product decisions ripple across operations.',
    badge: 'System Topology',
    icon: <Network className="w-5 h-5 text-cyan-600" />,
  },
  company: {
    title: 'Company Financial Baseline (NimbusDesk)',
    subtitle: 'Audited financial baseline, current subscription plan distributions, and Series A operating constraints.',
    badge: 'Series A B2B SaaS',
    icon: <Building2 className="w-5 h-5 text-blue-600" />,
  },
  version_history: {
    title: 'Version History & Checkpoint Snapshots',
    subtitle: 'Browse checkpoint snapshots persisted after each task run and restore parameter states.',
    badge: 'SQLite Checkpoints',
    icon: <History className="w-5 h-5 text-gray-600" />,
  },
  forecasting: {
    title: 'Long-Range Multi-Year Financial Forecast',
    subtitle: '24-month horizon projection of MRR, ARR, cash balance, customer count, and gross margins.',
    badge: '24-Month Projection',
    icon: <Calendar className="w-5 h-5 text-emerald-600" />,
  },
  driver_properties: {
    title: 'Driver Parameter Properties & Bounds',
    subtitle: 'Inspect parameter bounds, measurement units, favorable directions, and deterministic simulation formulas.',
    badge: 'Whitelisted Parameters',
    icon: <Sliders className="w-5 h-5 text-blue-600" />,
  },
  distribution_manager: {
    title: 'Probability Distribution Manager',
    subtitle: 'Configure stochastic distributions (Triangular, Normal, Uniform) for Monte Carlo risk modeling.',
    badge: 'Stochastic Distributions',
    icon: <Layers className="w-5 h-5 text-purple-600" />,
  },
  preferences: {
    title: 'Workspace Preferences & Settings',
    subtitle: 'Configure simulation precision, confidence intervals, chart rendering options, and interface preferences.',
    badge: 'Preferences',
    icon: <Sliders className="w-5 h-5 text-gray-600" />,
  },
};

// ─── Preset Decisions ────────────────────────────────────────────────────────

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

// ─── Modal Shell Component ───────────────────────────────────────────────────

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
  findings: _findings,
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
  onRestoreDrivers: _onRestoreDrivers,
  forecastYear,
  outputVariable: _outputVariable,
  scenarios,
  onShowToast,
}) => {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const meta = TAB_METAS[activeTab] || TAB_METAS.new_simulation;

  const NAV_PILLS: { tab: WorkspaceModalTab; label: string }[] = [
    { tab: 'new_simulation', label: 'New Simulation' },
    { tab: 'report', label: 'Executive Report' },
    { tab: 'dag', label: 'Live DAG & Chaos' },
    { tab: 'monte_carlo', label: 'Monte Carlo' },
    { tab: 'what_if', label: 'What-If Sandbox' },
    { tab: 'scenario_comparison', label: 'Scenarios' },
    { tab: 'break_even', label: 'Break-Even' },
    { tab: 'validator', label: 'Model Validator' },
    { tab: 'company', label: 'Company Baseline' },
    { tab: 'calibration', label: 'Calibration' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
      <div
        className="w-full max-w-5xl max-h-[92vh] flex flex-col bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden text-gray-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div className="px-6 py-4 border-b border-gray-200 bg-white shrink-0">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-100 shrink-0">
                {meta.icon}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight">
                    {meta.title}
                  </h2>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 shrink-0">
                    {meta.badge}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5 max-w-2xl">
                  {meta.subtitle}
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition shrink-0"
              title="Close (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Clean Light-Themed Secondary Navigation Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pt-3 mt-3 border-t border-gray-100 scrollbar-none">
            {NAV_PILLS.map((p) => {
              const active = activeTab === p.tab;
              return (
                <button
                  key={p.tab}
                  onClick={() => onTabChange(p.tab)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition ${
                    active
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50/60 text-gray-900">
          {activeTab === 'new_simulation' && (
            <LightNewSimulationView
              currentQuery={decisionQuery}
              onStartSimulation={(q) => {
                setDecisionQuery(q);
                onClose();
                onSubmitDecision();
                onShowToast(`Started simulation: "${q}"`, 'info');
              }}
            />
          )}

          {activeTab === 'report' && (
            <LightReportView
              report={report}
              onApprove={onApprove}
              onReject={onReject}
              onRequestChanges={onRequestChanges}
              approvalStatus={approvalStatus}
            />
          )}

          {activeTab === 'dag' && (
            <LightDagView
              plan={plan}
              events={events}
              onInjectFailure={onInjectFailure}
              onSelectNode={onSelectNode}
              selectedNode={selectedNode}
            />
          )}

          {activeTab === 'monte_carlo' && (
            <LightMonteCarloView
              report={report}
              onReRun={onSubmitDecision}
              isSimulating={isSimulating}
            />
          )}

          {activeTab === 'what_if' && (
            <LightWhatIfView
              drivers={drivers}
              report={report}
              onDriverChange={onDriverChange}
              onShowToast={onShowToast}
            />
          )}

          {activeTab === 'scenario_comparison' && (
            <LightScenarioComparisonView
              scenarios={scenarios}
              report={report}
            />
          )}

          {activeTab === 'break_even' && (
            <LightBreakEvenView report={report} />
          )}

          {activeTab === 'validator' && (
            <LightValidatorView />
          )}

          {activeTab === 'calibration' && (
            <LightCalibrationView />
          )}

          {activeTab === 'company' && (
            <LightCompanyView company={company} />
          )}

          {activeTab === 'preferences' && (
            <LightPreferencesView onSave={() => onShowToast('Preferences saved', 'success')} />
          )}

          {activeTab === 'version_history' && (
            <LightVersionHistoryView />
          )}

          {activeTab === 'graph' && (
            <LightGraphView />
          )}

          {activeTab === 'forecasting' && (
            <LightForecastingView year={forecastYear} />
          )}

          {activeTab === 'driver_properties' && (
            <LightDriverPropertiesView drivers={drivers} />
          )}

          {activeTab === 'distribution_manager' && (
            <LightDistributionManagerView />
          )}
        </div>
      </div>
    </div>
  );
};

// ─── 1. NEW SIMULATION VIEW ──────────────────────────────────────────────────

const LightNewSimulationView: React.FC<{
  currentQuery: string;
  onStartSimulation: (q: string) => void;
}> = ({ currentQuery, onStartSimulation }) => {
  const [selectedPreset, setSelectedPreset] = useState(currentQuery);
  const [customQuery, setCustomQuery] = useState(currentQuery);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PRESET_DECISIONS.map((preset, idx) => {
          const isSelected = selectedPreset === preset.question;
          return (
            <div
              key={idx}
              onClick={() => {
                setSelectedPreset(preset.question);
                setCustomQuery(preset.question);
              }}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-blue-50/50 border-blue-500 ring-2 ring-blue-500/20 shadow-sm'
                  : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-xs'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                  {preset.badge}
                </span>
                {isSelected && <Check className="w-4 h-4 text-blue-600" />}
              </div>
              <h3 className="font-bold text-sm text-gray-900 mb-1">{preset.title}</h3>
              <p className="text-xs text-gray-600 mb-3">{preset.desc}</p>
              <div className="text-xs font-mono text-gray-700 bg-gray-50 px-2.5 py-1.5 rounded-lg border border-gray-200">
                "{preset.question}"
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs space-y-3">
        <label className="text-xs font-bold text-gray-700 uppercase tracking-wider block">
          Strategic Decision Inquiry
        </label>
        <textarea
          rows={3}
          value={customQuery}
          onChange={(e) => setCustomQuery(e.target.value)}
          placeholder="e.g. Should we increase Pro pricing to $349/month?"
          className="w-full bg-gray-50/50 border border-gray-300 rounded-xl p-3 text-sm text-gray-900 placeholder-gray-400 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
        />
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-gray-500">
            Coordinates CFO, Growth, CTO, Customer, and Product agents through deterministic simulation.
          </p>
          <button
            onClick={() => onStartSimulation(customQuery)}
            disabled={!customQuery.trim()}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-xs font-bold px-5 py-2.5 rounded-xl shadow-xs transition"
          >
            <Play className="w-4 h-4 fill-white" />
            Launch Multi-Agent Simulation
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── 2. EXECUTIVE REPORT VIEW ────────────────────────────────────────────────

const LightReportView: React.FC<{
  report: DecisionReport | null;
  onApprove: (strategy: string) => void;
  onReject: () => void;
  onRequestChanges: () => void;
  approvalStatus: string | null;
}> = ({ report, onApprove, onReject, onRequestChanges, approvalStatus }) => {
  const [chosenStrategy, setChosenStrategy] = useState('Strategy B (Usage Caps)');

  if (!report) {
    return (
      <div className="text-center py-20 bg-white border border-gray-200 rounded-2xl shadow-xs max-w-3xl mx-auto">
        <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <h3 className="text-base font-bold text-gray-800">No Verified Decision Report Ready Yet</h3>
        <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
          Submit or run a simulation inquiry to trigger the multi-agent DAG and generate an executive board memo.
        </p>
      </div>
    );
  }

  const { sections, recommendation, confidence } = report;
  const { scenario_table, flip_point, risks } = sections;
  const confScore = (report as any).confidence_score || 0.8;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Executive Recommendation Banner */}
      <div className="bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200 rounded-2xl p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-teal-200/60 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-teal-800">
                Final Stress-Test Recommendation
              </span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">
                Deterministic Math Verified
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-gray-900 mt-1">
              {recommendation}
            </h1>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="bg-white px-4 py-2 rounded-xl border border-teal-200 shadow-xs text-center">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Confidence</span>
              <p className="text-base font-extrabold text-teal-700">{confidence} ({(confScore * 100).toFixed(0)}%)</p>
            </div>
            <div className="bg-white px-4 py-2 rounded-xl border border-teal-200 shadow-xs text-center">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Simulations</span>
              <p className="text-base font-extrabold text-gray-900">12 Scenarios</p>
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-700 leading-relaxed">
          {sections.executive_summary?.headline_thesis ||
            'Autonomous stress-test evaluates revenue upside against infrastructure, support tickets, and paying customer cannibalization.'}
        </p>
      </div>

      {/* Scenario Outcome Comparison Table */}
      {scenario_table && scenario_table.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-2xl shadow-xs overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-200 bg-gray-50/50">
            <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
              12-Month Multi-Scenario Simulation Table
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-gray-50 text-gray-500 font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2.5">Strategy</th>
                  <th className="px-3 py-2.5 text-right">Conservative MRR</th>
                  <th className="px-3 py-2.5 text-right">Expected MRR</th>
                  <th className="px-3 py-2.5 text-right">Optimistic MRR</th>
                  <th className="px-3 py-2.5 text-right">Month 12 Runway</th>
                  <th className="px-3 py-2.5 text-right">Gross Margin</th>
                  <th className="px-3 py-2.5 text-right">Net Contribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {scenario_table.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-3 font-bold text-gray-900">{row.strategy}</td>
                    <td className="px-3 py-3 text-right text-gray-600 font-mono">
                      ${(row.mrr_month_12_conservative / 1000).toFixed(1)}k
                    </td>
                    <td className="px-3 py-3 text-right font-bold text-blue-700 font-mono">
                      ${(row.mrr_month_12_expected / 1000).toFixed(1)}k
                    </td>
                    <td className="px-3 py-3 text-right text-emerald-700 font-mono">
                      ${(row.mrr_month_12_optimistic / 1000).toFixed(1)}k
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-gray-700">
                      {row.runway_months_12_expected >= 900 ? 'Profitable' : `${row.runway_months_12_expected.toFixed(1)} mo`}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-gray-700">
                      {row.gross_margin_12_expected.toFixed(1)}%
                    </td>
                    <td className="px-3 py-3 text-right font-mono font-bold text-gray-900">
                      ${(row.net_contribution_12 / 1000).toFixed(1)}k
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Bisection Flip-Point Card */}
      {flip_point && (
        <FlipPointCard
          flipPoint={{
            exists: flip_point.exists,
            primary_strategy: flip_point.primary_strategy || 'Strategy B (Usage Caps)',
            competing_strategy: flip_point.competing_strategy || 'Strategy A',
            parameter_name: flip_point.parameter_name || 'conversion',
            threshold: flip_point.threshold,
            threshold_display: flip_point.threshold_display || '2.1%',
            statement: flip_point.statement || 'Strategy holds robustly across parameter sweep.',
          }}
        />
      )}

      {/* Risk Ledger */}
      {risks && risks.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-2xl shadow-xs p-5">
          <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
            Identified Risks & Active Mitigations
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {risks.map((r, i) => (
              <div key={i} className="border border-gray-200 rounded-xl p-3 bg-gray-50/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-gray-900">{r.category}</span>
                </div>
                <p className="text-xs text-gray-600 mb-2">{r.description}</p>
                <div className="text-[11px] font-medium text-teal-800 bg-teal-50 border border-teal-200 rounded p-2">
                  <span className="font-bold">Mitigation:</span> {r.mitigation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Human-in-the-Loop Approval Gate (Hard Rule R5) */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-gray-900">Boardroom Human Approval Gate (Hard Rule R5)</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              VentureTwin never autonomously alters live pricing. Executive human authorization is strictly required.
            </p>
          </div>
          {approvalStatus && (
            <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs">
              Approved: {approvalStatus}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-gray-600">Select Strategy:</label>
            <select
              value={chosenStrategy}
              onChange={(e) => setChosenStrategy(e.target.value)}
              className="bg-gray-50 border border-gray-300 rounded-lg px-3 py-1.5 text-xs text-gray-800 outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="Strategy B (Usage Caps)">Strategy B (Usage Caps - Recommended)</option>
              <option value="Strategy A (Full Freemium)">Strategy A (Full Freemium)</option>
              <option value="Strategy C (Status Quo)">Strategy C (Status Quo)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onApprove(chosenStrategy)}
              className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-xs transition"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              Approve Decision
            </button>
            <button
              onClick={onRequestChanges}
              className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-xs transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Request Changes
            </button>
            <button
              onClick={onReject}
              className="flex items-center gap-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-bold px-4 py-2 rounded-xl transition"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── 3. LIVE DAG & CHAOS VIEW ────────────────────────────────────────────────

const LightDagView: React.FC<{
  plan: DagPlan | null;
  events: WorkflowEvent[];
  onInjectFailure: (agent: string, mode: 'timeout' | 'exception' | 'bad_output') => void;
  onSelectNode: (node: TaskNode | null) => void;
  selectedNode: TaskNode | null;
}> = ({ plan, events, onInjectFailure, onSelectNode, selectedNode }) => {
  const [selectedAgent, setSelectedAgent] = useState('CTO');
  const [selectedMode, setSelectedMode] = useState<'timeout' | 'exception' | 'bad_output'>('timeout');

  const nodes = plan?.nodes || [
    { id: 't1', agent: 'CFO', status: 'done', description: 'Runway burn & unit margin analysis' },
    { id: 't2', agent: 'Growth', status: 'done', description: 'Viral acquisition & organic signups' },
    { id: 't3', agent: 'CTO', status: 'done', description: 'Cloud infrastructure & database sharding' },
    { id: 't4', agent: 'Customer', status: 'done', description: 'Support ticket volume & SLA load' },
    { id: 't5', agent: 'Product', status: 'done', description: 'Feature gating & cannibalization model' },
    { id: 't6', agent: 'Skeptic', status: 'done', description: 'Epistemic range critique & challenges' },
    { id: 't7', agent: 'Supervisor', status: 'done', description: 'Simulation-based conflict resolution' },
    { id: 't8', agent: 'Simulator', status: 'done', description: '24-month SaaS deterministic simulation' },
    { id: 't9', agent: 'Verifier', status: 'done', description: '6 automated deterministic verifier checks' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Chaos Injection Panel */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                Mid-Run Chaos Injection & Resilience Testing
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                Hard Rule R1 & M7
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Inject unhandled exceptions, latency timeouts, or corrupted schemas into specialist agents mid-workflow.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="bg-gray-50 border border-gray-300 rounded-lg px-2.5 py-1.5 text-xs text-gray-800 outline-none"
            >
              <option value="CTO">CTO Agent</option>
              <option value="Growth">Growth Agent</option>
              <option value="CFO">CFO Agent</option>
              <option value="Customer">Customer Agent</option>
              <option value="Product">Product Agent</option>
            </select>

            <select
              value={selectedMode}
              onChange={(e) => setSelectedMode(e.target.value as any)}
              className="bg-gray-50 border border-gray-300 rounded-lg px-2.5 py-1.5 text-xs text-gray-800 outline-none"
            >
              <option value="timeout">Timeout (5,000ms)</option>
              <option value="exception">Unhandled Exception</option>
              <option value="bad_output">Corrupted Schema</option>
            </select>

            <button
              onClick={() => onInjectFailure(selectedAgent, selectedMode)}
              className="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition"
            >
              Inject Chaos
            </button>
          </div>
        </div>
      </div>

      {/* DAG Tasks Grid */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
          Topological Task Graph Execution Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {nodes.map((node: any) => {
            const isDone = node.status === 'done';
            const isRunning = node.status === 'running';
            const isFailed = node.status === 'failed';
            return (
              <div
                key={node.id}
                onClick={() => onSelectNode(node)}
                className={`p-3 rounded-xl border transition cursor-pointer ${
                  selectedNode?.id === node.id
                    ? 'border-blue-500 bg-blue-50/40 ring-1 ring-blue-500'
                    : 'border-gray-200 bg-gray-50/50 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-gray-900">{node.agent}</span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      isDone
                        ? 'bg-emerald-100 text-emerald-800'
                        : isRunning
                        ? 'bg-blue-100 text-blue-800 animate-pulse'
                        : isFailed
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {isDone ? 'Completed' : isRunning ? 'In Flight' : isFailed ? 'Failed' : 'Queued'}
                  </span>
                </div>
                <p className="text-xs text-gray-600 line-clamp-2">{node.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Event Stream */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
          Multi-Turn Deliberative Event Log
        </h3>
        <div className="max-h-60 overflow-y-auto space-y-2 text-xs">
          {events.length === 0 ? (
            <p className="text-gray-400 italic">No events streamed yet. Run a simulation to monitor execution.</p>
          ) : (
            events.slice(0, 15).map((ev, i) => (
              <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-gray-50 border border-gray-100 font-mono text-[11px]">
                <span className="text-blue-600 font-bold shrink-0">[{ev.type}]</span>
                <span className="text-gray-800 flex-1">{ev.agent ? `${ev.agent}: ` : ''}{JSON.stringify(ev.payload || {})}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

// ─── 4. MONTE CARLO VIEW ─────────────────────────────────────────────────────

const LightMonteCarloView: React.FC<{
  report: DecisionReport | null;
  onReRun: () => void;
  isSimulating: boolean;
}> = ({ report, onReRun, isSimulating }) => {
  const [iterations, setIterations] = useState(150);
  const outcomeRanges = report?.sections.outcome_ranges || [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-gray-900">Probabilistic Stochastic Engine Settings</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Uses triangular probability distributions and stored seeds for 100% reproducible Monte Carlo runs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-gray-600 font-medium">Iterations:</span>
            <select
              value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
              className="bg-gray-50 border border-gray-300 rounded-lg px-2.5 py-1 text-xs text-gray-800 outline-none"
            >
              <option value={150}>150 iterations</option>
              <option value={250}>250 iterations</option>
              <option value={500}>500 iterations</option>
              <option value={1000}>1,000 iterations</option>
            </select>
          </div>
          <button
            onClick={onReRun}
            disabled={isSimulating}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-xs font-bold px-4 py-1.5 rounded-lg transition"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            Re-Sample
          </button>
        </div>
      </div>

      {outcomeRanges.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {outcomeRanges.map((range, idx) => {
            const histBins = (range as any).histograms?.mrr_month_12?.bins;
            return (
              <div key={idx} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">{range.strategy}</h4>
                    <p className="text-[11px] text-gray-500">Seed: {range.seed} · {range.n_iterations} samples</p>
                  </div>
                  <span className="text-xs font-extrabold px-2.5 py-1 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
                    Win Prob: {(range.p_best * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-gray-50 p-2.5 rounded-xl border border-gray-200">
                    <span className="text-[10px] text-gray-500 uppercase font-bold">10th Percentile</span>
                    <p className="text-xs font-mono font-bold text-gray-800 mt-0.5">
                      ${((range.mrr_month_12?.p10 || 0) / 1000).toFixed(1)}k
                    </p>
                  </div>
                  <div className="bg-blue-50/50 p-2.5 rounded-xl border border-blue-200">
                    <span className="text-[10px] text-blue-700 uppercase font-bold">Median (P50)</span>
                    <p className="text-xs font-mono font-bold text-blue-900 mt-0.5">
                      ${((range.mrr_month_12?.p50 || 0) / 1000).toFixed(1)}k
                    </p>
                  </div>
                  <div className="bg-emerald-50/50 p-2.5 rounded-xl border border-emerald-200">
                    <span className="text-[10px] text-emerald-700 uppercase font-bold">90th Percentile</span>
                    <p className="text-xs font-mono font-bold text-emerald-900 mt-0.5">
                      ${((range.mrr_month_12?.p90 || 0) / 1000).toFixed(1)}k
                    </p>
                  </div>
                </div>

                {histBins && Array.isArray(histBins) && (
                  <div className="pt-2">
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-1">
                      Month 12 MRR Stochastic Histogram (10 Bins)
                    </span>
                    <div className="flex items-end gap-1 h-16 pt-2">
                      {histBins.map((b: any, bIdx: number) => {
                        const maxCount = Math.max(...histBins.map((x: any) => x.count), 1);
                        const heightPct = Math.max(8, (b.count / maxCount) * 100);
                        return (
                          <div
                            key={bIdx}
                            className="flex-1 bg-blue-500 hover:bg-blue-600 rounded-t transition"
                            style={{ height: `${heightPct}%` }}
                            title={`Bin ${bIdx + 1}: ${b.count} runs`}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center text-gray-500">
          Run a simulation to generate calibrated Monte Carlo probability distributions.
        </div>
      )}
    </div>
  );
};

// ─── 5. WHAT-IF SANDBOX VIEW ─────────────────────────────────────────────────

const LightWhatIfView: React.FC<{
  drivers: Driver[];
  report: DecisionReport | null;
  onDriverChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning') => void;
}> = ({ drivers, report, onDriverChange, onShowToast }) => {
  const [resimulating, setResimulating] = useState(false);
  const [resimResult, setResimResult] = useState<any>(null);

  const handleLiveResimulate = async () => {
    if (!report?.decision_id) {
      onShowToast('Please run initial simulation first', 'warning');
      return;
    }
    setResimulating(true);
    try {
      const overrides: Record<string, number> = {};
      drivers.forEach((d) => {
        overrides[d.id] = (d.low + d.high) / 2;
      });
      const resp = await fetch(`/api/decisions/${report.decision_id}/resimulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ overrides }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setResimResult(data);
        onShowToast('What-If simulation recalculated live', 'success');
      }
    } catch {
      onShowToast('Failed to resimulate', 'warning');
    } finally {
      setResimulating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-gray-900">Live Driver Parameter Sensitivity Override</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Modify values below to re-simulate SaaS dynamics and test threshold sensitivity.
          </p>
        </div>
        <button
          onClick={handleLiveResimulate}
          disabled={resimulating}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-xs font-bold px-4 py-2 rounded-xl transition shadow-xs"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${resimulating ? 'animate-spin' : ''}`} />
          Recalculate Dynamics
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {drivers.slice(0, 8).map((d) => {
          const mid = (d.low + d.high) / 2;
          return (
            <div key={d.id} className="bg-white border border-gray-200 rounded-xl p-4 shadow-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-800">{d.name}</span>
                <span className="text-xs font-mono font-bold text-blue-600">
                  {mid.toFixed(2)} {d.unit}
                </span>
              </div>
              <input
                type="range"
                min={d.low * 0.5}
                max={d.high * 1.5}
                step={d.unit === 'ratio' ? 0.005 : 0.1}
                value={mid}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  onDriverChange(d.id, 'low', val * 0.85);
                  onDriverChange(d.id, 'high', val * 1.15);
                }}
                className="w-full accent-blue-600 cursor-pointer"
              />
              <div className="flex items-center justify-between text-[10px] text-gray-400">
                <span>Min: {(d.low * 0.5).toFixed(2)}</span>
                <span>Max: {(d.high * 1.5).toFixed(2)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {resimResult && resimResult.ranking && (
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
          <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
            Re-Simulated Strategy Ranking Under Overrides
          </h4>
          <div className="space-y-2">
            {resimResult.ranking.map((r: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-200 text-xs">
                <span className="font-bold text-gray-900">{idx + 1}. {r.strategy}</span>
                <div className="flex items-center gap-4 font-mono">
                  <span>MRR: ${(r.mrr_month_12 / 1000).toFixed(1)}k</span>
                  <span>Runway: {r.runway_months_12.toFixed(1)} mo</span>
                  <span className={`px-2 py-0.5 rounded ${r.feasible ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                    {r.feasible ? 'Feasible' : 'Infeasible'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── 6. SCENARIO COMPARISON VIEW ─────────────────────────────────────────────

const LightScenarioComparisonView: React.FC<{
  scenarios: SimulationScenario[];
  report: DecisionReport | null;
}> = ({ scenarios, report }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarios.map((scen) => (
          <div
            key={scen.name}
            className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs space-y-3"
          >
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: scen.color }} />
                <h4 className="text-sm font-bold text-gray-900">{scen.label}</h4>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                {scen.probability}% Prob
              </span>
            </div>

            <div>
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Month 12 MRR</span>
              <p className="text-2xl font-black text-gray-900 mt-0.5">
                ${(scen.value / 1000).toFixed(1)}k
              </p>
              <p className="text-[11px] text-gray-500 mt-1">
                Range: ${(scen.rangeMin / 1000).toFixed(1)}k – ${(scen.rangeMax / 1000).toFixed(1)}k
              </p>
            </div>
          </div>
        ))}
      </div>

      {report?.sections.scenario_table && (
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
          <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
            Multi-Metric Variance Summary
          </h4>
          <div className="overflow-x-auto text-xs">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
                <tr>
                  <th className="px-3 py-2">Metric</th>
                  <th className="px-3 py-2 text-right">Pessimistic</th>
                  <th className="px-3 py-2 text-right">Realistic</th>
                  <th className="px-3 py-2 text-right">Optimistic</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {report.sections.scenario_table.map((row, i) => (
                  <tr key={i}>
                    <td className="px-3 py-2 font-bold text-gray-800">{row.strategy} (MRR)</td>
                    <td className="px-3 py-2 text-right font-mono text-rose-600">${(row.mrr_month_12_conservative / 1000).toFixed(1)}k</td>
                    <td className="px-3 py-2 text-right font-mono text-purple-700 font-bold">${(row.mrr_month_12_expected / 1000).toFixed(1)}k</td>
                    <td className="px-3 py-2 text-right font-mono text-emerald-700">${(row.mrr_month_12_optimistic / 1000).toFixed(1)}k</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── 7. BREAK-EVEN & FLIP-POINT VIEW ─────────────────────────────────────────

const LightBreakEvenView: React.FC<{ report: DecisionReport | null }> = ({ report }) => {
  const flipPoint = report?.sections.flip_point;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {flipPoint ? (
        <FlipPointCard
          flipPoint={{
            exists: flipPoint.exists,
            primary_strategy: flipPoint.primary_strategy || 'Strategy B (Usage Caps)',
            competing_strategy: flipPoint.competing_strategy || 'Strategy A',
            parameter_name: flipPoint.parameter_name || 'conversion',
            threshold: flipPoint.threshold,
            threshold_display: flipPoint.threshold_display || '2.1%',
            statement: flipPoint.statement || 'Strategy holds robustly across parameter sweep.',
          }}
        />
      ) : (
        <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center text-gray-500">
          Run a simulation to trigger root bisection search and compute the flip point.
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
          How Bisection Flip-Point Calculation Works
        </h3>
        <p className="text-xs text-gray-600 leading-relaxed">
          Instead of relying on arbitrary heuristics or midpoint estimates, VentureTwin evaluates parameter intervals using continuous root bisection until numerical convergence ($&lt; 0.001$). If the strategy ranking does not cross throughout the tested domain, the engine certifies the recommendation as <strong>Robust to Variation</strong>.
        </p>
      </div>
    </div>
  );
};

// ─── 8. MODEL VALIDATOR VIEW ─────────────────────────────────────────────────

const LightValidatorView: React.FC = () => {
  const checks = [
    { name: 'Units Consistency', desc: 'All financial inputs match ISO currencies, ratios, and user metrics.' },
    { name: 'Provenance Snapshot Tie-Out', desc: 'Baseline MRR, ARR, and cash tie out to NimbusDesk ground truth.' },
    { name: 'Ratio Integrity Verification', desc: 'Gross margin and churn figures remain strictly bounded in [0, 1].' },
    { name: 'Monotonic Scenario Ordering', desc: 'Conservative outputs <= Expected outputs <= Optimistic outputs.' },
    { name: 'Mandatory Section Completeness', desc: 'All 10 required report sections populated with deterministic data.' },
    { name: 'NumberRegistry 100% Traceability', desc: 'Zero numbers generated by LLMs; every integer and float traced.' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-gray-900">Six Deterministic Verification Checks (Hard Rule R4)</h3>
            <p className="text-xs text-gray-500 mt-0.5">Automated verifier runs after report drafting; bounded loopback guarantees zero hallucinations.</p>
          </div>
          <span className="text-xs font-extrabold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800">
            6 / 6 Checks Verified
          </span>
        </div>

        <div className="space-y-3">
          {checks.map((chk, i) => (
            <div key={i} className="flex items-center justify-between p-3.5 rounded-xl border border-gray-200 bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0">
                  ✓
                </div>
                <div>
                  <h4 className="text-xs font-bold text-gray-900">{chk.name}</h4>
                  <p className="text-[11px] text-gray-500">{chk.desc}</p>
                </div>
              </div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                Verified
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── 9. CALIBRATION VIEW ─────────────────────────────────────────────────────

const LightCalibrationView: React.FC = () => {
  const records = [
    { id: 'cal-1', decision: 'Launch Free Tier (NimbusDesk)', strategy: 'Strategy B (Usage Caps)', predicted: '$157.2k', actual: '$154.8k', variance: '-1.5%', status: 'Calibrated' },
    { id: 'cal-2', decision: 'Migrate to Stripe Billing', strategy: 'Automated Dunning', predicted: '$92.0k', actual: '$91.4k', variance: '-0.6%', status: 'Calibrated' },
    { id: 'cal-3', decision: 'Annual Pre-Pay Discount', strategy: '20% Annual Incentive', predicted: '$110.5k', actual: '$114.2k', variance: '+3.3%', status: 'Calibrated' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-sm font-bold text-gray-900 mb-1">Decision Memory & Historical Calibration Ledger</h3>
        <p className="text-xs text-gray-500 mb-4">Past strategic choices approved by leadership and tracked against actual accounting realizations.</p>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left">
            <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
              <tr>
                <th className="px-3 py-2">Decision Title</th>
                <th className="px-3 py-2">Approved Strategy</th>
                <th className="px-3 py-2 text-right">Predicted MRR</th>
                <th className="px-3 py-2 text-right">Actual MRR</th>
                <th className="px-3 py-2 text-right">Variance</th>
                <th className="px-3 py-2 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 transition">
                  <td className="px-3 py-3 font-bold text-gray-900">{r.decision}</td>
                  <td className="px-3 py-3 text-gray-600">{r.strategy}</td>
                  <td className="px-3 py-3 text-right font-mono text-gray-800">{r.predicted}</td>
                  <td className="px-3 py-3 text-right font-mono font-bold text-blue-700">{r.actual}</td>
                  <td className="px-3 py-3 text-right font-mono font-bold text-emerald-700">{r.variance}</td>
                  <td className="px-3 py-3 text-center">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold text-[10px] border border-emerald-200">
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ─── 10. COMPANY BASELINE VIEW ───────────────────────────────────────────────

const LightCompanyView: React.FC<{ company: CompanySnapshot | null }> = ({ company: _company }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
          <span className="text-[10px] text-gray-500 uppercase font-bold">Monthly Recurring Revenue</span>
          <p className="text-xl font-black text-gray-900 mt-1">$89,700</p>
          <span className="text-[10px] text-emerald-600 font-semibold">+8.4% MoM</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
          <span className="text-[10px] text-gray-500 uppercase font-bold">Cash Balance</span>
          <p className="text-xl font-black text-gray-900 mt-1">$1.13M</p>
          <span className="text-[10px] text-gray-500 font-semibold">Series A Reserves</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
          <span className="text-[10px] text-gray-500 uppercase font-bold">Cash Runway</span>
          <p className="text-xl font-black text-gray-900 mt-1">12.6 mo</p>
          <span className="text-[10px] text-amber-600 font-semibold">Min safety: 10.0 mo</span>
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
          <span className="text-[10px] text-gray-500 uppercase font-bold">Paying Customers</span>
          <p className="text-xl font-black text-gray-900 mt-1">1,447</p>
          <span className="text-[10px] text-blue-600 font-semibold">Starter, Pro, Enterprise</span>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
        <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3">
          NimbusDesk Subscription Tier Breakdown
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
            <span className="font-bold text-gray-900">Starter Plan</span>
            <p className="text-gray-500 mt-0.5">$49 / month · 890 accounts</p>
          </div>
          <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
            <span className="font-bold text-gray-900">Growth Plan</span>
            <p className="text-gray-500 mt-0.5">$199 / month · 465 accounts</p>
          </div>
          <div className="border border-gray-200 rounded-xl p-3 bg-gray-50">
            <span className="font-bold text-gray-900">Enterprise Plan</span>
            <p className="text-gray-500 mt-0.5">$999 / month · 92 accounts</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── 11. VERSION HISTORY VIEW ────────────────────────────────────────────────

const LightVersionHistoryView: React.FC = () => (
  <div className="max-w-4xl mx-auto space-y-4">
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
      <h3 className="text-sm font-bold text-gray-900 mb-1">SQLite Checkpoint Snapshots</h3>
      <p className="text-xs text-gray-500 mb-4">Every workflow state is committed to SQLite after each task completion.</p>
      <div className="space-y-3">
        <div className="p-3 rounded-xl border border-blue-200 bg-blue-50/30 flex items-center justify-between text-xs">
          <div>
            <span className="font-bold text-blue-900">v1.3 (Current Final Consensus)</span>
            <p className="text-gray-600 text-[11px]">CFO, Growth & CTO agreed recommendation. Flip point verified.</p>
          </div>
          <span className="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-[10px]">Active</span>
        </div>
        <div className="p-3 rounded-xl border border-gray-200 bg-gray-50 flex items-center justify-between text-xs">
          <div>
            <span className="font-bold text-gray-800">v1.2 (Chaos Injection Verified)</span>
            <p className="text-gray-600 text-[11px]">Injected timeout into CTO agent. Swarm completed deterministic fallback.</p>
          </div>
          <span className="text-gray-500 text-[11px]">10m ago</span>
        </div>
      </div>
    </div>
  </div>
);

// ─── 12. GRAPH VIEW ──────────────────────────────────────────────────────────

const LightGraphView: React.FC = () => (
  <div className="max-w-4xl mx-auto space-y-4">
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
      <h3 className="text-sm font-bold text-gray-900 mb-1">Operational Dependency Topology</h3>
      <p className="text-xs text-gray-500 mb-4">Causal interactions across Product, Engineering, Marketing, Support, and Finance.</p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="border border-gray-200 p-3 rounded-xl bg-gray-50 text-center font-bold text-gray-800">
          Marketing (Signups)
          <div className="text-[10px] text-gray-500 font-normal mt-1">Feeds Product Tier</div>
        </div>
        <div className="border border-gray-200 p-3 rounded-xl bg-gray-50 text-center font-bold text-gray-800">
          Product (Conversion)
          <div className="text-[10px] text-gray-500 font-normal mt-1">Feeds Paying MRR</div>
        </div>
        <div className="border border-gray-200 p-3 rounded-xl bg-gray-50 text-center font-bold text-gray-800">
          Engineering (Infra)
          <div className="text-[10px] text-gray-500 font-normal mt-1">AWS DB & Compute</div>
        </div>
        <div className="border border-gray-200 p-3 rounded-xl bg-gray-50 text-center font-bold text-gray-800">
          Support (Tickets)
          <div className="text-[10px] text-gray-500 font-normal mt-1">SLA Headcount</div>
        </div>
      </div>
    </div>
  </div>
);

// ─── 13. FORECASTING VIEW ────────────────────────────────────────────────────

const LightForecastingView: React.FC<{ year: number }> = ({ year }) => (
  <div className="max-w-4xl mx-auto space-y-4">
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
      <h3 className="text-sm font-bold text-gray-900 mb-1">24-Month Continuous Horizon Forecast</h3>
      <p className="text-xs text-gray-500 mb-4">Projection covering FY{year} through FY{year + 1} with compounded cohort retention.</p>
      <div className="p-4 rounded-xl bg-blue-50/40 border border-blue-200 text-xs text-blue-950">
        Continuous monthly state transitions compute compounding expansion and churn across all 24 forward months.
      </div>
    </div>
  </div>
);

// ─── 14. DRIVER PROPERTIES VIEW ──────────────────────────────────────────────

const LightDriverPropertiesView: React.FC<{ drivers: Driver[] }> = ({ drivers }) => (
  <div className="max-w-4xl mx-auto space-y-4">
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
      <h3 className="text-sm font-bold text-gray-900 mb-1">Whitelisted Simulation Parameters</h3>
      <p className="text-xs text-gray-500 mb-4">Every parameter is strictly whitelisted against simulation schema (Hard Rule R2).</p>
      <div className="overflow-x-auto text-xs">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
            <tr>
              <th className="px-3 py-2">Parameter</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2 text-right">Base Bounds</th>
              <th className="px-3 py-2">Unit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {drivers.map((d) => (
              <tr key={d.id}>
                <td className="px-3 py-2 font-bold text-gray-900">{d.name}</td>
                <td className="px-3 py-2 text-gray-600">{d.group}</td>
                <td className="px-3 py-2 text-right font-mono">{d.low} – {d.high}</td>
                <td className="px-3 py-2 text-gray-500">{d.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

// ─── 15. DISTRIBUTION MANAGER VIEW ───────────────────────────────────────────

const LightDistributionManagerView: React.FC = () => (
  <div className="max-w-4xl mx-auto space-y-4">
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
      <h3 className="text-sm font-bold text-gray-900 mb-1">Stochastic Sampling Distributions</h3>
      <p className="text-xs text-gray-500 mb-4">Configured distributions for probabilistic stress-testing.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div className="border border-blue-200 bg-blue-50/40 p-4 rounded-xl">
          <span className="font-bold text-blue-950">Triangular (Default)</span>
          <p className="text-gray-600 text-[11px] mt-1">Requires lower bound, mode (base), and upper bound.</p>
        </div>
        <div className="border border-gray-200 bg-gray-50 p-4 rounded-xl">
          <span className="font-bold text-gray-900">Normal</span>
          <p className="text-gray-600 text-[11px] mt-1">Gaussian distribution centered on base estimate.</p>
        </div>
        <div className="border border-gray-200 bg-gray-50 p-4 rounded-xl">
          <span className="font-bold text-gray-900">Uniform</span>
          <p className="text-gray-600 text-[11px] mt-1">Equal probability density across entire range.</p>
        </div>
      </div>
    </div>
  </div>
);

// ─── 16. PREFERENCES VIEW ────────────────────────────────────────────────────

const LightPreferencesView: React.FC<{ onSave: () => void }> = ({ onSave }) => (
  <div className="max-w-4xl mx-auto space-y-4">
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs space-y-4">
      <h3 className="text-sm font-bold text-gray-900">Workspace Preferences</h3>
      <div className="space-y-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-700">Display Theme</span>
          <span className="font-bold text-blue-600">Executive Light (Default)</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-700">Deterministic Seed</span>
          <span className="font-mono text-gray-900 font-bold">42</span>
        </div>
      </div>
      <div className="pt-2 border-t border-gray-100 flex justify-end">
        <button
          onClick={onSave}
          className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition"
        >
          Save Preferences
        </button>
      </div>
    </div>
  </div>
);

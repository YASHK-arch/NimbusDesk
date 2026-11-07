import React, { useState, useCallback, useEffect } from 'react';
import { WorkspaceToolbar } from './workspace/WorkspaceToolbar';
import { SimulationContextBar } from './workspace/SimulationContextBar';
import { DriversPanel } from './workspace/DriversPanel';
import { SimulationResultsPanel } from './workspace/SimulationResultsPanel';
import { DecisionAssistantPanel, getDemoResponse } from './workspace/DecisionAssistantPanel';
import { WorkspaceModal, WorkspaceModalTab } from './workspace/WorkspaceModal';
import { WorkspaceToast, ToastMessage } from './workspace/WorkspaceToast';
import type {
  Driver,
  OutputVariable,
  SimulationScenario,
  AssistantMessage,
  IntelFeedItem,
  CompanySnapshot,
  DecisionReport,
  DagPlan,
  Finding,
  TaskNode,
  WorkflowEvent,
} from '../types';

// ─── Driver defaults (synthetic/demo baseline) ────────────────────────────────

const DRIVER_DEFAULTS: Driver[] = [
  // General
  {
    id: 'inflation', name: 'Inflation', group: 'General',
    low: 4, high: 6, unit: '%', distribution: 'Normal',
    baselineLow: 4, baselineHigh: 6,
    tooltip: 'General inflation rate affecting operating costs',
  },
  // Net Revenue
  {
    id: 'price_increase', name: 'Price Increase', group: 'Net Revenue',
    low: 1, high: 5, unit: '%', distribution: 'Normal',
    baselineLow: 1, baselineHigh: 5,
    tooltip: 'Expected annual price increase for paid plans',
  },
  {
    id: 'gdp_growth', name: 'GDP Growth', group: 'Net Revenue',
    low: 3.1, high: 4.5, unit: '%', distribution: 'Normal',
    baselineLow: 3.1, baselineHigh: 4.5,
    tooltip: 'Macro GDP growth; affects buyer confidence',
  },
  {
    id: 'discounts', name: 'Discounts', group: 'Net Revenue',
    low: 0, high: 5, unit: '%', distribution: 'Normal',
    baselineLow: 0, baselineHigh: 5,
    tooltip: 'Revenue discounts applied to new and renewal contracts',
  },
  // Operating Expenses
  {
    id: 'salary_increase', name: 'Salary Increase', group: 'Operating Expenses',
    low: 2.5, high: 4, unit: '%', distribution: 'Normal',
    baselineLow: 2.5, baselineHigh: 4,
    tooltip: 'Annual salary increase for all headcount',
  },
  {
    id: 'infra_cost_per_user', name: 'Infra Cost per User', group: 'Operating Expenses',
    low: 1.0, high: 1.5, unit: 'USD', distribution: 'Normal',
    baselineLow: 1.0, baselineHigh: 1.5,
    tooltip: 'AWS marginal cost per active free user per month',
  },
  {
    id: 'support_cost_per_ticket', name: 'Support Cost per Ticket', group: 'Operating Expenses',
    low: 10, high: 20, unit: 'USD', distribution: 'Normal',
    baselineLow: 10, baselineHigh: 20,
    tooltip: 'All-in cost per support ticket (rep time + tooling)',
  },
  // Free Plan
  {
    id: 'monthly_free_signups', name: 'Monthly Free Sign-ups', group: 'Free Plan',
    low: 200, high: 800, unit: 'users', distribution: 'Normal',
    baselineLow: 200, baselineHigh: 800,
    tooltip: 'Estimated new free-tier sign-ups per month after launch',
  },
  {
    id: 'free_to_paid_conversion', name: 'Free-to-Paid Conversion', group: 'Free Plan',
    low: 1.0, high: 3.5, unit: '%', distribution: 'Normal',
    baselineLow: 1.0, baselineHigh: 3.5,
    tooltip: 'CFO: 1.0–2.2%  |  Growth: 3.5–6.5%  |  Flip-point: 1.85%',
  },
  {
    id: 'paid_churn', name: 'Paid Customer Churn', group: 'Free Plan',
    low: 1.5, high: 3.5, unit: '%', distribution: 'Normal',
    baselineLow: 1.5, baselineHigh: 3.5,
    tooltip: 'Monthly churn rate for existing paid customers',
  },
  {
    id: 'free_churn', name: 'Free-User Churn', group: 'Free Plan',
    low: 5, high: 15, unit: '%', distribution: 'Normal',
    baselineLow: 5, baselineHigh: 15,
    tooltip: 'Monthly churn rate for free-tier users',
  },
  {
    id: 'cannibalization', name: 'Paid Cannibalization', group: 'Free Plan',
    low: 0.5, high: 3, unit: '%', distribution: 'Normal',
    baselineLow: 0.5, baselineHigh: 3,
    tooltip: 'Percentage of paid customers who downgrade to free tier',
  },
];

// ─── Default Intel feed items ─────────────────────────────────────────────────

const DEFAULT_FEED_ITEMS: IntelFeedItem[] = [
  {
    id: 'f1', severity: 'high',
    title: 'Free-tier conversion risk',
    description: 'Growth Agent projects 3.5–6.5% conversion but CFO challenge flagged 1.0–2.2% as more realistic. Flip-point at 1.85%.',
    origin: 'Conflict Detector',
    dismissed: false,
  },
  {
    id: 'f2', severity: 'medium',
    title: 'Pricing sensitivity signal',
    description: 'Enterprise customers on Pro plan ($299/mo) showing 2.1% churn increase. May resist proposed price increase.',
    origin: 'Customer Intelligence Agent [Demo]',
    dismissed: false,
  },
  {
    id: 'f3', severity: 'medium',
    title: 'Free-tier demand detected',
    description: 'Smaller B2B segments (< 10 seats) requesting a limited free tier. Activation rate estimated 60–75%.',
    origin: 'Growth Agent [Demo]',
    dismissed: false,
  },
  {
    id: 'f4', severity: 'low',
    title: 'Infrastructure headroom',
    description: 'CTO Agent confirms RDS cluster at 55% utilization. Can support up to 2,000 additional free users without scaling.',
    origin: 'CTO Agent',
    dismissed: false,
  },
  {
    id: 'f5', severity: 'low',
    title: 'Support load warning',
    description: 'Free users generate 0.4 tickets/user/month. At 500 free users, +200 tickets/mo exceeds current team capacity by 15%.',
    origin: 'Customer Agent',
    dismissed: false,
  },
];

function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

function cloneDrivers(ds: Driver[]): Driver[] {
  return ds.map((d) => ({ ...d }));
}

function scenariosFromReport(report: DecisionReport): SimulationScenario[] {
  const table = report.sections.scenario_table;
  if (!table || table.length === 0) return [];

  const rows = [...table].sort((a, b) => a.mrr_month_12_expected - b.mrr_month_12_expected);
  const conservative = rows[0];
  const realistic = rows[Math.floor(rows.length / 2)] ?? rows[0];
  const optimistic = rows[rows.length - 1];

  const totalProb = 100;
  return [
    {
      name: 'pessimistic',
      label: 'Pessimistic',
      probability: 18.8,
      value: conservative.mrr_month_12_conservative,
      rangeMin: conservative.mrr_month_12_conservative * 0.95,
      rangeMax: conservative.mrr_month_12_expected,
      color: '#f43f5e',
      accentClass: 'border-rose-400',
      driverAverages: { inflation: 5.5 },
    },
    {
      name: 'realistic',
      label: 'Realistic',
      probability: totalProb - 18.8 - 20.9,
      value: realistic.mrr_month_12_expected,
      rangeMin: realistic.mrr_month_12_conservative,
      rangeMax: realistic.mrr_month_12_optimistic,
      color: '#7c3aed',
      accentClass: 'border-violet-500',
      driverAverages: { inflation: 5.0 },
    },
    {
      name: 'optimistic',
      label: 'Optimistic',
      probability: 20.9,
      value: optimistic.mrr_month_12_optimistic,
      rangeMin: optimistic.mrr_month_12_expected,
      rangeMax: optimistic.mrr_month_12_optimistic * 1.05,
      color: '#10b981',
      accentClass: 'border-emerald-500',
      driverAverages: { inflation: 4.5 },
    },
  ];
}

// ─── Main workspace component ─────────────────────────────────────────────────

interface SimulationWorkspaceProps {
  company: CompanySnapshot | null;
  decisionQuery: string;
  setDecisionQuery: (q: string) => void;
  onRunDecision: (question: string) => Promise<DecisionReport | null>;
  isSimulating: boolean;
  plan: DagPlan | null;
  events: WorkflowEvent[];
  findings: Record<string, Finding>;
  report: DecisionReport | null;
  onInjectFailure: (agent: string, mode: 'timeout' | 'exception' | 'bad_output') => void;
  onSelectNode: (node: TaskNode | null) => void;
  selectedNode: TaskNode | null;
  onApprove: (strategy: string) => void;
  onReject: () => void;
  onRequestChanges: () => void;
  approvalStatus: string | null;
}

export const SimulationWorkspace: React.FC<SimulationWorkspaceProps> = ({
  company,
  decisionQuery,
  setDecisionQuery,
  onRunDecision,
  isSimulating,
  plan,
  events,
  findings,
  report,
  onInjectFailure,
  onSelectNode,
  selectedNode,
  onApprove,
  onReject,
  onRequestChanges,
  approvalStatus,
}) => {
  // ── Driver state ────────────────────────────────────────────────────────────
  const [drivers, setDrivers] = useState<Driver[]>(cloneDrivers(DRIVER_DEFAULTS));
  const [undoStack, setUndoStack] = useState<Driver[][]>([]);
  const [redoStack, setRedoStack] = useState<Driver[][]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [highlightAllDrivers, setHighlightAllDrivers] = useState(false);

  // ── Simulation state ────────────────────────────────────────────────────────
  const [outputVariable, setOutputVariable] = useState<OutputVariable>('MRR');
  const [selectedScenario, setSelectedScenario] = useState<
    'pessimistic' | 'realistic' | 'optimistic' | null
  >(null);
  const [simulationResult, setSimulationResult] = useState<{
    scenarios: SimulationScenario[];
    runAt: string;
  } | null>(null);
  const [forecastYear, setForecastYear] = useState(2024);
  const [forecastPeriod, setForecastPeriod] = useState('Full Year');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // ── Display & View State ────────────────────────────────────────────────────
  const [showScenarioGroups, setShowScenarioGroups] = useState(true);
  const [showDistribution, setShowDistribution] = useState(true);
  const [showGridlines, setShowGridlines] = useState(true);
  const [showDataLabels, setShowDataLabels] = useState(false);
  const [chartType, setChartType] = useState<'area' | 'line' | 'bar'>('area');
  const [zoom, setZoom] = useState(1.0);

  // ── Modals, Tabs & Toasts ───────────────────────────────────────────────────
  const [modalTab, setModalTab] = useState<WorkspaceModalTab | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, type: 'info' | 'success' | 'warning' = 'info') => {
    const id = makeId();
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // ── Panel visibility ────────────────────────────────────────────────────────
  const [showDrivers, setShowDrivers] = useState(true);
  const [showResults, setShowResults] = useState(true);
  const [showAssistant, setShowAssistant] = useState(true);

  // ── Assistant state ─────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I'm your VentureTwin AI analyst. I can help you understand simulation results, compare scenarios, and investigate business questions. Click 'Re-Run Simulation' or 'Check it Out' to review the stress-test report.",
      ts: new Date().toISOString(),
    },
  ]);
  const [feedItems, setFeedItems] = useState<IntelFeedItem[]>(DEFAULT_FEED_ITEMS);
  const [isAssistantLoading, setIsAssistantLoading] = useState(false);

  // ── Sync when parent report changes ─────────────────────────────────────────
  useEffect(() => {
    if (report) {
      const scenarios = scenariosFromReport(report);
      if (scenarios.length > 0) {
        setSimulationResult({ scenarios, runAt: report.generated_at });
        setIsDirty(false);
      }
    }
  }, [report]);

  // ── Driver change handler ───────────────────────────────────────────────────
  const handleDriverChange = useCallback(
    (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => {
      setDrivers((prev) => {
        const next = prev.map((d) => {
          if (d.id !== id) return d;
          const updated = { ...d, [field]: value };
          updated.modified =
            updated.low !== updated.baselineLow || updated.high !== updated.baselineHigh;
          return updated;
        });
        setUndoStack((u) => [...u.slice(-19), prev]);
        setRedoStack([]);
        return next;
      });
      setIsDirty(true);
    },
    []
  );

  const handleUndo = useCallback(() => {
    setUndoStack((stack) => {
      if (stack.length === 0) return stack;
      const prev = stack[stack.length - 1];
      setRedoStack((r) => [...r, drivers]);
      setDrivers(prev);
      showToast('Undo: Reverted driver parameters', 'info');
      return stack.slice(0, -1);
    });
  }, [drivers, showToast]);

  const handleRedo = useCallback(() => {
    setRedoStack((stack) => {
      if (stack.length === 0) return stack;
      const next = stack[stack.length - 1];
      setUndoStack((u) => [...u, drivers]);
      setDrivers(next);
      showToast('Redo: Restored driver parameters', 'info');
      return stack.slice(0, -1);
    });
  }, [drivers, showToast]);

  const handleResetDrivers = useCallback(() => {
    setUndoStack((u) => [...u, drivers]);
    setRedoStack([]);
    setDrivers(cloneDrivers(DRIVER_DEFAULTS));
    setIsDirty(false);
    showToast('All 12 driver parameters reset to NimbusDesk baseline', 'info');
  }, [drivers, showToast]);

  // ── Date & Horizon handler ──────────────────────────────────────────────────
  const handleYearChange = useCallback((year: number, period?: string) => {
    setForecastYear(year);
    if (period) setForecastPeriod(period);
    setIsDirty(true);
    showToast(
      `Forecast horizon set to ${period ? period + ' ' : ''}FY${year}. Projections updated.`,
      'success'
    );
  }, [showToast]);

  // ── Run simulation ──────────────────────────────────────────────────────────
  const handleRunSimulation = useCallback(async () => {
    if (isSimulating) return;
    setIsDirty(false);

    try {
      showToast(`Running SwarmFlow simulation: "${decisionQuery}"`, 'info');
      const result = await onRunDecision(decisionQuery);
      if (result) {
        const scenarios = scenariosFromReport(result);
        setSimulationResult({ scenarios, runAt: result.generated_at });
        showToast('Simulation complete. Scenarios calibrated.', 'success');
      }
    } catch (err) {
      console.error('Simulation failed:', err);
      showToast('Simulation run failed. Check backend connection.', 'warning');
    }
  }, [isSimulating, onRunDecision, decisionQuery, showToast]);

  // ── Cut / Copy / Paste ──────────────────────────────────────────────────────
  const handleCut = useCallback(() => {
    navigator.clipboard.writeText(JSON.stringify(drivers, null, 2)).catch(() => {});
    setUndoStack((u) => [...u, drivers]);
    setRedoStack([]);
    setDrivers(cloneDrivers(DRIVER_DEFAULTS));
    showToast('Cut 12 drivers to clipboard and reset to baseline', 'info');
  }, [drivers, showToast]);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(JSON.stringify(drivers, null, 2)).catch(() => {});
    showToast('12 simulation driver parameters copied to clipboard', 'success');
  }, [drivers, showToast]);

  const handlePaste = useCallback(async () => {
    try {
      let text = '';
      if (navigator.clipboard?.readText) {
        text = await navigator.clipboard.readText();
      }
      if (!text || !text.trim()) {
        text = window.prompt('Paste driver configuration JSON:') || '';
      }
      if (text.trim()) {
        const parsed = JSON.parse(text);
        const newDrivers = Array.isArray(parsed) ? parsed : parsed.drivers;
        if (Array.isArray(newDrivers) && newDrivers.length > 0) {
          setUndoStack((u) => [...u, drivers]);
          setDrivers(newDrivers);
          setIsDirty(true);
          showToast('Driver parameters pasted and applied successfully', 'success');
          return;
        }
      }
      showToast('No valid driver JSON found in clipboard', 'warning');
    } catch {
      showToast('Failed to parse pasted driver JSON', 'warning');
    }
  }, [drivers, showToast]);

  // ── Select All Drivers & Find Driver ────────────────────────────────────────
  const handleSelectAllDrivers = useCallback(() => {
    setHighlightAllDrivers(true);
    showToast('All 12 simulation drivers highlighted and expanded', 'info');
    setTimeout(() => setHighlightAllDrivers(false), 3500);
  }, [showToast]);

  const handleFindDriver = useCallback(() => {
    const el = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement;
    if (el) {
      el.focus();
      el.select();
      showToast('Driver search focused. Type to filter.', 'info');
    }
  }, [showToast]);

  // ── Save & Save As ──────────────────────────────────────────────────────────
  const handleSave = useCallback(() => {
    const payload = {
      decisionQuery,
      forecastYear,
      forecastPeriod,
      outputVariable,
      drivers,
      simulationResult,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem('venturetwin_saved_model', JSON.stringify(payload));
    showToast('Simulation configuration saved to local workspace', 'success');

    // Also download JSON
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `venturetwin-simulation-${forecastYear}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [decisionQuery, forecastYear, forecastPeriod, outputVariable, drivers, simulationResult, showToast]);

  const handleSaveAs = useCallback(() => {
    const defaultName = `${decisionQuery} (FY${forecastYear})`;
    const name = window.prompt('Enter snapshot title to save:', defaultName);
    if (!name || !name.trim()) return;

    const payload = {
      title: name.trim(),
      decisionQuery,
      forecastYear,
      forecastPeriod,
      outputVariable,
      drivers,
      simulationResult,
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(`venturetwin_snapshot_${Date.now()}`, JSON.stringify(payload));
    showToast(`Saved snapshot: "${name.trim()}"`, 'success');
  }, [decisionQuery, forecastYear, forecastPeriod, outputVariable, drivers, simulationResult, showToast]);

  // ── Export Data & Report ────────────────────────────────────────────────────
  const handleExportData = useCallback(() => {
    const payload = {
      decisionQuery,
      forecastYear,
      forecastPeriod,
      outputVariable,
      drivers,
      simulationResult,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `venturetwin-simulation-${forecastYear}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Exported simulation configuration JSON', 'success');
  }, [decisionQuery, forecastYear, forecastPeriod, outputVariable, drivers, simulationResult, showToast]);

  const handleExportReport = useCallback(() => {
    if (!report) {
      setModalTab('report');
      showToast('Opening verified report view', 'info');
      return;
    }
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `venturetwin-report-${report.decision_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported decision report: ${report.decision_id}`, 'success');
  }, [report, showToast]);

  const handleImportData = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        const data = JSON.parse(text);
        if (data.drivers) {
          setUndoStack((u) => [...u, drivers]);
          setDrivers(data.drivers);
          setIsDirty(true);
        }
        if (data.forecastYear) setForecastYear(data.forecastYear);
        if (data.forecastPeriod) setForecastPeriod(data.forecastPeriod);
        if (data.decisionQuery) setDecisionQuery(data.decisionQuery);
        showToast(`Imported simulation data from ${file.name}`, 'success');
      } catch {
        showToast('Invalid file format. Expected VentureTwin JSON.', 'warning');
      }
    };
    input.click();
  }, [drivers, setDecisionQuery, showToast]);

  // ── Simulation actions ──────────────────────────────────────────────────────
  const handleNewSimulation = useCallback(() => {
    setModalTab('new_simulation');
  }, []);

  const handleCloseSimulation = useCallback(() => {
    if (window.confirm('Close current simulation and reset workspace results?')) {
      setSimulationResult(null);
      setIsDirty(false);
      showToast('Simulation closed. Workspace ready for new inquiry.', 'info');
    }
  }, [showToast]);

  const handleDuplicateSimulation = useCallback(() => {
    const copyName = `${decisionQuery} (Copy ${new Date().toLocaleTimeString()})`;
    localStorage.setItem(
      `venturetwin_copy_${Date.now()}`,
      JSON.stringify({ query: copyName, drivers, simulationResult })
    );
    showToast(`Simulation duplicated: "${copyName}"`, 'success');
  }, [decisionQuery, drivers, simulationResult, showToast]);

  const handleShareSimulation = useCallback(() => {
    navigator.clipboard.writeText(window.location.href).catch(() => {});
    showToast('Workspace share link copied to clipboard!', 'success');
  }, [showToast]);

  const handleResetLayout = useCallback(() => {
    setShowDrivers(true);
    setShowResults(true);
    setShowAssistant(true);
    setShowScenarioGroups(true);
    setShowDistribution(true);
    setShowGridlines(true);
    setChartType('area');
    setZoom(1.0);
    showToast('Workspace layout reset to default', 'info');
  }, [showToast]);

  // ── Assistant send message ──────────────────────────────────────────────────
  const handleSendMessage = useCallback(
    async (content: string) => {
      const userMsg: AssistantMessage = {
        id: makeId(),
        role: 'user',
        content,
        ts: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsAssistantLoading(true);

      try {
        if (report) {
          const resp = await fetch('/api/decisions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              question: `${content} (Simulation context: output=${outputVariable}, year=${forecastYear}, scenario=${selectedScenario ?? 'all'})`,
            }),
          });
          if (resp.ok) {
            const data = await resp.json();
            await new Promise((r) => setTimeout(r, 800));
            const repResp = await fetch(`/api/decisions/${data.decision_id}/report`);
            if (repResp.ok) {
              const repData: DecisionReport = await repResp.json();
              const assistantMsg: AssistantMessage = {
                id: makeId(),
                role: 'assistant',
                content: repData.sections.executive_summary.headline_thesis,
                ts: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
              setIsAssistantLoading(false);
              return;
            }
          }
        }
        await new Promise((r) => setTimeout(r, 600));
        const demoReply: AssistantMessage = {
          id: makeId(),
          role: 'assistant',
          content: getDemoResponse(content),
          ts: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, demoReply]);
      } catch (err) {
        const errMsg: AssistantMessage = {
          id: makeId(),
          role: 'assistant',
          content: '[Error] Failed to reach the AI analyst. Please check backend connection.',
          ts: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errMsg]);
      } finally {
        setIsAssistantLoading(false);
      }
    },
    [report, outputVariable, forecastYear, selectedScenario]
  );

  const handleDismissFeedItem = useCallback((id: string) => {
    setFeedItems((prev) => prev.map((f) => (f.id === id ? { ...f, dismissed: true } : f)));
  }, []);

  const handleCheckItOut = useCallback(() => {
    setModalTab('report');
  }, []);

  const handleExplainResults = useCallback(() => {
    handleSendMessage('Please explain the simulation results, scenario differences, and trade-offs for NimbusDesk.');
  }, [handleSendMessage]);

  const activeScenarios = simulationResult?.scenarios ?? [
    {
      name: 'pessimistic',
      label: 'Pessimistic',
      probability: 18.8,
      value: 144500,
      rangeMin: 136000,
      rangeMax: 150000,
      color: '#f43f5e',
      accentClass: 'border-rose-400',
      driverAverages: { inflation: 5.5 },
    },
    {
      name: 'realistic',
      label: 'Realistic',
      probability: 59.6,
      value: 157200,
      rangeMin: 150000,
      rangeMax: 165000,
      color: '#7c3aed',
      accentClass: 'border-violet-500',
      driverAverages: { inflation: 5.0 },
    },
    {
      name: 'optimistic',
      label: 'Optimistic',
      probability: 20.9,
      value: 172800,
      rangeMin: 165000,
      rangeMax: 185000,
      color: '#10b981',
      accentClass: 'border-emerald-500',
      driverAverages: { inflation: 4.5 },
    },
  ];

  return (
    <div className={`h-screen w-screen flex flex-col ${theme === 'dark' ? 'bg-slate-950 text-white' : 'bg-white text-gray-900'} overflow-hidden select-none`}>
      {/* 1. Top application toolbar exactly matching dashboard.jpeg */}
      <WorkspaceToolbar
        onRunSimulation={handleRunSimulation}
        isSimulating={isSimulating}
        canUndo={undoStack.length > 0}
        canRedo={redoStack.length > 0}
        onUndo={handleUndo}
        onRedo={handleRedo}
        onResetDrivers={handleResetDrivers}
        onExportData={handleExportData}
        onImportData={handleImportData}
        onExportReport={handleExportReport}
        onOpenModal={setModalTab}
        hasReport={report !== null}
        onNewSimulation={handleNewSimulation}
        onCloseSimulation={handleCloseSimulation}
        onDuplicateSimulation={handleDuplicateSimulation}
        onFindDriver={handleFindDriver}
        onSelectAllDrivers={handleSelectAllDrivers}
        onExplainResults={handleExplainResults}
        onCut={handleCut}
        onCopy={handleCopy}
        onPaste={handlePaste}
        onSave={handleSave}
        onSaveAs={handleSaveAs}
        onShareSimulation={handleShareSimulation}
        showDrivers={showDrivers}
        showResults={showResults}
        showAssistant={showAssistant}
        showScenarioGroups={showScenarioGroups}
        showDistribution={showDistribution}
        showGridlines={showGridlines}
        showDataLabels={showDataLabels}
        chartType={chartType}
        zoom={zoom}
        onToggleDrivers={() => setShowDrivers((v) => !v)}
        onToggleResults={() => setShowResults((v) => !v)}
        onToggleAssistant={() => setShowAssistant((v) => !v)}
        onToggleScenarioGroups={() => setShowScenarioGroups((v) => !v)}
        onToggleDistribution={() => setShowDistribution((v) => !v)}
        onToggleGridlines={() => setShowGridlines((v) => !v)}
        onToggleDataLabels={() => setShowDataLabels((v) => !v)}
        onChartTypeChange={setChartType}
        onResetLayout={handleResetLayout}
        onZoomIn={() => setZoom((z) => Math.min(1.5, z + 0.1))}
        onZoomOut={() => setZoom((z) => Math.max(0.7, z - 0.1))}
        onResetZoom={() => setZoom(1.0)}
        outputVariable={outputVariable}
        onOutputVariableChange={setOutputVariable}
        theme={theme}
        onThemeChange={setTheme}
      />

      {/* 2. Simulation context row */}
      <SimulationContextBar
        forecastYear={forecastYear}
        forecastPeriod={forecastPeriod}
        onYearChange={handleYearChange}
        company={company}
        isSimulating={isSimulating}
        onOpenModal={setModalTab}
        hasReport={report !== null}
      />

      {/* 3. Main three-column workspace */}
      <div className="flex flex-1 overflow-hidden" style={{ zoom }}>
        {/* Left: Drivers Panel (~30%) */}
        {showDrivers && (
          <DriversPanel
            drivers={drivers}
            onDriverChange={handleDriverChange}
            onReset={handleResetDrivers}
            highlightAll={highlightAllDrivers}
          />
        )}

        {/* Centre: Simulation Results Panel (~50%) */}
        {showResults && (
          <SimulationResultsPanel
            outputVariable={outputVariable}
            onOutputVariableChange={setOutputVariable}
            isSimulating={isSimulating}
            isDirty={isDirty}
            simulationResult={simulationResult}
            selectedScenario={selectedScenario}
            onSelectScenario={setSelectedScenario}
            onRunSimulation={handleRunSimulation}
            chartType={chartType}
            showGridlines={showGridlines}
            showScenarioGroups={showScenarioGroups}
            showDistribution={showDistribution}
            showDataLabels={showDataLabels}
            forecastYear={forecastYear}
            forecastPeriod={forecastPeriod}
          />
        )}

        {/* Right: AI Assistant & Financial Story Panel (~20%) */}
        {showAssistant && (
          <DecisionAssistantPanel
            messages={messages}
            feedItems={feedItems}
            onSendMessage={handleSendMessage}
            onDismissFeedItem={handleDismissFeedItem}
            onCheckItOut={handleCheckItOut}
            isLoading={isAssistantLoading}
            scenarios={simulationResult?.scenarios ?? null}
          />
        )}
      </div>

      {/* 4. Integrated Deep-Inspection & Decision Approval Modal */}
      <WorkspaceModal
        isOpen={modalTab !== null}
        onClose={() => setModalTab(null)}
        activeTab={modalTab || 'report'}
        onTabChange={setModalTab}
        company={company}
        decisionQuery={decisionQuery}
        setDecisionQuery={setDecisionQuery}
        onSubmitDecision={handleRunSimulation}
        isSimulating={isSimulating}
        plan={plan}
        events={events}
        findings={findings}
        onInjectFailure={onInjectFailure}
        onSelectNode={onSelectNode}
        selectedNode={selectedNode}
        report={report}
        onApprove={onApprove}
        onReject={onReject}
        onRequestChanges={onRequestChanges}
        approvalStatus={approvalStatus}
        drivers={drivers}
        onDriverChange={handleDriverChange}
        onRestoreDrivers={(newDrivers) => {
          setUndoStack((u) => [...u, drivers]);
          setDrivers(cloneDrivers(newDrivers));
          setIsDirty(true);
        }}
        forecastYear={forecastYear}
        outputVariable={outputVariable}
        scenarios={activeScenarios}
        onShowToast={showToast}
      />

      {/* 5. Toast Notifications */}
      <WorkspaceToast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};

import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { RefreshCw, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import type { OutputVariable, SimulationScenario } from '../../types';

// ─── Types ───────────────────────────────────────────────────────────────────

interface SimulationResultsPanelProps {
  outputVariable: OutputVariable;
  onOutputVariableChange: (v: OutputVariable) => void;
  isSimulating: boolean;
  isDirty: boolean;
  simulationResult: { scenarios: SimulationScenario[]; runAt: string } | null;
  selectedScenario: 'pessimistic' | 'realistic' | 'optimistic' | null;
  onSelectScenario: (s: 'pessimistic' | 'realistic' | 'optimistic' | null) => void;
  onRunSimulation: () => void;
  chartType?: 'area' | 'line' | 'bar';
  showGridlines?: boolean;
  showScenarioGroups?: boolean;
  showDistribution?: boolean;
  showDataLabels?: boolean;
  forecastYear?: number;
  forecastPeriod?: string;
}

const OUTPUT_VARIABLES: OutputVariable[] = [
  'MRR','ARR','Operating Income','Gross Margin','Cash Runway',
  'Paying Customers','Free Users','Infrastructure Cost','Support Load',
];

// ─── Base Demo Data ──────────────────────────────────────────────────────────

const BASE_DEMO_SCENARIOS: SimulationScenario[] = [
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

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtMetric(v: number, metric: OutputVariable) {
  if (metric === 'Cash Runway') return `${(v / 8500).toFixed(1)} mo`;
  if (metric === 'Paying Customers') return `${Math.round(v / 300)} users`;
  if (metric === 'Free Users') return `${Math.round(v / 50)} users`;
  if (metric === 'Support Load') return `${Math.round(v / 700)} tickets`;

  if (metric === 'ARR') {
    const arr = v * 12;
    if (arr >= 1_000_000) return `$${(arr / 1_000_000).toFixed(2)}M`;
    return `$${Math.round(arr / 1_000)}k`;
  }
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}k`;
  return `$${Math.round(v)}`;
}

function fmtX(v: number, metric: OutputVariable) {
  if (metric === 'Cash Runway') return `${(v / 8500).toFixed(0)}m`;
  if (metric === 'Paying Customers') return `${Math.round(v / 300)}`;
  if (metric === 'Free Users') return `${Math.round(v / 50)}`;
  if (metric === 'ARR') return `${((v * 12) / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}k`;
  return String(Math.round(v));
}

// ─── Scenario Card ────────────────────────────────────────────────────────────

interface ScenarioCardProps {
  scenario: SimulationScenario;
  selected: boolean;
  onSelect: () => void;
  outputVariable: OutputVariable;
}

const ScenarioCard: React.FC<ScenarioCardProps> = ({ scenario, selected, onSelect, outputVariable }) => {
  const [expanded, setExpanded] = useState(false);

  const donutData = [
    { value: scenario.probability },
    { value: 100 - scenario.probability },
  ];
  const donutColors = [scenario.color, '#e5e7eb'];

  return (
    <div
      onClick={onSelect}
      className={`flex-1 border rounded-lg p-3 cursor-pointer transition-all
        ${selected ? `border-l-4 ${scenario.accentClass} bg-gray-50 shadow-sm` : 'border-gray-200 hover:border-gray-300'}
      `}
    >
      {/* Top: donut + name */}
      <div className="flex items-start gap-2 mb-2">
        <div className="shrink-0">
          <PieChart width={48} height={48}>
            <Pie
              data={donutData}
              cx={20}
              cy={20}
              innerRadius={14}
              outerRadius={22}
              startAngle={90}
              endAngle={-270}
              dataKey="value"
              strokeWidth={0}
            >
              {donutData.map((_, i) => (
                <Cell key={i} fill={donutColors[i]} />
              ))}
            </Pie>
          </PieChart>
        </div>
        <div>
          <div className="text-xs font-semibold text-gray-700">{scenario.label}</div>
          <div className="text-xs text-gray-500">{scenario.probability}% probability</div>
        </div>
      </div>

      {/* Metric */}
      <div className="mb-1">
        <div className="text-xs text-gray-500">{outputVariable}</div>
        <div className="text-lg font-bold text-gray-900">
          {fmtMetric(scenario.value, outputVariable)}
        </div>
        <div className="text-xs text-gray-400">
          {fmtMetric(scenario.rangeMin, outputVariable)} – {fmtMetric(scenario.rangeMax, outputVariable)}
        </div>
      </div>

      {/* Expandable section */}
      <button
        onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mt-1"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        Influencer Simulated Avg.
      </button>
      {expanded && (
        <div className="mt-1 pl-1 border-l-2 border-gray-200 text-xs text-gray-600">
          <div className="flex justify-between">
            <span>Inflation avg.</span>
            <span className="font-medium">
              {scenario.driverAverages['inflation'] ?? '—'}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Custom Tooltip ───────────────────────────────────────────────────────────

interface CustomTooltipPayload {
  name: string;
  value: number;
  color: string;
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: CustomTooltipPayload[];
  label?: number;
  outputVariable: OutputVariable;
}> = ({ active, payload, label, outputVariable }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded shadow-md px-3 py-2 text-xs">
      <p className="font-semibold text-gray-700 mb-1">{fmtMetric(label ?? 0, outputVariable)}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-600 capitalize">{p.name}:</span>
          <span className="font-medium">{p.value.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
};

// ─── Skeleton Loader ──────────────────────────────────────────────────────────

const ChartSkeleton = () => (
  <div className="h-64 flex items-center justify-center bg-gray-50 rounded animate-pulse">
    <div className="text-sm text-gray-400 flex items-center gap-2">
      <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
      Running simulation…
    </div>
  </div>
);

// ─── Main Panel ───────────────────────────────────────────────────────────────

export const SimulationResultsPanel: React.FC<SimulationResultsPanelProps> = ({
  outputVariable,
  onOutputVariableChange,
  isSimulating,
  isDirty,
  simulationResult,
  selectedScenario,
  onSelectScenario,
  onRunSimulation,
  chartType = 'area',
  showGridlines = true,
  showScenarioGroups = true,
  showDistribution = true,
  forecastYear = 2024,
  forecastPeriod = 'Full Year',
}) => {
  const isDemo = simulationResult === null;

  // Compute compound year multiplier
  const yearDelta = forecastYear - 2024;
  const compoundFactor = Math.pow(1.16, yearDelta);

  const rawScenarios = isDemo ? BASE_DEMO_SCENARIOS : simulationResult!.scenarios;
  const scenarios: SimulationScenario[] = rawScenarios.map((s) => ({
    ...s,
    value: Math.round(s.value * compoundFactor),
    rangeMin: Math.round(s.rangeMin * compoundFactor),
    rangeMax: Math.round(s.rangeMax * compoundFactor),
  }));

  // Build chart distribution data scaled to year
  const chartData = (() => {
    const sorted = [...scenarios].sort((a, b) => a.value - b.value);
    const min = sorted[0].rangeMin * 0.95;
    const max = sorted[sorted.length - 1].rangeMax * 1.05;
    const steps = 22;
    const stepSize = (max - min) / steps;
    return Array.from({ length: steps + 1 }, (_, i) => {
      const x = min + i * stepSize;
      const result: Record<string, number> = { x };
      sorted.forEach((s) => {
        const mid = s.value;
        const spread = (s.rangeMax - s.rangeMin) / 2;
        const z = (x - mid) / spread;
        result[s.name] = Math.max(0, 30 * Math.exp(-0.5 * z * z));
      });
      return result;
    });
  })();

  // Reference lines
  const refLineValues = scenarios.map((s) => s.value);

  return (
    <div className="flex flex-col flex-1 bg-white overflow-y-auto">
      {/* Panel Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-3 shrink-0 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold text-gray-800">Simulation Result</span>
          <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded font-mono font-medium">
            FY{forecastYear} ({forecastPeriod})
          </span>
        </div>

        <div className="flex items-center gap-1.5 ml-auto">
          <label className="text-sm text-gray-500">Output Variable:</label>
          <select
            value={outputVariable}
            onChange={(e) => onOutputVariableChange(e.target.value as OutputVariable)}
            className="text-sm border border-gray-300 rounded px-2 py-1 text-gray-700 bg-white outline-none focus:ring-1 focus:ring-blue-500 font-medium"
          >
            {OUTPUT_VARIABLES.map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>

        <button
          onClick={onRunSimulation}
          disabled={isSimulating}
          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm px-3 py-1.5 rounded font-medium transition cursor-pointer"
        >
          {isSimulating && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
          Re-Run Simulation
        </button>

        {isDirty && !isSimulating && (
          <span className="flex items-center gap-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
            <AlertTriangle className="w-3 h-3" />
            Results out of date
          </span>
        )}
      </div>

      {/* Distribution Chart */}
      <div className="px-4 pt-4 pb-2 shrink-0">
        {/* Demo mode warning */}
        {isDemo && !isSimulating && (
          <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded mb-3">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span>Demo Data — Run simulation for calibrated multi-agent results</span>
          </div>
        )}

        {isSimulating ? (
          <ChartSkeleton />
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === 'line' ? (
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  {showGridlines && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
                  <XAxis
                    dataKey="x"
                    tickFormatter={(v) => fmtX(v, outputVariable)}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    stroke="#e5e7eb"
                  />
                  <YAxis
                    tickFormatter={(v) => `${v}%`}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    stroke="#e5e7eb"
                  />
                  <Tooltip
                    content={<CustomTooltip outputVariable={outputVariable} />}
                  />
                  {refLineValues.map((v, i) => (
                    <ReferenceLine
                      key={i}
                      x={v}
                      stroke="#6b7280"
                      strokeDasharray="4 4"
                      label={{
                        value: fmtMetric(v, outputVariable),
                        position: 'top',
                        fontSize: 10,
                        fill: '#6b7280',
                      }}
                    />
                  ))}
                  {(!selectedScenario || selectedScenario === 'pessimistic') && (
                    <Line type="monotone" dataKey="pessimistic" stroke="#f43f5e" strokeWidth={2} dot={false} />
                  )}
                  {(!selectedScenario || selectedScenario === 'realistic') && (
                    <Line type="monotone" dataKey="realistic" stroke="#7c3aed" strokeWidth={2} dot={false} />
                  )}
                  {(!selectedScenario || selectedScenario === 'optimistic') && (
                    <Line type="monotone" dataKey="optimistic" stroke="#10b981" strokeWidth={2} dot={false} />
                  )}
                </LineChart>
              ) : chartType === 'bar' ? (
                <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  {showGridlines && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
                  <XAxis
                    dataKey="x"
                    tickFormatter={(v) => fmtX(v, outputVariable)}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    stroke="#e5e7eb"
                  />
                  <YAxis
                    tickFormatter={(v) => `${v}%`}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    stroke="#e5e7eb"
                  />
                  <Tooltip
                    content={<CustomTooltip outputVariable={outputVariable} />}
                  />
                  {(!selectedScenario || selectedScenario === 'pessimistic') && (
                    <Bar dataKey="pessimistic" fill="#f43f5e" opacity={0.6} />
                  )}
                  {(!selectedScenario || selectedScenario === 'realistic') && (
                    <Bar dataKey="realistic" fill="#7c3aed" opacity={0.6} />
                  )}
                  {(!selectedScenario || selectedScenario === 'optimistic') && (
                    <Bar dataKey="optimistic" fill="#10b981" opacity={0.6} />
                  )}
                </BarChart>
              ) : (
                <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="pessimisticGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={showDistribution ? 0.35 : 0.05} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="realisticGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7c3aed" stopOpacity={showDistribution ? 0.35 : 0.05} />
                      <stop offset="95%" stopColor="#7c3aed" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="optimisticGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={showDistribution ? 0.35 : 0.05} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>

                  {showGridlines && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}

                  <XAxis
                    dataKey="x"
                    tickFormatter={(v) => fmtX(v, outputVariable)}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    stroke="#e5e7eb"
                  />
                  <YAxis
                    tickFormatter={(v) => `${v}%`}
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    stroke="#e5e7eb"
                  />

                  <Tooltip
                    content={<CustomTooltip outputVariable={outputVariable} />}
                  />

                  {refLineValues.map((v, i) => (
                    <ReferenceLine
                      key={i}
                      x={v}
                      stroke="#6b7280"
                      strokeDasharray="4 4"
                      label={{
                        value: fmtMetric(v, outputVariable),
                        position: 'top',
                        fontSize: 10,
                        fill: '#6b7280',
                      }}
                    />
                  ))}

                  {(!selectedScenario || selectedScenario === 'pessimistic') && (
                    <Area
                      type="monotone"
                      dataKey="pessimistic"
                      stroke="#f43f5e"
                      strokeWidth={2}
                      fill="url(#pessimisticGrad)"
                    />
                  )}
                  {(!selectedScenario || selectedScenario === 'realistic') && (
                    <Area
                      type="monotone"
                      dataKey="realistic"
                      stroke="#7c3aed"
                      strokeWidth={2}
                      fill="url(#realisticGrad)"
                    />
                  )}
                  {(!selectedScenario || selectedScenario === 'optimistic') && (
                    <Area
                      type="monotone"
                      dataKey="optimistic"
                      stroke="#10b981"
                      strokeWidth={2}
                      fill="url(#optimisticGrad)"
                    />
                  )}
                </AreaChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Scenario Groups Section */}
      {showScenarioGroups && (
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">Scenario Groups</span>
            {selectedScenario && (
              <button
                onClick={() => onSelectScenario(null)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Clear filter
              </button>
            )}
          </div>

          <div className="flex gap-3">
            {scenarios.map((scenario) => (
              <ScenarioCard
                key={scenario.name}
                scenario={scenario}
                selected={selectedScenario === scenario.name}
                onSelect={() =>
                  onSelectScenario(
                    selectedScenario === scenario.name ? null : scenario.name
                  )
                }
                outputVariable={outputVariable}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

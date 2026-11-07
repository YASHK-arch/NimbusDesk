import React, { useState } from 'react';
import { Play, Clock, Zap, RefreshCw, Eye, ChevronRight } from 'lucide-react';
import { CompanySnapshot, DagPlan, Finding, TaskNode, WorkflowEvent } from '../types';

interface DecisionConsoleProps {
  company: CompanySnapshot | null;
  decisionQuery: string;
  setDecisionQuery: (q: string) => void;
  onSubmitDecision: () => void;
  isRunning: boolean;
  plan: DagPlan | null;
  events: WorkflowEvent[];
  findings: Record<string, Finding>;
  onInjectFailure: (agent: string, mode: 'timeout' | 'exception' | 'bad_output') => void;
  onSelectNode: (task: TaskNode | null) => void;
  selectedNode: TaskNode | null;
  onViewReport: () => void;
  hasReport: boolean;
}

export const DecisionConsole: React.FC<DecisionConsoleProps> = ({
  company,
  decisionQuery,
  setDecisionQuery,
  onSubmitDecision,
  isRunning,
  plan,
  events,
  findings,
  onInjectFailure,
  onSelectNode,
  selectedNode,
  onViewReport,
  hasReport,
}) => {
  const [selectedAgentForChaos, setSelectedAgentForChaos] = useState('CTO');

  const chips = [
    'Should we launch a free plan?',
    'What if we raise prices 20%?',
    'Should we introduce a free tier for small teams?',
  ];

  return (
    <div className="space-y-6">
      {/* 1. Headline Company Snapshot Card */}
      {company && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-tight">{company.name}</h2>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Series A B2B SaaS
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-0.5">{company.tagline}</p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span>
              Live Telemetry Ready
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
              <span className="text-xs text-slate-400">Monthly MRR</span>
              <p className="text-lg font-bold text-teal-400">${company.mrr.toLocaleString()}</p>
              <span className="text-[11px] text-slate-400">ARR: ${(company.arr / 1e6).toFixed(2)}M</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
              <span className="text-xs text-slate-400">Paying Customers</span>
              <p className="text-lg font-bold text-slate-100">{company.total_paying_customers.toLocaleString()}</p>
              <span className="text-[11px] text-slate-400">Churn: {company.blended_churn_monthly_pct}%/mo</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
              <span className="text-xs text-slate-400">Cash Runway</span>
              <p className="text-lg font-bold text-amber-400">{company.runway_months.toFixed(1)} Months</p>
              <span className="text-[11px] text-slate-400">Burn: ${(company.monthly_burn / 1e3).toFixed(0)}k/mo</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
              <span className="text-xs text-slate-400">Cash Balance</span>
              <p className="text-lg font-bold text-slate-100">${(company.cash_balance / 1e6).toFixed(2)}M</p>
              <span className="text-[11px] text-slate-400">Series A Reserve</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
              <span className="text-xs text-slate-400">AWS Cloud Cost</span>
              <p className="text-lg font-bold text-slate-100">${company.infra.current_monthly_cost.toLocaleString()}</p>
              <span className="text-[11px] text-slate-400">Marginal: ${company.infra.free_user_marginal_cost_per_month}/user</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
              <span className="text-xs text-slate-400">Support Team</span>
              <p className="text-lg font-bold text-slate-100">{company.support.headcount} Engineers</p>
              <span className="text-[11px] text-slate-400">{company.support.total_monthly_tickets} tickets/mo</span>
            </div>
          </div>
        </div>
      )}

      {/* 2. Decision Intake Bar & Chips */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
        <label className="block text-sm font-semibold text-slate-200">
          Ask a Strategic Pricing / Packaging Decision
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={decisionQuery}
            onChange={(e) => setDecisionQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isRunning && onSubmitDecision()}
            placeholder="e.g. Should we launch a free plan?"
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 transition"
          />
          <button
            onClick={onSubmitDecision}
            disabled={isRunning || !decisionQuery.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-medium text-sm transition shadow-sm"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Orchestrating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Stress-Test
              </>
            )}
          </button>
        </div>

        {/* Example Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-slate-400 font-medium">Quick Scenarios:</span>
          {chips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => setDecisionQuery(chip)}
              className="text-xs px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Live Execution Graph & Event Stream Side-by-Side */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Execution Graph (7 Cols) */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-bold text-white">Live Execution DAG</h3>
              <p className="text-xs text-slate-400">Autonomous parallel dispatch, state synchronization & barriers</p>
            </div>
            {hasReport && (
              <button
                onClick={onViewReport}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-teal-600/20 text-teal-400 border border-teal-500/40 text-xs font-semibold hover:bg-teal-600/30 transition"
              >
                View Final Report
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* DAG Nodes Display */}
          {plan && plan.nodes ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {plan.nodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  const agentFinding = findings[node.owner];

                  let statusBadge = (
                    <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      Idle
                    </span>
                  );
                  let borderStyle = 'border-slate-800 bg-slate-950';

                  if (node.status === 'running') {
                    statusBadge = (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 font-mono animate-pulse">
                        Running
                      </span>
                    );
                    borderStyle = 'border-teal-500 bg-teal-950/20 shadow-md shadow-teal-900/20';
                  } else if (node.status === 'done') {
                    statusBadge = (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                        Done
                      </span>
                    );
                    borderStyle = 'border-emerald-800/80 bg-slate-950';
                  } else if (node.status === 'failed') {
                    statusBadge = (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono">
                        Failed
                      </span>
                    );
                    borderStyle = 'border-rose-700 bg-rose-950/20';
                  }

                  return (
                    <div
                      key={node.id}
                      onClick={() => onSelectNode(node)}
                      className={`cursor-pointer rounded-lg p-3 border transition hover:border-slate-600 ${borderStyle} ${
                        isSelected ? 'ring-2 ring-teal-400' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-bold text-sm text-slate-100">{node.owner}</span>
                        {statusBadge}
                      </div>
                      <p className="text-xs text-slate-400 font-mono truncate">{node.id}</p>

                      {agentFinding && (
                        <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                          <span
                            className={`font-semibold ${
                              agentFinding.recommendation === 'proceed'
                                ? 'text-emerald-400'
                                : agentFinding.recommendation === 'reject'
                                ? 'text-rose-400'
                                : 'text-amber-400'
                            }`}
                          >
                            Rec: {agentFinding.recommendation}
                          </span>
                          <span className="text-slate-400 text-[11px]">
                            Conf: {(agentFinding.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <p className="text-xs text-slate-400 italic">
                * Click any node to inspect its structured Finding, evidence citations, and assumption provenance.
              </p>
            </div>
          ) : (
            <div className="text-center py-12 border border-dashed border-slate-800 rounded-lg text-slate-500 text-sm">
              Submit a decision inquiry to generate and execute the multi-agent DAG.
            </div>
          )}

          {/* Node Inspector Drawer */}
          {selectedNode && (
            <div className="bg-slate-950 border border-teal-500/40 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-teal-400" />
                  <h4 className="text-sm font-bold text-white">
                    Inspector: {selectedNode.owner} ({selectedNode.id})
                  </h4>
                </div>
                <button
                  onClick={() => onSelectNode(null)}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  Close
                </button>
              </div>

              {findings[selectedNode.owner] ? (
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400">Claim:</span>
                    <p className="text-slate-200 font-medium mt-0.5">{findings[selectedNode.owner].claim}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Proposed Assumptions:</span>
                    <ul className="list-disc pl-4 mt-1 space-y-1 text-slate-300">
                      {findings[selectedNode.owner].assumptions.map((a, i) => (
                        <li key={i}>
                          <span className="font-mono text-teal-300">{a.name}</span>: [
                          {a.low}, {a.base}, {a.high}] {a.unit} (
                          <span className="text-amber-300">{a.provenance}</span>)
                        </li>
                      ))}
                    </ul>
                  </div>
                  {findings[selectedNode.owner].evidence.length > 0 && (
                    <div>
                      <span className="text-slate-400">Factual Evidence:</span>
                      <p className="text-slate-300 italic bg-slate-900 p-2 rounded mt-1 border border-slate-800">
                        "{findings[selectedNode.owner].evidence[0].snippet}"
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-500">Agent has not posted structured finding yet.</p>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Chaos Injection & Live Event Feed (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Chaos / Failure Injection Control */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white">Chaos / Live Failure Injection (Milestone 7)</h3>
            </div>
            <p className="text-xs text-slate-400">
              Inject a simulated failure into an agent mid-run. The supervisor will detect it, trigger backoff recovery, and complete the run.
            </p>

            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-400">Target Agent:</label>
              <select
                value={selectedAgentForChaos}
                onChange={(e) => setSelectedAgentForChaos(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded px-2.5 py-1"
              >
                <option value="CTO">CTO Agent</option>
                <option value="CFO">CFO Agent</option>
                <option value="Growth">Growth Agent</option>
                <option value="Customer">Customer Agent</option>
              </select>
            </div>

            <div className="grid grid-cols-3 gap-2 pt-1">
              <button
                onClick={() => onInjectFailure(selectedAgentForChaos, 'exception')}
                className="px-2 py-1.5 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium transition"
              >
                💥 Crash
              </button>
              <button
                onClick={() => onInjectFailure(selectedAgentForChaos, 'timeout')}
                className="px-2 py-1.5 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-medium transition"
              >
                ⏱ Timeout
              </button>
              <button
                onClick={() => onInjectFailure(selectedAgentForChaos, 'bad_output')}
                className="px-2 py-1.5 rounded bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-medium transition"
              >
                ⚠️ Corrupt
              </button>
            </div>
          </div>

          {/* Real-Time Event Stream Feed */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-bold text-white">Live Event Feed (SSE)</h3>
              </div>
              <span className="text-[11px] font-mono text-slate-500">{events.length} events</span>
            </div>

            <div className="h-[360px] overflow-y-auto space-y-2 pr-1 text-xs font-mono">
              {events.length === 0 ? (
                <div className="text-center py-16 text-slate-500">Waiting for workflow events...</div>
              ) : (
                events.map((ev, i) => {
                  let badge = 'text-slate-400 bg-slate-800';
                  if (ev.type.includes('failed')) badge = 'text-rose-400 bg-rose-950/60 border border-rose-800/80';
                  if (ev.type.includes('recovery')) badge = 'text-amber-400 bg-amber-950/60 border border-amber-800/80';
                  if (ev.type.includes('conflict')) badge = 'text-amber-300 bg-amber-900/40 border border-amber-700/60';
                  if (ev.type.includes('ready') || ev.type.includes('passed')) badge = 'text-emerald-400 bg-emerald-950/60 border border-emerald-800/80';
                  if (ev.type.includes('started')) badge = 'text-teal-300 bg-teal-950/60 border border-teal-800/80';

                  return (
                    <div key={i} className="bg-slate-950 p-2.5 rounded border border-slate-800/80 space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className={`px-1.5 py-0.5 rounded font-semibold ${badge}`}>
                          {ev.type}
                        </span>
                        <span className="text-slate-500 text-[10px]">
                          {ev.ts ? new Date(ev.ts).toLocaleTimeString() : ''}
                        </span>
                      </div>
                      <p className="text-slate-300 text-[11px]">
                        {ev.agent && <span className="text-teal-400 font-bold">[{ev.agent}] </span>}
                        {JSON.stringify(ev.payload)}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

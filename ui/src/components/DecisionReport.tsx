import React, { useState } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  FileText,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  TrendingUp,
} from 'lucide-react';
import { DecisionReport } from '../types';
import { FlipPointCard } from './FlipPointCard';

interface DecisionReportProps {
  report: DecisionReport | null;
  onApprove: (strategy: string) => void;
  onReject: () => void;
  onRequestChanges: () => void;
  approvalStatus: string | null;
}

export const DecisionReportView: React.FC<DecisionReportProps> = ({
  report,
  onApprove,
  onReject,
  onRequestChanges,
  approvalStatus,
}) => {
  const [selectedStrategy, setSelectedStrategy] = useState('Strategy B (Usage Caps)');

  if (!report) {
    return (
      <div className="text-center py-24 bg-slate-900 border border-slate-800 rounded-xl">
        <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-300">No Verified Decision Report Ready Yet</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
          Submit a strategic question in the Decision Console to decompose, simulate, and generate an executive report.
        </p>
      </div>
    );
  }

  const { sections, recommendation, confidence, disclaimer } = report;
  const { executive_summary, scenario_table, outcome_ranges, conflicts, sensitivity_tornado, flip_point, assumption_ledger, risks, verification_summary } = sections;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* 1. Executive Summary Banner */}
      <div className="bg-gradient-to-r from-teal-950/60 to-slate-900 border border-teal-500/40 rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-teal-500/20 pb-4 mb-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-wider text-teal-400 font-bold">
                Final Stress-Test Recommendation
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 font-mono">
                Verified: Deterministic Math
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono border border-blue-500/30">
                {report.llm_mode || "LLM Mode: Mock (deterministic seed)"}
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-white mt-1">{recommendation}</h1>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-center">
              <span className="text-[11px] text-slate-400 uppercase font-mono">Confidence</span>
              <p className="text-lg font-bold text-teal-400">{confidence}</p>
            </div>
            <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-center">
              <span className="text-[11px] text-slate-400 uppercase font-mono">Simulations</span>
              <p className="text-lg font-bold text-slate-100">12 Runs</p>
            </div>
          </div>
        </div>

        {report.degraded_agent_banner && (
          <div className="bg-amber-950/40 border border-amber-500/50 rounded-lg p-3 my-3 text-xs text-amber-200 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{report.degraded_agent_banner}</span>
          </div>
        )}

        <p className="text-sm text-slate-200 leading-relaxed">{executive_summary.headline_thesis}</p>
      </div>

      {/* 2. Critical Flip-Point Box */}
      {flip_point && <FlipPointCard flipPoint={flip_point} />}

      {/* 3. Strategy Scenario Comparison Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Strategy Scenario Comparison</h3>
            <p className="text-xs text-slate-400">Deterministic SaaS trajectories across conservative, expected, and optimistic bounds</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Horizon: 12 & 24 Months</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-3">Strategy</th>
                <th className="py-3 px-3">Conservative MRR</th>
                <th className="py-3 px-3">Expected MRR (12mo)</th>
                <th className="py-3 px-3">Optimistic MRR</th>
                <th className="py-3 px-3">Runway</th>
                <th className="py-3 px-3">Gross Margin</th>
                <th className="py-3 px-3 text-right">12mo Net Contribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {scenario_table.map((row, idx) => {
                const isWinner = row.strategy.includes('Strategy B');
                return (
                  <tr
                    key={idx}
                    className={`hover:bg-slate-800/40 transition ${isWinner ? 'bg-teal-950/10 font-medium' : ''}`}
                  >
                    <td className="py-3 px-3 font-semibold text-white flex items-center gap-1.5">
                      {isWinner && <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />}
                      {row.strategy}
                    </td>
                    <td className="py-3 px-3 text-slate-400">${row.mrr_month_12_conservative.toLocaleString()}</td>
                    <td className="py-3 px-3 text-teal-400 font-bold">${row.mrr_month_12_expected.toLocaleString()}</td>
                    <td className="py-3 px-3 text-slate-400">${row.mrr_month_12_optimistic.toLocaleString()}</td>
                    <td className="py-3 px-3 text-amber-400">{row.runway_months_12_expected.toFixed(1)} mo</td>
                    <td className="py-3 px-3">{row.gross_margin_12_expected.toFixed(1)}%</td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-slate-100">
                      ${row.net_contribution_12.toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Outcome Ranges (Monte Carlo Distributions) */}
      {outcome_ranges && outcome_ranges.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              <div>
                <h3 className="text-base font-bold text-white">Outcome Ranges (Monte Carlo Distributions)</h3>
                <p className="text-xs text-slate-400">
                  250 iterations across reconciled assumption bounds using triangular sampling (Seed: 42)
                </p>
              </div>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-700/50 text-indigo-300">
              Probabilistic Model
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="py-2.5 px-3">Strategy</th>
                  <th className="py-2.5 px-3 text-center">Win Prob (p_best)</th>
                  <th className="py-2.5 px-3 text-center">Feasibility (p_feasible)</th>
                  <th className="py-2.5 px-3 text-right">MRR (p10 / p50 / p90)</th>
                  <th className="py-2.5 px-3 text-right">Net Contribution (p10 / p50 / p90)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {outcome_ranges.map((mc, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-medium text-slate-200">{mc.strategy}</td>
                    <td className="py-3 px-3 text-center">
                      <span className="font-mono font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-2 py-0.5 rounded">
                        {(mc.p_best * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span className="font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-800/50 px-2 py-0.5 rounded">
                        {(mc.p_feasible * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-300">
                      ${Math.round(mc.mrr_month_12_p10).toLocaleString()} / ${Math.round(mc.mrr_month_12_p50).toLocaleString()} / ${Math.round(mc.mrr_month_12_p90).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold text-slate-100">
                      ${Math.round(mc.net_contribution_12_p10).toLocaleString()} / ${Math.round(mc.net_contribution_12_p50).toLocaleString()} / ${Math.round(mc.net_contribution_12_p90).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Conflict Resolution Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <div>
            <h3 className="text-base font-bold text-white">Simulation-Based Conflict Resolution</h3>
            <p className="text-xs text-slate-400">
              Disagreements settled by simulating competing agent parameters (R3: Never voting or LLM preference)
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {conflicts.map((conf, idx) => (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  Agents: {conf.agents.join(' vs ')}
                </span>
                <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Resolved with Simulation
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">{conf.disputed_item}</p>
              <div className="bg-slate-900 p-3 rounded text-xs text-slate-200 border border-slate-800 leading-relaxed">
                {conf.resolution}
              </div>
              {conf.simulation_ids.length > 0 && (
                <div className="text-[11px] text-slate-400 font-mono">
                  Simulation Runs: {conf.simulation_ids.map((id) => <span key={id} className="text-teal-400 mr-2">[{id}]</span>)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 4.5 Agent Discussion & Multi-Turn Deliberation */}
      {sections.discussion_messages && sections.discussion_messages.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Agent Discussion & Multi-Turn Deliberation</h3>
              <p className="text-xs text-slate-400">Inter-agent critique and rebuttal protocol before simulation modeling</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-teal-400 font-mono border border-slate-700">
              {sections.discussion_messages.length} Messages Exchanged
            </span>
          </div>

          <div className="space-y-3">
            {sections.discussion_messages.map((msg, i) => (
              <div key={i} className="bg-slate-950 border border-slate-800/80 rounded-lg p-3.5 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-teal-300">{msg.sender}</span>
                    <span className="text-slate-500 font-mono">&rarr;</span>
                    <span className="text-slate-400 font-medium">{msg.recipient}</span>
                  </div>
                  <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border ${
                    msg.kind === 'critique'
                      ? 'bg-amber-950/40 text-amber-300 border-amber-800/50'
                      : msg.kind === 'rebuttal'
                      ? 'bg-blue-950/40 text-blue-300 border-blue-800/50'
                      : 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
                    {msg.kind}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{msg.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Sensitivity Tornado Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div>
          <h3 className="text-base font-bold text-white">One-At-A-Time Sensitivity Analysis (Tornado)</h3>
          <p className="text-xs text-slate-400">
            Ranked impact on 12-Month Net Contribution when varying each assumption from Low to High
          </p>
        </div>

        <div className="space-y-3">
          {sensitivity_tornado.map((t, idx) => {
            const maxSwing = sensitivity_tornado[0].swing;
            const barWidth = Math.max(10, (t.swing / maxSwing) * 100);

            return (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">
                    {idx + 1}. {t.assumption_name}{' '}
                    <span className="text-slate-400 font-normal">
                      ({t.low_param} to {t.high_param} {t.unit})
                    </span>
                  </span>
                  <span className="font-mono font-bold text-teal-400">±${t.swing.toLocaleString()}</span>
                </div>
                <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="bg-gradient-to-r from-teal-600 to-teal-400 h-full rounded-full transition-all duration-500"
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 6. Assumption Ledger with Provenance */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Assumption Ledger with Provenance</h3>
            <p className="text-xs text-slate-400">Full audit trail answering "Where did this number come from?"</p>
          </div>
          <span className="text-xs text-slate-400">{assumption_ledger.length} Assumptions Audited</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Assumption</th>
                <th className="py-2.5 px-3">Low</th>
                <th className="py-2.5 px-3">Base</th>
                <th className="py-2.5 px-3">High</th>
                <th className="py-2.5 px-3">Unit</th>
                <th className="py-2.5 px-3">Provenance</th>
                <th className="py-2.5 px-3">Proposed By</th>
                <th className="py-2.5 px-3">Skeptic Check</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {assumption_ledger.map((a, i) => {
                let provColor = 'text-slate-300 bg-slate-800';
                if (a.provenance === 'verified_data') provColor = 'text-emerald-300 bg-emerald-950/60 border border-emerald-800/80';
                if (a.provenance === 'external_research') provColor = 'text-sky-300 bg-sky-950/60 border border-sky-800/80';
                if (a.provenance === 'simulated_estimate') provColor = 'text-purple-300 bg-purple-950/60 border border-purple-800/80';
                if (a.provenance === 'ai_assumption') provColor = 'text-amber-300 bg-amber-950/60 border border-amber-800/80';

                return (
                  <tr key={i} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-100">{a.name}</td>
                    <td className="py-2.5 px-3 text-slate-400">{a.low}</td>
                    <td className="py-2.5 px-3 font-bold text-teal-400">{a.base}</td>
                    <td className="py-2.5 px-3 text-slate-400">{a.high}</td>
                    <td className="py-2.5 px-3 text-slate-400">{a.unit}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${provColor}`}>
                        {a.provenance}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 font-medium">{a.proposed_by || 'System'}</td>
                    <td className="py-2.5 px-3">
                      {a.challenged_by_skeptic ? (
                        <span className="text-amber-400 text-[11px] font-medium flex items-center gap-1">
                          ⚠️ Challenged
                        </span>
                      ) : (
                        <span className="text-emerald-400 text-[11px] flex items-center gap-1">
                          ✓ Verified
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 7. Key Risks and Mitigation */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
        <h3 className="text-base font-bold text-white">Risks, Uncertainties & Flip Triggers</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {risks.map((r, i) => (
            <div key={i} className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
              <span className="text-xs font-bold text-amber-400">{r.category}</span>
              <p className="text-xs text-slate-300">{r.description}</p>
              <p className="text-[11px] text-teal-400 italic pt-1 border-t border-slate-800/80">
                Mitigation: {r.mitigation}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 8. Verification Summary Checks */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
        <h3 className="text-base font-bold text-white">Deterministic Verification Checks</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {verification_summary.map((v, i) => (
            <div key={i} className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-mono text-xs font-bold text-slate-200">{v.check_name}</span>
                <p className="text-xs text-slate-400 mt-0.5">{v.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 8. Human in the Loop Approval Gate */}
      <div className="bg-slate-900 border border-teal-500/50 rounded-xl p-6 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-teal-400" />
              Human-in-the-Loop Approval Gate (Hard Rule R5)
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              The system never executes external business actions autonomously. Approval persists the decision into calibration memory.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Chosen Strategy:</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded px-3 py-1.5 font-medium"
            >
              <option value="Strategy B (Usage Caps)">Strategy B (Usage Caps) - Recommended</option>
              <option value="Strategy A (Limited Features)">Strategy A (Limited Features)</option>
              <option value="Strategy C (Funnel Optimization Only)">Strategy C (Funnel Optimization)</option>
            </select>
          </div>
        </div>

        {approvalStatus ? (
          <div className="bg-emerald-950/40 border border-emerald-500/50 p-4 rounded-lg flex items-center gap-3 text-emerald-300">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <span className="text-sm font-semibold">
              Decision Recorded: {approvalStatus}. Added to Calibration screen as "Awaiting Outcome".
            </span>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button
              onClick={() => onApprove(selectedStrategy)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm transition shadow-sm"
            >
              <ThumbsUp className="w-4 h-4" />
              Approve Decision
            </button>
            <button
              onClick={onRequestChanges}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm border border-slate-700 transition"
            >
              <RotateCcw className="w-4 h-4" />
              Request Re-Run / Changes
            </button>
            <button
              onClick={onReject}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/80 font-medium text-sm transition"
            >
              <ThumbsDown className="w-4 h-4" />
              Reject Proposal
            </button>
          </div>
        )}
      </div>

      {/* Mandatory Disclaimer */}
      <div className="text-center py-4 border-t border-slate-800/80">
        <p className="text-xs text-slate-500 max-w-2xl mx-auto italic">{disclaimer}</p>
      </div>
    </div>
  );
};

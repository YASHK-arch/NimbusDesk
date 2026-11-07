import React, { useEffect, useState } from 'react';
import { Clock, AlertCircle } from 'lucide-react';

interface CalibrationData {
  seeded_decisions: Array<{
    id: string;
    question: string;
    decision_date: string;
    chosen_strategy: string;
    predicted_metrics: Record<string, any>;
    actual_metrics: Record<string, any>;
    error_analysis: {
      metric_evaluated: string;
      absolute_error_pct: number;
      most_wrong_assumption: string;
      lesson_learned: string;
    };
  }>;
  live_approved_decisions: Array<{
    decision_id: string;
    chosen_strategy: string;
    approved_at: string;
    predicted_metrics: Record<string, any>;
    status: string;
  }>;
  calibration: {
    average_absolute_error_pct: number;
    most_wrong_assumptions: Array<{ assumption: string; avg_error: number }>;
    note: string;
  };
}

export const CalibrationScreen: React.FC = () => {
  const [data, setData] = useState<CalibrationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/history')
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching calibration data:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="text-center py-20 text-slate-500 font-mono">Loading calibration telemetry...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-rose-400 font-mono">Failed to load calibration history.</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-tight">
                Decision Memory & Forecast Calibration
              </h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-medium">
                Seeded Demo Data
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Tracks predicted vs. actual outcomes to calculate prediction error and expose repeatedly wrong assumptions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-center">
              <span className="text-[11px] text-slate-400 uppercase font-mono">Avg Model Error</span>
              <p className="text-xl font-bold text-teal-400">
                ±{data.calibration.average_absolute_error_pct}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Calibration Diagnostics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.calibration.most_wrong_assumptions.map((item, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-mono">Repeated Error #{idx + 1}</span>
              <span className="text-xs font-bold text-rose-400 font-mono">±{item.avg_error}% Error</span>
            </div>
            <h4 className="text-sm font-semibold text-slate-200">{item.assumption}</h4>
            <p className="text-xs text-slate-500">Prior distribution requires tightening based on retrospective drift.</p>
          </div>
        ))}
      </div>

      {/* Live Approved Decisions (Awaiting Outcome) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-400" />
            <h3 className="text-base font-bold text-white">Live Approved Decisions (Awaiting Outcome)</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">{data.live_approved_decisions.length} Enqueued</span>
        </div>

        {data.live_approved_decisions.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
            No live decisions approved yet. Approve a verified report in the Decision Report tab to persist it here.
          </div>
        ) : (
          <div className="space-y-2">
            {data.live_approved_decisions.map((dec, i) => (
              <div key={i} className="bg-slate-950 p-3 rounded-lg border border-teal-500/30 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-100">{dec.chosen_strategy}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 font-mono border border-teal-500/30">
                      Awaiting Outcome
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    ID: {dec.decision_id} | Approved: {new Date(dec.approved_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-right text-xs font-mono">
                  <span className="text-slate-400">Predicted 12mo MRR: </span>
                  <span className="text-teal-400 font-bold">${dec.predicted_metrics?.mrr_month_12?.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Historical Seeded Decisions Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-white">Historical Seeded Decisions (Predicted vs. Actual)</h3>

        <div className="space-y-4">
          {data.seeded_decisions.map((dec) => (
            <div key={dec.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                <div>
                  <span className="text-xs font-mono text-teal-400 font-bold">[{dec.id}]</span>{' '}
                  <span className="text-sm font-bold text-white">{dec.question}</span>
                </div>
                <span className="text-xs text-slate-500 font-mono">{dec.decision_date}</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="bg-slate-900/60 p-3 rounded border border-slate-800 space-y-1">
                  <span className="text-slate-400 uppercase font-mono text-[10px]">Predicted Metrics:</span>
                  <pre className="text-slate-300 font-mono text-[11px]">
                    {JSON.stringify(dec.predicted_metrics, null, 2)}
                  </pre>
                </div>

                <div className="bg-slate-900/60 p-3 rounded border border-slate-800 space-y-1">
                  <span className="text-emerald-400 uppercase font-mono text-[10px]">Actual Realized Metrics:</span>
                  <pre className="text-slate-300 font-mono text-[11px]">
                    {JSON.stringify(dec.actual_metrics, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="bg-amber-950/20 border border-amber-500/30 rounded p-2.5 text-xs text-slate-300 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-amber-300">
                    Retrospective Error: ±{dec.error_analysis.absolute_error_pct}% ({dec.error_analysis.most_wrong_assumption})
                  </span>
                  <p className="text-slate-400 mt-0.5">{dec.error_analysis.lesson_learned}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

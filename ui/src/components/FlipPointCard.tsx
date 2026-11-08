import React from 'react';
import { Sliders, ShieldCheck } from 'lucide-react';

interface FlipPointData {
  exists?: boolean;
  primary_strategy: string;
  competing_strategy: string;
  parameter_name: string;
  threshold: number | null;
  threshold_display: string;
  statement: string;
  flip_value?: number | null;
  tested_range?: [number, number];
  outcome_at_low?: number;
  outcome_at_high?: number;
  outcome_at_flip?: number;
}

interface FlipPointCardProps {
  flipPoint: FlipPointData;
}

export const FlipPointCard: React.FC<FlipPointCardProps> = ({ flipPoint }) => {
  const isRobust = flipPoint.exists === false;

  if (isRobust) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex items-start gap-4 shadow-xs">
        <div className="bg-emerald-100 p-2.5 rounded-lg text-emerald-700 shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-emerald-900 uppercase tracking-wide">
            Robust to Variation (No Flip Point)
          </h3>
          <p className="text-sm text-gray-800 font-medium mt-1">{flipPoint.statement}</p>
          <span className="text-xs text-emerald-700 mt-1 inline-block">
            Parametric sweep confirms the strategy ranking remains invariant across tested bounds.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-4 shadow-xs">
      <div className="bg-amber-100 p-2.5 rounded-lg text-amber-700 shrink-0">
        <Sliders className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wide">
          Deterministic Flip-Point Condition
        </h3>
        <p className="text-sm text-gray-800 font-medium mt-1">{flipPoint.statement}</p>
        <span className="text-xs text-amber-800 mt-1 inline-block">
          Threshold derived via bisection search across {flipPoint.primary_strategy} vs {flipPoint.competing_strategy}.
        </span>
      </div>
    </div>
  );
};

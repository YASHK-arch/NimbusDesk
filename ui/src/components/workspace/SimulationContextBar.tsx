import React, { useState, useRef, useEffect } from 'react';
import {
  Calendar as CalendarIcon,
  AlertTriangle,
  ShieldCheck,
  Activity,
  Check,
  Clock,
  TrendingUp,
  ChevronDown,
} from 'lucide-react';
import type { CompanySnapshot } from '../../types';
import type { WorkspaceModalTab } from './WorkspaceModal';

interface SimulationContextBarProps {
  forecastYear: number;
  forecastPeriod: string;
  onYearChange: (year: number, period?: string) => void;
  company: CompanySnapshot | null;
  isSimulating: boolean;
  onOpenModal?: (tab: WorkspaceModalTab) => void;
  hasReport?: boolean;
}

export const SimulationContextBar: React.FC<SimulationContextBarProps> = ({
  forecastYear,
  forecastPeriod,
  onYearChange,
  company,
  isSimulating,
  onOpenModal,
  hasReport,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempYear, setTempYear] = useState(forecastYear);
  const [tempPeriod, setTempPeriod] = useState(forecastPeriod || 'Full Year');
  const [tempDate, setTempDate] = useState(`${forecastYear}-12-31`);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Sync temp state when props change
  useEffect(() => {
    setTempYear(forecastYear);
    setTempDate(`${forecastYear}-12-31`);
  }, [forecastYear]);

  // Click outside to close popover
  useEffect(() => {
    if (!isOpen) return;
    const handleOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', handleOutside);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleOutside);
      document.removeEventListener('keydown', handleKey);
    };
  }, [isOpen]);

  const handleApply = (yr: number, prd: string) => {
    onYearChange(yr, prd);
    setIsOpen(false);
  };

  const years = [2023, 2024, 2025, 2026, 2027];
  const periods = ['Full Year', 'Q1', 'Q2', 'Q3', 'Q4'];

  // Horizon calculations based on selected year
  const yearDelta = tempYear - 2024;
  const currentMRR = company?.mrr ?? 0;

  return (
    <div className="h-10 bg-white border-b border-gray-200 flex items-center px-4 gap-4 shrink-0 relative z-30 select-none">
      {/* Date & Forecast Horizon Selector */}
      <div className="relative" ref={popoverRef}>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 font-medium">Date:</span>
          <button
            onClick={() => setIsOpen((v) => !v)}
            title="Click to change simulation forecast year &amp; timeline"
            className="flex items-center gap-2 border border-gray-300 hover:border-blue-500 rounded px-2.5 py-1 bg-white hover:bg-gray-50 transition cursor-pointer text-sm font-semibold text-gray-800 shadow-sm"
          >
            <span>
              {forecastPeriod && forecastPeriod !== 'Full Year' ? `${forecastPeriod} ` : ''}
              {forecastYear}
            </span>
            <CalendarIcon className="w-3.5 h-3.5 text-blue-600" />
            <ChevronDown className={`w-3 h-3 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Date / Forecast Horizon Popover */}
        {isOpen && (
          <div className="absolute top-full left-0 mt-2 w-80 bg-white border border-gray-200 rounded-xl shadow-2xl z-50 p-4 animate-in fade-in slide-in-from-top-1 text-gray-800">
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-gray-100">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-gray-800">
                <Clock className="w-3.5 h-3.5 text-blue-600" />
                <span>Simulation Forecast Horizon</span>
              </div>
              <span className="text-[11px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono font-medium">
                FY{tempYear}
              </span>
            </div>

            {/* Quick Year Selector */}
            <div className="mb-3">
              <label className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">
                Target Forecast Year
              </label>
              <div className="grid grid-cols-5 gap-1.5">
                {years.map((y) => {
                  const isSelected = tempYear === y;
                  return (
                    <button
                      key={y}
                      onClick={() => {
                        setTempYear(y);
                        setTempDate(`${y}-12-31`);
                      }}
                      className={`py-1.5 text-xs font-semibold rounded transition text-center ${
                        isSelected
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {y}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Period Selector */}
            <div className="mb-3">
              <label className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">
                Period Granularity
              </label>
              <div className="grid grid-cols-5 gap-1">
                {periods.map((p) => {
                  const isSelected = tempPeriod === p;
                  return (
                    <button
                      key={p}
                      onClick={() => setTempPeriod(p)}
                      className={`py-1 text-[11px] font-medium rounded transition text-center ${
                        isSelected
                          ? 'bg-slate-800 text-white'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      {p}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Target Checkpoint Date Picker */}
            <div className="mb-3">
              <label className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">
                Exact Checkpoint Date
              </label>
              <input
                type="date"
                value={tempDate}
                onChange={(e) => {
                  setTempDate(e.target.value);
                  const parsed = new Date(e.target.value);
                  if (!isNaN(parsed.getFullYear())) {
                    setTempYear(parsed.getFullYear());
                  }
                }}
                className="w-full text-xs border border-gray-300 rounded px-2.5 py-1.5 text-gray-800 outline-none focus:ring-1 focus:ring-blue-500 bg-white"
              />
            </div>

            {/* Real Snapshot & Horizon Context */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 mb-3 text-xs">
              <div className="flex items-center gap-1.5 text-slate-700 font-semibold mb-1">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                <span>Simulation Horizon ({tempYear})</span>
              </div>
              <div className="flex justify-between text-slate-500 text-[11px] mb-1">
                <span>Baseline Horizon:</span>
                <span className="font-medium text-slate-700">
                  {yearDelta <= 0 ? 'Current Baseline' : `+${yearDelta * 12} Months Forward`}
                </span>
              </div>
              <div className="flex justify-between text-slate-500 text-[11px]">
                <span>Current Baseline MRR:</span>
                <span className="font-semibold text-emerald-600">
                  ${(currentMRR / 1000).toFixed(1)}k/mo
                </span>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-between gap-2 pt-2 border-t border-gray-100">
              <button
                onClick={() => {
                  setTempYear(2024);
                  setTempPeriod('Full Year');
                  handleApply(2024, 'Full Year');
                }}
                className="text-xs text-gray-500 hover:text-gray-800 underline"
              >
                Reset to 2024
              </button>
              <button
                onClick={() => handleApply(tempYear, tempPeriod)}
                className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow transition"
              >
                <Check className="w-3.5 h-3.5" />
                Apply Timeline
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px h-5 bg-gray-200" />

      {/* Synthetic data badge */}
      <button
        onClick={() => onOpenModal?.('company')}
        title="View NimbusDesk baseline company dataset"
        className="flex items-center gap-1.5 text-xs text-amber-600 hover:text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-2.5 py-1 rounded transition cursor-pointer"
      >
        <AlertTriangle className="w-3.5 h-3.5" />
        <span>Synthetic Data: NimbusDesk</span>
      </button>

      {/* Quick Verified Report Pill Badge when ready */}
      {hasReport && (
        <button
          onClick={() => onOpenModal?.('report')}
          className="flex items-center gap-1.5 text-xs bg-emerald-50 text-emerald-700 border border-emerald-300 hover:bg-emerald-100 px-2.5 py-1 rounded-full transition font-semibold"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Decision Report Ready (Click to Review &amp; Approve)</span>
        </button>
      )}

      <div className="flex-1" />

      {/* Company + status */}
      <div className="flex items-center gap-2">
        {company && (
          <button
            onClick={() => onOpenModal?.('company')}
            title="Click to view company metrics"
            className="text-sm text-gray-700 hover:text-blue-600 font-medium transition cursor-pointer"
          >
            {company.name}
          </button>
        )}
        {isSimulating ? (
          <button
            onClick={() => onOpenModal?.('dag')}
            title="Click to inspect Live DAG &amp; agent execution"
            className="flex items-center gap-1 text-xs bg-blue-50 border border-blue-200 text-blue-600 px-2 py-0.5 rounded animate-pulse cursor-pointer hover:bg-blue-100"
          >
            <Activity className="w-3 h-3 text-blue-500 animate-spin" />
            Simulating…
          </button>
        ) : (
          <span className="text-xs bg-gray-100 text-gray-500 border border-gray-200 px-2 py-0.5 rounded">
            Idle
          </span>
        )}
      </div>
    </div>
  );
};

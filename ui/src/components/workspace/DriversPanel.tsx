import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Search, Filter, MoreHorizontal, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react';
import type { Driver } from '../../types';

interface DriversPanelProps {
  drivers: Driver[];
  onDriverChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
  onReset: () => void;
  highlightAll?: boolean;
}

type GroupState = Record<string, boolean>; // groupName -> isExpanded

function groupDrivers(drivers: Driver[]): Record<string, Driver[]> {
  return drivers.reduce<Record<string, Driver[]>>((acc, d) => {
    if (!acc[d.group]) acc[d.group] = [];
    acc[d.group].push(d);
    return acc;
  }, {});
}

const DISTRIBUTION_OPTIONS = ['Normal', 'Uniform', 'Triangular'] as const;

// ─── Driver Row ───────────────────────────────────────────────────────────────

interface DriverRowProps {
  driver: Driver;
  onChange: (id: string, field: 'low' | 'high' | 'distribution', value: number | string) => void;
  highlighted?: boolean;
}

const DriverRow: React.FC<DriverRowProps> = ({ driver, onChange, highlighted }) => {
  const lowStr = String(driver.low);
  const highStr = String(driver.high);
  const isInvalid = driver.low > driver.high;

  const inputBase =
    'w-14 text-xs border rounded px-1.5 py-0.5 text-right outline-none focus:ring-1 focus:ring-blue-500 transition';
  const inputValid = highlighted
    ? 'border-blue-400 text-blue-900 bg-blue-50/50'
    : 'border-gray-300 text-gray-700 bg-white';
  const inputInvalid = 'border-red-400 bg-red-50 text-red-700';

  return (
    <tr
      className={`border-b border-gray-100 hover:bg-gray-50 group transition ${
        highlighted ? 'bg-blue-50/20' : ''
      }`}
      title={driver.tooltip}
    >
      {/* Name */}
      <td className="pl-5 pr-2 py-1.5 text-sm text-gray-700 whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          {driver.modified && (
            <span
              className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0"
              title="Modified from baseline"
            />
          )}
          <span className={highlighted ? 'font-semibold text-blue-900' : ''}>{driver.name}</span>
          {isInvalid && (
            <span title="Invalid range: low > high">
              <AlertCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
            </span>
          )}
        </div>
      </td>

      {/* Value Range */}
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-1">
          <input
            type="number"
            value={lowStr}
            onChange={(e) => onChange(driver.id, 'low', parseFloat(e.target.value) || 0)}
            className={`${inputBase} ${isInvalid ? inputInvalid : inputValid}`}
          />
          <span className="text-gray-400 text-xs">to</span>
          <input
            type="number"
            value={highStr}
            onChange={(e) => onChange(driver.id, 'high', parseFloat(e.target.value) || 0)}
            className={`${inputBase} ${isInvalid ? inputInvalid : inputValid}`}
          />
          <span className="text-xs text-gray-500 w-8">{driver.unit}</span>
        </div>
      </td>

      {/* Distribution */}
      <td className="px-2 py-1.5">
        <select
          value={driver.distribution}
          onChange={(e) => onChange(driver.id, 'distribution', e.target.value)}
          className="text-xs border border-gray-300 rounded px-1 py-0.5 text-gray-700 bg-white outline-none focus:ring-1 focus:ring-blue-500"
        >
          {DISTRIBUTION_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </td>
    </tr>
  );
};

// ─── Group Header ─────────────────────────────────────────────────────────────

interface GroupHeaderProps {
  name: string;
  count: number;
  expanded: boolean;
  onToggle: () => void;
}

const GroupHeader: React.FC<GroupHeaderProps> = ({ name, count, expanded, onToggle }) => (
  <tr
    className="bg-gray-50 cursor-pointer select-none hover:bg-gray-100"
    onClick={onToggle}
  >
    <td colSpan={3} className="px-3 py-1.5">
      <div className="flex items-center gap-1.5">
        {expanded
          ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
          : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
        }
        <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{name}</span>
        <span className="text-xs text-gray-400 ml-1">{count}</span>
      </div>
    </td>
  </tr>
);

// ─── More Actions Dropdown ────────────────────────────────────────────────────

interface MoreMenuProps {
  onReset: () => void;
}

const MoreMenu: React.FC<MoreMenuProps> = ({ onReset }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="p-1 rounded hover:bg-gray-100 text-gray-500"
        title="More actions"
      >
        <MoreHorizontal className="w-4 h-4" />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-44 bg-white border border-gray-200 rounded shadow-lg z-50 py-1">
          <button
            onClick={() => { onReset(); setOpen(false); }}
            className="w-full text-left px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
          >
            Reset All Drivers
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Main Panel ───────────────────────────────────────────────────────────────

export const DriversPanel: React.FC<DriversPanelProps> = ({
  drivers,
  onDriverChange,
  onReset,
  highlightAll = false,
}) => {
  const [search, setSearch] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  const allGroups = Array.from(new Set(drivers.map((d) => d.group)));
  const [groupState, setGroupState] = useState<GroupState>(() =>
    Object.fromEntries(allGroups.map((g) => [g, true]))
  );

  // If highlightAll changes to true, expand all groups
  useEffect(() => {
    if (highlightAll) {
      setGroupState(Object.fromEntries(allGroups.map((g) => [g, true])));
    }
  }, [highlightAll]);

  const toggleGroup = useCallback((name: string) => {
    setGroupState((prev) => ({ ...prev, [name]: !prev[name] }));
  }, []);

  const handleReset = () => {
    if (window.confirm('Reset all drivers to their baseline values?')) onReset();
  };

  const filtered = search
    ? drivers.filter((d) => d.name.toLowerCase().includes(search.toLowerCase()))
    : drivers;

  const grouped = groupDrivers(filtered);

  return (
    <div className="flex flex-col h-full border-r border-gray-200 bg-white overflow-hidden" style={{ width: '30%' }}>
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-100 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-gray-800">Drivers</span>
          <div className="flex items-center gap-1">
            <MoreMenu onReset={handleReset} />
            <button className="p-1 rounded hover:bg-gray-100 text-gray-500" title="Filter">
              <Filter className="w-4 h-4" />
            </button>
          </div>
        </div>
        {/* Search */}
        <div className="flex items-center gap-1.5 border border-gray-300 rounded px-2 py-1 bg-white focus-within:ring-1 focus-within:ring-blue-500">
          <Search className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search drivers…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 text-xs outline-none text-gray-700 placeholder-gray-400 bg-transparent"
          />
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 bg-white z-10">
            <tr className="border-b border-gray-200">
              <th className="text-left pl-3 pr-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                Driver
              </th>
              <th className="text-left px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                Value Range
              </th>
              <th className="text-left px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide whitespace-nowrap">
                Distribution
              </th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(grouped).map(([groupName, groupDrivers]) => (
              <React.Fragment key={groupName}>
                <GroupHeader
                  name={groupName}
                  count={groupDrivers.length}
                  expanded={groupState[groupName] ?? true}
                  onToggle={() => toggleGroup(groupName)}
                />
                {(groupState[groupName] ?? true) &&
                  groupDrivers.map((d) => (
                    <DriverRow
                      key={d.id}
                      driver={d}
                      onChange={onDriverChange}
                      highlighted={highlightAll}
                    />
                  ))
                }
              </React.Fragment>
            ))}
            {Object.keys(grouped).length === 0 && (
              <tr>
                <td colSpan={3} className="text-center py-8 text-sm text-gray-400">
                  No drivers match your search.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 px-3 py-2 shrink-0 flex justify-between items-center">
        <button
          onClick={handleReset}
          className="text-xs border border-gray-300 text-gray-700 hover:bg-gray-50 px-3 py-1 rounded transition"
        >
          Reset
        </button>
        {highlightAll && (
          <span className="text-[11px] text-blue-600 font-medium">All 12 Drivers Selected</span>
        )}
      </div>
    </div>
  );
};

import React from 'react';
import { Layers, ShieldCheck, Activity, LineChart, Network, Database, LayoutDashboard } from 'lucide-react';

interface NavbarProps {
  currentTab: 'workspace' | 'console' | 'report' | 'calibration' | 'graph';
  setCurrentTab: (tab: 'workspace' | 'console' | 'report' | 'calibration' | 'graph') => void;
  hasReport: boolean;
  status: string;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, hasReport, status }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-3">
      <div className="max-w-full mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="bg-teal-500/10 p-2 rounded-lg border border-teal-500/30 text-teal-400">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight">VentureTwin</span>
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono border border-slate-700">
                SwarmFlow Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Multi-Agent Coordination &amp; SaaS Decision Stress-Test Platform
            </p>
          </div>
        </div>

        {/* Global Synthetic Data Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium">
            <Database className="w-3.5 h-3.5" />
            <span>Synthetic Data: NimbusDesk</span>
          </div>

          {status === 'running' && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-mono animate-pulse">
              <Activity className="w-3.5 h-3.5" />
              <span>Agents Active</span>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          {/* Simulation Workspace — primary new tab */}
          <button
            onClick={() => setCurrentTab('workspace')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              currentTab === 'workspace'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Simulation Workspace
          </button>

          <button
            onClick={() => setCurrentTab('console')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              currentTab === 'console'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Decision Console
          </button>

          <button
            onClick={() => setCurrentTab('report')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              currentTab === 'report'
                ? 'bg-teal-600 text-white shadow-sm'
                : hasReport
                ? 'text-teal-400 hover:bg-slate-900 font-semibold'
                : 'text-slate-500 hover:text-slate-400 hover:bg-slate-900'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Decision Report
            {hasReport && <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />}
          </button>

          <button
            onClick={() => setCurrentTab('calibration')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              currentTab === 'calibration'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <LineChart className="w-3.5 h-3.5" />
            Calibration &amp; History
          </button>

          <button
            onClick={() => setCurrentTab('graph')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              currentTab === 'graph'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            Company Graph
          </button>
        </nav>
      </div>
    </header>
  );
};

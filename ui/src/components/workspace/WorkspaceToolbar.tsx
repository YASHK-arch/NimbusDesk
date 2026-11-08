import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronDown,
  RotateCcw,
  RotateCw,
  RefreshCw,
  Bookmark,
  ChevronRight,
} from 'lucide-react';
import type { OutputVariable } from '../../types';
import type { WorkspaceModalTab } from './WorkspaceModal';

// ─── Types ──────────────────────────────────────────────────────────────────

interface WorkspaceToolbarProps {
  onRunSimulation: () => void;
  isSimulating: boolean;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onResetDrivers: () => void;
  onExportData: () => void;
  onImportData: () => void;
  onExportReport?: () => void;
  onOpenModal?: (tab: WorkspaceModalTab) => void;
  hasReport?: boolean;
  onNewSimulation?: () => void;
  onCloseSimulation?: () => void;
  onDuplicateSimulation?: () => void;
  onFindDriver?: () => void;
  onSelectAllDrivers?: () => void;
  onExplainResults?: () => void;
  onCut?: () => void;
  onCopy?: () => void;
  onPaste?: () => void;
  onSave?: () => void;
  onSaveAs?: () => void;
  onShareSimulation?: () => void;
  showDrivers: boolean;
  showResults: boolean;
  showAssistant: boolean;
  showScenarioGroups: boolean;
  showDistribution: boolean;
  showGridlines: boolean;
  showDataLabels: boolean;
  chartType: 'area' | 'line' | 'bar';
  zoom: number;
  onToggleDrivers: () => void;
  onToggleResults: () => void;
  onToggleAssistant: () => void;
  onToggleScenarioGroups: () => void;
  onToggleDistribution: () => void;
  onToggleGridlines: () => void;
  onToggleDataLabels: () => void;
  onChartTypeChange: (type: 'area' | 'line' | 'bar') => void;
  onResetLayout: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  outputVariable: OutputVariable;
  onOutputVariableChange: (v: OutputVariable) => void;
  theme: 'light' | 'dark';
  onThemeChange: (t: 'light' | 'dark') => void;
}

// ─── Menu hook ───────────────────────────────────────────────────────────────

function useMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const kbHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    document.addEventListener('keydown', kbHandler);
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('keydown', kbHandler);
    };
  }, [open]);

  return { open, setOpen, ref };
}

// ─── Shared menu item components ─────────────────────────────────────────────

interface MenuItemProps {
  label: string;
  disabled?: boolean;
  onClick?: () => void;
  hint?: string;
  checkmark?: boolean;
}

const MenuItem: React.FC<MenuItemProps> = ({ label, disabled, onClick, hint, checkmark }) => (
  <button
    disabled={disabled}
    onClick={onClick}
    title={disabled && hint ? hint : undefined}
    className={`w-full text-left px-3 py-1.5 text-xs flex items-center justify-between rounded transition
      ${disabled
        ? 'text-gray-400 cursor-not-allowed'
        : 'text-gray-700 hover:bg-gray-100 cursor-pointer'
      }`}
  >
    <span className="flex items-center gap-1.5">
      {checkmark !== undefined && (
        <span className={`w-3 h-3 inline-block font-bold ${checkmark ? 'text-blue-600' : 'text-transparent'}`}>
          ✓
        </span>
      )}
      {label}
    </span>
  </button>
);

const MenuDivider = () => <div className="my-1 border-t border-gray-200" />;

interface MenuGroupProps {
  children: React.ReactNode;
}
const MenuGroup: React.FC<MenuGroupProps> = ({ children }) => (
  <div className="py-0.5">{children}</div>
);

// ─── FILE MENU ────────────────────────────────────────────────────────────────

const FileMenu: React.FC<{
  onExport: () => void;
  onImport: () => void;
  onExportReport?: () => void;
  onOpenModal?: (tab: WorkspaceModalTab) => void;
  hasReport?: boolean;
  onNewSimulation?: () => void;
  onCloseSimulation?: () => void;
  onDuplicateSimulation?: () => void;
  onSave?: () => void;
  onSaveAs?: () => void;
  onShareSimulation?: () => void;
}> = ({
  onExport,
  onImport,
  onExportReport,
  onOpenModal,
  hasReport,
  onNewSimulation,
  onCloseSimulation,
  onDuplicateSimulation,
  onSave,
  onSaveAs,
  onShareSimulation,
}) => {
  const { open, setOpen, ref } = useMenu();
  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="px-2.5 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-0.5"
      >
        File <ChevronDown className="w-3 h-3 ml-0.5 text-gray-400" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-xl z-50 py-1">
          <MenuGroup>
            <MenuItem
              label="New Simulation"
              onClick={() => {
                if (onNewSimulation) onNewSimulation();
                else onOpenModal?.('new_simulation');
                setOpen(false);
              }}
            />
            <MenuItem
              label="Open Simulation"
              onClick={() => { onOpenModal?.('calibration'); setOpen(false); }}
            />
            <MenuItem
              label="Recent Simulations"
              onClick={() => { onOpenModal?.('calibration'); setOpen(false); }}
            />
            <MenuItem
              label="Close Simulation"
              onClick={() => {
                if (onCloseSimulation) onCloseSimulation();
                setOpen(false);
              }}
            />
          </MenuGroup>
          <MenuDivider />
          <MenuGroup>
            <MenuItem
              label="Save"
              onClick={() => {
                if (onSave) onSave();
                else onExport();
                setOpen(false);
              }}
            />
            <MenuItem
              label="Save As…"
              onClick={() => {
                if (onSaveAs) onSaveAs();
                else onExport();
                setOpen(false);
              }}
            />
            <MenuItem
              label="Duplicate Simulation"
              onClick={() => {
                if (onDuplicateSimulation) onDuplicateSimulation();
                setOpen(false);
              }}
            />
            <MenuItem
              label="Version History"
              onClick={() => {
                onOpenModal?.('version_history');
                setOpen(false);
              }}
            />
          </MenuGroup>
          <MenuDivider />
          <MenuGroup>
            <MenuItem
              label="Import Data"
              onClick={() => { onImport(); setOpen(false); }}
            />
            <MenuItem
              label="Export Data"
              onClick={() => { onExport(); setOpen(false); }}
            />
          </MenuGroup>
          <MenuDivider />
          <MenuGroup>
            <MenuItem
              label={hasReport ? "Export Report" : "View Verified Report"}
              onClick={() => {
                if (onExportReport) onExportReport();
                else onOpenModal?.('report');
                setOpen(false);
              }}
            />
            <MenuItem
              label="Share Simulation"
              onClick={() => {
                if (onShareSimulation) onShareSimulation();
                setOpen(false);
              }}
            />
          </MenuGroup>
        </div>
      )}
    </div>
  );
};

// ─── EDIT MENU ────────────────────────────────────────────────────────────────

const EditMenu: React.FC<{
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onReset: () => void;
  onOpenModal?: (tab: WorkspaceModalTab) => void;
  onFindDriver?: () => void;
  onSelectAllDrivers?: () => void;
  onCut?: () => void;
  onCopy?: () => void;
  onPaste?: () => void;
}> = ({
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onReset,
  onOpenModal,
  onFindDriver,
  onSelectAllDrivers,
  onCut,
  onCopy,
  onPaste,
}) => {
  const { open, setOpen, ref } = useMenu();
  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="px-2.5 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-0.5"
      >
        Edit <ChevronDown className="w-3 h-3 ml-0.5 text-gray-400" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-xl z-50 py-1">
          <MenuGroup>
            <MenuItem
              label="Undo"
              disabled={!canUndo}
              onClick={() => { onUndo(); setOpen(false); }}
            />
            <MenuItem
              label="Redo"
              disabled={!canRedo}
              onClick={() => { onRedo(); setOpen(false); }}
            />
          </MenuGroup>
          <MenuDivider />
          <MenuGroup>
            <MenuItem
              label="Cut"
              onClick={() => { onCut?.(); setOpen(false); }}
            />
            <MenuItem
              label="Copy"
              onClick={() => { onCopy?.(); setOpen(false); }}
            />
            <MenuItem
              label="Paste"
              onClick={() => { onPaste?.(); setOpen(false); }}
            />
          </MenuGroup>
          <MenuDivider />
          <MenuGroup>
            <MenuItem
              label="Reset Parameters"
              onClick={() => { onReset(); setOpen(false); }}
            />
            <MenuItem
              label="Select All Drivers"
              onClick={() => {
                if (onSelectAllDrivers) onSelectAllDrivers();
                setOpen(false);
              }}
            />
            <MenuItem
              label="Find Driver"
              onClick={() => {
                if (onFindDriver) onFindDriver();
                setOpen(false);
              }}
            />
            <MenuItem
              label="Edit Driver Properties"
              onClick={() => {
                onOpenModal?.('driver_properties');
                setOpen(false);
              }}
            />
            <MenuItem
              label="Edit Model Assumptions"
              onClick={() => {
                onOpenModal?.('report');
                setOpen(false);
              }}
            />
          </MenuGroup>
          <MenuDivider />
          <MenuGroup>
            <MenuItem
              label="Preferences"
              onClick={() => {
                onOpenModal?.('preferences');
                setOpen(false);
              }}
            />
          </MenuGroup>
        </div>
      )}
    </div>
  );
};

// ─── TOOLS MENU ───────────────────────────────────────────────────────────────

const ToolsMenu: React.FC<{
  onRun: () => void;
  onOpenModal?: (tab: WorkspaceModalTab) => void;
  onExplainResults?: () => void;
}> = ({ onRun, onOpenModal, onExplainResults }) => {
  const { open, setOpen, ref } = useMenu();
  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="px-2.5 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-0.5"
      >
        Tools <ChevronDown className="w-3 h-3 ml-0.5 text-gray-400" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-xl z-50 py-1 max-h-[85vh] overflow-y-auto">
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">Simulation</div>
          <MenuGroup>
            <MenuItem label="Run Simulation" onClick={() => { onRun(); setOpen(false); }} />
            <MenuItem label="Monte Carlo Simulation" onClick={() => { onOpenModal?.('monte_carlo'); setOpen(false); }} />
            <MenuItem label="What-if Analysis" onClick={() => { onOpenModal?.('what_if'); setOpen(false); }} />
            <MenuItem label="Scenario Comparison" onClick={() => { onOpenModal?.('scenario_comparison'); setOpen(false); }} />
            <MenuItem label="Stress Testing (Chaos Injection)" onClick={() => { onOpenModal?.('dag'); setOpen(false); }} />
            <MenuItem label="Break-even Analysis" onClick={() => { onOpenModal?.('break_even'); setOpen(false); }} />
            <MenuItem label="Forecasting" onClick={() => { onOpenModal?.('forecasting'); setOpen(false); }} />
          </MenuGroup>
          <MenuDivider />
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">Model Management</div>
          <MenuGroup>
            <MenuItem label="Driver Manager" onClick={() => { onOpenModal?.('driver_properties'); setOpen(false); }} />
            <MenuItem label="Distribution Manager" onClick={() => { onOpenModal?.('distribution_manager'); setOpen(false); }} />
            <MenuItem label="Dependency Manager" onClick={() => { onOpenModal?.('graph'); setOpen(false); }} />
            <MenuItem label="Model Validator (5 Checks)" onClick={() => { onOpenModal?.('validator'); setOpen(false); }} />
            <MenuItem label="Assumption Ledger (Provenance)" onClick={() => { onOpenModal?.('report'); setOpen(false); }} />
          </MenuGroup>
          <MenuDivider />
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">AI Intelligence &amp; Swarm</div>
          <MenuGroup>
            <MenuItem
              label="Ask AI Analyst"
              onClick={() => {
                const el = document.querySelector('textarea');
                if (el) el.focus();
                setOpen(false);
              }}
            />
            <MenuItem label="Agent Analysis (Live DAG)" onClick={() => { onOpenModal?.('dag'); setOpen(false); }} />
            <MenuItem label="Conflict Analysis (R3 Resolver)" onClick={() => { onOpenModal?.('report'); setOpen(false); }} />
            <MenuItem label="Risk Detection" onClick={() => { onOpenModal?.('report'); setOpen(false); }} />
            <MenuItem label="Executive Report &amp; Approval Gate" onClick={() => { onOpenModal?.('report'); setOpen(false); }} />
            <MenuItem
              label="Explain Results"
              onClick={() => {
                if (onExplainResults) onExplainResults();
                setOpen(false);
              }}
            />
          </MenuGroup>
          <MenuDivider />
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">Advanced Analysis</div>
          <MenuGroup>
            <MenuItem label="Sensitivity Analysis" onClick={() => { onOpenModal?.('what_if'); setOpen(false); }} />
            <MenuItem label="Sensitivity Tornado (OAT)" onClick={() => { onOpenModal?.('what_if'); setOpen(false); }} />
            <MenuItem label="Flip-point Threshold Analysis" onClick={() => { onOpenModal?.('break_even'); setOpen(false); }} />
            <MenuItem label="Simulation History &amp; Calibration" onClick={() => { onOpenModal?.('calibration'); setOpen(false); }} />
            <MenuItem label="Company Dependency Graph" onClick={() => { onOpenModal?.('graph'); setOpen(false); }} />
            <MenuItem label="Agent Telemetry &amp; Event Stream" onClick={() => { onOpenModal?.('dag'); setOpen(false); }} />
          </MenuGroup>
        </div>
      )}
    </div>
  );
};

// ─── DISPLAY MENU ─────────────────────────────────────────────────────────────

const OUTPUT_VARIABLES: OutputVariable[] = [
  'MRR','ARR','Operating Income','Gross Margin','Cash Runway',
  'Paying Customers','Free Users','Infrastructure Cost','Support Load',
];

const DisplayMenu: React.FC<{
  showDrivers: boolean;
  showResults: boolean;
  showAssistant: boolean;
  showScenarioGroups: boolean;
  showDistribution: boolean;
  showGridlines: boolean;
  showDataLabels: boolean;
  chartType: 'area' | 'line' | 'bar';
  zoom: number;
  onToggleDrivers: () => void;
  onToggleResults: () => void;
  onToggleAssistant: () => void;
  onToggleScenarioGroups: () => void;
  onToggleDistribution: () => void;
  onToggleGridlines: () => void;
  onToggleDataLabels: () => void;
  onChartTypeChange: (type: 'area' | 'line' | 'bar') => void;
  onResetLayout: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  outputVariable: OutputVariable;
  onOutputVariableChange: (v: OutputVariable) => void;
  theme: 'light' | 'dark';
  onThemeChange: (t: 'light' | 'dark') => void;
}> = (props) => {
  const { open, setOpen, ref } = useMenu();
  const [showOutputVarSub, setShowOutputVarSub] = useState(false);
  const [showChartTypeSub, setShowChartTypeSub] = useState(false);

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="px-2.5 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded flex items-center gap-0.5"
      >
        Display <ChevronDown className="w-3 h-3 ml-0.5 text-gray-400" />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-xl z-50 py-1">
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">Panels</div>
          <MenuGroup>
            <MenuItem
              label="Show/Hide Drivers"
              checkmark={props.showDrivers}
              onClick={() => { props.onToggleDrivers(); setOpen(false); }}
            />
            <MenuItem
              label="Show/Hide Simulation Results"
              checkmark={props.showResults}
              onClick={() => { props.onToggleResults(); setOpen(false); }}
            />
            <MenuItem
              label="Show/Hide AI Assistant"
              checkmark={props.showAssistant}
              onClick={() => { props.onToggleAssistant(); setOpen(false); }}
            />
            <MenuItem
              label="Show/Hide Scenario Groups"
              checkmark={props.showScenarioGroups}
              onClick={() => { props.onToggleScenarioGroups(); setOpen(false); }}
            />
            <MenuItem
              label="Reset Workspace Layout"
              onClick={() => { props.onResetLayout(); setOpen(false); }}
            />
          </MenuGroup>

          <MenuDivider />
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">Visualization</div>
          <MenuGroup>
            {/* Output Variable Submenu */}
            <div className="relative">
              <button
                onMouseEnter={() => { setShowOutputVarSub(true); setShowChartTypeSub(false); }}
                onClick={() => setShowOutputVarSub((v) => !v)}
                className="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-100 flex items-center justify-between"
              >
                <span>Output Variable ({props.outputVariable})</span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
              </button>
              {showOutputVarSub && (
                <div
                  onMouseLeave={() => setShowOutputVarSub(false)}
                  className="absolute left-full top-0 w-48 bg-white border border-gray-200 rounded-lg shadow-xl py-1 z-50"
                >
                  {OUTPUT_VARIABLES.map((v) => (
                    <MenuItem
                      key={v}
                      label={v}
                      checkmark={props.outputVariable === v}
                      onClick={() => {
                        props.onOutputVariableChange(v);
                        setShowOutputVarSub(false);
                        setOpen(false);
                      }}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Chart Type Submenu */}
            <div className="relative">
              <button
                onMouseEnter={() => { setShowChartTypeSub(true); setShowOutputVarSub(false); }}
                onClick={() => setShowChartTypeSub((v) => !v)}
                className="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-100 flex items-center justify-between"
              >
                <span>Chart Type ({props.chartType.toUpperCase()})</span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
              </button>
              {showChartTypeSub && (
                <div
                  onMouseLeave={() => setShowChartTypeSub(false)}
                  className="absolute left-full top-0 w-44 bg-white border border-gray-200 rounded-lg shadow-xl py-1 z-50"
                >
                  <MenuItem
                    label="Area (Distribution)"
                    checkmark={props.chartType === 'area'}
                    onClick={() => { props.onChartTypeChange('area'); setShowChartTypeSub(false); setOpen(false); }}
                  />
                  <MenuItem
                    label="Line Chart"
                    checkmark={props.chartType === 'line'}
                    onClick={() => { props.onChartTypeChange('line'); setShowChartTypeSub(false); setOpen(false); }}
                  />
                  <MenuItem
                    label="Bar Chart"
                    checkmark={props.chartType === 'bar'}
                    onClick={() => { props.onChartTypeChange('bar'); setShowChartTypeSub(false); setOpen(false); }}
                  />
                </div>
              )}
            </div>

            <MenuItem
              label="Show Probability Distribution"
              checkmark={props.showDistribution}
              onClick={() => { props.onToggleDistribution(); setOpen(false); }}
            />
            <MenuItem
              label="Show Data Labels"
              checkmark={props.showDataLabels}
              onClick={() => { props.onToggleDataLabels(); setOpen(false); }}
            />
            <MenuItem
              label="Show Gridlines"
              checkmark={props.showGridlines}
              onClick={() => { props.onToggleGridlines(); setOpen(false); }}
            />
          </MenuGroup>

          <MenuDivider />
          <div className="px-3 py-1 text-[11px] font-bold text-gray-400 uppercase tracking-wider">Workspace</div>
          <MenuGroup>
            <MenuItem
              label="Full Screen"
              onClick={() => { toggleFullScreen(); setOpen(false); }}
            />
            <MenuItem
              label="Zoom In"
              onClick={() => { props.onZoomIn(); setOpen(false); }}
            />
            <MenuItem
              label="Zoom Out"
              onClick={() => { props.onZoomOut(); setOpen(false); }}
            />
            <MenuItem
              label={`Reset Zoom (${Math.round(props.zoom * 100)}%)`}
              onClick={() => { props.onResetZoom(); setOpen(false); }}
            />
            <MenuItem
              label="Theme: Light"
              checkmark={props.theme === 'light'}
              onClick={() => { props.onThemeChange('light'); setOpen(false); }}
            />
            <MenuItem
              label="Theme: Dark"
              checkmark={props.theme === 'dark'}
              onClick={() => { props.onThemeChange('dark'); setOpen(false); }}
            />
          </MenuGroup>
        </div>
      )}
    </div>
  );
};

// ─── MAIN TOOLBAR ─────────────────────────────────────────────────────────────

export const WorkspaceToolbar: React.FC<WorkspaceToolbarProps> = (props) => {
  return (
    <div className="h-9 bg-white border-b border-gray-200 flex items-center px-3 gap-1 select-none shrink-0 z-40">
      {/* Brand & chevron icon exactly like reference dashboard.jpeg */}
      <button
        onClick={() => props.onOpenModal?.('company')}
        title="NimbusDesk Overview"
        className="p-1 rounded hover:bg-gray-100 text-gray-500 mr-1 flex items-center"
      >
        <ChevronDown className="w-4 h-4 text-gray-600" />
      </button>

      {/* Menus */}
      <FileMenu
        onExport={props.onExportData}
        onImport={props.onImportData}
        onExportReport={props.onExportReport}
        onOpenModal={props.onOpenModal}
        hasReport={props.hasReport}
        onNewSimulation={props.onNewSimulation}
        onCloseSimulation={props.onCloseSimulation}
        onDuplicateSimulation={props.onDuplicateSimulation}
        onSave={props.onSave}
        onSaveAs={props.onSaveAs}
        onShareSimulation={props.onShareSimulation}
      />
      <EditMenu
        canUndo={props.canUndo}
        canRedo={props.canRedo}
        onUndo={props.onUndo}
        onRedo={props.onRedo}
        onReset={props.onResetDrivers}
        onOpenModal={props.onOpenModal}
        onFindDriver={props.onFindDriver}
        onSelectAllDrivers={props.onSelectAllDrivers}
        onCut={props.onCut}
        onCopy={props.onCopy}
        onPaste={props.onPaste}
      />
      <ToolsMenu
        onRun={props.onRunSimulation}
        onOpenModal={props.onOpenModal}
        onExplainResults={props.onExplainResults}
      />
      <DisplayMenu
        showDrivers={props.showDrivers}
        showResults={props.showResults}
        showAssistant={props.showAssistant}
        showScenarioGroups={props.showScenarioGroups}
        showDistribution={props.showDistribution}
        showGridlines={props.showGridlines}
        showDataLabels={props.showDataLabels}
        chartType={props.chartType}
        zoom={props.zoom}
        onToggleDrivers={props.onToggleDrivers}
        onToggleResults={props.onToggleResults}
        onToggleAssistant={props.onToggleAssistant}
        onToggleScenarioGroups={props.onToggleScenarioGroups}
        onToggleDistribution={props.onToggleDistribution}
        onToggleGridlines={props.onToggleGridlines}
        onToggleDataLabels={props.onToggleDataLabels}
        onChartTypeChange={props.onChartTypeChange}
        onResetLayout={props.onResetLayout}
        onZoomIn={props.onZoomIn}
        onZoomOut={props.onZoomOut}
        onResetZoom={props.onResetZoom}
        outputVariable={props.outputVariable}
        onOutputVariableChange={props.onOutputVariableChange}
        theme={props.theme}
        onThemeChange={props.onThemeChange}
      />

      {/* Divider */}
      <div className="w-px h-5 bg-gray-200 mx-1" />

      {/* Undo / Redo */}
      <button
        onClick={props.onUndo}
        disabled={!props.canUndo}
        title="Undo (Ctrl+Z)"
        className={`p-1.5 rounded hover:bg-gray-100 transition ${props.canUndo ? 'text-gray-600' : 'text-gray-300'}`}
      >
        <RotateCcw className="w-3.5 h-3.5" />
      </button>
      <button
        onClick={props.onRedo}
        disabled={!props.canRedo}
        title="Redo (Ctrl+Y)"
        className={`p-1.5 rounded hover:bg-gray-100 transition ${props.canRedo ? 'text-gray-600' : 'text-gray-300'}`}
      >
        <RotateCw className="w-3.5 h-3.5" />
      </button>

      {/* Divider */}
      <div className="w-px h-5 bg-gray-200 mx-1" />

      {/* Refresh / Re-run */}
      <button
        onClick={props.onRunSimulation}
        disabled={props.isSimulating}
        title="Re-run simulation"
        className={`p-1.5 rounded hover:bg-gray-100 transition ${props.isSimulating ? 'text-gray-300' : 'text-gray-600'} ${props.isSimulating ? 'animate-spin' : ''}`}
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>

      {/* Bookmark */}
      <button
        onClick={() => {
          localStorage.setItem('venturetwin_bookmarked', JSON.stringify({ date: new Date().toISOString() }));
          alert('Current view bookmarked successfully!');
        }}
        title="Bookmark this view"
        className="p-1.5 rounded hover:bg-gray-100 text-gray-600 transition"
      >
        <Bookmark className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};

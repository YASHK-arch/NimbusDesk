import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { DecisionConsole } from './components/DecisionConsole';
import { DecisionReportView } from './components/DecisionReport';
import { CalibrationScreen } from './components/CalibrationScreen';
import { CompanyGraphView } from './components/CompanyGraph';
import { CompanySnapshot, DagPlan, DecisionReport, Finding, TaskNode, WorkflowEvent } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'console' | 'report' | 'calibration' | 'graph'>('console');
  const [company, setCompany] = useState<CompanySnapshot | null>(null);
  const [decisionQuery, setDecisionQuery] = useState('Should we launch a free plan?');
  const [currentDecisionId, setCurrentDecisionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [plan, setPlan] = useState<DagPlan | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [findings, setFindings] = useState<Record<string, Finding>>({});
  const [report, setReport] = useState<DecisionReport | null>(null);
  const [selectedNode, setSelectedNode] = useState<TaskNode | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<string | null>(null);

  // Fetch company snapshot on mount
  useEffect(() => {
    fetch('/api/company')
      .then((res) => res.json())
      .then((data) => setCompany(data))
      .catch((err) => console.error('Failed to load company snapshot:', err));
  }, []);

  const handleSubmitDecision = async () => {
    if (!decisionQuery.trim()) return;
    setIsRunning(true);
    setEvents([]);
    setFindings({});
    setReport(null);
    setApprovalStatus(null);

    try {
      const resp = await fetch('/api/decisions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: decisionQuery }),
      });

      if (!resp.ok) {
        const errData = await resp.json();
        alert(errData.detail?.message || 'Unsupported decision');
        setIsRunning(false);
        return;
      }

      const data = await resp.json();
      setCurrentDecisionId(data.decision_id);
      setPlan(data.plan);

      // Start SSE Event Stream
      const eventSource = new EventSource(`/api/decisions/${data.decision_id}/stream`);

      eventSource.onmessage = (e) => {
        try {
          const parsed: WorkflowEvent = JSON.parse(e.data);
          setEvents((prev) => [parsed, ...prev]);

          // Update node status in DAG plan
          if (parsed.type === 'agent_started' && parsed.payload?.task_id) {
            updateNodeStatus(parsed.payload.task_id, 'running');
          } else if (parsed.type === 'finding_posted' && parsed.agent) {
            updateNodeStatus(parsed.payload?.task_id, 'done');
          } else if (parsed.type === 'agent_failed' && parsed.payload?.task_id) {
            updateNodeStatus(parsed.payload.task_id, 'failed');
          } else if (parsed.type === 'recovery_done' && parsed.payload?.task_id) {
            updateNodeStatus(parsed.payload.task_id, 'done');
          }

          // Report Ready trigger
          if (parsed.type === 'report_ready') {
            eventSource.close();
            setIsRunning(false);
            fetchReport(data.decision_id);
          }
        } catch (err) {
          console.error('SSE parsing error:', err);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setIsRunning(false);
        // Fallback fetch
        fetchReport(data.decision_id);
      };
    } catch (err) {
      console.error('Error submitting decision:', err);
      setIsRunning(false);
    }
  };

  const updateNodeStatus = (taskId: string, status: 'pending' | 'running' | 'done' | 'failed') => {
    setPlan((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((n) => (n.id === taskId ? { ...n, status } : n)),
      };
    });
  };

  const fetchReport = async (decId: string) => {
    try {
      // Fetch full decision state including findings
      const statusResp = await fetch(`/api/decisions/${decId}`);
      if (statusResp.ok) {
        const statusData = await statusResp.json();
        setFindings(statusData.findings || {});
      }

      const reportResp = await fetch(`/api/decisions/${decId}/report`);
      if (reportResp.ok) {
        const reportData = await reportResp.json();
        setReport(reportData);
      }
    } catch (e) {
      console.error('Failed to fetch report:', e);
    }
  };

  const handleInjectFailure = async (agent: string, mode: 'timeout' | 'exception' | 'bad_output') => {
    if (!currentDecisionId) {
      alert('Please submit a decision before injecting failure.');
      return;
    }
    try {
      await fetch(`/api/decisions/${currentDecisionId}/inject-failure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent, mode }),
      });
      alert(`Chaos Injected: ${mode.toUpperCase()} on ${agent}. Supervisor will handle recovery.`);
    } catch (e) {
      console.error('Failed to inject failure:', e);
    }
  };

  const handleApprove = async (strategy: string) => {
    if (!currentDecisionId) return;
    try {
      const resp = await fetch(`/api/decisions/${currentDecisionId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve', chosen_strategy: strategy }),
      });
      if (resp.ok) {
        setApprovalStatus(strategy);
      }
    } catch (e) {
      console.error('Approval failed:', e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        hasReport={report !== null}
        status={isRunning ? 'running' : 'idle'}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {currentTab === 'console' && (
          <DecisionConsole
            company={company}
            decisionQuery={decisionQuery}
            setDecisionQuery={setDecisionQuery}
            onSubmitDecision={handleSubmitDecision}
            isRunning={isRunning}
            plan={plan}
            events={events}
            findings={findings}
            onInjectFailure={handleInjectFailure}
            onSelectNode={setSelectedNode}
            selectedNode={selectedNode}
            onViewReport={() => setCurrentTab('report')}
            hasReport={report !== null}
          />
        )}

        {currentTab === 'report' && (
          <DecisionReportView
            report={report}
            onApprove={handleApprove}
            onReject={() => alert('Proposal rejected. Recorded in audit log.')}
            onRequestChanges={() => {
              setCurrentTab('console');
              handleSubmitDecision();
            }}
            approvalStatus={approvalStatus}
          />
        )}

        {currentTab === 'calibration' && <CalibrationScreen />}

        {currentTab === 'graph' && <CompanyGraphView />}
      </main>
    </div>
  );
};

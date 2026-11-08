import React, { useEffect, useState } from 'react';
import { SimulationWorkspace } from './components/SimulationWorkspace';
import {
  CompanySnapshot,
  DagPlan,
  DecisionReport,
  Finding,
  TaskNode,
  WorkflowEvent,
} from './types';

export const App: React.FC = () => {
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

  const handleSubmitDecision = async (): Promise<DecisionReport | null> => {
    if (!decisionQuery.trim()) return null;
    setIsRunning(true);
    setEvents([]);
    setFindings({});
    setReport(null);
    setApprovalStatus(null);

    return new Promise((resolve) => {
      (async () => {
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
            resolve(null);
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

              if (parsed.type === 'agent_started' && parsed.payload?.task_id) {
                updateNodeStatus(parsed.payload.task_id, 'running');
              } else if (parsed.type === 'finding_posted' && parsed.agent) {
                updateNodeStatus(parsed.payload?.task_id, 'done');
              } else if (parsed.type === 'agent_failed' && parsed.payload?.task_id) {
                updateNodeStatus(parsed.payload.task_id, 'failed');
              } else if (parsed.type === 'recovery_done' && parsed.payload?.task_id) {
                updateNodeStatus(parsed.payload.task_id, 'done');
              }

              if (parsed.type === 'report_ready') {
                eventSource.close();
                setIsRunning(false);
                fetchReport(data.decision_id).then(resolve);
              }
            } catch (err) {
              console.error('SSE parsing error:', err);
            }
          };

          eventSource.onerror = () => {
            eventSource.close();
            setIsRunning(false);
            fetchReport(data.decision_id).then(resolve);
          };
        } catch (err) {
          console.error('Error submitting decision:', err);
          setIsRunning(false);
          resolve(null);
        }
      })();
    });
  };

  const updateNodeStatus = (
    taskId: string,
    status: 'pending' | 'running' | 'done' | 'failed'
  ) => {
    setPlan((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((n) => (n.id === taskId ? { ...n, status } : n)),
      };
    });
  };

  const fetchReport = async (decId: string): Promise<DecisionReport | null> => {
    try {
      const statusResp = await fetch(`/api/decisions/${decId}`);
      if (statusResp.ok) {
        const statusData = await statusResp.json();
        setFindings(statusData.findings || {});
      }

      const reportResp = await fetch(`/api/decisions/${decId}/report`);
      if (reportResp.ok) {
        const reportData: DecisionReport = await reportResp.json();
        setReport(reportData);
        return reportData;
      }
    } catch (e) {
      console.error('Failed to fetch report:', e);
    }
    return null;
  };

  const handleInjectFailure = async (
    agent: string,
    mode: 'timeout' | 'exception' | 'bad_output'
  ) => {
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
      alert(
        `Chaos Injected: ${mode.toUpperCase()} on ${agent}. Supervisor will handle recovery.`
      );
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
    <SimulationWorkspace
      company={company}
      decisionQuery={decisionQuery}
      setDecisionQuery={setDecisionQuery}
      onRunDecision={handleSubmitDecision}
      isSimulating={isRunning}
      plan={plan}
      events={events}
      findings={findings}
      report={report}
      onInjectFailure={handleInjectFailure}
      onSelectNode={setSelectedNode}
      selectedNode={selectedNode}
      onApprove={handleApprove}
      onReject={() => alert('Proposal rejected. Recorded in audit log.')}
      onRequestChanges={() => {
        handleSubmitDecision();
      }}
      approvalStatus={approvalStatus}
    />
  );
};

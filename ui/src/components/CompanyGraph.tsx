import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';

interface GraphData {
  nodes: Array<{
    id: string;
    data: { label: string; category: string; affected?: boolean };
    position: { x: number; y: number };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
    animated?: boolean;
  }>;
}

export const CompanyGraphView: React.FC = () => {
  const [data, setData] = useState<GraphData | null>(null);

  useEffect(() => {
    fetch('/api/graph')
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error('Error fetching graph:', err));
  }, []);

  if (!data) {
    return <div className="text-center py-20 text-slate-500 font-mono">Loading company dependency topology...</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-tight">Company Intelligence Graph (F16)</h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 font-medium">
                networkx / Topology View
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Dependency topology linking plans, funnel traffic, infrastructure costs, support load, and cash runway.
            </p>
          </div>
          <span className="text-xs font-mono text-amber-400 bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full">
            ● Affected Nodes Highlighted
          </span>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-white">Operational Nodes & Dependencies</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.nodes.map((node) => {
            const isAffected = node.data.affected;
            return (
              <div
                key={node.id}
                className={`p-4 rounded-xl border transition ${
                  isAffected
                    ? 'border-amber-500/60 bg-amber-950/20 shadow-md shadow-amber-950/30'
                    : 'border-slate-800 bg-slate-950'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {node.data.category}
                  </span>
                  {isAffected && (
                    <span className="text-[10px] font-mono text-amber-300 bg-amber-500/20 px-1.5 py-0.5 rounded font-bold">
                      Impacted
                    </span>
                  )}
                </div>
                <h4 className="font-semibold text-sm text-white">{node.data.label}</h4>
                <p className="text-[11px] text-slate-500 font-mono mt-1">ID: {node.id}</p>
              </div>
            );
          })}
        </div>

        <div className="border-t border-slate-800/80 pt-4 mt-6">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-3">Dependency Edges & Causal Paths</h4>
          <div className="space-y-2">
            {data.edges.map((e) => (
              <div key={e.id} className="bg-slate-950 p-2.5 rounded border border-slate-800 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-teal-400">{e.source.replace('node_', '')}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-teal-300">{e.target.replace('node_', '')}</span>
                </div>
                <span className="text-slate-400 italic">[{e.label}]</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

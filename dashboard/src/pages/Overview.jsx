import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSummary, fetchNodes } from "../services/api";
import NodeCard from "../components/NodeCard";

export default function Overview() {
  const { data: summary } = useQuery({ queryKey: ["summary"], queryFn: fetchSummary, refetchInterval: 10_000 });
  const { data: nodes, isLoading } = useQuery({ queryKey: ["nodes"], queryFn: fetchNodes, refetchInterval: 10_000 });

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
        <div>
          <h1 className="section-title">Network Overview</h1>
          <p className="section-subtitle">Live health and energy signals across all registered nodes.</p>
        </div>
      </header>

      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Nodes", value: summary.total_nodes, tone: "text-[var(--ink)]" },
            { label: "Online", value: summary.online, tone: "text-emerald-700" },
            { label: "Stale", value: summary.stale, tone: "text-amber-700" },
            { label: "Offline", value: summary.offline, tone: "text-rose-700" },
          ].map((s) => (
            <div key={s.label} className="panel p-4 sm:p-5">
              <div className="text-[11px] uppercase tracking-[0.08em] text-[var(--ink-muted)]">{s.label}</div>
              <div className={`mt-1 text-3xl font-semibold ${s.tone}`}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="panel p-6 text-sm text-[var(--ink-muted)]">Loading nodes...</div>
      ) : (
        <div className="panel p-4 sm:p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-[var(--ink)]">Nodes</h2>
            <span className="text-xs text-[var(--ink-muted)]">{(nodes || []).length} visible</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {(nodes || []).map((node) => (
              <NodeCard key={node.node_id} node={node} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

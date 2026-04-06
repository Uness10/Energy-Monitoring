import React from "react";
import { Link } from "react-router-dom";
import StatusIndicator from "./StatusIndicator";

export default function NodeCard({ node }) {
  const metrics = node.latest_metrics || {};
  return (
    <Link
      to={`/nodes/${node.node_id}`}
      className="block panel-strong p-4 hover:-translate-y-0.5 hover:shadow-[0_16px_35px_rgba(31,54,44,0.14)] transition"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-[var(--ink)] text-sm truncate pr-2">{node.node_id}</h3>
        <StatusIndicator status={node.status} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-[var(--ink-muted)]">
        <div className="rounded-lg bg-[rgba(31,122,92,0.06)] px-2 py-1.5">
          Power: <span className="font-medium text-[var(--ink)]">{metrics.power_w?.toFixed(1) ?? "—"} W</span>
        </div>
        <div className="rounded-lg bg-[rgba(21,123,185,0.08)] px-2 py-1.5">
          CPU: <span className="font-medium text-[var(--ink)]">{metrics.cpu_util?.toFixed(1) ?? "—"}%</span>
        </div>
        <div className="rounded-lg bg-[rgba(163,94,60,0.08)] px-2 py-1.5">
          RAM: <span className="font-medium text-[var(--ink)]">{metrics.ram_util?.toFixed(1) ?? "—"}%</span>
        </div>
        <div className="rounded-lg bg-[rgba(217,179,80,0.12)] px-2 py-1.5">
          Temp: <span className="font-medium text-[var(--ink)]">{metrics.temperature?.toFixed(1) ?? "—"}&deg;C</span>
        </div>
      </div>
    </Link>
  );
}

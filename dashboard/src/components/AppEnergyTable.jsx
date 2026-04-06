import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchApps } from "../services/api";

export default function AppEnergyTable({ nodeId }) {
  const { data, isLoading } = useQuery({
    queryKey: ["apps", nodeId],
    queryFn: () => fetchApps(nodeId),
    refetchInterval: 10_000,
  });

  const apps = data?.apps || [];

  if (isLoading) return <div className="panel p-6 text-sm text-[var(--ink-muted)]">Loading apps...</div>;
  if (!apps.length) return <div className="panel p-6 text-sm text-[var(--ink-muted)]">No application data yet.</div>;

  return (
    <div className="panel overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--line)] bg-white/70">
        <h4 className="text-sm font-semibold text-[var(--ink)]">Application Energy Ranking</h4>
        <p className="text-xs text-[var(--ink-muted)]">Sorted by average power in the last hour.</p>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-[rgba(31,122,92,0.08)] text-xs text-[var(--ink-muted)] uppercase">
          <tr>
            <th className="text-left px-4 py-2">Application</th>
            <th className="text-right px-4 py-2">Avg Power</th>
            <th className="text-right px-4 py-2">Peak Power</th>
            <th className="text-right px-4 py-2">Samples</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--line)]">
          {apps.map((app, i) => (
            <tr key={app.app_name} className="hover:bg-[rgba(31,122,92,0.06)] transition">
              <td className="px-4 py-2 font-medium text-[var(--ink)] flex items-center gap-2">
                <span className="text-xs text-[var(--ink-muted)]">#{i + 1}</span>
                {app.app_name}
              </td>
              <td className="px-4 py-2 text-right text-amber-700 font-semibold">
                {app.avg_power_w.toFixed(1)} W
              </td>
              <td className="px-4 py-2 text-right text-rose-600">
                {app.peak_power_w.toFixed(1)} W
              </td>
              <td className="px-4 py-2 text-right text-[var(--ink-muted)]">{app.samples}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

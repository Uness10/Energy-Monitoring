import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchApps } from "../services/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b",
  "#8b5cf6", "#ec4899", "#14b8a6", "#f97316",
  "#6366f1", "#84cc16",
];

export default function AppEnergyBreakdown({ nodeId }) {
  const { data, isLoading } = useQuery({
    queryKey: ["apps", nodeId],
    queryFn: () => fetchApps(nodeId),
    refetchInterval: 10_000,
  });

  const apps = (data?.apps || []).slice(0, 10);

  if (isLoading) return <div className="h-64 panel animate-pulse" />;

  return (
    <div className="panel p-4 sm:p-5">
      <h4 className="text-sm font-semibold text-[var(--ink)] mb-1">Power by Application</h4>
      <p className="text-xs text-[var(--ink-muted)] mb-3">Average watts in the last hour.</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={apps} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(44,84,68,0.14)" horizontal={false} />
          <XAxis type="number" unit=" W" tick={{ fontSize: 10, fill: "#5b7266" }} />
          <YAxis
            type="category"
            dataKey="app_name"
            tick={{ fontSize: 11, fill: "#30473c" }}
            width={90}
          />
          <Tooltip
            contentStyle={{ borderRadius: 12, border: "1px solid rgba(44,84,68,0.15)", background: "rgba(255,255,255,0.96)" }}
            formatter={(v) => [`${v.toFixed(2)} W`, "Avg Power"]}
          />
          <Bar dataKey="avg_power_w" radius={[0, 4, 4, 0]}>
            {apps.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

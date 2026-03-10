import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchApps } from "../services/api";

export default function AppSelector({ nodeId, selected, onChange }) {
  const { data } = useQuery({
    queryKey: ["apps", nodeId],
    queryFn: () => fetchApps(nodeId),
    enabled: !!nodeId,
    staleTime: 30_000,
  });

  const apps = data?.apps || [];

  return (
    <select
      value={selected || ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="border border-gray-300 rounded px-3 py-1.5 text-sm"
    >
      <option value="">All Apps</option>
      {apps.map((a) => (
        <option key={a.app_name} value={a.app_name}>
          {a.app_name} ({a.avg_power_w.toFixed(1)} W avg)
        </option>
      ))}
    </select>
  );
}

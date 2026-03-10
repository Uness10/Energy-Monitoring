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

  if (isLoading) return <p className="text-sm text-gray-400">Loading apps...</p>;
  if (!apps.length) return <p className="text-sm text-gray-400">No application data yet.</p>;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-3 border-b">
        <h4 className="text-sm font-semibold text-gray-700">Application Energy Ranking</h4>
        <p className="text-xs text-gray-400">Sorted by average power — last hour</p>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
          <tr>
            <th className="text-left px-4 py-2">Application</th>
            <th className="text-right px-4 py-2">Avg Power</th>
            <th className="text-right px-4 py-2">Peak Power</th>
            <th className="text-right px-4 py-2">Samples</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {apps.map((app, i) => (
            <tr key={app.app_name} className="hover:bg-gray-50">
              <td className="px-4 py-2 font-medium text-gray-800 flex items-center gap-2">
                <span className="text-xs text-gray-400">#{i + 1}</span>
                {app.app_name}
              </td>
              <td className="px-4 py-2 text-right text-orange-600 font-medium">
                {app.avg_power_w.toFixed(1)} W
              </td>
              <td className="px-4 py-2 text-right text-red-500">
                {app.peak_power_w.toFixed(1)} W
              </td>
              <td className="px-4 py-2 text-right text-gray-400">{app.samples}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

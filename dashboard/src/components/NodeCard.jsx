import React from "react";
import { Link } from "react-router-dom";
import StatusIndicator from "./StatusIndicator";

export default function NodeCard({ node }) {
  const metrics = node.latest_metrics || {};
  return (
    <Link
      to={`/nodes/${node.node_id}`}
      className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-800 text-sm">{node.node_id}</h3>
        <StatusIndicator status={node.status} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
        <div>
          Power: <span className="font-medium">{metrics.power_w?.toFixed(1) ?? "—"} W</span>
        </div>
        <div>
          CPU: <span className="font-medium">{metrics.cpu_util?.toFixed(1) ?? "—"}%</span>
        </div>
        <div>
          RAM: <span className="font-medium">{metrics.ram_util?.toFixed(1) ?? "—"}%</span>
        </div>
        <div>
          Temp: <span className="font-medium">{metrics.temperature?.toFixed(1) ?? "—"}&deg;C</span>
        </div>
      </div>
    </Link>
  );
}

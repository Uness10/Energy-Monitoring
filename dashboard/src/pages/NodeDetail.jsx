import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchNodeStatus } from "../services/api";
import { useMetrics } from "../hooks/useMetrics";
import KpiChart from "../components/KpiChart";
import TimeRangePicker from "../components/TimeRangePicker";
import StatusIndicator from "../components/StatusIndicator";

const KPI_LIST = [
  { key: "power_w", label: "Power (W)", color: "#ef4444" },
  { key: "cpu_util", label: "CPU (%)", color: "#3b82f6" },
  { key: "ram_util", label: "RAM (%)", color: "#8b5cf6" },
  { key: "temperature", label: "Temperature (C)", color: "#f59e0b" },
  { key: "voltage", label: "Voltage (V)", color: "#10b981" },
  { key: "cpu_freq", label: "CPU Freq (MHz)", color: "#6366f1" },
  { key: "energy_wh", label: "Energy (Wh)", color: "#ec4899" },
  { key: "uptime_s", label: "Uptime (s)", color: "#14b8a6" },
];

export default function NodeDetail() {
  const { nodeId } = useParams();
  const [rangeMinutes, setRangeMinutes] = useState(60);

  const { data: nodeStatus } = useQuery({
    queryKey: ["nodeStatus", nodeId],
    queryFn: () => fetchNodeStatus(nodeId),
    refetchInterval: 10_000,
  });

  const now = new Date();
  const start = new Date(now.getTime() - rangeMinutes * 60 * 1000);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">{nodeId}</h2>
          {nodeStatus && <StatusIndicator status={nodeStatus.status} />}
        </div>
        <TimeRangePicker selected={rangeMinutes} onChange={setRangeMinutes} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {KPI_LIST.map((kpi) => (
          <KpiChartForNode
            key={kpi.key}
            nodeId={nodeId}
            metric={kpi.key}
            title={kpi.label}
            color={kpi.color}
            start={start}
            end={now}
          />
        ))}
      </div>
    </div>
  );
}

function KpiChartForNode({ nodeId, metric, title, color, start, end }) {
  const { data } = useMetrics({
    nodeId,
    metric,
    start: start.toISOString(),
    end: end.toISOString(),
  });

  return (
    <KpiChart
      data={data?.data || []}
      dataKey={data?.aggregation ? "avg_value" : "value"}
      title={title}
      color={color}
    />
  );
}

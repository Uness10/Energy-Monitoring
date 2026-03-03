import React, { useState } from "react";
import { useMetrics } from "../hooks/useMetrics";
import { useNodeStatus } from "../hooks/useNodeStatus";
import KpiChart from "../components/KpiChart";
import NodeSelector from "../components/NodeSelector";

export default function RealtimeMonitor() {
  const [selectedNode, setSelectedNode] = useState(null);
  const { data: nodes } = useNodeStatus();

  const now = new Date();
  const fifteenMinAgo = new Date(now.getTime() - 15 * 60 * 1000);

  const { data: powerData } = useMetrics(
    { nodeId: selectedNode, metric: "power_w", start: fifteenMinAgo.toISOString(), end: now.toISOString() },
    5_000
  );
  const { data: cpuData } = useMetrics(
    { nodeId: selectedNode, metric: "cpu_util", start: fifteenMinAgo.toISOString(), end: now.toISOString() },
    5_000
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Realtime Monitor</h2>
        <NodeSelector nodes={nodes} selected={selectedNode} onChange={setSelectedNode} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <KpiChart data={powerData?.data || []} title="Power (W)" color="#ef4444" />
        <KpiChart data={cpuData?.data || []} title="CPU Utilization (%)" color="#3b82f6" />
      </div>
    </div>
  );
}

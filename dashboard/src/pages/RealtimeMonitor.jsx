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
    <div className="space-y-5">
      <div className="panel p-4 sm:p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h2 className="section-title">Realtime Monitor</h2>
          <p className="section-subtitle">Live 15-minute trend window updating every 5 seconds.</p>
        </div>
        <NodeSelector nodes={nodes} selected={selectedNode} onChange={setSelectedNode} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <KpiChart data={powerData?.data || []} title="Power (W)" color="#ef4444" />
        <KpiChart data={cpuData?.data || []} title="CPU Utilization (%)" color="#3b82f6" />
      </div>
    </div>
  );
}

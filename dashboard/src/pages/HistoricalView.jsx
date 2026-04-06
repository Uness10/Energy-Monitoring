import React, { useState } from "react";
import { useMetrics } from "../hooks/useMetrics";
import { useNodeStatus } from "../hooks/useNodeStatus";
import KpiChart from "../components/KpiChart";
import TimeRangePicker from "../components/TimeRangePicker";
import NodeSelector from "../components/NodeSelector";

export default function HistoricalView() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [rangeMinutes, setRangeMinutes] = useState(1440); // default 24h
  const { data: nodes } = useNodeStatus();

  const now = new Date();
  const start = new Date(now.getTime() - rangeMinutes * 60 * 1000);

  const { data: powerData } = useMetrics({
    nodeId: selectedNode,
    metric: "power_w",
    start: start.toISOString(),
    end: now.toISOString(),
  });

  const { data: tempData } = useMetrics({
    nodeId: selectedNode,
    metric: "temperature",
    start: start.toISOString(),
    end: now.toISOString(),
  });

  return (
    <div className="space-y-5">
      <div className="panel p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h2 className="section-title">Historical Analytics</h2>
          <p className="section-subtitle">Explore long-range behavior with adaptive aggregation.</p>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-2">
          <NodeSelector nodes={nodes} selected={selectedNode} onChange={setSelectedNode} />
          <TimeRangePicker selected={rangeMinutes} onChange={setRangeMinutes} />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <KpiChart
          data={powerData?.data || []}
          dataKey={powerData?.aggregation ? "avg_value" : "value"}
          title="Power Trend (W)"
          color="#ef4444"
        />
        <KpiChart
          data={tempData?.data || []}
          dataKey={tempData?.aggregation ? "avg_value" : "value"}
          title="Temperature Trend (C)"
          color="#f59e0b"
        />
      </div>
    </div>
  );
}

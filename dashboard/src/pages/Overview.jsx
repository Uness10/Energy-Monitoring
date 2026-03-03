import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSummary, fetchNodes } from "../services/api";
import NodeCard from "../components/NodeCard";

export default function Overview() {
  const { data: summary } = useQuery({ queryKey: ["summary"], queryFn: fetchSummary, refetchInterval: 10_000 });
  const { data: nodes, isLoading } = useQuery({ queryKey: ["nodes"], queryFn: fetchNodes, refetchInterval: 10_000 });

  return (
    <div>
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: "Total Nodes", value: summary.total_nodes },
            { label: "Online", value: summary.online, color: "text-green-600" },
            { label: "Stale", value: summary.stale, color: "text-yellow-600" },
            { label: "Offline", value: summary.offline, color: "text-red-600" },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-lg shadow p-4 text-center">
              <div className={`text-2xl font-bold ${s.color || "text-gray-800"}`}>{s.value}</div>
              <div className="text-xs text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {isLoading ? (
        <p className="text-gray-500">Loading nodes...</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {(nodes || []).map((node) => (
            <NodeCard key={node.node_id} node={node} />
          ))}
        </div>
      )}
    </div>
  );
}

import React from "react";

export default function NodeSelector({ nodes, selected, onChange }) {
  return (
    <select
      value={selected || ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="border border-gray-300 rounded px-3 py-1.5 text-sm"
    >
      <option value="">All Nodes</option>
      {(nodes || []).map((n) => (
        <option key={n.node_id} value={n.node_id}>
          {n.node_id}
        </option>
      ))}
    </select>
  );
}

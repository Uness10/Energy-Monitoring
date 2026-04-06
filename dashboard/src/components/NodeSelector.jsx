import React from "react";

export default function NodeSelector({ nodes, selected, onChange }) {
  return (
    <select
      value={selected || ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="control-select min-w-[160px]"
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

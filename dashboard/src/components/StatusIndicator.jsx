import React from "react";

const STATUS_COLORS = {
  ONLINE: "bg-green-500",
  STALE: "bg-yellow-400",
  OFFLINE: "bg-red-500",
  UNKNOWN: "bg-gray-400",
};

export default function StatusIndicator({ status }) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.UNKNOWN;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
      <span className="text-xs font-medium text-gray-600">{status}</span>
    </span>
  );
}

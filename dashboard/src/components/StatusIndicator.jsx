import React from "react";

const STATUS_COLORS = {
  ONLINE: "bg-emerald-500",
  STALE: "bg-amber-400",
  OFFLINE: "bg-rose-500",
  UNKNOWN: "bg-slate-400",
};

const STATUS_BADGES = {
  ONLINE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  STALE: "bg-amber-50 text-amber-700 border-amber-200",
  OFFLINE: "bg-rose-50 text-rose-700 border-rose-200",
  UNKNOWN: "bg-slate-50 text-slate-600 border-slate-200",
};

export default function StatusIndicator({ status }) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.UNKNOWN;
  const badge = STATUS_BADGES[status] || STATUS_BADGES.UNKNOWN;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[11px] font-semibold border ${badge}`}>
      <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
      <span>{status}</span>
    </span>
  );
}

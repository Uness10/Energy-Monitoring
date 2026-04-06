import React from "react";

const RANGES = [
  { label: "15m", minutes: 15 },
  { label: "1h", minutes: 60 },
  { label: "24h", minutes: 1440 },
  { label: "7d", minutes: 10080 },
  { label: "30d", minutes: 43200 },
];

export default function TimeRangePicker({ selected, onChange }) {
  return (
    <div className="flex gap-1.5 flex-wrap">
      {RANGES.map((r) => (
        <button
          key={r.label}
          onClick={() => onChange(r.minutes)}
          className={`px-3 py-1.5 text-xs rounded-xl font-semibold transition ${
            selected === r.minutes
              ? "bg-[var(--brand)] text-white shadow"
              : "bg-white/80 border border-[var(--line)] text-[var(--ink-muted)] hover:bg-[rgba(31,122,92,0.1)] hover:text-[var(--ink)]"
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

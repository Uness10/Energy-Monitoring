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
    <div className="flex gap-1">
      {RANGES.map((r) => (
        <button
          key={r.label}
          onClick={() => onChange(r.minutes)}
          className={`px-3 py-1 text-xs rounded font-medium ${
            selected === r.minutes
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

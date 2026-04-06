import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function KpiChart({ data, dataKey = "value", title, color = "#3b82f6" }) {
  const displayData = data || [];

  return (
    <div className="panel p-4 sm:p-5">
      {title && <h4 className="text-sm font-semibold text-[var(--ink)] mb-3">{title}</h4>}
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={displayData} margin={{ top: 6, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(44,84,68,0.14)" />
          <XAxis
            dataKey="timestamp"
            tick={{ fontSize: 10, fill: "#5b7266" }}
            tickFormatter={(value) => {
              if (!value) return "";
              const d = new Date(value);
              return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            }}
            minTickGap={24}
          />
          <YAxis tick={{ fontSize: 10, fill: "#5b7266" }} />
          <Tooltip
            contentStyle={{ borderRadius: 12, border: "1px solid rgba(44,84,68,0.15)", background: "rgba(255,255,255,0.96)" }}
            labelStyle={{ color: "#30473c", fontWeight: 600 }}
            formatter={(value) => {
              const n = Number(value);
              return [Number.isFinite(n) ? n.toFixed(2) : value, "Value"];
            }}
          />
          <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

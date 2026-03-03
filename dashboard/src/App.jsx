import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import Overview from "./pages/Overview";
import RealtimeMonitor from "./pages/RealtimeMonitor";
import HistoricalView from "./pages/HistoricalView";
import NodeDetail from "./pages/NodeDetail";

const navLinks = [
  { to: "/", label: "Overview" },
  { to: "/realtime", label: "Realtime" },
  { to: "/historical", label: "Historical" },
];

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-6">
          <span className="font-bold text-lg text-gray-800">
            Energy Monitor
          </span>
          {navLinks.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `text-sm font-medium ${
                  isActive
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-gray-500 hover:text-gray-700"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/realtime" element={<RealtimeMonitor />} />
          <Route path="/historical" element={<HistoricalView />} />
          <Route path="/nodes/:nodeId" element={<NodeDetail />} />
        </Routes>
      </main>
    </div>
  );
}

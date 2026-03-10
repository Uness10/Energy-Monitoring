import React from "react";
import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import Overview       from "./pages/Overview";
import RealtimeMonitor from "./pages/RealtimeMonitor";
import HistoricalView  from "./pages/HistoricalView";
import NodeDetail      from "./pages/NodeDetail";
import Login           from "./pages/Login";
import { isAuthenticated } from "./services/auth";

const NAV = [
  { to: "/",           label: "Overview"   },
  { to: "/realtime",   label: "Realtime"   },
  { to: "/historical", label: "Historical" },
];

function ProtectedRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="*"
          element={
            <ProtectedRoute>
              <nav className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-6">
                  <span className="font-bold text-gray-800">Energy Monitor</span>
                  {NAV.map((l) => (
                    <NavLink
                      key={l.to}
                      to={l.to}
                      end={l.to === "/"}
                      className={({ isActive }) =>
                        `text-sm font-medium pb-0.5 ${
                          isActive
                            ? "text-blue-600 border-b-2 border-blue-600"
                            : "text-gray-500 hover:text-gray-700"
                        }`
                      }
                    >
                      {l.label}
                    </NavLink>
                  ))}
                  <div className="ml-auto">
                    <button
                      onClick={() => {
                        localStorage.removeItem("token");
                        window.location.href = "/login";
                      }}
                      className="text-xs text-gray-400 hover:text-gray-600"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              </nav>

              <main className="max-w-7xl mx-auto px-4 py-6">
                <Routes>
                  <Route path="/"                element={<Overview />}        />
                  <Route path="/realtime"        element={<RealtimeMonitor />} />
                  <Route path="/historical"      element={<HistoricalView />}  />
                  <Route path="/nodes/:nodeId"   element={<NodeDetail />}      />
                </Routes>
              </main>
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

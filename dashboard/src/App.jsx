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
    <div className="min-h-screen">
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="*"
          element={
            <ProtectedRoute>
              <nav className="sticky top-0 z-50 border-b border-[var(--line)] bg-[rgba(245,247,243,0.86)] backdrop-blur">
                <div className="app-shell py-3 flex flex-wrap items-center gap-3 sm:gap-6">
                  <div className="panel-strong px-3.5 py-2 flex items-center gap-2.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-[var(--brand)]" />
                    <span className="font-semibold text-sm text-[var(--ink)] tracking-tight">Energy Monitor</span>
                  </div>
                  <div className="panel px-1.5 py-1 flex items-center gap-1 overflow-x-auto">
                    {NAV.map((l) => (
                      <NavLink
                        key={l.to}
                        to={l.to}
                        end={l.to === "/"}
                        className={({ isActive }) =>
                          `px-3 py-1.5 rounded-xl text-sm font-medium transition whitespace-nowrap ${
                            isActive
                              ? "bg-[var(--brand)] text-white"
                              : "text-[var(--ink-muted)] hover:bg-[rgba(31,122,92,0.1)] hover:text-[var(--ink)]"
                          }`
                        }
                      >
                        {l.label}
                      </NavLink>
                    ))}
                  </div>
                  <div className="ml-auto panel px-1.5 py-1">
                    <button
                      onClick={() => {
                        localStorage.removeItem("token");
                        window.location.href = "/login";
                      }}
                      className="px-3 py-1.5 rounded-xl text-sm text-[var(--ink-muted)] hover:text-[var(--ink)] hover:bg-[rgba(31,122,92,0.1)] transition"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              </nav>

              <main className="app-shell py-6 sm:py-8">
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

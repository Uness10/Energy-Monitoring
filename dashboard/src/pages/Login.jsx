import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/auth";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Invalid username or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="panel-strong w-full max-w-md p-8 sm:p-10">
        <div className="inline-flex items-center gap-2 rounded-full px-3 py-1 bg-[rgba(31,122,92,0.12)] text-[var(--brand-dark)] text-xs font-semibold mb-4">
          <span className="h-2 w-2 rounded-full bg-[var(--brand)]" />
          Secure Access
        </div>
        <h1 className="text-2xl font-semibold text-[var(--ink)] mb-1">Energy Monitor</h1>
        <p className="text-sm text-[var(--ink-muted)] mb-6">Sign in to continue to your distributed monitoring dashboard.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[var(--ink-muted)] mb-1.5 uppercase tracking-wide">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-xl px-3.5 py-2.5 text-sm border border-[var(--line)] bg-white/90 text-[var(--ink)]
                         focus:outline-none focus:ring-2 focus:ring-[rgba(31,122,92,0.22)] focus:border-[var(--brand)]"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[var(--ink-muted)] mb-1.5 uppercase tracking-wide">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl px-3.5 py-2.5 text-sm border border-[var(--line)] bg-white/90 text-[var(--ink)]
                         focus:outline-none focus:ring-2 focus:ring-[rgba(31,122,92,0.22)] focus:border-[var(--brand)]"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-rose-600 font-medium">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl py-2.5 text-sm font-semibold transition
                       bg-[var(--brand)] text-white hover:bg-[var(--brand-dark)] disabled:opacity-50
                       focus:outline-none focus:ring-2 focus:ring-[rgba(31,122,92,0.24)]"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

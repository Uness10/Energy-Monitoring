import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Nodes ──────────────────────────────────────────────────────────────────
export const fetchNodes    = ()       => api.get("/nodes").then((r) => r.data);
export const fetchNodeStatus = (id)   => api.get(`/nodes/${id}/status`).then((r) => r.data);
export const fetchSummary  = ()       => api.get("/summary").then((r) => r.data);

// ── Metrics ────────────────────────────────────────────────────────────────
export const fetchMetrics = ({ nodeId, appName, metric, start, end, aggregation }) =>
  api.get("/metrics", {
    params: { node_id: nodeId, app_name: appName, metric, start, end, aggregation },
  }).then((r) => r.data);

export const fetchAggregatedMetrics = ({ nodeId, appName, metric, start, end, aggregation }) =>
  api.get("/metrics/aggregated", {
    params: { node_id: nodeId, app_name: appName, metric, start, end, aggregation },
  }).then((r) => r.data);

// ── Apps ───────────────────────────────────────────────────────────────────
export const fetchApps = (nodeId) =>
  api.get("/apps", { params: { node_id: nodeId } }).then((r) => r.data);

export const fetchAppEnergy = ({ appName, nodeId, start, end, aggregation = "1h" }) =>
  api.get(`/apps/${encodeURIComponent(appName)}/energy`, {
    params: { node_id: nodeId, start, end, aggregation },
  }).then((r) => r.data);

export default api;

import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
});

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function fetchNodes() {
  return api.get("/nodes").then((r) => r.data);
}

export function fetchNodeStatus(nodeId) {
  return api.get(`/nodes/${nodeId}/status`).then((r) => r.data);
}

export function fetchMetrics({ nodeId, metric, start, end, aggregation }) {
  return api
    .get("/metrics", { params: { node_id: nodeId, metric, start, end, aggregation } })
    .then((r) => r.data);
}

export function fetchAggregatedMetrics({ nodeId, metric, start, end, aggregation }) {
  return api
    .get("/metrics/aggregated", {
      params: { node_id: nodeId, metric, start, end, aggregation },
    })
    .then((r) => r.data);
}

export function fetchSummary() {
  return api.get("/summary").then((r) => r.data);
}

export default api;

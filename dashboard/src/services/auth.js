import api from "./api";

export async function login(username, password) {
  const resp = await api.post("/auth/login", { username, password });
  const { access_token } = resp.data;
  localStorage.setItem("token", access_token);
  return access_token;
}

export function logout() {
  localStorage.removeItem("token");
}

export function isAuthenticated() {
  return !!localStorage.getItem("token");
}

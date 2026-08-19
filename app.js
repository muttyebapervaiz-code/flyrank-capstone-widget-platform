const API_BASE = "http://127.0.0.1:8000";

// Token ko memory mein rakhne ke liye (localStorage yahan use nahi kar rahe, simplicity ke liye)
function getToken() {
  return sessionStorage.getItem("token");
}

function setToken(token) {
  sessionStorage.setItem("token", token);
}

function clearToken() {
  sessionStorage.removeItem("token");
}

function isLoggedIn() {
  return !!getToken();
}

// ---------- AUTH ----------

async function signup(email, password) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.[0]?.msg || data.detail || "Signup failed");
  setToken(data.access_token);
  return data;
}

async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  setToken(data.access_token);
  return data;
}

function logout() {
  clearToken();
  window.location.href = "index.html";
}

// ---------- WIDGETS ----------

async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };
  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    window.location.href = "index.html";
    throw new Error("Session expired, please login again");
  }
  return res;
}

async function getWidgets() {
  const res = await authFetch("/widgets");
  return res.json();
}

async function createWidget(widgetData) {
  const res = await authFetch("/widgets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(widgetData),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(data.detail));
  return data;
}

async function deleteWidget(widgetId) {
  const res = await authFetch(`/widgets/${widgetId}`, { method: "DELETE" });
  return res.json();
}

async function getWidgetSubmissions(widgetId) {
  const res = await authFetch(`/widgets/${widgetId}/submissions`);
  return res.json();
}

async function getWidgetStats(widgetId) {
  const res = await authFetch(`/widgets/${widgetId}/stats`);
  return res.json();
}

async function getEmbedCode(widgetId) {
  const res = await authFetch(`/widgets/${widgetId}/embed`);
  return res.json();
}
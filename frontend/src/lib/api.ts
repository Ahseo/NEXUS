const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    credentials: "include",
    ...options,
  });
  if (res.status === 401) {
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// Auth Endpoints
export const auth = {
  me: () => fetchApi<{ user_id: string; email: string }>("/api/auth/me"),
  logout: () =>
    fetch(`${API_BASE}/api/auth/logout`, {
      method: "POST",
      credentials: "include",
    }),
};

// Event Endpoints
export const events = {
  list: (params?: Record<string, string>) => {
    const qs = params ? `?${new URLSearchParams(params)}` : "";
    return fetchApi(`/api/events${qs}`);
  },
  get: (id: string) => fetchApi(`/api/events/${id}`),
  accept: (id: string) => fetchApi(`/api/events/${id}/accept`, { method: "POST" }),
  reject: (id: string, reason: string) =>
    fetchApi(`/api/events/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  apply: (id: string) => fetchApi(`/api/events/${id}/apply`, { method: "POST" }),
  people: (id: string) => fetchApi(`/api/events/${id}/people`),
  rate: (id: string, rating: number) =>
    fetchApi(`/api/events/${id}/rate`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    }),
};

// People Endpoints
export const people = {
  list: () => fetchApi("/api/people"),
  get: (id: string) => fetchApi(`/api/people/${id}`),
  graph: (id: string) => fetchApi(`/api/people/${id}/graph`),
  mark: (id: string, action: string) =>
    fetchApi(`/api/people/${id}/mark`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
};

// Target People Endpoints
export const targets = {
  list: () => fetchApi("/api/targets"),
  create: (data: { name: string; company?: string; role?: string; reason: string; priority: string }) =>
    fetchApi("/api/targets", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: Record<string, unknown>) =>
    fetchApi(`/api/targets/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string) => fetchApi(`/api/targets/${id}`, { method: "DELETE" }),
  matches: (id: string) => fetchApi(`/api/targets/${id}/matches`),
};

// Message Endpoints
export const messages = {
  list: () => fetchApi("/api/messages"),
  get: (id: string) => fetchApi(`/api/messages/${id}`),
  approve: (id: string) => fetchApi(`/api/messages/${id}/approve`, { method: "POST" }),
  edit: (id: string, content: string) =>
    fetchApi(`/api/messages/${id}/edit`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  reject: (id: string) => fetchApi(`/api/messages/${id}/reject`, { method: "POST" }),
};

// Profile Endpoints
export const profile = {
  get: () => fetchApi("/api/profile"),
  update: (data: Record<string, unknown>) =>
    fetchApi("/api/profile", { method: "PUT", body: JSON.stringify(data) }),
  getPreferences: () => fetchApi("/api/profile/preferences"),
  updatePreferences: (data: Record<string, unknown>) =>
    fetchApi("/api/profile/preferences", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// Feedback Endpoints
export const feedback = {
  submit: (data: Record<string, unknown>) =>
    fetchApi("/api/feedback", { method: "POST", body: JSON.stringify(data) }),
  stats: () => fetchApi("/api/feedback/stats"),
};

// Graph Endpoints
export const graph = {
  network: () => fetchApi("/api/graph/network"),
  suggestions: () => fetchApi("/api/graph/suggestions"),
};

// Agent Control
export const agent = {
  status: () => fetchApi("/api/agent/status"),
  events: (params?: { limit?: number; source?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.source) qs.set("source", params.source);
    const q = qs.toString();
    return fetchApi<
      { id: string; type: string; source: string; message: string; detail: string; time: string }[]
    >(`/api/agent/events${q ? `?${q}` : ""}`);
  },
  pause: () => fetchApi("/api/agent/pause", { method: "POST" }),
  resume: () => fetchApi("/api/agent/resume", { method: "POST" }),
  runNow: () => fetchApi("/api/agent/run-now", { method: "POST" }),
};

// Chat Endpoints
export const chat = {
  send: (message: string) =>
    fetch(`${API_BASE}/api/chat/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ message }),
    }),
  history: () => fetchApi<{ role: string; content: string }[]>("/api/chat/history"),
  clear: () => fetchApi("/api/chat/history", { method: "DELETE" }),
};

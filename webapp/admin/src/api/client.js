const API_BASE = import.meta.env.VITE_API_URL || "/api";

function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  if (token) localStorage.setItem("access_token", token);
  else localStorage.removeItem("access_token");
}

export function setUser(user) {
  if (user) localStorage.setItem("user", JSON.stringify(user));
  else localStorage.removeItem("user");
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    setToken(null);
    setUser(null);
    if (!window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }

  if (res.status === 204) return null;
  return res.json();
}

export const authApi = {
  login: (email, password) =>
    api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => api("/auth/me"),
};

export const devicesApi = {
  list: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api(`/devices${q ? `?${q}` : ""}`);
  },
  get: (id) => api(`/devices/${id}`),
  command: (id, command) =>
    api(`/devices/${id}/command`, {
      method: "POST",
      body: JSON.stringify({ command }),
    }),
};

export const usersApi = {
  list: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api(`/users${q ? `?${q}` : ""}`);
  },
};

export const cardsApi = {
  list: () => api("/cards"),
};

export const logsApi = {
  list: (limit = 50) => api(`/logs?limit=${limit}`),
};

export const statsApi = {
  get: () => api("/stats"),
};

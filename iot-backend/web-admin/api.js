// Lop goi API — tu dong gan Bearer token, tu dong lam moi token het han
const Api = (() => {
  function getAccessToken() { return localStorage.getItem("accessToken"); }
  function getRefreshToken() { return localStorage.getItem("refreshToken"); }
  function getUser() {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  }

  function saveSession({ accessToken, refreshToken, user }) {
    localStorage.setItem("accessToken", accessToken);
    if (refreshToken) localStorage.setItem("refreshToken", refreshToken);
    if (user) localStorage.setItem("user", JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
  }

  async function login(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Dang nhap that bai");
    saveSession(data);
    return data;
  }

  async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) throw new Error("Khong co refresh token");
    const res = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error("Refresh that bai");
    localStorage.setItem("accessToken", data.accessToken);
    return data.accessToken;
  }

  // Goi API co xac thuc — tu retry 1 lan neu bi 401 (token het han)
  async function authFetch(path, options = {}, retried = false) {
    const token = getAccessToken();
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
      },
    });

    if (res.status === 401 && !retried) {
      try {
        await refreshAccessToken();
        return authFetch(path, options, true);
      } catch {
        clearSession();
        window.location.reload();
      }
    }

    return res;
  }

  async function getLatestSensor(deviceUid) {
    const res = await authFetch(`/api/sensors/latest?device_uid=${deviceUid}`);
    if (!res.ok) throw new Error("Loi tai du lieu cam bien");
    return res.json();
  }

  async function getSensorHistory(deviceUid, hours) {
    const res = await authFetch(`/api/sensors/history?device_uid=${deviceUid}&hours=${hours}`);
    if (!res.ok) throw new Error("Loi tai lich su");
    return res.json();
  }

  async function getDoorLogs(deviceUid) {
    const res = await authFetch(`/api/door/logs?device_uid=${deviceUid}`);
    if (!res.ok) throw new Error("Loi tai log cua");
    return res.json();
  }

  async function openDoor(deviceUid) {
    const res = await authFetch(`/api/door/open`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_uid: deviceUid }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Khong mo duoc cua");
    return data;
  }

  function openEventStream(onSensor, onDoor, onOpen, onError) {
    const token = getAccessToken();
    const es = new EventSource(`${API_BASE}/api/events/stream?token=${token}`);
    es.addEventListener("sensor_update", (e) => onSensor(JSON.parse(e.data)));
    es.addEventListener("door_event", (e) => onDoor(JSON.parse(e.data)));
    es.onopen = onOpen;
    es.onerror = onError;
    return es;
  }

  return {
    getAccessToken, getUser, login, clearSession,
    getLatestSensor, getSensorHistory, getDoorLogs, openDoor,
    openEventStream,
  };
})();

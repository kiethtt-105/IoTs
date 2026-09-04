// ===================== TIEN ICH =====================
function fmtTime(iso) {
  if (!iso) return "chưa có dữ liệu";
  const d = new Date(iso);
  return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
function fmtDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
function pulseTile(metric) {
  const el = document.querySelector(`.sensor-tile[data-metric="${metric}"]`);
  if (!el) return;
  el.classList.add("pulse");
  clearTimeout(el._pulseTimer);
  el._pulseTimer = setTimeout(() => el.classList.remove("pulse"), 1500);
}

// ===================== ĐĂNG NHẬP =====================
const loginScreen = document.getElementById("loginScreen");
const appEl = document.getElementById("app");
const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.hidden = true;
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  try {
    await Api.login(username, password);
    enterApp();
  } catch (err) {
    loginError.textContent = err.message;
    loginError.hidden = false;
  }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  Api.clearSession();
  window.location.reload();
});

function enterApp() {
  if (window._appEntered) return; // chan goi enterApp() nhieu lan gay loi bieu do
  window._appEntered = true;

  const user = Api.getUser();
  loginScreen.hidden = true;
  appEl.hidden = false;
  document.getElementById("userLabel").textContent = `${user.username} · ${user.role === "chunha" ? "Chủ nhà" : "Khách"}`;

  // Chi chunha moi thay/duoc bam nut mo cua
  const openBtn = document.getElementById("openDoorBtn");
  if (user.role !== "chunha") {
    openBtn.disabled = true;
    openBtn.title = "Chỉ tài khoản chủ nhà mới có quyền mở cửa";
  }

  initNav();
  initCharts();
  loadInitialData();
  connectRealtime();
  loadRules();
  document.getElementById("historyRange").addEventListener("change", loadHistoryCharts);
  document.getElementById("openDoorBtn").addEventListener("click", handleOpenDoor);
}

// Da dang nhap tu truoc (token con trong localStorage) -> vao thang app
if (Api.getAccessToken() && Api.getUser()) {
  enterApp();
}

// ===================== ĐIỀU HƯỚNG ===================== 
function initNav() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`view-${btn.dataset.view}`).classList.add("active");
      if (btn.dataset.view === "history") loadHistoryCharts();
      if (btn.dataset.view === "door") loadDoorLogs();
    });
  });
}

// ===================== DỮ LIỆU BAN ĐẦU ===================== 
async function loadInitialData() {
  try {
    const latest = await Api.getLatestSensor(DEVICE_UID);
    if (latest) applySensorUpdate(latest, false);
  } catch (err) {
    console.error(err);
  }
  loadHistoryCharts();
}

function applySensorUpdate(data, live = true) {
  ["temperature", "humidity", "gas_level"].forEach((metric) => {
    const val = data[metric];
    if (val === undefined || val === null) return;
    document.getElementById(`val-${metric}`).textContent = Number(val).toFixed(1);
    document.getElementById(`time-${metric}`).textContent = fmtTime(data.recorded_at);
    if (live) pulseTile(metric);
  });

  if (data.motion !== undefined) {
    document.getElementById("val-motion").textContent = data.motion ? "Có chuyển động" : "Không có";
    document.getElementById("time-motion").textContent = fmtTime(data.recorded_at);
    if (live) pulseTile("motion");
  }

  if (live) {
    pushActivity(`Cập nhật cảm biến — nhiệt độ ${data.temperature}°C, độ ẩm ${data.humidity}%`, data.recorded_at);
    pushChartPoint(data);
  }
}

function pushActivity(text, iso) {
  const feed = document.getElementById("activityFeed");
  const emptyEl = feed.querySelector(".activity-empty");
  if (emptyEl) emptyEl.remove();

  const li = document.createElement("li");
  li.innerHTML = `<span>${text}</span><span class="activity-time">${fmtDateTime(iso)}</span>`;
  feed.prepend(li);
  while (feed.children.length > 20) feed.removeChild(feed.lastChild);
}

// ===================== REALTIME (SSE) ===================== 
function connectRealtime() {
  const statusEl = document.getElementById("connStatus");
  const labelEl = document.getElementById("connLabel");

  const es = Api.openEventStream(
    (data) => applySensorUpdate(data, true),
    (data) => {
      const label = data.method === "app" ? "Mở cửa qua App" : data.method === "nfc" ? `Quẹt thẻ ${data.card_uid || ""}` : "Sự kiện cửa";
      const status = data.status === "success" ? "thành công" : "bị từ chối";
      pushActivity(`${label} — ${status}`, data.created_at);
      if (document.getElementById("view-door").classList.contains("active")) loadDoorLogs();
    },
    () => { statusEl.classList.add("online"); statusEl.classList.remove("offline"); labelEl.textContent = "Đang kết nối trực tiếp"; },
    () => { statusEl.classList.add("offline"); statusEl.classList.remove("online"); labelEl.textContent = "Mất kết nối — đang thử lại…"; }
  );
  return es;
}

// ===================== BIỂU ĐỒ ===================== 
let overviewChart, historyChart, gasChart;
const chartPoints = { temperature: [], humidity: [] };

function initCharts() {
  // Chong loi "Canvas is already in use" khi ham nay bi goi lai lan 2
  // (vi du: nguoi dung dang nhap trong khi phien cu van con luu trong trinh duyet)
  [overviewChart, historyChart, gasChart].forEach((c) => c && c.destroy());

  const commonOpts = {
    responsive: true,
    animation: { duration: 300 },
    interaction: { mode: "index", intersect: false },
    scales: {
      x: { ticks: { color: "#7C8AA0", maxTicksLimit: 8 }, grid: { color: "#182131" } },
      y: { ticks: { color: "#7C8AA0" }, grid: { color: "#182131" } },
    },
    plugins: { legend: { labels: { color: "#E8EDF4" } } },
  };

  overviewChart = new Chart(document.getElementById("overviewChart"), {
    type: "line",
    data: { labels: [], datasets: [
      { label: "Nhiệt độ (°C)", data: [], borderColor: "#2FD9C4", backgroundColor: "transparent", tension: 0.3 },
      { label: "Độ ẩm (%)", data: [], borderColor: "#F2B84B", backgroundColor: "transparent", tension: 0.3 },
    ]},
    options: commonOpts,
  });

  historyChart = new Chart(document.getElementById("historyChart"), {
    type: "line",
    data: { labels: [], datasets: [
      { label: "Nhiệt độ (°C)", data: [], borderColor: "#2FD9C4", backgroundColor: "rgba(47,217,196,0.08)", fill: true, tension: 0.25 },
      { label: "Độ ẩm (%)", data: [], borderColor: "#F2B84B", backgroundColor: "transparent", tension: 0.25 },
    ]},
    options: commonOpts,
  });

  gasChart = new Chart(document.getElementById("gasChart"), {
    type: "line",
    data: { labels: [], datasets: [
      { label: "Khí gas (ppm)", data: [], borderColor: "#E5555A", backgroundColor: "rgba(229,85,90,0.08)", fill: true, tension: 0.25 },
    ]},
    options: commonOpts,
  });
}

function pushChartPoint(data) {
  const label = fmtTime(data.recorded_at);
  chartPoints.temperature.push(data.temperature);
  chartPoints.humidity.push(data.humidity);

  overviewChart.data.labels.push(label);
  overviewChart.data.datasets[0].data.push(data.temperature);
  overviewChart.data.datasets[1].data.push(data.humidity);
  if (overviewChart.data.labels.length > 40) {
    overviewChart.data.labels.shift();
    overviewChart.data.datasets.forEach((ds) => ds.data.shift());
  }
  overviewChart.update("none");
}

async function loadHistoryCharts() {
  const hours = document.getElementById("historyRange").value;
  try {
    const rows = await Api.getSensorHistory(DEVICE_UID, hours);
    const labels = rows.map((r) => fmtDateTime(r.recorded_at));

    historyChart.data.labels = labels;
    historyChart.data.datasets[0].data = rows.map((r) => r.temperature);
    historyChart.data.datasets[1].data = rows.map((r) => r.humidity);
    historyChart.update();

    gasChart.data.labels = labels;
    gasChart.data.datasets[0].data = rows.map((r) => r.gas_level);
    gasChart.update();

    // Cung nap du lieu ban dau cho bieu do tong quan (40 diem gan nhat)
    const recent = rows.slice(-40);
    overviewChart.data.labels = recent.map((r) => fmtTime(r.recorded_at));
    overviewChart.data.datasets[0].data = recent.map((r) => r.temperature);
    overviewChart.data.datasets[1].data = recent.map((r) => r.humidity);
    overviewChart.update();
  } catch (err) {
    console.error(err);
  }
}

// ===================== CỬA & NFC ===================== 
async function handleOpenDoor() {
  const btn = document.getElementById("openDoorBtn");
  const msg = document.getElementById("doorMsg");
  btn.disabled = true;
  try {
    await Api.openDoor(DEVICE_UID);
    msg.textContent = "Đã gửi lệnh mở cửa thành công.";
    msg.classList.remove("error");
    msg.hidden = false;
    loadDoorLogs();
  } catch (err) {
    msg.textContent = err.message;
    msg.classList.add("error");
    msg.hidden = false;
  } finally {
    setTimeout(() => { btn.disabled = Api.getUser().role !== "chunha"; }, 800);
  }
}

async function loadDoorLogs() {
  const tbody = document.querySelector("#doorLogTable tbody");
  try {
    const rows = await Api.getDoorLogs(DEVICE_UID);
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Chưa có dữ liệu</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>${fmtDateTime(r.created_at)}</td>
        <td>${r.method === "app" ? "App" : "Thẻ NFC"}</td>
        <td>${r.card_uid || r.username || "—"}</td>
        <td><span class="status-badge ${r.status}">${r.status === "success" ? "Thành công" : "Từ chối"}</span></td>
        <td>${r.reason || "—"}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Lỗi tải dữ liệu</td></tr>`;
  }
}

// ===================== LUẬT TỰ ĐỘNG ===================== 
async function loadRules() {
  const tbody = document.querySelector("#rulesTable tbody");
  try {
    const token = Api.getAccessToken();
    const res = await fetch(`${API_BASE}/api/rules?device_uid=${DEVICE_UID}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error();
    const rows = await res.json();
    if (!rows.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Chưa có luật nào</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>${r.name}</td>
        <td>${r.condition.metric} ${r.condition.operator} ${r.condition.value}</td>
        <td>${r.action.target} → ${r.action.command}</td>
        <td class="${r.enabled ? "rule-enabled" : "rule-disabled"}">${r.enabled ? "Đang bật" : "Đang tắt"}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Lỗi tải danh sách luật</td></tr>`;
  }
}

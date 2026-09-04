import { useEffect, useState } from "react";
import {
  Lock,
  Users,
  Activity,
  AlertTriangle,
  BatteryLow,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import { statsApi, devicesApi, logsApi } from "../api/client";

const statusColor = {
  locked: "bg-emerald-100 text-emerald-700",
  unlocked: "bg-amber-100 text-amber-700",
  offline: "bg-slate-200 text-slate-600",
  tamper: "bg-red-100 text-red-700",
};

const statusLabel = {
  locked: "Đã khóa",
  unlocked: "Đang mở",
  offline: "Offline",
  tamper: "Bị xâm nhập",
};

const methodLabel = {
  app_ble: "BLE App",
  app_remote: "Remote",
  nfc_card: "NFC",
  pin: "PIN",
  auto: "Auto",
};

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-start gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={22} />
      </div>
      <div>
        <div className="text-2xl font-bold text-slate-800">{value}</div>
        <div className="text-sm text-slate-500 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

function formatTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
  });
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [devices, setDevices] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, d, l] = await Promise.all([
          statsApi.get(),
          devicesApi.list(),
          logsApi.list(8),
        ]);
        if (!cancelled) {
          setStats(s);
          setDevices(d);
          setLogs(l);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-500 gap-2">
        <Loader2 className="animate-spin" size={20} />
        Đang tải dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
        Lỗi: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Dashboard</h2>
        <p className="text-sm text-slate-500 mt-1">Tổng quan hệ thống khóa thông minh</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          icon={Lock}
          label="Thiết bị online"
          value={`${stats.online_devices}/${stats.total_devices}`}
          color="bg-emerald-100 text-emerald-600"
        />
        <StatCard
          icon={Users}
          label="Người dùng"
          value={stats.total_users}
          color="bg-blue-100 text-blue-600"
        />
        <StatCard
          icon={Activity}
          label="Truy cập hôm nay"
          value={stats.today_access}
          color="bg-violet-100 text-violet-600"
        />
        <StatCard
          icon={AlertTriangle}
          label="Cảnh báo"
          value={stats.failed_access_today + stats.tamper_alerts}
          color="bg-red-100 text-red-600"
        />
      </div>

      {/* Alerts */}
      {(stats.low_battery > 0 || stats.tamper_alerts > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stats.tamper_alerts > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
              <ShieldAlert className="text-red-600 shrink-0" size={22} />
              <div>
                <div className="font-medium text-red-800">
                  {stats.tamper_alerts} thiết bị bị xâm nhập
                </div>
                <div className="text-sm text-red-600">Cần kiểm tra ngay</div>
              </div>
            </div>
          )}
          {stats.low_battery > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
              <BatteryLow className="text-amber-600 shrink-0" size={22} />
              <div>
                <div className="font-medium text-amber-800">
                  {stats.low_battery} thiết bị pin yếu
                </div>
                <div className="text-sm text-amber-600">Dưới 20%</div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Devices */}
        <div className="bg-white rounded-xl border border-slate-200">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800">Thiết bị</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {devices.slice(0, 5).map((d) => (
              <div key={d.id} className="px-5 py-3.5 flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Lock size={16} className="text-slate-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-slate-800 text-sm truncate">{d.name}</div>
                  <div className="text-xs text-slate-500">{d.location || "—"}</div>
                </div>
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                    statusColor[d.status] || statusColor.offline
                  }`}
                >
                  {statusLabel[d.status] || d.status}
                </span>
              </div>
            ))}
            {devices.length === 0 && (
              <div className="px-5 py-8 text-center text-slate-400 text-sm">
                Chưa có thiết bị
              </div>
            )}
          </div>
        </div>

        {/* Recent logs */}
        <div className="bg-white rounded-xl border border-slate-200">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800">Truy cập gần đây</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {logs.map((log) => (
              <div key={log.id} className="px-5 py-3.5 flex items-center gap-3">
                <div
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    log.result === "success" ? "bg-emerald-500" : "bg-red-500"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-slate-800">
                    <span className="font-medium">{log.device_name || "—"}</span>
                    <span className="text-slate-400"> · </span>
                    <span className="text-slate-500">
                      {methodLabel[log.method] || log.method}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500">
                    {log.user_name || "Không xác định"}
                  </div>
                </div>
                <span className="text-xs text-slate-400 whitespace-nowrap">
                  {formatTime(log.created_at)}
                </span>
              </div>
            ))}
            {logs.length === 0 && (
              <div className="px-5 py-8 text-center text-slate-400 text-sm">
                Chưa có lịch sử
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

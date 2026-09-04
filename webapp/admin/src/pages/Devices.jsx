import { useEffect, useState } from "react";
import {
  Search,
  Plus,
  MoreVertical,
  Battery,
  Lock,
  Unlock,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { devicesApi } from "../api/client";

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

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await devicesApi.list();
      setDevices(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = devices.filter(
    (d) =>
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      (d.location || "").toLowerCase().includes(search.toLowerCase()) ||
      d.mac_address.toLowerCase().includes(search.toLowerCase())
  );

  const sendCommand = async (id, command) => {
    setActionId(id);
    try {
      await devicesApi.command(id, command);
      // refresh after short delay so MQTT can update status
      setTimeout(load, 800);
    } catch (err) {
      alert("Gửi lệnh thất bại: " + err.message);
    } finally {
      setActionId(null);
    }
  };

  if (loading && devices.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-500 gap-2">
        <Loader2 className="animate-spin" size={20} />
        Đang tải thiết bị...
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Thiết bị</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý khóa thông minh</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={load}
            className="inline-flex items-center gap-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium px-3.5 py-2.5 rounded-lg transition-colors"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Làm mới
          </button>
          <button className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors">
            <Plus size={18} />
            Thêm thiết bị
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Tìm theo tên, vị trí, MAC..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-slate-500 text-xs uppercase tracking-wider">
                <th className="px-5 py-3 font-medium">Thiết bị</th>
                <th className="px-5 py-3 font-medium">Trạng thái</th>
                <th className="px-5 py-3 font-medium">Pin</th>
                <th className="px-5 py-3 font-medium">MAC</th>
                <th className="px-5 py-3 font-medium">Firmware</th>
                <th className="px-5 py-3 font-medium">Chủ sở hữu</th>
                <th className="px-5 py-3 font-medium">Điều khiển</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                        <Lock size={16} className="text-slate-600" />
                      </div>
                      <div>
                        <div className="font-medium text-slate-800">{d.name}</div>
                        <div className="text-xs text-slate-500">{d.location || "—"}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-block text-xs font-medium px-2.5 py-1 rounded-full ${
                        statusColor[d.status] || statusColor.offline
                      }`}
                    >
                      {statusLabel[d.status] || d.status}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-1.5">
                      <Battery
                        size={14}
                        className={
                          (d.battery_level ?? 100) < 20
                            ? "text-red-500"
                            : (d.battery_level ?? 100) < 50
                            ? "text-amber-500"
                            : "text-emerald-500"
                        }
                      />
                      <span
                        className={
                          (d.battery_level ?? 100) < 20
                            ? "text-red-600 font-medium"
                            : "text-slate-700"
                        }
                      >
                        {d.battery_level != null ? `${d.battery_level}%` : "—"}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-slate-600">
                    {d.mac_address}
                  </td>
                  <td className="px-5 py-4 text-slate-600">{d.firmware_version || "—"}</td>
                  <td className="px-5 py-4 text-slate-700">{d.owner_name || "—"}</td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-1.5">
                      <button
                        title="Khóa"
                        disabled={actionId === d.id || d.status === "offline"}
                        onClick={() => sendCommand(d.id, "lock")}
                        className="p-1.5 rounded-lg hover:bg-emerald-50 text-slate-400 hover:text-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {actionId === d.id ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Lock size={16} />
                        )}
                      </button>
                      <button
                        title="Mở khóa"
                        disabled={actionId === d.id || d.status === "offline"}
                        onClick={() => sendCommand(d.id, "unlock")}
                        className="p-1.5 rounded-lg hover:bg-amber-50 text-slate-400 hover:text-amber-600 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <Unlock size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-slate-400">
                    Không tìm thấy thiết bị
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Search, Loader2, RefreshCw } from "lucide-react";
import { logsApi } from "../api/client";

const methodLabel = {
  app_ble: "BLE App",
  app_remote: "Remote",
  nfc_card: "NFC",
  pin: "PIN",
  auto: "Auto",
};

const resultColor = {
  success: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  denied: "bg-amber-100 text-amber-700",
};

const resultLabel = {
  success: "Thành công",
  failed: "Thất bại",
  denied: "Từ chối",
};

function formatTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("vi-VN");
}

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await logsApi.list(100);
      setLogs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = logs.filter(
    (l) =>
      (l.device_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (l.user_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (l.method || "").toLowerCase().includes(search.toLowerCase())
  );

  if (loading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-500 gap-2">
        <Loader2 className="animate-spin" size={20} />
        Đang tải lịch sử...
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Lịch sử truy cập</h2>
          <p className="text-sm text-slate-500 mt-1">Tất cả sự kiện mở/khóa cửa</p>
        </div>
        <button
          onClick={load}
          className="inline-flex items-center gap-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium px-3.5 py-2.5 rounded-lg transition-colors"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Làm mới
        </button>
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
          placeholder="Tìm theo thiết bị, người dùng, phương thức..."
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
                <th className="px-5 py-3 font-medium">Thời gian</th>
                <th className="px-5 py-3 font-medium">Thiết bị</th>
                <th className="px-5 py-3 font-medium">Người dùng</th>
                <th className="px-5 py-3 font-medium">Phương thức</th>
                <th className="px-5 py-3 font-medium">Kết quả</th>
                <th className="px-5 py-3 font-medium">Lý do</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-4 text-slate-600 whitespace-nowrap">
                    {formatTime(log.created_at)}
                  </td>
                  <td className="px-5 py-4 font-medium text-slate-800">
                    {log.device_name || "—"}
                  </td>
                  <td className="px-5 py-4 text-slate-700">{log.user_name || "—"}</td>
                  <td className="px-5 py-4 text-slate-600">
                    {methodLabel[log.method] || log.method}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                        resultColor[log.result] || "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {resultLabel[log.result] || log.result}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-500 text-xs">
                    {log.failure_reason || "—"}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-slate-400">
                    Không có lịch sử
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

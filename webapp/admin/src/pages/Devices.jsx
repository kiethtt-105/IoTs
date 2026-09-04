import { useState } from "react";
import { Lock, Battery, Wifi, Search, Plus, MoreVertical } from "lucide-react";
import { devices as mockDevices } from "../data/mock";

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
  tamper: "Tamper",
};

export default function Devices() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const filtered = mockDevices.filter((d) => {
    const matchSearch =
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      d.location.toLowerCase().includes(search.toLowerCase()) ||
      d.mac_address.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === "all" || d.status === filter;
    return matchSearch && matchFilter;
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Thiết bị</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý khóa thông minh</p>
        </div>
        <button className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors">
          <Plus size={18} />
          Thêm thiết bị
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo tên, vị trí, MAC..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {["all", "locked", "unlocked", "offline", "tamper"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                filter === s
                  ? "bg-slate-800 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {s === "all" ? "Tất cả" : statusLabel[s]}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
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
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50/80">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                        <Lock size={16} className="text-slate-600" />
                      </div>
                      <div>
                        <div className="font-medium text-slate-800">{d.name}</div>
                        <div className="text-xs text-slate-500">{d.location}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-block text-xs font-medium px-2.5 py-1 rounded-full ${
                        statusColor[d.status]
                      }`}
                    >
                      {statusLabel[d.status]}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-1.5">
                      <Battery
                        size={14}
                        className={
                          d.battery_level < 20
                            ? "text-red-500"
                            : d.battery_level < 50
                            ? "text-amber-500"
                            : "text-emerald-500"
                        }
                      />
                      <span
                        className={
                          d.battery_level < 20
                            ? "text-red-600 font-medium"
                            : "text-slate-700"
                        }
                      >
                        {d.battery_level}%
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-slate-600">
                    {d.mac_address}
                  </td>
                  <td className="px-5 py-4 text-slate-600">{d.firmware_version}</td>
                  <td className="px-5 py-4 text-slate-700">{d.owner}</td>
                  <td className="px-5 py-4">
                    <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                      <MoreVertical size={16} />
                    </button>
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

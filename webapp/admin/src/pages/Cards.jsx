import { useEffect, useState } from "react";
import { Search, Plus, CreditCard, Loader2 } from "lucide-react";
import { cardsApi } from "../api/client";

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN");
}

export default function Cards() {
  const [cards, setCards] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    cardsApi
      .list()
      .then((data) => {
        if (!cancelled) setCards(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = cards.filter(
    (c) =>
      (c.label || "").toLowerCase().includes(search.toLowerCase()) ||
      c.card_uid.toLowerCase().includes(search.toLowerCase()) ||
      (c.user_name || "").toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-500 gap-2">
        <Loader2 className="animate-spin" size={20} />
        Đang tải thẻ NFC...
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Thẻ NFC</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý thẻ truy cập</p>
        </div>
        <button className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors">
          <Plus size={18} />
          Thêm thẻ
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
          placeholder="Tìm theo label, UID, người dùng..."
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
                <th className="px-5 py-3 font-medium">Thẻ</th>
                <th className="px-5 py-3 font-medium">UID</th>
                <th className="px-5 py-3 font-medium">Người dùng</th>
                <th className="px-5 py-3 font-medium">Thiết bị</th>
                <th className="px-5 py-3 font-medium">Trạng thái</th>
                <th className="px-5 py-3 font-medium">Ngày cấp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                        <CreditCard size={16} className="text-slate-600" />
                      </div>
                      <span className="font-medium text-slate-800">{c.label || "Không tên"}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-slate-600">{c.card_uid}</td>
                  <td className="px-5 py-4 text-slate-700">{c.user_name || "—"}</td>
                  <td className="px-5 py-4 text-slate-600">{c.device_name || "—"}</td>
                  <td className="px-5 py-4">
                    <span
                      className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                        c.is_active
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {c.is_active ? "Active" : "Revoked"}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-600">{formatDate(c.issued_at)}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-slate-400">
                    Không tìm thấy thẻ
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

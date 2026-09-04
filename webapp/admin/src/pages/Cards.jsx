import { Plus, CreditCard, MoreVertical } from "lucide-react";
import { cards } from "../data/mock";

export default function Cards() {
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

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {cards.map((c) => (
          <div
            key={c.id}
            className="bg-white rounded-xl border border-slate-200 p-5 relative"
          >
            <button className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-slate-100 text-slate-400">
              <MoreVertical size={16} />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center ${
                  c.is_active ? "bg-emerald-100 text-emerald-600" : "bg-slate-100 text-slate-400"
                }`}
              >
                <CreditCard size={22} />
              </div>
              <div>
                <div className="font-semibold text-slate-800">{c.label}</div>
                <div className="text-xs text-slate-500 font-mono">{c.card_uid}</div>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Người dùng</span>
                <span className="text-slate-800 font-medium">{c.user_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Thiết bị</span>
                <span className="text-slate-800">{c.device_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Ngày cấp</span>
                <span className="text-slate-800">{c.issued_at}</span>
              </div>
              <div className="flex justify-between items-center pt-1">
                <span className="text-slate-500">Trạng thái</span>
                {c.is_active ? (
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                    Active
                  </span>
                ) : (
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                    Revoked
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

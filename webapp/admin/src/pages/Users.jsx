import { useState } from "react";
import { Search, Plus, MoreVertical } from "lucide-react";
import { users as mockUsers } from "../data/mock";

const roleColor = {
  owner: "bg-violet-100 text-violet-700",
  member: "bg-blue-100 text-blue-700",
  guest: "bg-slate-100 text-slate-600",
};

const roleLabel = {
  owner: "Owner",
  member: "Member",
  guest: "Guest",
};

export default function Users() {
  const [search, setSearch] = useState("");

  const filtered = mockUsers.filter(
    (u) =>
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Người dùng</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý tài khoản hệ thống</p>
        </div>
        <button className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors">
          <Plus size={18} />
          Thêm người dùng
        </button>
      </div>

      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Tìm theo tên, email..."
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
                <th className="px-5 py-3 font-medium">Người dùng</th>
                <th className="px-5 py-3 font-medium">Vai trò</th>
                <th className="px-5 py-3 font-medium">Số điện thoại</th>
                <th className="px-5 py-3 font-medium">Trạng thái</th>
                <th className="px-5 py-3 font-medium">Ngày tạo</th>
                <th className="px-5 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/80">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-semibold text-sm shrink-0">
                        {u.full_name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-medium text-slate-800">{u.full_name}</div>
                        <div className="text-xs text-slate-500">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-block text-xs font-medium px-2.5 py-1 rounded-full ${
                        roleColor[u.role]
                      }`}
                    >
                      {roleLabel[u.role]}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-600">{u.phone}</td>
                  <td className="px-5 py-4">
                    {u.is_active ? (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                        Disabled
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-slate-600">{u.created_at}</td>
                  <td className="px-5 py-4">
                    <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                      <MoreVertical size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

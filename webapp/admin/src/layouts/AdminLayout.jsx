import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Lock,
  Users,
  CreditCard,
  History,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/devices", icon: Lock, label: "Thiết bị" },
  { to: "/users", icon: Users, label: "Người dùng" },
  { to: "/cards", icon: CreditCard, label: "Thẻ NFC" },
  { to: "/logs", icon: History, label: "Lịch sử truy cập" },
  { to: "/notifications", icon: Bell, label: "Thông báo" },
  { to: "/settings", icon: Settings, label: "Cài đặt" },
];

export default function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    // TODO: clear auth
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-100 flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-64 bg-slate-900 text-white flex flex-col
          transform transition-transform duration-200
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-700">
          <div className="w-9 h-9 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-lg">
            SL
          </div>
          <div>
            <div className="font-semibold text-sm leading-tight">Smart Lock</div>
            <div className="text-xs text-slate-400">Admin Panel</div>
          </div>
          <button
            className="ml-auto lg:hidden text-slate-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-emerald-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-slate-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LogOut size={18} />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-4 lg:px-6 gap-4 sticky top-0 z-10">
          <button
            className="lg:hidden p-2 rounded-lg hover:bg-slate-100"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-slate-800">
              Hệ thống Khóa thông minh
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:block text-right">
              <div className="text-sm font-medium text-slate-800">Admin</div>
              <div className="text-xs text-slate-500">owner@example.com</div>
            </div>
            <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-semibold text-sm">
              A
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

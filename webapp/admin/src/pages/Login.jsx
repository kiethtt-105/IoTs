import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("owner@example.com");
  const [password, setPassword] = useState("admin123");

  const handleSubmit = (e) => {
    e.preventDefault();
    // Demo: bỏ qua auth thật
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-emerald-500 items-center justify-center mb-4">
            <Lock size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Smart Lock Admin</h1>
          <p className="text-slate-400 mt-1 text-sm">Đăng nhập để quản lý hệ thống</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-2xl p-6 shadow-xl space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Mật khẩu
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded-lg transition-colors"
          >
            Đăng nhập
          </button>
          <p className="text-xs text-center text-slate-400 pt-1">
            Demo: dùng tài khoản có sẵn, không cần đúng mật khẩu
          </p>
        </form>
      </div>
    </div>
  );
}

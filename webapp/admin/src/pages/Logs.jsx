import { accessLogs } from "../data/mock";

const methodLabel = {
  app_ble: "BLE App",
  app_remote: "Remote",
  nfc_card: "NFC Card",
  pin: "PIN",
  auto: "Auto",
};

const resultStyle = {
  success: "bg-emerald-100 text-emerald-700",
  failed: "bg-amber-100 text-amber-700",
  denied: "bg-red-100 text-red-700",
};

const resultLabel = {
  success: "Thành công",
  failed: "Thất bại",
  denied: "Từ chối",
};

export default function Logs() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Lịch sử truy cập</h2>
        <p className="text-sm text-slate-500 mt-1">Tất cả sự kiện mở / đóng khóa</p>
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
              {accessLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/80">
                  <td className="px-5 py-3.5 text-slate-600 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString("vi-VN")}
                  </td>
                  <td className="px-5 py-3.5 font-medium text-slate-800">
                    {log.device_name}
                  </td>
                  <td className="px-5 py-3.5 text-slate-700">
                    {log.user_name || (
                      <span className="text-slate-400 italic">Không xác định</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    {methodLabel[log.method]}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`inline-block text-xs font-medium px-2.5 py-1 rounded-full ${
                        resultStyle[log.result]
                      }`}
                    >
                      {resultLabel[log.result]}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-slate-500 text-xs">
                    {log.failure_reason || "—"}
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

import { Bell, BatteryLow, ShieldAlert, WifiOff, Unlock } from "lucide-react";

const items = [
  {
    id: 1,
    type: "tamper",
    title: "Cảnh báo xâm nhập",
    message: "Khóa văn phòng phát hiện tín hiệu tamper",
    time: "12:55",
    unread: true,
  },
  {
    id: 2,
    type: "low_battery",
    title: "Pin yếu",
    message: "Khóa cửa phụ còn 12% pin",
    time: "10:20",
    unread: true,
  },
  {
    id: 3,
    type: "unlock_success",
    title: "Mở khóa thành công",
    message: "Nguyễn Văn A mở Khóa cửa chính qua BLE",
    time: "13:35",
    unread: false,
  },
  {
    id: 4,
    type: "offline",
    title: "Thiết bị offline",
    message: "Khóa cửa phụ mất kết nối",
    time: "Hôm qua",
    unread: false,
  },
  {
    id: 5,
    type: "unlock_failed",
    title: "Mở khóa thất bại",
    message: "PIN sai tại Khóa cửa gara",
    time: "11:55",
    unread: false,
  },
];

const iconMap = {
  tamper: { icon: ShieldAlert, color: "bg-red-100 text-red-600" },
  low_battery: { icon: BatteryLow, color: "bg-amber-100 text-amber-600" },
  unlock_success: { icon: Unlock, color: "bg-emerald-100 text-emerald-600" },
  unlock_failed: { icon: Unlock, color: "bg-amber-100 text-amber-600" },
  offline: { icon: WifiOff, color: "bg-slate-100 text-slate-600" },
};

export default function Notifications() {
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Thông báo</h2>
        <p className="text-sm text-slate-500 mt-1">Cảnh báo và sự kiện hệ thống</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        {items.map((n) => {
          const { icon: Icon, color } = iconMap[n.type] || {
            icon: Bell,
            color: "bg-slate-100 text-slate-600",
          };
          return (
            <div
              key={n.id}
              className={`px-5 py-4 flex items-start gap-4 ${
                n.unread ? "bg-emerald-50/40" : ""
              }`}
            >
              <div className={`p-2.5 rounded-lg shrink-0 ${color}`}>
                <Icon size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-800">{n.title}</span>
                  {n.unread && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  )}
                </div>
                <p className="text-sm text-slate-500 mt-0.5">{n.message}</p>
              </div>
              <span className="text-xs text-slate-400 whitespace-nowrap">{n.time}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

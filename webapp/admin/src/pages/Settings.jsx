export default function Settings() {
  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Cài đặt</h2>
        <p className="text-sm text-slate-500 mt-1">Cấu hình hệ thống</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        <div className="px-5 py-4">
          <div className="font-medium text-slate-800">MQTT Broker</div>
          <div className="text-sm text-slate-500 mt-1">localhost:1883</div>
        </div>
        <div className="px-5 py-4">
          <div className="font-medium text-slate-800">Auto-lock mặc định</div>
          <div className="text-sm text-slate-500 mt-1">10 giây sau khi mở</div>
        </div>
        <div className="px-5 py-4">
          <div className="font-medium text-slate-800">Ngưỡng pin yếu</div>
          <div className="text-sm text-slate-500 mt-1">Dưới 20%</div>
        </div>
        <div className="px-5 py-4">
          <div className="font-medium text-slate-800">Phiên bản Admin</div>
          <div className="text-sm text-slate-500 mt-1">0.1.0 (demo)</div>
        </div>
      </div>
    </div>
  );
}

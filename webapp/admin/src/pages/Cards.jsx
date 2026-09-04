import { useEffect, useState, useRef } from "react";
import { Search, Plus, CreditCard, Loader2, X, Radio } from "lucide-react";
import { cardsApi, devicesApi, usersApi } from "../api/client";

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("vi-VN");
}

export default function Cards() {
  const [cards, setCards] = useState([]);
  const [devices, setDevices] = useState([]);
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [enrollStep, setEnrollStep] = useState("select"); // select | scanning | form | done
  const [selectedDevice, setSelectedDevice] = useState("");
  const [commandId, setCommandId] = useState(null);
  const [scannedUid, setScannedUid] = useState("");
  const [label, setLabel] = useState("");
  const [userId, setUserId] = useState("");
  const [busy, setBusy] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const pollRef = useRef(null);

  const loadCards = () =>
    cardsApi
      .list()
      .then(setCards)
      .catch((err) => setError(err.message));

  useEffect(() => {
    let cancelled = false;
    Promise.all([cardsApi.list(), devicesApi.list(), usersApi.list()])
      .then(([c, d, u]) => {
        if (!cancelled) {
          setCards(c);
          setDevices(d);
          setUsers(u);
          if (d.length) setSelectedDevice(d[0].id);
          if (u.length) setUserId(u[0].id);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const openAdd = () => {
    setShowModal(true);
    setEnrollStep("select");
    setScannedUid("");
    setLabel("");
    setStatusMsg("");
    setCommandId(null);
    setError("");
  };

  const closeModal = () => {
    setShowModal(false);
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const startScan = async () => {
    if (!selectedDevice) {
      setStatusMsg("Chọn thiết bị / đầu đọc");
      return;
    }
    setBusy(true);
    setStatusMsg("Đang gửi lệnh quét thẻ tới đầu đọc...");
    try {
      const res = await cardsApi.enroll(selectedDevice, 45);
      setCommandId(res.command_id);
      setEnrollStep("scanning");
      setStatusMsg(res.message || "Chờ quét thẻ NFC trên đầu đọc...");

      // Poll every 1.5s
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const r = await cardsApi.pollEnroll(res.command_id);
          if (r.status === "scanned" && r.card_uid) {
            clearInterval(pollRef.current);
            setScannedUid(r.card_uid);
            setLabel(`Thẻ ${r.card_uid.slice(-6)}`);
            setEnrollStep("form");
            setStatusMsg(`Đã quét: ${r.card_uid}`);
          }
        } catch {
          /* ignore poll errors */
        }
      }, 1500);
    } catch (err) {
      setStatusMsg(err.message || "Lỗi gửi lệnh");
    } finally {
      setBusy(false);
    }
  };

  const saveCard = async () => {
    if (!scannedUid || !userId) return;
    setBusy(true);
    try {
      await cardsApi.create({
        card_uid: scannedUid,
        label: label || undefined,
        user_id: userId,
        device_id: selectedDevice || undefined,
      });
      setEnrollStep("done");
      setStatusMsg("Đã thêm thẻ thành công!");
      await loadCards();
      setTimeout(closeModal, 1200);
    } catch (err) {
      setStatusMsg(err.message || "Lỗi lưu thẻ");
    } finally {
      setBusy(false);
    }
  };

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
        <button
          onClick={openAdd}
          className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
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
          className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-400"
        />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-slate-500 text-left">
              <th className="px-4 py-3 font-medium">Label</th>
              <th className="px-4 py-3 font-medium">UID</th>
              <th className="px-4 py-3 font-medium">Người dùng</th>
              <th className="px-4 py-3 font-medium">Thiết bị</th>
              <th className="px-4 py-3 font-medium">Trạng thái</th>
              <th className="px-4 py-3 font-medium">Ngày cấp</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-400">
                  <CreditCard className="mx-auto mb-2 opacity-40" size={28} />
                  Không có thẻ nào
                </td>
              </tr>
            ) : (
              filtered.map((c) => (
                <tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">{c.label || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">{c.card_uid}</td>
                  <td className="px-4 py-3">{c.user_name || "—"}</td>
                  <td className="px-4 py-3">{c.device_name || "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                        c.is_active
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {c.is_active ? "Hoạt động" : "Vô hiệu"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{formatDate(c.issued_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Thêm thẻ */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-800">Thêm thẻ NFC</h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>

            <div className="px-5 py-4 space-y-4">
              {enrollStep === "select" && (
                <>
                  <p className="text-sm text-slate-500">
                    Chọn thiết bị (đầu đọc) rồi bấm quét. Simulator sẽ nhận lệnh{" "}
                    <code className="text-xs bg-slate-100 px-1 rounded">enroll_card</code>.
                  </p>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">
                      Thiết bị / Đầu đọc
                    </label>
                    <select
                      value={selectedDevice}
                      onChange={(e) => setSelectedDevice(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                    >
                      {devices.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.location || d.mac_address})
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={startScan}
                    disabled={busy || !selectedDevice}
                    className="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2.5 rounded-lg"
                  >
                    {busy ? <Loader2 className="animate-spin" size={16} /> : <Radio size={16} />}
                    Gọi đầu đọc quét thẻ
                  </button>
                </>
              )}

              {enrollStep === "scanning" && (
                <div className="text-center py-6 space-y-3">
                  <Loader2 className="animate-spin mx-auto text-emerald-600" size={36} />
                  <p className="text-sm font-medium text-slate-700">Đang chờ quét thẻ NFC...</p>
                  <p className="text-xs text-slate-500">
                    Trên Sensor Simulator: chọn <b>[1]</b> hoặc <b>[2]</b> để giả lập chạm thẻ
                  </p>
                  <p className="text-xs text-slate-400 font-mono">cmd: {commandId}</p>
                </div>
              )}

              {enrollStep === "form" && (
                <>
                  <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-sm text-emerald-800">
                    UID đã quét: <span className="font-mono font-semibold">{scannedUid}</span>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">Label</label>
                    <input
                      value={label}
                      onChange={(e) => setLabel(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                      placeholder="Tên thẻ"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1">
                      Gán cho người dùng
                    </label>
                    <select
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                    >
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.full_name} ({u.email})
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={saveCard}
                    disabled={busy}
                    className="w-full inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2.5 rounded-lg"
                  >
                    {busy ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
                    Lưu thẻ
                  </button>
                </>
              )}

              {enrollStep === "done" && (
                <div className="text-center py-6 text-emerald-700 font-medium">
                  ✓ Đã thêm thẻ thành công
                </div>
              )}

              {statusMsg && enrollStep !== "done" && (
                <p className="text-xs text-slate-500 text-center">{statusMsg}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

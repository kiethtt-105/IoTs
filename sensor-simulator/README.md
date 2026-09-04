# Smart Lock Sensor Simulator

Giả lập thiết bị khóa thông minh: **WiFi (MQTT) + BLE + NFC + PIN**

## Cài đặt & Chạy

```bash
cd sensor-simulator
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Menu

```
1. NFC Tap (thẻ hợp lệ)
2. NFC Tap (thẻ lạ)
3. BLE Unlock
4. Nhập PIN
5. Lock thủ công
6. Trigger TAMPER
7. Clear TAMPER
8. Xem trạng thái
9. Thêm thẻ NFC
0. Thoát
```

## Thẻ & PIN demo

- NFC hợp lệ: `04A1B2C3D4E5F6`, `04F6E5D4C3B2A1`
- PIN hợp lệ: `123456`, `999999`

## MQTT Topics

| Topic | Chiều | Nội dung |
|-------|-------|----------|
| `smartlock/{id}/command` | Backend → Device | lock/unlock/reboot/ota |
| `smartlock/{id}/status` | Device → Backend | Telemetry |
| `smartlock/{id}/access` | Device → Backend | Sự kiện mở/đóng |
| `smartlock/{id}/ack` | Device → Backend | Xác nhận lệnh |

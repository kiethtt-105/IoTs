# Backend Nhà thông minh — Bảo mật ưu tiên

Backend này chạy được **hoàn toàn không cần phần cứng thật** — dùng `simulator/deviceSimulator.js`
để giả lập ESP32 gửi dữ liệu cảm biến + quẹt thẻ NFC qua MQTT. Khi có board thật, chỉ cần viết
firmware C++ publish đúng JSON format y hệt simulator, kiến trúc backend giữ nguyên 100%.

## Cài đặt

```bash
# 1. Cài PostgreSQL (hoặc dùng Docker)
docker run --name pg-smarthome -e POSTGRES_PASSWORD=yourpassword -e POSTGRES_DB=smart_home -p 5432:5432 -d postgres

# 2. Cài Mosquitto MQTT broker (hoặc dùng Docker) — bản dev chạy 1883 (không TLS) để code trước cho nhanh
docker run --name mosquitto -p 1883:1883 -d eclipse-mosquitto

# 3. Cài dependencies
npm install

# 4. Tạo file .env từ mẫu, điền thông tin thật
cp .env.example .env
# Với dev/test bạn có thể tạm để MQTT_URL=mqtt://localhost:1883 (không TLS)
# NHƯNG bản nộp cuối phải chuyển sang mqtts://...:8883 (có TLS) — xem mục "Bật TLS" bên dưới

# 5. Tạo bảng trong DB
psql $DATABASE_URL -f db/schema.sql
psql $DATABASE_URL -f db/seed_rules.sql

# 6. Chạy backend
npm start

# 7. (terminal khác) chạy simulator giả lập ESP32
npm run simulate
```

## Test nhanh bằng curl

```bash
# Đăng ký tài khoản chủ nhà
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"chunha1","password":"MatKhauManh123","role":"chunha"}'

# Đăng nhập
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"chunha1","password":"MatKhauManh123"}'
# -> lấy accessToken trong response

# Xem dữ liệu cảm biến mới nhất (thay TOKEN)
curl http://localhost:3000/api/sensors/latest?device_uid=esp32-demo-01 \
  -H "Authorization: Bearer TOKEN"

# Mở cửa qua app (chỉ role chunha mới làm được — thử bằng role khach sẽ bị 403)
curl -X POST http://localhost:3000/api/door/open \
  -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"device_uid":"esp32-demo-01"}'
```

## Bật TLS cho MQTT (bắt buộc trước khi nộp bài — Lớp 6)

1. Tạo chứng chỉ tự ký cho Mosquitto:
   ```bash
   openssl req -new -x509 -days 365 -nodes -out ca.crt -keyout ca.key
   openssl genrsa -out server.key 2048
   openssl req -new -out server.csr -key server.key
   openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365
   ```
2. Cấu hình `mosquitto.conf` bật cổng 8883 với `cafile/certfile/keyfile` trỏ tới các file trên.
3. Đổi `.env`: `MQTT_URL=mqtts://localhost:8883`.
4. Đây chính là bước để bạn làm **Kịch bản A** trong phần thử nghiệm tấn công: bắt gói tin bằng
   Wireshark ở cổng 1883 (đọc được nội dung) rồi so sánh với cổng 8883 (không đọc được) — chụp
   màn hình cả 2 trường hợp cho báo cáo.

## Các điểm bảo mật đã cài (map với mục 7.2 trong tài liệu đề tài)

| Biện pháp | File |
|---|---|
| Mật khẩu hash bằng bcrypt, không lưu plaintext | `src/routes/auth.routes.js` |
| JWT ngắn hạn (15 phút) + refresh token dài hạn | `src/routes/auth.routes.js`, `src/middleware/auth.js` |
| RBAC — chỉ "chunha" mở được cửa | `src/middleware/auth.js` → `authorize()` |
| Rate-limit chống brute-force đăng nhập | `src/middleware/rateLimit.js` |
| Whitelist UID thẻ NFC (không hardcode) | `src/mqtt/mqttClient.js` → `handleNfcScan()` |
| Parameterized query chống SQL Injection | mọi file trong `src/routes/`, `src/mqtt/` |
| Validate input đầu vào (Joi) | `src/routes/auth.routes.js` |
| Security HTTP headers (Helmet) | `src/app.js` |
| Rule engine cấu hình qua DB, không hardcode | `src/rules/ruleEngine.js` |

## Cấu trúc thư mục

```
iot-backend/
├── db/
│   ├── schema.sql       # 7 bảng — dùng để vẽ ERD cho báo cáo
│   └── seed_rules.sql   # 4 luật mẫu (yêu cầu ≥3)
├── src/
│   ├── config/db.js
│   ├── middleware/auth.js       # JWT + RBAC
│   ├── middleware/rateLimit.js  # chống brute-force/DoS
│   ├── routes/auth.routes.js
│   ├── routes/sensor.routes.js
│   ├── routes/door.routes.js
│   ├── mqtt/mqttClient.js       # nhận dữ liệu, check whitelist NFC
│   ├── rules/ruleEngine.js
│   ├── app.js
│   └── server.js
├── simulator/deviceSimulator.js # giả lập ESP32 khi chưa có hardware
├── .env.example
└── package.json
```

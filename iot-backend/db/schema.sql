-- ============================================================
-- SCHEMA CSDL — Hệ thống Nhà thông minh
-- Dùng PostgreSQL. Dùng file này để tạo DB và cũng để vẽ ERD
-- (import vào dbdiagram.io hoặc pgAdmin để xuất hình ERD cho báo cáo)
-- ============================================================

-- Bảng người dùng — có phân quyền (RBAC) theo yêu cầu Lớp 3 & 6
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,           -- bcrypt hash, KHÔNG BAO GIỜ lưu plaintext
    role          VARCHAR(20) NOT NULL CHECK (role IN ('chunha', 'khach')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Bảng thiết bị (mỗi ESP32 là 1 device, cho phép mở rộng nhiều phòng/nhiều board)
CREATE TABLE devices (
    id          SERIAL PRIMARY KEY,
    device_uid  VARCHAR(50) UNIQUE NOT NULL,   -- vd: "esp32-phongkhach-01"
    name        VARCHAR(100) NOT NULL,
    location    VARCHAR(100),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Dữ liệu cảm biến — bảng lớn nhất, cần chạy liên tục ≥7 ngày trước bảo vệ
CREATE TABLE sensor_readings (
    id           BIGSERIAL PRIMARY KEY,
    device_id    INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    temperature  NUMERIC(5,2),
    humidity     NUMERIC(5,2),
    gas_level    NUMERIC(6,2),
    motion       BOOLEAN DEFAULT false,
    recorded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Index để dashboard truy vấn lịch sử nhanh
CREATE INDEX idx_sensor_readings_device_time ON sensor_readings(device_id, recorded_at DESC);

-- Thẻ NFC hợp lệ — whitelist, KHÔNG hardcode trong firmware (yêu cầu bảo mật mục 7.2)
CREATE TABLE nfc_cards (
    id          SERIAL PRIMARY KEY,
    card_uid    VARCHAR(50) UNIQUE NOT NULL,
    owner_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Log ra vào cửa — bằng chứng cho cả tính năng lẫn phần chống tấn công replay
CREATE TABLE door_logs (
    id          BIGSERIAL PRIMARY KEY,
    device_id   INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    method      VARCHAR(10) NOT NULL CHECK (method IN ('nfc', 'app')),
    card_uid    VARCHAR(50),                  -- null nếu mở bằng app
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status      VARCHAR(10) NOT NULL CHECK (status IN ('success', 'denied')),
    reason      VARCHAR(100),                 -- vd: 'uid_not_whitelisted', 'rate_limited'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Rule engine — luật cấu hình được, KHÔNG hardcode trong code (yêu cầu Lớp 3: ≥3 luật)
CREATE TABLE rules (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    device_id    INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    condition    JSONB NOT NULL,   -- vd: {"metric":"temperature","operator":">","value":30}
    action       JSONB NOT NULL,   -- vd: {"target":"fan","command":"ON"}
    enabled      BOOLEAN NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Refresh token — hỗ trợ JWT ngắn hạn + refresh dài hạn (bảo mật tốt hơn JWT sống mãi)
CREATE TABLE refresh_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed 1 device mẫu để chạy simulator ngay
INSERT INTO devices (device_uid, name, location) VALUES ('esp32-demo-01', 'ESP32 Demo', 'Phòng khách');

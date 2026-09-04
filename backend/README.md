# Smart Lock Backend

FastAPI + PostgreSQL + MQTT

## Cài đặt

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

## Cấu hình

Copy `.env.example` → `.env` và sửa connection string PostgreSQL:

```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/smart_lock
```

## Chạy

```bash
# Seed dữ liệu mẫu (chạy 1 lần)
python seed.py

# Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Tài khoản demo

| Email | Password | Role |
|-------|----------|------|
| owner@example.com | admin123 | owner |
| member@example.com | member123 | member |
| guest@example.com | guest123 | guest |

## API chính

| Method | Path | Mô tả |
|--------|------|-------|
| POST | /api/auth/login | Đăng nhập |
| GET | /api/auth/me | User hiện tại |
| GET | /api/devices | Danh sách thiết bị |
| POST | /api/devices/{id}/command | Gửi lệnh lock/unlock |
| GET | /api/users | Người dùng |
| GET | /api/cards | Thẻ NFC |
| GET | /api/logs | Lịch sử truy cập |
| GET | /api/stats | Thống kê dashboard |

## MQTT Topics

- `smartlock/{device_id}/command` — Backend → Device
- `smartlock/{device_id}/status` — Device → Backend
- `smartlock/{device_id}/access` — Device → Backend
- `smartlock/{device_id}/ack` — Device → Backend

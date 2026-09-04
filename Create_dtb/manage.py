#!/usr/bin/env python3
"""
Smart Lock - Menu quản lý nhanh
Tổng hợp: reset DB, tạo admin, backup/restore, cấu hình nguồn dữ liệu thiết bị.

Chạy từ thư mục backend:
    python manage.py
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Paths & defaults
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
# SQL nằm cùng cấp: IoTs/Create_dtb/ (không phải backend/sql)
SQL_DIR = ROOT.parent / "Create_dtb"
BACKUP_DIR = ROOT / "backups"
ENV_FILE = ROOT / ".env"
DATA_SOURCE_CONFIG = ROOT / "data_source.json"

# Admin mặc định (có thể đổi trong menu)
DEFAULT_ADMIN = {
    "email": "kieth@admin.vn",
    "password": "109002",
    "full_name": "Kieth Admin",
}

# Thứ tự DROP (FK dependency) — khớp schema smart_lock
DROP_TABLES_SQL = """
DROP TABLE IF EXISTS device_commands CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS device_status_logs CASCADE;
DROP TABLE IF EXISTS access_logs CASCADE;
DROP TABLE IF EXISTS invites CASCADE;
DROP TABLE IF EXISTS pin_codes CASCADE;
DROP TABLE IF EXISTS access_permissions CASCADE;
DROP TABLE IF EXISTS access_cards CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS device_types CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"""

DROP_TYPES_SQL = """
DROP TYPE IF EXISTS command_status CASCADE;
DROP TYPE IF EXISTS command_type CASCADE;
DROP TYPE IF EXISTS notification_type CASCADE;
DROP TYPE IF EXISTS door_status CASCADE;
DROP TYPE IF EXISTS access_result CASCADE;
DROP TYPE IF EXISTS access_method CASCADE;
DROP TYPE IF EXISTS invite_status CASCADE;
DROP TYPE IF EXISTS pin_type CASCADE;
DROP TYPE IF EXISTS permission_status CASCADE;
DROP TYPE IF EXISTS schedule_type CASCADE;
DROP TYPE IF EXISTS device_status CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_env() -> dict:
    """Đọc .env đơn giản (không phụ thuộc python-dotenv)."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def parse_db_url(sync_url: str) -> dict:
    """
    postgresql://user:pass@host:port/dbname
    """
    u = urlparse(sync_url)
    return {
        "user": u.username or "postgres",
        "password": u.password or "",
        "host": u.hostname or "localhost",
        "port": str(u.port or 5432),
        "dbname": (u.path or "/smart_lock").lstrip("/") or "smart_lock",
    }


def get_db_info() -> dict:
    env = load_env()
    sync = env.get(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/smart_lock",
    )
    # Sửa nếu .env bị lỗi (ví dụ dính pip install...)
    if "pip install" in sync or " " in sync.split("@")[0]:
        # fallback an toàn
        sync = "postgresql://postgres:109002@localhost:5432/smart_lock"
    return parse_db_url(sync)


def run_psql(sql: str, dbname: str | None = None, as_postgres: bool = False) -> tuple[int, str]:
    """Chạy SQL qua psql. Trả về (returncode, combined output)."""
    info = get_db_info()
    env = os.environ.copy()
    env["PGPASSWORD"] = info["password"]
    cmd = [
        "psql",
        "-h", info["host"],
        "-p", info["port"],
        "-U", info["user"],
        "-d", dbname or info["dbname"],
        "-v", "ON_ERROR_STOP=1",
        "-c", sql,
    ]
    try:
        r = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out
    except FileNotFoundError:
        return 1, "Không tìm thấy lệnh 'psql'. Hãy cài PostgreSQL client tools."
    except subprocess.TimeoutExpired:
        return 1, "Timeout khi chạy psql."


def run_psql_file(path: Path, dbname: str | None = None) -> tuple[int, str]:
    info = get_db_info()
    env = os.environ.copy()
    env["PGPASSWORD"] = info["password"]
    cmd = [
        "psql",
        "-h", info["host"],
        "-p", info["port"],
        "-U", info["user"],
        "-d", dbname or info["dbname"],
        "-v", "ON_ERROR_STOP=1",
        "-f", str(path),
    ]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out
    except FileNotFoundError:
        return 1, "Không tìm thấy lệnh 'psql'."
    except subprocess.TimeoutExpired:
        return 1, "Timeout."


def pause():
    input("\nNhấn Enter để quay lại menu...")


def banner():
    print("\n" + "=" * 56)
    print("   SMART LOCK — MENU QUẢN LÝ (DB / Admin / Backup)")
    print("=" * 56)
    info = get_db_info()
    print(f"  DB: {info['user']}@{info['host']}:{info['port']}/{info['dbname']}")
    print("-" * 56)


# ---------------------------------------------------------------------------
# 1. Xóa toàn bộ dữ liệu + bảng, tạo lại schema, tạo admin
# ---------------------------------------------------------------------------
def find_sql_files() -> tuple[Path | None, Path | None]:
    # Ưu tiên: IoTs/Create_dtb (cùng cấp backend)
    candidates = [
        ROOT.parent / "Create_dtb",
        ROOT.parent / "Create_dtb" / "Create_dtb",
        SQL_DIR,
        ROOT / "sql",
    ]
    t1 = t2 = None
    for d in candidates:
        if not d.exists():
            continue
        a = d / "01_create_tables.sql"
        b = d / "02_create_constraints.sql"
        if a.exists():
            t1 = a
        if b.exists():
            t2 = b
        if t1 and t2:
            break
    return t1, t2


def reset_database(create_admin_after: bool = True):
    """
    Xóa ENUM + bảng → tạo lại từ SQL → (tuỳ chọn) tạo admin.
    KHÔNG seed dữ liệu mẫu.
    """
    print("\n⚠️  Sẽ XÓA TOÀN BỘ dữ liệu và bảng trong database hiện tại.")
    confirm = input("Gõ YES để xác nhận: ").strip()
    if confirm != "YES":
        print("Đã hủy.")
        return

    info = get_db_info()
    print(f"\n→ Đang làm việc trên DB: {info['dbname']}")

    # 1) Extension
    print("→ Bật extension pgcrypto...")
    code, out = run_psql('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    if code != 0:
        print(out)
        print("⚠ Không bật được pgcrypto (có thể đã có). Tiếp tục...")

    # 2) Drop tables + types
    print("→ DROP tables...")
    code, out = run_psql(DROP_TABLES_SQL)
    if code != 0:
        print(out)
    print("→ DROP ENUM types...")
    code, out = run_psql(DROP_TYPES_SQL)
    if code != 0:
        print(out)

    # 3) Recreate schema
    t1, t2 = find_sql_files()
    if not t1:
        print("❌ Không tìm thấy 01_create_tables.sql")
        print("   Đặt file SQL cạnh project hoặc trong Create_dtb/")
        return
    print(f"→ Chạy {t1.name}...")
    code, out = run_psql_file(t1)
    if code != 0:
        print(out)
        print("❌ Lỗi khi tạo tables.")
        return
    print("  OK tables.")

    if t2:
        print(f"→ Chạy {t2.name}...")
        code, out = run_psql_file(t2)
        if code != 0:
            print(out)
            print("⚠ Constraints có thể lỗi (một số index đã có). Kiểm tra lại.")
        else:
            print("  OK constraints.")
    else:
        print("⚠ Không tìm thấy 02_create_constraints.sql — bỏ qua.")

    print("\n✅ Schema đã tạo lại (trống, không có dữ liệu mẫu).")

    if create_admin_after:
        print("→ Tạo admin...")
        asyncio.run(create_admin_async())


# ---------------------------------------------------------------------------
# 2. Tạo / cập nhật admin (chỉ admin, không seed)
# ---------------------------------------------------------------------------
async def create_admin_async(
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
):
    # Import trong hàm để script vẫn chạy được khi thiếu dependency lúc chỉ backup
    sys.path.insert(0, str(ROOT))
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from app.config import get_settings
    from app.services.auth import hash_password
    from app.models.user import User, UserRole

    settings = get_settings()
    email = email or DEFAULT_ADMIN["email"]
    password = password or DEFAULT_ADMIN["password"]
    full_name = full_name or DEFAULT_ADMIN["full_name"]

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with Session() as db:
            # Kiểm tra bảng users tồn tại
            try:
                await db.execute(text("SELECT 1 FROM users LIMIT 1"))
            except Exception as e:
                print(f"❌ Bảng users chưa tồn tại. Hãy chạy reset DB trước.\n   {e}")
                await engine.dispose()
                return

            result = await db.execute(select(User).where(User.email == email))
            existing = result.scalar_one_or_none()

            if existing:
                existing.password_hash = hash_password(password)
                existing.role = UserRole.owner
                existing.full_name = full_name
                existing.is_active = True
                print(f"Đã cập nhật admin: {email}")
            else:
                db.add(
                    User(
                        full_name=full_name,
                        email=email,
                        password_hash=hash_password(password),
                        role=UserRole.owner,
                        is_active=True,
                    )
                )
                print(f"Đã tạo admin: {email}")

            await db.commit()
            print("\n✅ Admin sẵn sàng:")
            print(f"   Email   : {email}")
            print(f"   Password: {password}")
            print(f"   Role    : owner")
    finally:
        await engine.dispose()


def create_admin_interactive():
    print("\n--- Tạo / cập nhật Admin (KHÔNG seed dữ liệu mẫu) ---")
    email = input(f"Email [{DEFAULT_ADMIN['email']}]: ").strip() or DEFAULT_ADMIN["email"]
    password = input(f"Password [{DEFAULT_ADMIN['password']}]: ").strip() or DEFAULT_ADMIN["password"]
    name = input(f"Họ tên [{DEFAULT_ADMIN['full_name']}]: ").strip() or DEFAULT_ADMIN["full_name"]
    asyncio.run(create_admin_async(email, password, name))


# ---------------------------------------------------------------------------
# 3. Backup / Restore
# ---------------------------------------------------------------------------
def backup_db():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    info = get_db_info()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = BACKUP_DIR / f"smart_lock_{ts}.sql"
    env = os.environ.copy()
    env["PGPASSWORD"] = info["password"]
    cmd = [
        "pg_dump",
        "-h", info["host"],
        "-p", info["port"],
        "-U", info["user"],
        "-d", info["dbname"],
        "--no-owner",
        "--no-acl",
        "-F", "p",
        "-f", str(out_file),
    ]
    print(f"→ Backup → {out_file}")
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(r.stderr or r.stdout)
            print("❌ Backup thất bại.")
            return
        size = out_file.stat().st_size
        print(f"✅ Backup OK ({size:,} bytes)")
    except FileNotFoundError:
        print("❌ Không tìm thấy pg_dump.")
    except subprocess.TimeoutExpired:
        print("❌ Timeout.")


def list_backups() -> list[Path]:
    if not BACKUP_DIR.exists():
        return []
    files = sorted(BACKUP_DIR.glob("smart_lock_*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def restore_db():
    files = list_backups()
    if not files:
        print("Chưa có file backup trong", BACKUP_DIR)
        return
    print("\nDanh sách backup (mới nhất trước):")
    for i, f in enumerate(files[:15], 1):
        sz = f.stat().st_size
        print(f"  {i}. {f.name}  ({sz:,} bytes)")
    choice = input("Chọn số (hoặc Enter hủy): ").strip()
    if not choice.isdigit():
        print("Hủy.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(files):
        print("Số không hợp lệ.")
        return
    path = files[idx]
    print(f"\n⚠️  Restore sẽ GHI ĐÈ dữ liệu hiện tại từ: {path.name}")
    if input("Gõ YES để xác nhận: ").strip() != "YES":
        print("Hủy.")
        return

    # Drop + recreate empty schema rồi import
    print("→ DROP tables/types...")
    run_psql(DROP_TABLES_SQL)
    run_psql(DROP_TYPES_SQL)
    run_psql('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    info = get_db_info()
    env = os.environ.copy()
    env["PGPASSWORD"] = info["password"]
    cmd = [
        "psql",
        "-h", info["host"],
        "-p", info["port"],
        "-U", info["user"],
        "-d", info["dbname"],
        "-v", "ON_ERROR_STOP=0",
        "-f", str(path),
    ]
    print("→ Đang restore...")
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stderr or r.stdout)
        print("⚠ Restore có cảnh báo/lỗi — kiểm tra lại.")
    else:
        print("✅ Restore xong.")


# ---------------------------------------------------------------------------
# 4. Nguồn dữ liệu thiết bị: simulator / real / both
# ---------------------------------------------------------------------------
def load_data_source() -> dict:
    default = {
        "mode": "simulator",  # simulator | real | both
        "simulator": {
            "enabled": True,
            "mqtt_topic_prefix": "smartlock",
            "note": "Nhận telemetry/access từ sensor-simulator (MQTT)",
        },
        "real_device": {
            "enabled": False,
            "mqtt_topic_prefix": "smartlock",
            "note": "Thiết bị thật (ESP32/ESP8266...) — bật khi có hardware",
            "device_ids": [],
        },
        "description": (
            "mode=simulator: chỉ giả lập | real: chỉ thiết bị thật | both: cả hai. "
            "Backend MQTT subscriber lắng nghe cùng prefix; phân biệt bằng device_id."
        ),
    }
    if DATA_SOURCE_CONFIG.exists():
        try:
            data = json.loads(DATA_SOURCE_CONFIG.read_text(encoding="utf-8"))
            default.update(data)
        except Exception:
            pass
    return default


def save_data_source(cfg: dict):
    DATA_SOURCE_CONFIG.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ Đã lưu cấu hình → {DATA_SOURCE_CONFIG}")


def configure_data_source():
    cfg = load_data_source()
    print("\n--- Nguồn dữ liệu thiết bị ---")
    print(f"  Hiện tại: mode = {cfg.get('mode')}")
    print("  1. Chỉ Simulator (giả lập)")
    print("  2. Chỉ Thiết bị thật (hardware)")
    print("  3. Cả hai đồng thời (simulator + real)")
    print("  0. Quay lại")
    c = input("Chọn: ").strip()
    if c == "1":
        cfg["mode"] = "simulator"
        cfg["simulator"]["enabled"] = True
        cfg["real_device"]["enabled"] = False
    elif c == "2":
        cfg["mode"] = "real"
        cfg["simulator"]["enabled"] = False
        cfg["real_device"]["enabled"] = True
    elif c == "3":
        cfg["mode"] = "both"
        cfg["simulator"]["enabled"] = True
        cfg["real_device"]["enabled"] = True
    else:
        return
    save_data_source(cfg)
    print(
        "\nGhi chú cho đồ án:\n"
        "  - Simulator & thiết bị thật cùng publish MQTT topic smartlock/{device_id}/...\n"
        "  - Backend subscriber nhận tất cả; phân biệt qua device_id trong DB.\n"
        "  - Khi mua ESP, chỉ cần đăng ký device_id mới + bật mode real/both."
    )


def show_data_source():
    cfg = load_data_source()
    print("\nCấu hình nguồn dữ liệu hiện tại:")
    print(json.dumps(cfg, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# 5. Xóa chỉ dữ liệu (giữ schema) — truncate
# ---------------------------------------------------------------------------
TRUNCATE_SQL = """
TRUNCATE TABLE
    device_commands,
    notifications,
    device_status_logs,
    access_logs,
    invites,
    pin_codes,
    access_permissions,
    access_cards,
    devices,
    device_types,
    users
RESTART IDENTITY CASCADE;
"""


def clear_data_only():
    print("\n⚠️  Xóa toàn bộ DỮ LIỆU (giữ nguyên bảng/schema).")
    if input("Gõ YES để xác nhận: ").strip() != "YES":
        print("Hủy.")
        return
    code, out = run_psql(TRUNCATE_SQL)
    if code != 0:
        print(out)
        print("❌ Lỗi truncate (có thể bảng chưa tồn tại).")
        return
    print("✅ Đã xóa hết dữ liệu.")
    if input("Tạo admin ngay? (y/N): ").strip().lower() == "y":
        asyncio.run(create_admin_async())


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
def main():
    while True:
        banner()
        print("  1. RESET DB (xóa bảng + tạo lại schema) + tạo Admin")
        print("  2. Chỉ tạo / cập nhật Admin (không đụng dữ liệu khác)")
        print("  3. Xóa hết dữ liệu (TRUNCATE, giữ schema) + tùy chọn tạo Admin")
        print("  4. Backup database (pg_dump)")
        print("  5. Restore database từ backup")
        print("  6. Cấu hình nguồn dữ liệu (Simulator / Real / Both)")
        print("  7. Xem cấu hình nguồn dữ liệu")
        print("  8. Liệt kê file backup")
        print("  0. Thoát")
        print("-" * 56)
        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            reset_database(create_admin_after=True)
            pause()
        elif choice == "2":
            create_admin_interactive()
            pause()
        elif choice == "3":
            clear_data_only()
            pause()
        elif choice == "4":
            backup_db()
            pause()
        elif choice == "5":
            restore_db()
            pause()
        elif choice == "6":
            configure_data_source()
            pause()
        elif choice == "7":
            show_data_source()
            pause()
        elif choice == "8":
            files = list_backups()
            if not files:
                print("Chưa có backup.")
            else:
                for f in files:
                    print(f"  {f.name}  ({f.stat().st_size:,} bytes)")
            pause()
        elif choice == "0":
            print("Bye.")
            break
        else:
            print("Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    main()

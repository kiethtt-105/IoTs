#!/usr/bin/env python3
"""
Smart Lock - Menu quản lý nhanh
Chạy từ thư mục backend (đã activate venv):
    python manage.py

Dùng psycopg2 (có trong venv) — KHÔNG cần lệnh psql trong PATH.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
# SQL cùng cấp: IoTs/Create_dtb/
SQL_DIR = ROOT.parent / "Create_dtb"
BACKUP_DIR = ROOT / "backups"
ENV_FILE = ROOT / ".env"
DATA_SOURCE_CONFIG = ROOT / "data_source.json"

DEFAULT_ADMIN = {
    "email": "admin@admin.vn",
    "password": "admin123",
    "full_name": "Admin",
}

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


def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_db_info() -> dict:
    env = load_env()
    sync = env.get(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/smart_lock",
    )
    if "pip install" in sync or (" " in sync.split("@")[0] if "@" in sync else False):
        sync = "postgresql://postgres:109002@localhost:5432/smart_lock"
    u = urlparse(sync)
    return {
        "user": u.username or "postgres",
        "password": u.password or "",
        "host": u.hostname or "localhost",
        "port": int(u.port or 5432),
        "dbname": (u.path or "/smart_lock").lstrip("/") or "smart_lock",
    }


def get_connection():
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("Thieu psycopg2. Chay: pip install psycopg2-binary")
        return None

    info = get_db_info()
    try:
        conn = psycopg2.connect(
            host=info["host"],
            port=info["port"],
            user=info["user"],
            password=info["password"],
            dbname=info["dbname"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"Khong ket noi duoc PostgreSQL: {e}")
        print(f"   Host={info['host']} Port={info['port']} DB={info['dbname']} User={info['user']}")
        print("   Kiem tra PostgreSQL dang chay + mat khau trong file .env")
        return None


def run_sql(sql: str) -> tuple[bool, str]:
    conn = get_connection()
    if conn is None:
        return False, "no connection"
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.close()
        return True, "ok"
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return False, str(e)


def run_sql_file(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"File khong ton tai: {path}"
    sql = path.read_text(encoding="utf-8")
    conn = get_connection()
    if conn is None:
        return False, "no connection"
    try:
        with conn.cursor() as cur:
            # PostgreSQL chap nhan nhieu cau lenh trong 1 execute
            cur.execute(sql)
        conn.close()
        return True, "ok"
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return False, str(e)


def pause():
    input("\nNhan Enter de quay lai menu...")


def banner():
    print("\n" + "=" * 56)
    print("   SMART LOCK — MENU QUAN LY (DB / Admin / Backup)")
    print("=" * 56)
    info = get_db_info()
    print(f"  DB: {info['user']}@{info['host']}:{info['port']}/{info['dbname']}")
    print("-" * 56)


def find_sql_files() -> tuple[Path | None, Path | None]:
    candidates = [
        ROOT.parent / "Create_dtb",
        ROOT.parent / "Create_dtb" / "Create_dtb",
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
    print("\nCANH BAO: Se XOA TOAN BO du lieu va bang trong database hien tai.")
    confirm = input("Go YES de xac nhan: ").strip()
    if confirm != "YES":
        print("Da huy.")
        return

    info = get_db_info()
    print(f"\n-> Dang lam viec tren DB: {info['dbname']}")

    print("-> Bat extension pgcrypto...")
    ok, msg = run_sql('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    if not ok:
        print(f"  Canh bao: {msg}")

    print("-> DROP tables...")
    ok, msg = run_sql(DROP_TABLES_SQL)
    if not ok:
        print(f"  Canh bao: {msg}")

    print("-> DROP ENUM types...")
    ok, msg = run_sql(DROP_TYPES_SQL)
    if not ok:
        print(f"  Canh bao: {msg}")

    t1, t2 = find_sql_files()
    if not t1:
        print("Khong tim thay 01_create_tables.sql")
        print("   Dat file trong: D:\\.GitHub\\IoTs\\Create_dtb\\")
        return

    print(f"-> Chay {t1} ...")
    ok, msg = run_sql_file(t1)
    if not ok:
        print(f"Loi tao tables:\n{msg}")
        return
    print("  OK tables.")

    if t2:
        print(f"-> Chay {t2} ...")
        ok, msg = run_sql_file(t2)
        if not ok:
            print(f"Canh bao constraints: {msg}")
        else:
            print("  OK constraints.")
    else:
        print("Khong tim thay 02_create_constraints.sql")

    print("\nSchema da tao lai (trong, khong du lieu mau).")

    if create_admin_after:
        print("-> Tao admin...")
        asyncio.run(create_admin_async())


async def create_admin_async(
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
):
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
            try:
                await db.execute(text("SELECT 1 FROM users LIMIT 1"))
            except Exception as e:
                print(f"Bang users chua ton tai. Chay menu 1 (RESET DB) truoc.\n   {e}")
                await engine.dispose()
                return

            result = await db.execute(select(User).where(User.email == email))
            existing = result.scalar_one_or_none()

            if existing:
                existing.password_hash = hash_password(password)
                existing.role = UserRole.owner
                existing.full_name = full_name
                existing.is_active = True
                print(f"Da cap nhat admin: {email}")
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
                print(f"Da tao admin: {email}")

            await db.commit()
            print("\nAdmin san sang:")
            print(f"   Email   : {email}")
            print(f"   Password: {password}")
            print(f"   Role    : owner")
    finally:
        await engine.dispose()


def create_admin_interactive():
    print("\n--- Tao / cap nhat Admin (KHONG seed du lieu mau) ---")
    email = input(f"Email [{DEFAULT_ADMIN['email']}]: ").strip() or DEFAULT_ADMIN["email"]
    password = input(f"Password [{DEFAULT_ADMIN['password']}]: ").strip() or DEFAULT_ADMIN["password"]
    name = input(f"Ho ten [{DEFAULT_ADMIN['full_name']}]: ").strip() or DEFAULT_ADMIN["full_name"]
    asyncio.run(create_admin_async(email, password, name))


def clear_data_only():
    print("\nXoa toan bo DU LIEU (giu nguyen bang/schema).")
    if input("Go YES de xac nhan: ").strip() != "YES":
        print("Huy.")
        return
    ok, msg = run_sql(TRUNCATE_SQL)
    if not ok:
        print(f"Loi: {msg}")
        return
    print("Da xoa het du lieu.")
    if input("Tao admin ngay? (y/N): ").strip().lower() == "y":
        asyncio.run(create_admin_async())


def backup_db():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = BACKUP_DIR / f"smart_lock_{ts}.sql"

    conn = get_connection()
    if conn is None:
        return

    try:
        import shutil
        import subprocess

        info = get_db_info()
        if shutil.which("pg_dump"):
            env = os.environ.copy()
            env["PGPASSWORD"] = info["password"]
            r = subprocess.run(
                [
                    "pg_dump",
                    "-h", info["host"],
                    "-p", str(info["port"]),
                    "-U", info["user"],
                    "-d", info["dbname"],
                    "--no-owner",
                    "--no-acl",
                    "-F", "p",
                    "-f", str(out_file),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if r.returncode == 0:
                print(f"Backup OK -> {out_file} ({out_file.stat().st_size:,} bytes)")
                conn.close()
                return
            print(f"pg_dump loi, chuyen sang backup Python: {r.stderr}")

        lines = ["-- Smart Lock backup (Python)", f"-- {ts}", ""]
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            )
            tables = [r[0] for r in cur.fetchall()]

        for table in tables:
            lines.append(f"-- TABLE {table}")
            with conn.cursor() as cur:
                cur.execute(f'SELECT * FROM "{table}"')
                cols = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchall()
            if not rows:
                lines.append(f"-- (empty) {table}")
                continue
            col_list = ", ".join(f'"{c}"' for c in cols)
            for row in rows:
                vals = []
                for v in row:
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, bool):
                        vals.append("TRUE" if v else "FALSE")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        s = str(v).replace("'", "''")
                        vals.append(f"'{s}'")
                lines.append(f'INSERT INTO "{table}" ({col_list}) VALUES ({", ".join(vals)});')
            lines.append("")

        out_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"Backup (Python) OK -> {out_file} ({out_file.stat().st_size:,} bytes)")
    except Exception as e:
        print(f"Backup loi: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_backups() -> list[Path]:
    if not BACKUP_DIR.exists():
        return []
    return sorted(
        BACKUP_DIR.glob("smart_lock_*.sql"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def restore_db():
    files = list_backups()
    if not files:
        print("Chua co file backup trong", BACKUP_DIR)
        return
    print("\nDanh sach backup:")
    for i, f in enumerate(files[:15], 1):
        print(f"  {i}. {f.name}  ({f.stat().st_size:,} bytes)")
    choice = input("Chon so (Enter huy): ").strip()
    if not choice.isdigit():
        print("Huy.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(files):
        print("So khong hop le.")
        return
    path = files[idx]
    print(f"\nRestore tu: {path.name}")
    if input("Go YES de xac nhan: ").strip() != "YES":
        print("Huy.")
        return

    print("-> RESET schema truoc...")
    run_sql(DROP_TABLES_SQL)
    run_sql(DROP_TYPES_SQL)
    run_sql('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    t1, t2 = find_sql_files()
    if t1:
        run_sql_file(t1)
    if t2:
        run_sql_file(t2)

    print("-> Import data...")
    ok, msg = run_sql_file(path)
    if not ok:
        print(f"Canh bao: {msg}")
    else:
        print("Restore xong.")


def load_data_source() -> dict:
    default = {
        "mode": "simulator",
        "simulator": {"enabled": True, "mqtt_topic_prefix": "smartlock"},
        "real_device": {
            "enabled": False,
            "mqtt_topic_prefix": "smartlock",
            "device_ids": [],
        },
        "description": "simulator | real | both",
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
    print(f"Da luu -> {DATA_SOURCE_CONFIG}")


def configure_data_source():
    cfg = load_data_source()
    print("\n--- Nguon du lieu thiet bi ---")
    print(f"  Hien tai: mode = {cfg.get('mode')}")
    print("  1. Chi Simulator")
    print("  2. Chi Thiet bi that")
    print("  3. Ca hai (Both)")
    print("  0. Quay lai")
    c = input("Chon: ").strip()
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


def show_data_source():
    print(json.dumps(load_data_source(), ensure_ascii=False, indent=2))


def main():
    while True:
        banner()
        print("  1. RESET DB (xoa bang + tao lai schema) + tao Admin")
        print("  2. Chi tao / cap nhat Admin")
        print("  3. Xoa het du lieu (TRUNCATE) + tuy chon tao Admin")
        print("  4. Backup database")
        print("  5. Restore database tu backup")
        print("  6. Cau hinh nguon du lieu (Simulator / Real / Both)")
        print("  7. Xem cau hinh nguon du lieu")
        print("  8. Liet ke file backup")
        print("  0. Thoat")
        print("-" * 56)
        choice = input("Chon chuc nang: ").strip()

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
                print("Chua co backup.")
            else:
                for f in files:
                    print(f"  {f.name}  ({f.stat().st_size:,} bytes)")
            pause()
        elif choice == "0":
            print("Bye.")
            break
        else:
            print("Lua chon khong hop le.")


if __name__ == "__main__":
    main()

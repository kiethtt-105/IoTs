"""
Seed dữ liệu mẫu vào PostgreSQL smart_lock
Chạy: python seed.py
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.services.auth import hash_password

settings = get_settings()

# Import models after path setup
from app.models.user import User, UserRole
from app.models.device import DeviceType, Device, DeviceStatus
from app.models.access import AccessCard, AccessLog, AccessMethod, AccessResult
from app.database import Base


OWNER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
MEMBER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
GUEST_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
TYPE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
DEVICE1_ID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")  # khớp sensor-simulator
DEVICE2_ID = uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")
DEVICE3_ID = uuid.UUID("c3d4e5f6-a7b8-9012-cdef-123456789012")
DEVICE4_ID = uuid.UUID("d4e5f6a7-b8c9-0123-def0-234567890123")


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # Users
        for u in [
            User(id=OWNER_ID, full_name="Nguyễn Văn A", email="owner@example.com",
                 phone="0901234567", password_hash=hash_password("admin123"), role=UserRole.owner),
            User(id=MEMBER_ID, full_name="Trần Thị B", email="member@example.com",
                 phone="0912345678", password_hash=hash_password("member123"), role=UserRole.member),
            User(id=GUEST_ID, full_name="Lê Văn C", email="guest@example.com",
                 phone="0923456789", password_hash=hash_password("guest123"), role=UserRole.guest),
        ]:
            exists = await db.execute(select(User).where(User.email == u.email))
            if not exists.scalar_one_or_none():
                db.add(u)

        # Device type
        exists = await db.execute(select(DeviceType).where(DeviceType.code == "smart_lock"))
        if not exists.scalar_one_or_none():
            db.add(DeviceType(
                id=TYPE_ID,
                code="smart_lock",
                name="Smart Lock",
                capabilities=["nfc_unlock", "ble_unlock", "pin_unlock"],
            ))

        await db.flush()

        # Devices
        devices = [
            Device(id=DEVICE1_ID, device_type_id=TYPE_ID, owner_id=OWNER_ID,
                   name="Khóa cửa chính", mac_address="AA:BB:CC:DD:EE:01",
                   firmware_version="1.2.0", status=DeviceStatus.locked,
                   battery_level=87, location="Cửa chính"),
            Device(id=DEVICE2_ID, device_type_id=TYPE_ID, owner_id=OWNER_ID,
                   name="Khóa cửa gara", mac_address="AA:BB:CC:DD:EE:02",
                   firmware_version="1.2.0", status=DeviceStatus.unlocked,
                   battery_level=62, location="Gara"),
            Device(id=DEVICE3_ID, device_type_id=TYPE_ID, owner_id=MEMBER_ID,
                   name="Khóa cửa phụ", mac_address="AA:BB:CC:DD:EE:03",
                   firmware_version="1.1.5", status=DeviceStatus.offline,
                   battery_level=12, location="Cửa phụ sau"),
            Device(id=DEVICE4_ID, device_type_id=TYPE_ID, owner_id=OWNER_ID,
                   name="Khóa văn phòng", mac_address="AA:BB:CC:DD:EE:04",
                   firmware_version="1.2.0", status=DeviceStatus.tamper,
                   battery_level=45, location="Tầng 2"),
        ]
        for d in devices:
            exists = await db.execute(select(Device).where(Device.mac_address == d.mac_address))
            if not exists.scalar_one_or_none():
                db.add(d)

        await db.flush()

        # Cards
        cards = [
            AccessCard(user_id=OWNER_ID, device_id=DEVICE1_ID,
                       card_uid="04A1B2C3D4E5F6", label="Thẻ của bố", is_active=True),
            AccessCard(user_id=MEMBER_ID, device_id=DEVICE1_ID,
                       card_uid="04F6E5D4C3B2A1", label="Thẻ của mẹ", is_active=True),
            AccessCard(user_id=GUEST_ID, device_id=DEVICE2_ID,
                       card_uid="04AABBCCDDEEFF", label="Thẻ khách", is_active=False),
        ]
        for c in cards:
            exists = await db.execute(select(AccessCard).where(AccessCard.card_uid == c.card_uid))
            if not exists.scalar_one_or_none():
                db.add(c)

        # Sample access logs
        logs = [
            AccessLog(device_id=DEVICE1_ID, user_id=OWNER_ID, method=AccessMethod.app_ble,
                      result=AccessResult.success, created_at=datetime.utcnow() - timedelta(minutes=10)),
            AccessLog(device_id=DEVICE1_ID, user_id=MEMBER_ID, method=AccessMethod.nfc_card,
                      result=AccessResult.success, created_at=datetime.utcnow() - timedelta(hours=1)),
            AccessLog(device_id=DEVICE2_ID, method=AccessMethod.pin,
                      result=AccessResult.failed, failure_reason="wrong_pin",
                      created_at=datetime.utcnow() - timedelta(hours=2)),
            AccessLog(device_id=DEVICE4_ID, method=AccessMethod.nfc_card,
                      result=AccessResult.denied, failure_reason="card_not_allowed",
                      created_at=datetime.utcnow() - timedelta(hours=3)),
        ]
        for log in logs:
            db.add(log)

        await db.commit()
        print("✅ Seed data OK")
        print("   Login: owner@example.com / admin123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

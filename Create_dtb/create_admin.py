"""
Tạo / cập nhật admin (KHÔNG seed dữ liệu mẫu).
Chạy: python create_admin.py

Hoặc dùng menu: python manage.py  → chọn 2
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.services.auth import hash_password
from app.models.user import User, UserRole

settings = get_settings()

NEW_EMAIL = "kieth@admin.vn"
NEW_PASSWORD = "109002"
NEW_NAME = "Kieth Admin"


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        result = await db.execute(select(User).where(User.email == NEW_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            existing.password_hash = hash_password(NEW_PASSWORD)
            existing.role = UserRole.owner
            existing.full_name = NEW_NAME
            existing.is_active = True
            print(f"Đã cập nhật: {NEW_EMAIL}")
        else:
            db.add(User(
                full_name=NEW_NAME,
                email=NEW_EMAIL,
                password_hash=hash_password(NEW_PASSWORD),
                role=UserRole.owner,
                is_active=True,
            ))
            print(f"Đã tạo mới: {NEW_EMAIL}")

        await db.commit()
        print("\n✅ Xong! (không seed dữ liệu mẫu)")
        print(f"   Email   : {NEW_EMAIL}")
        print(f"   Password: {NEW_PASSWORD}")
        print(f"   Role    : owner")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

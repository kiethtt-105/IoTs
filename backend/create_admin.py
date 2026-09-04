"""
Xóa admin cũ + tạo admin mới
Chạy: python create_admin.py
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

OLD_EMAILS = [
    "owner@example.com",
    "member@example.com",
    "guest@example.com",
]


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # 1. Xóa admin cũ
        for email in OLD_EMAILS:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                await db.delete(user)
                print(f"Đã xóa: {email}")

        # 2. Tạo / cập nhật admin mới
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
        print("\n✅ Xong!")
        print(f"   Email   : {NEW_EMAIL}")
        print(f"   Password: {NEW_PASSWORD}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.services.auth import get_current_user, hash_password

router = APIRouter()


@router.get("", response_model=list[UserOut])
async def list_users(
    search: str | None = None,
    role: UserRole | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(User).order_by(User.created_at.desc())
    if role:
        q = q.where(User.role == role)
    result = await db.execute(q)
    users = result.scalars().all()
    if search:
        s = search.lower()
        users = [u for u in users if s in u.full_name.lower() or s in u.email.lower()]
    return [UserOut.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    return UserOut.model_validate(u)


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exists = await db.execute(select(User).where(User.email == body.email))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")
    new_user = User(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return UserOut.model_validate(new_user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    await db.flush()
    return UserOut.model_validate(u)

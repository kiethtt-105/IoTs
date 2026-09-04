from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.access import AccessCard
from app.schemas.access import AccessCardOut
from app.services.auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[AccessCardOut])
async def list_cards(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AccessCard)
        .options(selectinload(AccessCard.user), selectinload(AccessCard.device))
        .order_by(AccessCard.issued_at.desc())
    )
    cards = result.scalars().all()
    out = []
    for c in cards:
        out.append(
            AccessCardOut(
                id=c.id,
                label=c.label,
                card_uid=c.card_uid,
                user_id=c.user_id,
                user_name=c.user.full_name if c.user else None,
                device_id=c.device_id,
                device_name=c.device.name if c.device else None,
                is_active=c.is_active,
                issued_at=c.issued_at,
            )
        )
    return out

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.access import AccessLog
from app.schemas.access import AccessLogOut
from app.services.auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[AccessLogOut])
async def list_logs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AccessLog)
        .options(selectinload(AccessLog.device), selectinload(AccessLog.user))
        .order_by(AccessLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        AccessLogOut(
            id=log.id,
            device_id=log.device_id,
            device_name=log.device.name if log.device else None,
            user_id=log.user_id,
            user_name=log.user.full_name if log.user else None,
            method=log.method,
            result=log.result,
            failure_reason=log.failure_reason,
            created_at=log.created_at,
        )
        for log in logs
    ]

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.device import Device, DeviceStatus
from app.models.access import AccessLog, AccessResult
from app.schemas.access import StatsOut
from app.services.auth import get_current_user

router = APIRouter()


@router.get("", response_model=StatsOut)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total_devices = (await db.execute(select(func.count(Device.id)))).scalar() or 0
    online_devices = (
        await db.execute(
            select(func.count(Device.id)).where(
                Device.status.in_([DeviceStatus.locked, DeviceStatus.unlocked])
            )
        )
    ).scalar() or 0
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_access = (
        await db.execute(
            select(func.count(AccessLog.id)).where(AccessLog.created_at >= today_start)
        )
    ).scalar() or 0
    failed_access_today = (
        await db.execute(
            select(func.count(AccessLog.id)).where(
                and_(
                    AccessLog.created_at >= today_start,
                    AccessLog.result.in_([AccessResult.failed, AccessResult.denied]),
                )
            )
        )
    ).scalar() or 0
    low_battery = (
        await db.execute(
            select(func.count(Device.id)).where(
                and_(Device.battery_level.isnot(None), Device.battery_level < 20)
            )
        )
    ).scalar() or 0
    tamper_alerts = (
        await db.execute(
            select(func.count(Device.id)).where(Device.status == DeviceStatus.tamper)
        )
    ).scalar() or 0

    return StatsOut(
        total_devices=total_devices,
        online_devices=online_devices,
        total_users=total_users,
        today_access=today_access,
        failed_access_today=failed_access_today,
        low_battery=low_battery,
        tamper_alerts=tamper_alerts,
    )

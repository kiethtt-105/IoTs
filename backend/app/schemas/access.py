from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.access import AccessMethod, AccessResult


class AccessCardOut(BaseModel):
    id: UUID
    label: str | None
    card_uid: str
    user_id: UUID
    user_name: str | None = None
    device_id: UUID | None
    device_name: str | None = None
    is_active: bool
    issued_at: datetime

    model_config = {"from_attributes": True}


class AccessLogOut(BaseModel):
    id: UUID
    device_id: UUID
    device_name: str | None = None
    user_id: UUID | None
    user_name: str | None = None
    method: AccessMethod
    result: AccessResult
    failure_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total_devices: int
    online_devices: int
    total_users: int
    today_access: int
    failed_access_today: int
    low_battery: int
    tamper_alerts: int

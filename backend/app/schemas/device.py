from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.device import DeviceStatus
from app.models.telemetry import CommandType


class DeviceOut(BaseModel):
    id: UUID
    name: str
    location: str | None
    status: DeviceStatus
    battery_level: int | None
    mac_address: str
    firmware_version: str | None
    owner_id: UUID
    owner_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    """Tạo thiết bị. id / device_type_id / owner_id đều optional để simulator tự đăng ký."""
    name: str
    location: str | None = None
    mac_address: str
    device_type_id: UUID | None = None
    owner_id: UUID | None = None
    firmware_version: str | None = "1.0.0"
    id: UUID | None = None  # cho phép simulator giữ ID cố định (MQTT topic)


class DeviceUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    status: DeviceStatus | None = None
    battery_level: int | None = None
    firmware_version: str | None = None


class DeviceCommandRequest(BaseModel):
    command: CommandType
    version: str | None = None  # for ota_update

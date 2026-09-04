from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.device import Device, DeviceStatus
from app.models.telemetry import DeviceCommand, CommandType, CommandStatus
from app.schemas.device import DeviceOut, DeviceCreate, DeviceUpdate, DeviceCommandRequest
from app.services.auth import get_current_user
from app.mqtt.publisher import publish_command

router = APIRouter()


def to_device_out(d: Device) -> DeviceOut:
    return DeviceOut(
        id=d.id,
        name=d.name,
        location=d.location,
        status=d.status,
        battery_level=d.battery_level,
        mac_address=d.mac_address,
        firmware_version=d.firmware_version,
        owner_id=d.owner_id,
        owner_name=d.owner.full_name if d.owner else None,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    status: DeviceStatus | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Device).options(selectinload(Device.owner)).order_by(Device.created_at.desc())
    if status:
        q = q.where(Device.status == status)
    result = await db.execute(q)
    devices = result.scalars().all()
    if search:
        s = search.lower()
        devices = [
            d for d in devices
            if s in d.name.lower()
            or (d.location and s in d.location.lower())
            or s in d.mac_address.lower()
        ]
    return [to_device_out(d) for d in devices]


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).options(selectinload(Device.owner)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    return to_device_out(device)


@router.post("", response_model=DeviceOut, status_code=201)
async def create_device(
    body: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Tạo / đăng ký thiết bị. Simulator có thể gửi sẵn id + mac để giữ topic MQTT."""
    from app.models.device import DeviceType

    # MAC trùng → trả về device đã có (idempotent đăng ký)
    exists = await db.execute(select(Device).options(selectinload(Device.owner)).where(Device.mac_address == body.mac_address))
    existing = exists.scalar_one_or_none()
    if existing:
        return to_device_out(existing)

    # Nếu client gửi id sẵn có → kiểm tra
    if body.id:
        by_id = await db.execute(select(Device).where(Device.id == body.id))
        if by_id.scalar_one_or_none():
            raise HTTPException(400, f"Device id {body.id} already exists")

    # device_type: dùng id gửi lên hoặc lấy/tạo mặc định smart_lock_nfc
    type_id = body.device_type_id
    if not type_id:
        r = await db.execute(select(DeviceType).where(DeviceType.code == "smart_lock_nfc"))
        dt = r.scalar_one_or_none()
        if not dt:
            dt = DeviceType(
                code="smart_lock_nfc",
                name="Khóa thông minh NFC",
                capabilities={"nfc": True, "ble": True, "pin": True, "wifi": True},
            )
            db.add(dt)
            await db.flush()
        type_id = dt.id

    owner_id = body.owner_id or user.id

    kwargs = dict(
        name=body.name,
        location=body.location,
        mac_address=body.mac_address,
        device_type_id=type_id,
        owner_id=owner_id,
        firmware_version=body.firmware_version or "1.0.0",
        status=DeviceStatus.offline,
    )
    if body.id:
        kwargs["id"] = body.id

    device = Device(**kwargs)
    db.add(device)
    await db.flush()
    await db.refresh(device, attribute_names=["owner"])
    result = await db.execute(
        select(Device).options(selectinload(Device.owner)).where(Device.id == device.id)
    )
    device = result.scalar_one()
    return to_device_out(device)


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(
    device_id: UUID,
    body: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Device).options(selectinload(Device.owner)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(device, k, v)
    await db.flush()
    return to_device_out(device)


@router.post("/{device_id}/command")
async def send_command(
    device_id: UUID,
    body: DeviceCommandRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    cmd = DeviceCommand(
        id=uuid4(),
        device_id=device_id,
        command=body.command,
        status=CommandStatus.pending,
        issued_by=user.id,
    )
    db.add(cmd)
    await db.flush()

    payload = {
        "command_id": str(cmd.id),
        "command": body.command.value,
    }
    if body.version:
        payload["version"] = body.version

    ok = publish_command(str(device_id), payload)
    if ok:
        cmd.status = CommandStatus.sent
    else:
        cmd.status = CommandStatus.failed

    return {"command_id": str(cmd.id), "status": cmd.status.value, "mqtt_sent": ok}

from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.access import AccessCard, CardDeviceAccess, PermissionStatus
from app.models.device import Device
from app.models.telemetry import DeviceCommand, CommandType, CommandStatus
from app.schemas.access import AccessCardOut, CardDeviceAccessOut
from app.services.auth import get_current_user
from app.mqtt.publisher import publish_command
from app.mqtt.subscriber import get_enroll_result

router = APIRouter()


class EnrollStartRequest(BaseModel):
    device_id: UUID
    timeout_sec: int = 30


class EnrollStartResponse(BaseModel):
    command_id: UUID
    device_id: UUID
    message: str


class CardCreateRequest(BaseModel):
    """Lưu thẻ vào DB (registry global) sau khi quét máy tổng."""
    card_uid: str
    label: str | None = None
    user_id: UUID
    # Optional: gán ngay vào 1 khóa + thời hạn
    device_id: UUID | None = None
    expires_at: datetime | None = None


class AssignCardRequest(BaseModel):
    """Gán thẻ đã có trong DB vào 1 khóa (có thể nhiều khóa)."""
    device_id: UUID
    expires_at: datetime | None = Field(
        default=None, description="NULL = không hết hạn; set khi thêm vào khóa"
    )


def _card_out(c: AccessCard) -> AccessCardOut:
    devices = []
    for a in (c.device_accesses or []):
        devices.append(
            CardDeviceAccessOut(
                id=a.id,
                device_id=a.device_id,
                device_name=a.device.name if a.device else None,
                expires_at=a.expires_at,
                status=a.status,
                created_at=a.created_at,
            )
        )
    return AccessCardOut(
        id=c.id,
        label=c.label,
        card_uid=c.card_uid,
        user_id=c.user_id,
        user_name=c.user.full_name if c.user else None,
        is_active=c.is_active,
        issued_at=c.issued_at,
        devices=devices,
    )


@router.get("", response_model=list[AccessCardOut])
async def list_cards(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AccessCard)
        .options(
            selectinload(AccessCard.user),
            selectinload(AccessCard.device_accesses).selectinload(CardDeviceAccess.device),
        )
        .order_by(AccessCard.issued_at.desc())
    )
    cards = result.scalars().all()
    return [_card_out(c) for c in cards]


@router.post("/enroll", response_model=EnrollStartResponse)
async def start_enroll(
    body: EnrollStartRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Gửi lệnh enroll_card xuống thiết bị / máy quét tổng."""
    result = await db.execute(select(Device).where(Device.id == body.device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    cmd_id = uuid4()
    cmd = DeviceCommand(
        id=cmd_id,
        device_id=body.device_id,
        command=CommandType.enroll_card,
        status=CommandStatus.pending,
        issued_by=user.id,
    )
    db.add(cmd)
    await db.commit()

    payload = {
        "command": "enroll_card",
        "command_id": str(cmd_id),
        "timeout_sec": body.timeout_sec,
    }
    ok = publish_command(str(body.device_id), payload)
    if ok:
        cmd.status = CommandStatus.sent
        await db.commit()
        msg = "Đã gửi lệnh quét thẻ tới đầu đọc. Hãy đưa thẻ vào đầu đọc."
    else:
        msg = "MQTT không khả dụng — lệnh đã lưu nhưng chưa gửi tới thiết bị."

    return EnrollStartResponse(command_id=cmd_id, device_id=body.device_id, message=msg)


@router.post("", response_model=AccessCardOut, status_code=201)
async def create_card(
    body: CardCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Lưu thẻ NFC vào DB sau khi quét.
    - Bắt buộc: card_uid + user_id
    - Tuỳ chọn: device_id + expires_at → cấp quyền ngay cho khóa đó
    """
    exists = await db.execute(
        select(AccessCard).where(AccessCard.card_uid == body.card_uid.upper())
    )
    if exists.scalar_one_or_none():
        raise HTTPException(400, f"Thẻ {body.card_uid} đã tồn tại trong DB")

    card = AccessCard(
        card_uid=body.card_uid.upper(),
        label=body.label or f"Thẻ {body.card_uid[-6:]}",
        user_id=body.user_id,
        is_active=True,
    )
    db.add(card)
    await db.flush()

    if body.device_id:
        dev = await db.execute(select(Device).where(Device.id == body.device_id))
        if not dev.scalar_one_or_none():
            raise HTTPException(404, "Device not found")
        access = CardDeviceAccess(
            access_card_id=card.id,
            device_id=body.device_id,
            granted_by=user.id,
            expires_at=body.expires_at,
            status=PermissionStatus.active,
        )
        db.add(access)

    await db.commit()

    result = await db.execute(
        select(AccessCard)
        .options(
            selectinload(AccessCard.user),
            selectinload(AccessCard.device_accesses).selectinload(CardDeviceAccess.device),
        )
        .where(AccessCard.id == card.id)
    )
    return _card_out(result.scalar_one())


@router.post("/{card_id}/assign", response_model=CardDeviceAccessOut, status_code=201)
async def assign_card_to_device(
    card_id: UUID,
    body: AssignCardRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Thẻ đã có trong DB → gán thêm để mở khóa khác.
    Thiết lập expires_at khi thêm vào khóa.
    """
    result = await db.execute(select(AccessCard).where(AccessCard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(404, "Card not found")
    if not card.is_active:
        raise HTTPException(400, "Thẻ đã bị vô hiệu")

    dev = await db.execute(select(Device).where(Device.id == body.device_id))
    device = dev.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    existing = await db.execute(
        select(CardDeviceAccess).where(
            CardDeviceAccess.access_card_id == card_id,
            CardDeviceAccess.device_id == body.device_id,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        # Cập nhật lại thời hạn / kích hoạt lại
        row.expires_at = body.expires_at
        row.status = PermissionStatus.active
        row.granted_by = user.id
        await db.commit()
        await db.refresh(row)
        return CardDeviceAccessOut(
            id=row.id,
            device_id=row.device_id,
            device_name=device.name,
            expires_at=row.expires_at,
            status=row.status,
            created_at=row.created_at,
        )

    access = CardDeviceAccess(
        access_card_id=card_id,
        device_id=body.device_id,
        granted_by=user.id,
        expires_at=body.expires_at,
        status=PermissionStatus.active,
    )
    db.add(access)
    await db.commit()
    await db.refresh(access)
    return CardDeviceAccessOut(
        id=access.id,
        device_id=access.device_id,
        device_name=device.name,
        expires_at=access.expires_at,
        status=access.status,
        created_at=access.created_at,
    )


@router.delete("/{card_id}/assign/{device_id}", status_code=204)
async def revoke_card_from_device(
    card_id: UUID,
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CardDeviceAccess).where(
            CardDeviceAccess.access_card_id == card_id,
            CardDeviceAccess.device_id == device_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Assignment not found")
    row.status = PermissionStatus.revoked
    await db.commit()
    return None


@router.delete("/{card_id}", status_code=204)
async def delete_card(
    card_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(AccessCard).where(AccessCard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(404, "Card not found")
    await db.delete(card)
    await db.commit()
    return None


@router.get("/enroll/{command_id}")
async def poll_enroll(
    command_id: UUID,
    user: User = Depends(get_current_user),
):
    """Poll kết quả quét thẻ (frontend gọi định kỳ sau khi start enroll)."""
    result = get_enroll_result(str(command_id))
    if not result:
        return {"status": "waiting", "card_uid": None}
    return {"status": "scanned", **result}

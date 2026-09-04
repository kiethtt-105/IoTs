from uuid import UUID, uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.access import AccessCard
from app.models.device import Device
from app.models.telemetry import DeviceCommand, CommandType, CommandStatus
from app.schemas.access import AccessCardOut
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
    card_uid: str
    label: str | None = None
    user_id: UUID
    device_id: UUID | None = None


class ScannedCardOut(BaseModel):
    card_uid: str
    device_id: UUID
    scanned_at: datetime


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


@router.post("/enroll", response_model=EnrollStartResponse)
async def start_enroll(
    body: EnrollStartRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Gửi lệnh enroll_card xuống thiết bị — đầu đọc chờ quét thẻ NFC."""
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
    """Lưu thẻ NFC sau khi đã quét được UID."""
    exists = await db.execute(
        select(AccessCard).where(AccessCard.card_uid == body.card_uid)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(400, f"Thẻ {body.card_uid} đã tồn tại")

    card = AccessCard(
        card_uid=body.card_uid.upper(),
        label=body.label or f"Thẻ {body.card_uid[-6:]}",
        user_id=body.user_id,
        device_id=body.device_id,
        is_active=True,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)

    # reload relations
    result = await db.execute(
        select(AccessCard)
        .options(selectinload(AccessCard.user), selectinload(AccessCard.device))
        .where(AccessCard.id == card.id)
    )
    c = result.scalar_one()
    return AccessCardOut(
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

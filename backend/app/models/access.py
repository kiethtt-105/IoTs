import uuid
from datetime import datetime, time
from sqlalchemy import String, Boolean, Integer, DateTime, Time, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ScheduleType(str, enum.Enum):
    always = "always"
    time_range = "time_range"
    recurring = "recurring"


class PermissionStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class PinType(str, enum.Enum):
    permanent = "permanent"
    one_time = "one_time"
    duress = "duress"


class InviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
    revoked = "revoked"


class AccessMethod(str, enum.Enum):
    app_ble = "app_ble"
    app_remote = "app_remote"
    nfc_card = "nfc_card"
    pin = "pin"
    auto = "auto"


class AccessResult(str, enum.Enum):
    success = "success"
    failed = "failed"
    denied = "denied"


class AccessCard(Base):
    __tablename__ = "access_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"))
    card_uid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)

    user = relationship("User", back_populates="access_cards")
    device = relationship("Device", back_populates="access_cards")


class AccessPermission(Base):
    __tablename__ = "access_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    schedule_type: Mapped[ScheduleType] = mapped_column(
        SAEnum(ScheduleType, name="schedule_type", create_type=False),
        default=ScheduleType.always,
    )
    valid_from: Mapped[datetime | None] = mapped_column(DateTime)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime)
    recurring_days: Mapped[dict | None] = mapped_column(JSONB)
    recurring_start_time: Mapped[time | None] = mapped_column(Time)
    recurring_end_time: Mapped[time | None] = mapped_column(Time)
    status: Mapped[PermissionStatus] = mapped_column(
        SAEnum(PermissionStatus, name="permission_status", create_type=False),
        default=PermissionStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PinCode(Base):
    __tablename__ = "pin_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[PinType] = mapped_column(
        SAEnum(PinType, name="pin_type", create_type=False),
        default=PinType.permanent,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[InviteStatus] = mapped_column(
        SAEnum(InviteStatus, name="invite_status", create_type=False),
        default=InviteStatus.pending,
    )


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    access_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("access_cards.id"))
    pin_code_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pin_codes.id"))
    method: Mapped[AccessMethod] = mapped_column(
        SAEnum(AccessMethod, name="access_method", create_type=False),
        nullable=False,
    )
    result: Mapped[AccessResult] = mapped_column(
        SAEnum(AccessResult, name="access_result", create_type=False),
        nullable=False,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    device = relationship("Device", back_populates="access_logs")
    user = relationship("User")

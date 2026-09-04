import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class DoorStatus(str, enum.Enum):
    closed = "closed"
    open = "open"


class NotificationType(str, enum.Enum):
    unlock_success = "unlock_success"
    unlock_failed = "unlock_failed"
    tamper = "tamper"
    low_battery = "low_battery"
    offline = "offline"


class CommandType(str, enum.Enum):
    lock = "lock"
    unlock = "unlock"
    reboot = "reboot"
    ota_update = "ota_update"
    enroll_card = "enroll_card"


class CommandStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    acked = "acked"
    failed = "failed"


class DeviceStatusLog(Base):
    __tablename__ = "device_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    battery_level: Mapped[int | None] = mapped_column(Integer)
    rssi: Mapped[int | None] = mapped_column(Integer)
    door_status: Mapped[DoorStatus | None] = mapped_column(
        SAEnum(DoorStatus, name="door_status", create_type=False)
    )
    tamper_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"))
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type", create_type=False),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    command: Mapped[CommandType] = mapped_column(
        SAEnum(CommandType, name="command_type", create_type=False),
        nullable=False,
    )
    status: Mapped[CommandStatus] = mapped_column(
        SAEnum(CommandStatus, name="command_status", create_type=False),
        default=CommandStatus.pending,
    )
    issued_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acked_at: Mapped[datetime | None] = mapped_column(DateTime)

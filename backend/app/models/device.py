import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class DeviceStatus(str, enum.Enum):
    locked = "locked"
    unlocked = "unlocked"
    offline = "offline"
    tamper = "tamper"


class DeviceType(Base):
    __tablename__ = "device_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capabilities: Mapped[dict | None] = mapped_column(JSONB)
    sensor_schema: Mapped[dict | None] = mapped_column(JSONB)

    devices = relationship("Device", back_populates="device_type")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("device_types.id"), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mac_address: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    firmware_version: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[DeviceStatus] = mapped_column(
        SAEnum(DeviceStatus, name="device_status", create_type=False),
        nullable=False,
        default=DeviceStatus.offline,
    )
    battery_level: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(100))
    paired_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    device_type = relationship("DeviceType", back_populates="devices")
    owner = relationship("User", back_populates="devices", foreign_keys=[owner_id])
    access_cards = relationship("AccessCard", back_populates="device")
    access_logs = relationship("AccessLog", back_populates="device")

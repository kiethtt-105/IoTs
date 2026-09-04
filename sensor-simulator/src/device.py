"""Device model - Quản lý trạng thái khóa thông minh giả lập"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import random
import uuid


class DeviceStatus(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    OFFLINE = "offline"
    TAMPER = "tamper"


class DoorStatus(str, Enum):
    CLOSED = "closed"
    OPEN = "open"


class AccessMethod(str, Enum):
    APP_BLE = "app_ble"
    APP_REMOTE = "app_remote"
    NFC_CARD = "nfc_card"
    PIN = "pin"
    AUTO = "auto"


class AccessResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"


@dataclass
class AccessEvent:
    method: AccessMethod
    result: AccessResult
    card_uid: Optional[str] = None
    pin: Optional[str] = None
    user_id: Optional[str] = None
    failure_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SmartLockDevice:
    device_id: str
    name: str
    mac_address: str
    firmware_version: str
    location: str

    status: DeviceStatus = DeviceStatus.LOCKED
    battery_level: int = 100
    door_status: DoorStatus = DoorStatus.CLOSED
    tamper_detected: bool = False
    rssi: int = -55

    allowed_cards: set = field(default_factory=set)
    allowed_pins: set = field(default_factory=set)

    def __post_init__(self):
        if not self.device_id:
            self.device_id = str(uuid.uuid4())

    def lock(self, method: AccessMethod = AccessMethod.AUTO) -> AccessEvent:
        if self.status == DeviceStatus.TAMPER:
            return AccessEvent(method=method, result=AccessResult.DENIED, failure_reason="device_in_tamper_mode")
        self.status = DeviceStatus.LOCKED
        self.door_status = DoorStatus.CLOSED
        return AccessEvent(method=method, result=AccessResult.SUCCESS)

    def unlock(self, method: AccessMethod, card_uid: str = None, pin: str = None) -> AccessEvent:
        if self.status == DeviceStatus.TAMPER:
            return AccessEvent(method=method, result=AccessResult.DENIED, failure_reason="device_in_tamper_mode", card_uid=card_uid, pin=pin)

        if method == AccessMethod.NFC_CARD:
            if not card_uid or card_uid not in self.allowed_cards:
                return AccessEvent(method=method, result=AccessResult.DENIED, failure_reason="card_not_allowed", card_uid=card_uid)

        if method == AccessMethod.PIN:
            if not pin or pin not in self.allowed_pins:
                return AccessEvent(method=method, result=AccessResult.FAILED, failure_reason="wrong_pin", pin=pin)

        self.status = DeviceStatus.UNLOCKED
        self.door_status = DoorStatus.OPEN
        return AccessEvent(method=method, result=AccessResult.SUCCESS, card_uid=card_uid, pin=pin)

    def get_telemetry(self) -> dict:
        self.rssi = random.randint(-70, -40)
        return {
            "device_id": self.device_id,
            "status": self.status.value,
            "battery_level": self.battery_level,
            "rssi": self.rssi,
            "door_status": self.door_status.value,
            "tamper_detected": self.tamper_detected,
            "firmware_version": self.firmware_version,
            "recorded_at": datetime.utcnow().isoformat() + "Z"
        }

    def drain_battery(self, amount: int = 1):
        self.battery_level = max(0, self.battery_level - amount)
        if self.battery_level == 0:
            self.status = DeviceStatus.OFFLINE

    def trigger_tamper(self):
        self.tamper_detected = True
        self.status = DeviceStatus.TAMPER

    def clear_tamper(self):
        self.tamper_detected = False
        if self.status == DeviceStatus.TAMPER:
            self.status = DeviceStatus.LOCKED

    def reboot(self):
        self.status = DeviceStatus.LOCKED
        self.door_status = DoorStatus.CLOSED
        self.tamper_detected = False

    def add_card(self, card_uid: str):
        self.allowed_cards.add(card_uid)

    def remove_card(self, card_uid: str):
        self.allowed_cards.discard(card_uid)

    def add_pin(self, pin: str):
        self.allowed_pins.add(pin)

    def remove_pin(self, pin: str):
        self.allowed_pins.discard(pin)

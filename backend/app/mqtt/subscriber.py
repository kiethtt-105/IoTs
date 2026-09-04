"""MQTT subscriber - nhận telemetry / access / ack / enroll từ thiết bị"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from app.config import get_settings
from app.database import AsyncSessionLocal as async_session
from app.models.device import Device, DeviceStatus
from app.models.access import AccessLog, AccessMethod, AccessResult
from app.models.telemetry import DeviceStatusLog, DeviceCommand, CommandStatus, DoorStatus

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory store: command_id -> {card_uid, device_id, scanned_at}
_enroll_results: dict[str, dict] = {}


def get_enroll_result(command_id: str) -> dict | None:
    return _enroll_results.get(command_id)


def start_mqtt_subscriber(loop: asyncio.AbstractEventLoop):
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("paho-mqtt not installed, MQTT subscriber disabled")
        return

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            client.subscribe("smartlock/+/status", qos=1)
            client.subscribe("smartlock/+/access", qos=1)
            client.subscribe("smartlock/+/ack", qos=1)
            client.subscribe("smartlock/+/enroll", qos=1)
            logger.info("MQTT subscriber connected & subscribed")
        else:
            logger.error(f"MQTT subscriber connect failed: {reason_code}")

    def on_message(client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            parts = topic.split("/")
            if len(parts) < 3:
                return
            device_id = parts[1]
            kind = parts[2]  # status | access | ack | enroll
            asyncio.run_coroutine_threadsafe(
                handle_mqtt_message(device_id, kind, payload), loop
            )
        except Exception as e:
            logger.exception(f"on_message error: {e}")

    client = mqtt.Client(
        client_id="smartlock_backend_sub",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    if settings.MQTT_USERNAME:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        client.loop_start()
        logger.info("MQTT subscriber started")
    except Exception as e:
        logger.warning(f"MQTT subscriber connect failed: {e}")


async def handle_mqtt_message(device_id: str, kind: str, payload: dict):
    try:
        device_uuid = UUID(device_id)
    except ValueError:
        logger.warning(f"Invalid device_id: {device_id}")
        return

    # Enroll result — no DB needed, store in memory
    if kind == "enroll":
        cmd_id = payload.get("command_id") or "unknown"
        card_uid = payload.get("card_uid")
        if card_uid:
            _enroll_results[cmd_id] = {
                "card_uid": card_uid,
                "device_id": device_id,
                "scanned_at": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "event": payload.get("event", "card_scanned"),
            }
            logger.info(f"Enroll card scanned: {card_uid} (cmd={cmd_id})")
        return

    async with async_session() as db:
        try:
            if kind == "status":
                result = await db.execute(select(Device).where(Device.id == device_uuid))
                device = result.scalar_one_or_none()
                if device:
                    status_val = payload.get("status")
                    if status_val:
                        try:
                            device.status = DeviceStatus(status_val)
                        except ValueError:
                            pass
                    if "battery_level" in payload:
                        device.battery_level = payload["battery_level"]
                    if "firmware_version" in payload:
                        device.firmware_version = payload["firmware_version"]
                    device.updated_at = datetime.now(timezone.utc)

                    log = DeviceStatusLog(
                        device_id=device_uuid,
                        battery_level=payload.get("battery_level"),
                        rssi=payload.get("rssi"),
                        door_status=DoorStatus(payload["door_status"]) if payload.get("door_status") in ("closed", "open") else None,
                        tamper_detected=payload.get("tamper_detected", False),
                    )
                    db.add(log)
                    await db.commit()
                    logger.debug(f"Status updated for {device_id}")

            elif kind == "access":
                method = payload.get("method", "auto")
                result_val = payload.get("result", "success")
                try:
                    method_enum = AccessMethod(method)
                except ValueError:
                    method_enum = AccessMethod.auto
                try:
                    result_enum = AccessResult(result_val)
                except ValueError:
                    result_enum = AccessResult.failed

                log = AccessLog(
                    device_id=device_uuid,
                    method=method_enum,
                    result=result_enum,
                    failure_reason=payload.get("failure_reason"),
                )
                db.add(log)
                await db.commit()
                logger.info(f"Access log saved for {device_id}: {method}/{result_val}")

            elif kind == "ack":
                command_id = payload.get("command_id")
                status = payload.get("status")
                message = payload.get("message", "")
                # Also capture card from ack message "card_scanned:UID"
                if status == "acked" and message.startswith("card_scanned:"):
                    uid = message.split(":", 1)[1]
                    _enroll_results[command_id or "unknown"] = {
                        "card_uid": uid,
                        "device_id": device_id,
                        "scanned_at": datetime.now(timezone.utc).isoformat(),
                        "event": "card_scanned",
                    }
                    logger.info(f"Enroll via ACK: {uid}")
                if command_id:
                    try:
                        cmd_uuid = UUID(command_id)
                        result = await db.execute(
                            select(DeviceCommand).where(DeviceCommand.id == cmd_uuid)
                        )
                        cmd = result.scalar_one_or_none()
                        if cmd:
                            if status == "acked":
                                cmd.status = CommandStatus.acked
                                cmd.acked_at = datetime.now(timezone.utc)
                            else:
                                cmd.status = CommandStatus.failed
                            await db.commit()
                    except ValueError:
                        pass

        except Exception as e:
            await db.rollback()
            logger.exception(f"handle_mqtt_message error: {e}")

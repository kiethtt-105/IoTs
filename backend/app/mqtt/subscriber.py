"""MQTT subscriber - nhận telemetry & access events từ sensor"""

import json
import logging
import asyncio
from uuid import UUID
from datetime import datetime
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def start_mqtt_subscriber(loop: asyncio.AbstractEventLoop):
    """Chạy MQTT subscriber trong background thread.

    Nguồn dữ liệu (simulator / real / both) cấu hình qua data_source.json
    (menu manage.py mục 6). Cùng topic prefix smartlock/{device_id}/...
    Backend phân biệt thiết bị theo device_id đã đăng ký trong bảng devices.
    """
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.warning("paho-mqtt not installed")
        return

    try:
        from app.data_source import current_mode, describe
        logger.info("Data source mode: %s — %s", current_mode(), describe())
    except Exception:
        pass

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            # Cùng prefix cho simulator và thiết bị thật — phân biệt bằng device_id
            client.subscribe("smartlock/+/status", qos=1)
            client.subscribe("smartlock/+/access", qos=1)
            client.subscribe("smartlock/+/ack", qos=1)
            logger.info("MQTT subscriber connected & subscribed (simulator + real ready)")
        else:
            logger.error(f"MQTT subscribe connect failed: {reason_code}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            parts = topic.split("/")
            if len(parts) < 3:
                return
            device_id = parts[1]
            kind = parts[2]  # status | access | ack

            # Schedule async handler on main loop
            asyncio.run_coroutine_threadsafe(
                handle_mqtt_message(device_id, kind, payload),
                loop,
            )
        except Exception as e:
            logger.error(f"MQTT message error: {e}")

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
        logger.warning(f"MQTT subscriber failed to start: {e}")


async def handle_mqtt_message(device_id: str, kind: str, payload: dict):
    from app.database import AsyncSessionLocal
    from app.models.device import Device, DeviceStatus
    from app.models.access import AccessLog, AccessMethod, AccessResult
    from app.models.telemetry import DeviceStatusLog, DoorStatus, DeviceCommand, CommandStatus
    from sqlalchemy import select

    try:
        device_uuid = UUID(device_id)
    except ValueError:
        logger.warning(f"Invalid device_id: {device_id}")
        return

    async with AsyncSessionLocal() as db:
        try:
            if kind == "status":
                # Update device cache + insert status log
                result = await db.execute(select(Device).where(Device.id == device_uuid))
                device = result.scalar_one_or_none()
                if device:
                    if "status" in payload:
                        try:
                            device.status = DeviceStatus(payload["status"])
                        except ValueError:
                            pass
                    if "battery_level" in payload:
                        device.battery_level = payload["battery_level"]
                    if "firmware_version" in payload:
                        device.firmware_version = payload["firmware_version"]

                log = DeviceStatusLog(
                    device_id=device_uuid,
                    battery_level=payload.get("battery_level"),
                    rssi=payload.get("rssi"),
                    door_status=DoorStatus(payload["door_status"]) if payload.get("door_status") else None,
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

                # Update device status on success unlock/lock
                result = await db.execute(select(Device).where(Device.id == device_uuid))
                device = result.scalar_one_or_none()
                if device and result_enum == AccessResult.success:
                    if method_enum != AccessMethod.auto or True:
                        if result_val == "success":
                            # infer from method context - simpler: if unlock methods
                            pass

                await db.commit()
                logger.info(f"Access log saved for {device_id}: {method}/{result_val}")

            elif kind == "ack":
                command_id = payload.get("command_id")
                status = payload.get("status")
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
                                cmd.acked_at = datetime.utcnow()
                            else:
                                cmd.status = CommandStatus.failed
                            await db.commit()
                    except ValueError:
                        pass

        except Exception as e:
            await db.rollback()
            logger.exception(f"handle_mqtt_message error: {e}")

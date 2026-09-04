"""MQTT publisher - gửi lệnh xuống thiết bị"""

import json
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client = None


def get_mqtt_client():
    global _client
    if _client is not None:
        return _client
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client(
            client_id="smartlock_backend",
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        if settings.MQTT_USERNAME:
            client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        client.loop_start()
        _client = client
        logger.info("MQTT publisher connected")
        return _client
    except Exception as e:
        logger.warning(f"MQTT connect failed: {e}")
        return None


def publish_command(device_id: str, payload: dict) -> bool:
    client = get_mqtt_client()
    if client is None:
        logger.warning("MQTT not available, command not sent")
        return False
    topic = f"smartlock/{device_id}/command"
    try:
        client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Published command to {topic}: {payload}")
        return True
    except Exception as e:
        logger.error(f"Publish failed: {e}")
        return False

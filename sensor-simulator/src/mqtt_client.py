"""MQTT Client - Giao tiếp với Backend"""

import json
import logging
from typing import Callable, Optional
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, host: str, port: int, client_id: str, device_id: str,
                 username: str = "", password: str = "", on_command: Optional[Callable] = None):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.device_id = device_id
        self.on_command = on_command

        self.client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        if username:
            self.client.username_pw_set(username, password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.topic_command = f"smartlock/{device_id}/command"
        self.topic_status = f"smartlock/{device_id}/status"
        self.topic_access = f"smartlock/{device_id}/access"
        self.topic_ack = f"smartlock/{device_id}/ack"

    def connect(self):
        logger.info(f"Connecting to MQTT broker {self.host}:{self.port} ...")
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT disconnected")

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("MQTT connected successfully")
            client.subscribe(self.topic_command, qos=1)
            logger.info(f"Subscribed: {self.topic_command}")
        else:
            logger.error(f"MQTT connect failed: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        logger.warning(f"MQTT disconnected: {reason_code}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received command: {payload}")
            if self.on_command:
                self.on_command(payload)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def publish_status(self, telemetry: dict):
        self.client.publish(self.topic_status, json.dumps(telemetry), qos=1)

    def publish_access(self, event: dict):
        self.client.publish(self.topic_access, json.dumps(event), qos=1)
        logger.info(f"Published access event → {self.topic_access}")

    def publish_ack(self, command_id: str, status: str, message: str = ""):
        payload = {"command_id": command_id, "status": status, "message": message, "device_id": self.device_id}
        self.client.publish(self.topic_ack, json.dumps(payload), qos=1)
        logger.info(f"Published ACK → {status}")

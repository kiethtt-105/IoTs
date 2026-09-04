"""
Cấu hình nguồn dữ liệu thiết bị: simulator / real / both.

Admin (manage.py) ghi file data_source.json.
MQTT subscriber và API đọc file này để biết đang nhận từ nguồn nào.
Khi có thiết bị thật: đăng ký device_id trong DB + bật mode real|both.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "data_source.json"

_DEFAULT = {
    "mode": "simulator",
    "simulator": {"enabled": True, "mqtt_topic_prefix": "smartlock"},
    "real_device": {"enabled": False, "mqtt_topic_prefix": "smartlock", "device_ids": []},
}


def load() -> dict:
    if not CONFIG_PATH.exists():
        return dict(_DEFAULT)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        out = dict(_DEFAULT)
        out.update(data)
        return out
    except Exception as e:
        logger.warning("Không đọc được data_source.json: %s", e)
        return dict(_DEFAULT)


def current_mode() -> str:
    """Trả về: simulator | real | both"""
    return str(load().get("mode", "simulator")).lower()


def is_simulator_enabled() -> bool:
    cfg = load()
    mode = current_mode()
    if mode == "both":
        return True
    if mode == "simulator":
        return True
    return bool(cfg.get("simulator", {}).get("enabled"))


def is_real_enabled() -> bool:
    cfg = load()
    mode = current_mode()
    if mode == "both":
        return True
    if mode == "real":
        return True
    return bool(cfg.get("real_device", {}).get("enabled"))


def describe() -> str:
    mode = current_mode()
    return {
        "simulator": "Chỉ nhận từ Sensor Simulator (MQTT giả lập)",
        "real": "Chỉ nhận từ thiết bị thật (hardware)",
        "both": "Nhận đồng thời Simulator + thiết bị thật (phân biệt bằng device_id)",
    }.get(mode, mode)

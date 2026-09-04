#!/usr/bin/env python3
"""
Smart Lock Sensor Simulator
Giả lập: WiFi (MQTT) + BLE + NFC + PIN
"""

import logging
import sys
import threading
import time
from pathlib import Path

import requests
import yaml
from colorama import Fore, Style, init as colorama_init
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent))

from device import AccessMethod, AccessResult, DeviceStatus, DoorStatus, SmartLockDevice
from mqtt_client import MQTTClient

colorama_init(autoreset=True)
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent / "logs" / "simulator.log")
    ]
)
logger = logging.getLogger("simulator")


class SensorSimulator:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        dev_cfg = self.config["device"]
        init = self.config["initial_state"]
        mqtt_cfg = self.config["mqtt"]
        self.sim_cfg = self.config["simulation"]
        self.backend_cfg = self.config.get("backend") or {}
        self._config_path = config_path

        self.device = SmartLockDevice(
            device_id=dev_cfg["id"],
            name=dev_cfg["name"],
            mac_address=dev_cfg["mac_address"],
            firmware_version=dev_cfg["firmware_version"],
            location=dev_cfg["location"],
            status=DeviceStatus(init["status"]),
            battery_level=init["battery_level"],
            door_status=DoorStatus(init["door_status"]),
            tamper_detected=init["tamper_detected"],
            rssi=init["rssi"],
        )

        self.device.add_card("04A1B2C3D4E5F6")
        self.device.add_card("04F6E5D4C3B2A1")
        self.device.add_pin("123456")
        self.device.add_pin("999999")

        self.mqtt = MQTTClient(
            host=mqtt_cfg["host"],
            port=mqtt_cfg["port"],
            client_id=mqtt_cfg["client_id"],
            device_id=dev_cfg["id"],
            username=mqtt_cfg.get("username", ""),
            password=mqtt_cfg.get("password", ""),
            on_command=self.handle_command
        )

        self._running = False
        self._auto_lock_timer = None
        self._enroll_mode = False
        self._enroll_command_id = None
        self._enroll_timeout_timer = None
        self._registered = False

    # ------------------------------------------------------------------
    # Đăng ký khóa lên Backend (giống pair WiFi/BLE lần đầu)
    # ------------------------------------------------------------------
    def register_device(self):
        """Gọi API backend để thêm khóa (device) + đầu đọc đi kèm."""
        base = (self.backend_cfg.get("base_url") or "http://localhost:8000").rstrip("/")
        email = self.backend_cfg.get("email") or "kieth@admin.vn"
        password = self.backend_cfg.get("password") or "109002"

        console.print("\n[bold cyan]📡 Đăng ký khóa lên Backend (WiFi/API)...[/]")
        console.print(f"[dim]  API: {base}[/]")
        console.print(f"[dim]  Device ID: {self.device.device_id}[/]")
        console.print(f"[dim]  MAC: {self.device.mac_address}[/]")

        try:
            # 1. Login lấy token
            r = requests.post(
                f"{base}/api/auth/login",
                json={"email": email, "password": password},
                timeout=8,
            )
            if r.status_code != 200:
                console.print(f"[red]✗ Login thất bại ({r.status_code}): {r.text}[/]")
                console.print("[yellow]  Kiểm tra backend đã chạy chưa, và email/password trong config/device.yaml[/]")
                return False
            data = r.json()
            token = data.get("access_token")
            if not token:
                console.print(f"[red]✗ Không nhận được access_token: {data}[/]")
                return False
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            # 2. Đăng ký device (id cố định để MQTT topic khớp)
            payload = {
                "id": self.device.device_id,
                "name": self.device.name,
                "location": self.device.location,
                "mac_address": self.device.mac_address,
                "firmware_version": self.device.firmware_version,
            }
            r2 = requests.post(f"{base}/api/devices", json=payload, headers=headers, timeout=8)

            if r2.status_code in (200, 201):
                out = r2.json()
                self._registered = True
                console.print(f"[bold green]✓ Đã đăng ký khóa thành công![/]")
                console.print(f"  Tên      : {out.get('name')}")
                console.print(f"  ID       : {out.get('id')}")
                console.print(f"  MAC      : {out.get('mac_address')}")
                console.print(f"  Chủ sở hữu: {out.get('owner_name')}")
                console.print("[dim]  → Refresh trang Thiết bị / Thẻ NFC trên web để thấy khóa.[/]")
                return True

            # MAC đã tồn tại → backend trả device cũ (idempotent)
            if r2.status_code == 400 and "already" in (r2.text or "").lower():
                console.print(f"[yellow]⚠ Thiết bị có thể đã tồn tại: {r2.text}[/]")
                return False

            console.print(f"[red]✗ Đăng ký thất bại ({r2.status_code}): {r2.text}[/]")
            return False

        except requests.exceptions.ConnectionError:
            console.print(f"[red]✗ Không kết nối được Backend tại {base}[/]")
            console.print("[yellow]  Hãy chạy backend: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000[/]")
            return False
        except Exception as e:
            logger.exception(e)
            console.print(f"[red]✗ Lỗi: {e}[/]")
            return False

    def handle_command(self, payload: dict):
        command = payload.get("command")
        command_id = payload.get("command_id", "unknown")
        console.print(f"\n[bold yellow]⚡ Nhận lệnh từ Backend:[/] {command}")

        try:
            if command == "lock":
                event = self.device.lock(AccessMethod.APP_REMOTE)
                self._publish_access(event)
                self.mqtt.publish_ack(command_id, "acked", "Device locked")
            elif command == "unlock":
                event = self.device.unlock(AccessMethod.APP_REMOTE)
                self._publish_access(event)
                self.mqtt.publish_ack(command_id, "acked", "Device unlocked")
                self._schedule_auto_lock()
            elif command == "reboot":
                self.device.reboot()
                self.mqtt.publish_ack(command_id, "acked", "Device rebooted")
                self._publish_telemetry()
            elif command == "ota_update":
                new_version = payload.get("version", "1.3.0")
                console.print(f"[cyan]📥 Đang cập nhật firmware → {new_version}...[/]")
                time.sleep(2)
                self.device.firmware_version = new_version
                self.mqtt.publish_ack(command_id, "acked", f"OTA to {new_version} success")
                self._publish_telemetry()
            elif command == "enroll_card":
                timeout = int(payload.get("timeout_sec", 30))
                self._enroll_mode = True
                self._enroll_command_id = command_id
                console.print(f"[bold magenta]📇 ENROLL MODE — chờ quét thẻ NFC ({timeout}s)...[/]")
                console.print("[dim]  → Dùng menu [1] hoặc [2] để giả lập chạm thẻ, hoặc [9] nhập UID[/]")
                self.mqtt.publish_ack(command_id, "acked", f"Enroll mode active for {timeout}s")
                if self._enroll_timeout_timer and self._enroll_timeout_timer.is_alive():
                    self._enroll_timeout_timer.cancel()

                def _timeout():
                    if self._enroll_mode:
                        self._enroll_mode = False
                        console.print("[yellow]⏱️  Enroll timeout — thoát chế độ quét thẻ[/]")
                        self.mqtt.publish_ack(command_id, "failed", "enroll_timeout")

                self._enroll_timeout_timer = threading.Timer(timeout, _timeout)
                self._enroll_timeout_timer.daemon = True
                self._enroll_timeout_timer.start()
            else:
                self.mqtt.publish_ack(command_id, "failed", f"Unknown command: {command}")
            self.print_status()
        except Exception as e:
            logger.exception(e)
            self.mqtt.publish_ack(command_id, "failed", str(e))

    def simulate_nfc_tap(self, card_uid: str):
        console.print(f"\n[bold magenta]📇 NFC Tap:[/] {card_uid}")
        if getattr(self, "_enroll_mode", False):
            self._enroll_mode = False
            if self._enroll_timeout_timer and self._enroll_timeout_timer.is_alive():
                self._enroll_timeout_timer.cancel()
            console.print(f"[bold green]✓ Đã quét thẻ enroll: {card_uid}[/]")
            self.device.add_card(card_uid)
            payload = {
                "device_id": self.device.device_id,
                "command_id": self._enroll_command_id,
                "card_uid": card_uid,
                "event": "card_scanned",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            }
            self.mqtt.publish_enroll(payload)
            self.mqtt.publish_ack(self._enroll_command_id or "unknown", "acked", f"card_scanned:{card_uid}")
            self.print_status()
            return None
        event = self.device.unlock(AccessMethod.NFC_CARD, card_uid=card_uid)
        self._publish_access(event)
        if event.result == AccessResult.SUCCESS:
            self._schedule_auto_lock()
        self.print_status()
        return event

    def simulate_ble_unlock(self):
        console.print(f"\n[bold blue]📡 BLE Unlock (App gần)[/]")
        event = self.device.unlock(AccessMethod.APP_BLE)
        self._publish_access(event)
        if event.result == AccessResult.SUCCESS:
            self._schedule_auto_lock()
        self.print_status()
        return event

    def simulate_pin(self, pin: str):
        console.print(f"\n[bold green]🔢 PIN nhập:[/] {pin}")
        event = self.device.unlock(AccessMethod.PIN, pin=pin)
        self._publish_access(event)
        if event.result == AccessResult.SUCCESS:
            self._schedule_auto_lock()
        self.print_status()
        return event

    def simulate_lock(self):
        console.print(f"\n[bold white]🔒 Lock thủ công[/]")
        event = self.device.lock(AccessMethod.APP_BLE)
        self._publish_access(event)
        self.print_status()
        return event

    def simulate_tamper(self):
        console.print(f"\n[bold red]🚨 TAMPER DETECTED![/]")
        self.device.trigger_tamper()
        self._publish_telemetry()
        self.print_status()

    def clear_tamper(self):
        self.device.clear_tamper()
        self._publish_telemetry()
        self.print_status()

    def _publish_access(self, event):
        payload = {
            "device_id": self.device.device_id,
            "method": event.method.value,
            "result": event.result.value,
            "card_uid": event.card_uid,
            "pin": event.pin,
            "failure_reason": event.failure_reason,
            "timestamp": event.timestamp.isoformat() + "Z"
        }
        self.mqtt.publish_access(payload)

    def _publish_telemetry(self):
        self.mqtt.publish_status(self.device.get_telemetry())

    def _schedule_auto_lock(self):
        if self._auto_lock_timer and self._auto_lock_timer.is_alive():
            self._auto_lock_timer.cancel()
        delay = self.sim_cfg.get("auto_lock_after_sec", 10)

        def auto_lock():
            if self.device.status == DeviceStatus.UNLOCKED:
                console.print(f"\n[dim]⏱️  Auto-lock sau {delay}s[/]")
                event = self.device.lock(AccessMethod.AUTO)
                self._publish_access(event)
                self.print_status()

        self._auto_lock_timer = threading.Timer(delay, auto_lock)
        self._auto_lock_timer.daemon = True
        self._auto_lock_timer.start()

    def print_status(self):
        d = self.device
        status_color = {
            DeviceStatus.LOCKED: "green",
            DeviceStatus.UNLOCKED: "yellow",
            DeviceStatus.OFFLINE: "red",
            DeviceStatus.TAMPER: "bold red",
        }.get(d.status, "white")

        table = Table(title=f"🔐 {d.name}", show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        table.add_row("Device ID", d.device_id)
        table.add_row("MAC", d.mac_address)
        table.add_row("Status", f"[{status_color}]{d.status.value.upper()}[/]")
        table.add_row("Door", d.door_status.value)
        table.add_row("Battery", f"{d.battery_level}%")
        table.add_row("RSSI", f"{d.rssi} dBm")
        table.add_row("Tamper", "⚠️ YES" if d.tamper_detected else "No")
        table.add_row("Firmware", d.firmware_version)
        table.add_row("Cards", ", ".join(d.allowed_cards) or "(none)")
        table.add_row("Location", d.location)
        table.add_row("Đăng ký BE", "✓ Đã đăng ký" if self._registered else "Chưa (chọn [A])")
        console.print(Panel(table, expand=False))

    def _telemetry_loop(self):
        interval = self.sim_cfg.get("telemetry_interval_sec", 15)
        while self._running:
            self._publish_telemetry()
            time.sleep(interval)

    def _battery_loop(self):
        interval = self.sim_cfg.get("battery_drain_interval_sec", 120)
        amount = self.sim_cfg.get("battery_drain_amount", 1)
        while self._running:
            time.sleep(interval)
            self.device.drain_battery(amount)
            if self.device.battery_level % 10 == 0:
                console.print(f"[dim]🔋 Pin còn {self.device.battery_level}%[/]")

    def start(self):
        self._running = True
        console.print(Panel.fit(
            "[bold green]Smart Lock Sensor Simulator[/]\n"
            "Giả lập: WiFi (MQTT) + BLE + NFC + PIN",
            border_style="green"
        ))
        self.print_status()

        try:
            self.mqtt.connect()
        except Exception as e:
            console.print(f"[yellow]⚠️  Không kết nối được MQTT ({e}). Vẫn chạy offline.[/]")

        threading.Thread(target=self._telemetry_loop, daemon=True).start()
        threading.Thread(target=self._battery_loop, daemon=True).start()
        self._interactive_menu()

    def stop(self):
        self._running = False
        self.mqtt.disconnect()
        console.print("[bold]Simulator stopped.[/]")

    def _interactive_menu(self):
        menu = """
[bold cyan]═══ MENU GIẢ LẬP ═══[/]
  [A] Thêm khóa / Đăng ký thiết bị lên Backend  ← [mới]
  [1] NFC Tap (thẻ hợp lệ)
  [2] NFC Tap (thẻ lạ)
  [3] BLE Unlock (App gần)
  [4] Nhập PIN
  [5] Lock thủ công
  [6] Trigger TAMPER
  [7] Clear TAMPER
  [8] Xem trạng thái
  [9] Thêm thẻ NFC
  [0] Thoát
"""
        while self._running:
            console.print(menu)
            try:
                choice = input(f"{Fore.CYAN}Chọn > {Style.RESET_ALL}").strip().upper()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "A":
                self.register_device()
            elif choice == "1":
                self.simulate_nfc_tap("04A1B2C3D4E5F6")
            elif choice == "2":
                self.simulate_nfc_tap("FFFFFFFFFFFF")
            elif choice == "3":
                self.simulate_ble_unlock()
            elif choice == "4":
                pin = input("Nhập PIN (6 số): ").strip()
                self.simulate_pin(pin)
            elif choice == "5":
                self.simulate_lock()
            elif choice == "6":
                self.simulate_tamper()
            elif choice == "7":
                self.clear_tamper()
            elif choice == "8":
                self.print_status()
            elif choice == "9":
                uid = input("Card UID mới: ").strip()
                if uid:
                    self.device.add_card(uid)
                    console.print(f"[green]✓ Đã thêm thẻ {uid}[/]")
            elif choice == "0":
                break
            else:
                console.print("[red]Lựa chọn không hợp lệ[/]")
        self.stop()


def main():
    config_path = Path(__file__).parent.parent / "config" / "device.yaml"
    if not config_path.exists():
        console.print(f"[red]Không tìm thấy config: {config_path}[/]")
        sys.exit(1)
    (Path(__file__).parent.parent / "logs").mkdir(exist_ok=True)
    sim = SensorSimulator(str(config_path))
    sim.start()


if __name__ == "__main__":
    main()

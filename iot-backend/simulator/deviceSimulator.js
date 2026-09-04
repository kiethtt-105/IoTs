/**
 * GIA LAP ESP32 — dung khi CHUA co phan cung that.
 * Publish du lieu cam bien gia + gia lap quet the NFC len MQTT broker,
 * y het nhu firmware ESP32 that se lam. Khi co board that, thay file nay
 * bang code C++ (Arduino) publish cung dung topic/format JSON nay.
 *
 * Chay: node simulator/deviceSimulator.js
 */
const mqtt = require("mqtt");
require("dotenv").config();

const DEVICE_UID = "esp32-demo-01";
const client = mqtt.connect(process.env.MQTT_URL || "mqtt://localhost:1883", {
  username: process.env.MQTT_USERNAME,
  password: process.env.MQTT_PASSWORD,
});

// The NFC hop le va the la de test whitelist (Kich ban B trong phan tan cong)
const VALID_UID = "A1B2C3D4";
const FAKE_UID = "DEADBEEF";

client.on("connect", () => {
  console.log(`[Simulator] Da ket noi, gia lap thiet bi ${DEVICE_UID}`);

  // Publish du lieu cam bien moi 5 giay
  setInterval(() => {
    const payload = {
      temperature: (25 + Math.random() * 10).toFixed(1) * 1,
      humidity: (50 + Math.random() * 20).toFixed(1) * 1,
      gas_level: (100 + Math.random() * 250).toFixed(1) * 1,
      motion: Math.random() > 0.8,
    };
    client.publish(`smarthome/${DEVICE_UID}/sensors`, JSON.stringify(payload));
    console.log("[Simulator] Sensor ->", payload);
  }, 5000);

  // Gia lap quet the hop le sau 10 giay
  setTimeout(() => {
    client.publish(`smarthome/${DEVICE_UID}/nfc`, JSON.stringify({ card_uid: VALID_UID }));
    console.log("[Simulator] Quet the HOP LE:", VALID_UID);
  }, 10000);

  // Gia lap quet the la sau 15 giay -> dung de demo Kich ban B (thu nghiem tan cong)
  setTimeout(() => {
    client.publish(`smarthome/${DEVICE_UID}/nfc`, JSON.stringify({ card_uid: FAKE_UID }));
    console.log("[Simulator] Quet the LA (test whitelist):", FAKE_UID);
  }, 15000);
});

// Lang nghe lenh dieu khien tu backend gui xuong (vd: bat quat, mo cua)
client.subscribe(`smarthome/${DEVICE_UID}/commands`);
client.on("message", (topic, payload) => {
  console.log(`[Simulator] Nhan lenh:`, payload.toString());
});

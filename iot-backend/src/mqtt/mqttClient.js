const mqtt = require("mqtt");
const pool = require("../config/db");
const { evaluateRules } = require("../rules/ruleEngine");
require("dotenv").config();

// Ket noi MQTT qua TLS (mqtts://) -> doi pho moi de doa #2, #3 trong bao cao
// Khi CHUA co broker that, doi MQTT_URL trong .env sang mqtt://localhost:1883 de test tam
// (nhung PHAI ghi ro trong bao cao day la cau hinh dev, ban that phai dung mqtts://)
const client = mqtt.connect(process.env.MQTT_URL, {
  username: process.env.MQTT_USERNAME,
  password: process.env.MQTT_PASSWORD,
  rejectUnauthorized: true, // KHONG tat khi bao ve — chi tat tam khi test voi self-signed cert cuc bo
});

const SENSOR_TOPIC_PREFIX = "smarthome/+/sensors";
const NFC_TOPIC_PREFIX = "smarthome/+/nfc";

client.on("connect", () => {
  console.log("[MQTT] Da ket noi broker");
  client.subscribe([`${SENSOR_TOPIC_PREFIX}`, `${NFC_TOPIC_PREFIX}`], (err) => {
    if (err) console.error("[MQTT] Loi subscribe:", err.message);
  });
});

client.on("error", (err) => {
  console.error("[MQTT] Loi ket noi:", err.message);
});

client.on("message", async (topic, payload) => {
  try {
    const data = JSON.parse(payload.toString());
    const deviceUid = topic.split("/")[1];

    if (topic.includes("/sensors")) {
      await handleSensorData(deviceUid, data);
    } else if (topic.includes("/nfc")) {
      await handleNfcScan(deviceUid, data);
    }
  } catch (err) {
    console.error("[MQTT] Loi xu ly message:", err.message);
  }
});

async function handleSensorData(deviceUid, data) {
  const deviceResult = await pool.query("SELECT id FROM devices WHERE device_uid = $1", [deviceUid]);
  const device = deviceResult.rows[0];
  if (!device) return console.warn(`[MQTT] Device la ${deviceUid} chua duoc dang ky, bo qua`);

  await pool.query(
    `INSERT INTO sensor_readings (device_id, temperature, humidity, gas_level, motion)
     VALUES ($1, $2, $3, $4, $5)`,
    [device.id, data.temperature, data.humidity, data.gas_level, data.motion || false]
  );

  // Sau khi luu, cham luat trong rule engine (Lop 3: >=3 luat cau hinh duoc)
  await evaluateRules(device.id, deviceUid, data, publishCommand);
}

// Xu ly quet the NFC — CHECK WHITELIST tu DB, khong tin bat ky UID nao gui len (moi de doa #1)
async function handleNfcScan(deviceUid, data) {
  const { card_uid } = data;

  const deviceResult = await pool.query("SELECT id FROM devices WHERE device_uid = $1", [deviceUid]);
  const device = deviceResult.rows[0];
  if (!device) return;

  const cardResult = await pool.query(
    "SELECT * FROM nfc_cards WHERE card_uid = $1 AND is_active = true",
    [card_uid]
  );
  const card = cardResult.rows[0];

  if (card) {
    await pool.query(
      `INSERT INTO door_logs (device_id, method, card_uid, user_id, status) VALUES ($1, 'nfc', $2, $3, 'success')`,
      [device.id, card_uid, card.owner_id]
    );
    publishCommand(deviceUid, { target: "door", command: "OPEN" });
    console.log(`[NFC] The hop le ${card_uid} -> mo cua ${deviceUid}`);
  } else {
    await pool.query(
      `INSERT INTO door_logs (device_id, method, card_uid, status, reason) VALUES ($1, 'nfc', $2, 'denied', 'uid_not_whitelisted')`,
      [device.id, card_uid]
    );
    publishCommand(deviceUid, { target: "buzzer", command: "ALERT" });
    console.warn(`[NFC] The LA ${card_uid} bi tu choi tren ${deviceUid}`);
  }
}

// Gui lenh dieu khien nguoc lai thiet bi (backend -> ESP32)
function publishCommand(deviceUid, commandObj) {
  const topic = `smarthome/${deviceUid}/commands`;
  client.publish(topic, JSON.stringify(commandObj), { qos: 1 });
}

module.exports = { client, publishCommand };

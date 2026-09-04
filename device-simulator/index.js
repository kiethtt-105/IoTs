// device-simulator/index.js
import mqtt from "mqtt";
import readline from "readline";

const DEVICE_ID = process.env.DEVICE_ID || "lock-01";
const client = mqtt.connect(process.env.MQTT_URL || "mqtt://mosquitto:1883");

client.on("connect", () => {
  client.publish(`device/${DEVICE_ID}/status`, JSON.stringify({ status: "ONLINE" }));
  client.subscribe(`device/${DEVICE_ID}/cmd`);
  console.log(`[${DEVICE_ID}] connected. Gõ mã thẻ (uid) rồi Enter để giả lập quẹt thẻ.`);
});

client.on("message", (topic, payload) => {
  const cmd = JSON.parse(payload.toString());
  console.log(`[${DEVICE_ID}] LỆNH NHẬN:`, cmd); // vd { action: "UNLOCK" } -> giả lập mở khóa
});

const rl = readline.createInterface({ input: process.stdin });
rl.on("line", (uid) => {
  client.publish(`device/${DEVICE_ID}/scan`, JSON.stringify({ cardUid: uid.trim() }));
});
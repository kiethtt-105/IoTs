require("dotenv").config();
const app = require("./app");
require("./mqtt/mqttClient"); // khoi dong ket noi MQTT ngay khi server start

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`[Server] Backend dang chay tai http://localhost:${PORT}`);
});

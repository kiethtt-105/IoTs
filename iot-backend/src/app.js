const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const { globalLimiter } = require("./middleware/rateLimit");

const authRoutes = require("./routes/auth.routes");
const sensorRoutes = require("./routes/sensor.routes");
const doorRoutes = require("./routes/door.routes");

const app = express();

// ---- Security headers co ban (chong XSS, clickjacking, MIME sniffing...) ----
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || "*" })); // sieu chinh lai origin cu the khi deploy that
app.use(express.json({ limit: "10kb" })); // gioi han kich thuoc body -> chong payload qua khich

// ---- Rate limit toan cuc, chong DoS co ban (moi de doa #5) ----
app.use(globalLimiter);

// ---- Routes ----
app.use("/api/auth", authRoutes);
app.use("/api/sensors", sensorRoutes);
app.use("/api/door", doorRoutes);

app.get("/api/health", (req, res) => res.json({ status: "ok" }));

// ---- Xu ly loi tap trung — KHONG lo chi tiet stack trace ra ngoai (rieng cho demo hoc) ----
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: "Da xay ra loi. Vui long thu lai." });
});

module.exports = app;

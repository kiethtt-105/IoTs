const express = require("express");
const pool = require("../config/db");
const { authenticate } = require("../middleware/auth");

const router = express.Router();

// GET /api/sensors/latest?device_uid=esp32-demo-01
// Ca chunha va khach deu xem duoc (chi khong dieu khien duoc cua)
router.get("/latest", authenticate, async (req, res) => {
  const { device_uid } = req.query;

  try {
    const result = await pool.query(
      `SELECT sr.* FROM sensor_readings sr
       JOIN devices d ON d.id = sr.device_id
       WHERE d.device_uid = $1
       ORDER BY sr.recorded_at DESC LIMIT 1`,
      [device_uid]
    );
    res.json(result.rows[0] || null);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

// GET /api/sensors/history?device_uid=...&hours=24
// Dung cho bieu do lich su tren dashboard (yeu cau Lop 5)
router.get("/history", authenticate, async (req, res) => {
  const { device_uid, hours = 24 } = req.query;
  const hoursInt = Math.min(parseInt(hours, 10) || 24, 168); // gioi han toi da 7 ngay/request

  try {
    const result = await pool.query(
      `SELECT sr.temperature, sr.humidity, sr.gas_level, sr.motion, sr.recorded_at
       FROM sensor_readings sr
       JOIN devices d ON d.id = sr.device_id
       WHERE d.device_uid = $1 AND sr.recorded_at > now() - ($2 || ' hours')::interval
       ORDER BY sr.recorded_at ASC`,
      [device_uid, hoursInt]
    );
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

module.exports = router;

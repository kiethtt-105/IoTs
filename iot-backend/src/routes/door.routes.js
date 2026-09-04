const express = require("express");
const pool = require("../config/db");
const { authenticate, authorize } = require("../middleware/auth");
const { doorActionLimiter } = require("../middleware/rateLimit");
const { publishCommand } = require("../mqtt/mqttClient");

const router = express.Router();

// POST /api/door/open  — CHI role "chunha" moi mo cua qua App duoc (RBAC)
// Day la endpoint dung de demo Kich ban B / C trong phan tan cong
router.post("/open", authenticate, authorize("chunha"), doorActionLimiter, async (req, res) => {
  const { device_uid } = req.body;

  try {
    const deviceResult = await pool.query("SELECT id FROM devices WHERE device_uid = $1", [device_uid]);
    const device = deviceResult.rows[0];
    if (!device) return res.status(404).json({ error: "Khong tim thay thiet bi" });

    await pool.query(
      `INSERT INTO door_logs (device_id, method, user_id, status) VALUES ($1, 'app', $2, 'success')`,
      [device.id, req.user.id]
    );

    publishCommand(device_uid, { target: "door", command: "OPEN" });
    res.json({ message: "Da gui lenh mo cua" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

// GET /api/door/logs?device_uid=... — xem lich su ra vao (ca 2 role deu xem duoc)
router.get("/logs", authenticate, async (req, res) => {
  const { device_uid } = req.query;

  try {
    const result = await pool.query(
      `SELECT dl.method, dl.card_uid, dl.status, dl.reason, dl.created_at, u.username
       FROM door_logs dl
       JOIN devices d ON d.id = dl.device_id
       LEFT JOIN users u ON u.id = dl.user_id
       WHERE d.device_uid = $1
       ORDER BY dl.created_at DESC LIMIT 50`,
      [device_uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

module.exports = router;

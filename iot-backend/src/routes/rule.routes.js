const express = require("express");
const pool = require("../config/db");
const { authenticate } = require("../middleware/auth");

const router = express.Router();

// GET /api/rules?device_uid=... — xem danh sach luat cua thiet bi (dung cho dashboard)
router.get("/", authenticate, async (req, res) => {
  const { device_uid } = req.query;

  try {
    const result = await pool.query(
      `SELECT r.name, r.condition, r.action, r.enabled
       FROM rules r
       JOIN devices d ON d.id = r.device_id
       WHERE d.device_uid = $1
       ORDER BY r.id ASC`,
      [device_uid]
    );
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

module.exports = router;

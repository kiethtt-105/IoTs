const express = require("express");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const crypto = require("crypto");
const Joi = require("joi");
const pool = require("../config/db");
const { loginLimiter } = require("../middleware/rateLimit");
require("dotenv").config();

const router = express.Router();
const SALT_ROUNDS = 12;

// Validate input truoc khi cham vao DB -> chong injection va du lieu ban (moi de doa #7)
const registerSchema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  password: Joi.string().min(8).required(),
  role: Joi.string().valid("chunha", "khach").required(),
});

const loginSchema = Joi.object({
  username: Joi.string().required(),
  password: Joi.string().required(),
});

// ---- Dang ky (chi chunha dau tien tao thu cong, sau do chunha tao tai khoan khach) ----
router.post("/register", async (req, res) => {
  const { error, value } = registerSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });

  const { username, password, role } = value;

  try {
    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

    // Parameterized query ($1, $2, $3) -> KHONG noi chuoi SQL
    const result = await pool.query(
      "INSERT INTO users (username, password_hash, role) VALUES ($1, $2, $3) RETURNING id, username, role",
      [username, passwordHash, role]
    );

    res.status(201).json({ user: result.rows[0] });
  } catch (err) {
    if (err.code === "23505") {
      return res.status(409).json({ error: "Username da ton tai" });
    }
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

// ---- Dang nhap (co rate-limit chong brute-force) ----
router.post("/login", loginLimiter, async (req, res) => {
  const { error, value } = loginSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });

  const { username, password } = value;

  try {
    const result = await pool.query("SELECT * FROM users WHERE username = $1", [username]);
    const user = result.rows[0];

    // Luon so sanh bcrypt du user co ton tai hay khong -> tranh "timing attack"
    // do lo user nao ton tai trong he thong
    const dummyHash = "$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ";
    const isValid = await bcrypt.compare(password, user ? user.password_hash : dummyHash);

    if (!user || !isValid) {
      return res.status(401).json({ error: "Sai username hoac password" });
    }

    const accessToken = jwt.sign(
      { id: user.id, username: user.username, role: user.role },
      process.env.JWT_ACCESS_SECRET,
      { expiresIn: process.env.JWT_ACCESS_EXPIRES, algorithm: "HS256" }
    );

    const refreshToken = crypto.randomBytes(40).toString("hex");
    const refreshHash = crypto.createHash("sha256").update(refreshToken).digest("hex");
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

    await pool.query(
      "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
      [user.id, refreshHash, expiresAt]
    );

    res.json({
      accessToken,
      refreshToken,
      user: { id: user.id, username: user.username, role: user.role },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

// ---- Lam moi access token bang refresh token ----
router.post("/refresh", async (req, res) => {
  const { refreshToken } = req.body;
  if (!refreshToken) return res.status(400).json({ error: "Thieu refreshToken" });

  const tokenHash = crypto.createHash("sha256").update(refreshToken).digest("hex");

  try {
    const result = await pool.query(
      `SELECT rt.*, u.username, u.role FROM refresh_tokens rt
       JOIN users u ON u.id = rt.user_id
       WHERE rt.token_hash = $1 AND rt.revoked = false AND rt.expires_at > now()`,
      [tokenHash]
    );

    const row = result.rows[0];
    if (!row) return res.status(401).json({ error: "Refresh token khong hop le" });

    const accessToken = jwt.sign(
      { id: row.user_id, username: row.username, role: row.role },
      process.env.JWT_ACCESS_SECRET,
      { expiresIn: process.env.JWT_ACCESS_EXPIRES, algorithm: "HS256" }
    );

    res.json({ accessToken });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Loi server" });
  }
});

// ---- Dang xuat: thu hoi refresh token ----
router.post("/logout", async (req, res) => {
  const { refreshToken } = req.body;
  if (!refreshToken) return res.status(400).json({ error: "Thieu refreshToken" });

  const tokenHash = crypto.createHash("sha256").update(refreshToken).digest("hex");
  await pool.query("UPDATE refresh_tokens SET revoked = true WHERE token_hash = $1", [tokenHash]);
  res.json({ message: "Da dang xuat" });
});

module.exports = router;

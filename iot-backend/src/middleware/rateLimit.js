const rateLimit = require("express-rate-limit");

/**
 * Gioi han so lan dang nhap sai.
 * Day chinh la bien phap doi pho moi de doa #4 (brute-force JWT/mat khau)
 * va la thu ban se BAT/TAT de demo Kich ban C (thu nghiem tan cong) trong bao cao.
 */
const loginLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 phut
  max: 5, // toi da 5 lan thu trong 5 phut
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: "Qua nhieu lan dang nhap sai. Thu lai sau 5 phut." },
});

/**
 * Gioi han cho hanh dong quet the NFC / mo cua qua API
 * -> doi pho moi de doa #1 va #5 (gia mao UID, DoS)
 */
const doorActionLimiter = rateLimit({
  windowMs: 30 * 1000, // 30 giay
  max: 3,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: "Qua nhieu lan thao tac cua. Vui long doi." },
});

/**
 * Gioi han chung cho toan bo API -> chong DoS co ban (moi de doa #5)
 */
const globalLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
});

module.exports = { loginLimiter, doorActionLimiter, globalLimiter };

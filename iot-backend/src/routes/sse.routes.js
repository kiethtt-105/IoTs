const express = require("express");
const jwt = require("jsonwebtoken");
const { addClient, removeClient } = require("../sse");
require("dotenv").config();

const router = express.Router();

// EventSource cua trinh duyet KHONG gui duoc custom header, nen nhan token qua query string
// -> chi dung rieng cho endpoint SSE nay, cac API khac van bat buoc header Authorization
router.get("/stream", (req, res) => {
  const { token } = req.query;

  try {
    jwt.verify(token, process.env.JWT_ACCESS_SECRET, { algorithms: ["HS256"] });
  } catch (err) {
    return res.status(401).end();
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });
  res.write("\n");

  addClient(res);

  const keepAlive = setInterval(() => res.write(": ping\n\n"), 20000);

  req.on("close", () => {
    clearInterval(keepAlive);
    removeClient(res);
  });
});

module.exports = router;

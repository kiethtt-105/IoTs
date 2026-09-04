const { Pool } = require("pg");
require("dotenv").config();

// Connection pool — dùng $1, $2... (parameterized queries) ở MỌI nơi truy vấn
// để chống SQL Injection. KHÔNG BAO GIỜ nối chuỗi SQL bằng dấu + hoặc template string.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

pool.on("error", (err) => {
  console.error("Loi ket noi PostgreSQL:", err.message);
});

module.exports = pool;

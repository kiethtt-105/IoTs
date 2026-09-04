const jwt = require("jsonwebtoken");
require("dotenv").config();

/**
 * Middleware xac thuc JWT.
 * Doi pho moi de doa #4 (brute-force / danh cap token) trong muc 7.1 bao cao:
 * - Access token song ngan (15 phut) -> giam thiet hai neu bi lo
 * - Kiem tra chu ky nghiem ngat, KHONG chap nhan token khong ky hoac ky sai
 */
function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Thieu token xac thuc" });
  }

  const token = authHeader.split(" ")[1];

  try {
    const payload = jwt.verify(token, process.env.JWT_ACCESS_SECRET, {
      algorithms: ["HS256"], // chi chap nhan dung 1 thuat toan -> chong "alg:none" attack
    });
    req.user = payload; // { id, username, role }
    next();
  } catch (err) {
    return res.status(401).json({ error: "Token khong hop le hoac da het han" });
  }
}

/**
 * Middleware phan quyen (RBAC).
 * Dung: router.post('/door/open', authenticate, authorize('chunha'), handler)
 */
function authorize(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user || !allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: "Ban khong co quyen thuc hien hanh dong nay" });
    }
    next();
  };
}

module.exports = { authenticate, authorize };

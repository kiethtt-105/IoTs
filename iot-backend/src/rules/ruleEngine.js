const pool = require("../config/db");

/**
 * Rule engine — doc luat tu bang `rules` trong DB (KHONG hardcode if/else trong code)
 * De dap ung yeu cau Lop 3: ">=3 luat cau hinh duoc".
 * Vi du 1 row trong bang rules:
 *   condition = {"metric": "temperature", "operator": ">", "value": 30}
 *   action    = {"target": "fan", "command": "ON"}
 *
 * De them luat moi, chi can INSERT vao bang `rules`, KHONG can sua code / build lai firmware.
 */
async function evaluateRules(deviceId, deviceUid, sensorData, publishCommand) {
  const result = await pool.query(
    "SELECT * FROM rules WHERE device_id = $1 AND enabled = true",
    [deviceId]
  );

  for (const rule of result.rows) {
    const { metric, operator, value } = rule.condition;
    const currentValue = sensorData[metric];

    if (currentValue === undefined) continue;

    const matched = compare(currentValue, operator, value);

    if (matched) {
      publishCommand(deviceUid, {
        target: rule.action.target,
        command: rule.action.command,
      });
      console.log(`[RuleEngine] Luat "${rule.name}" kich hoat tren ${deviceUid}`);
    }
  }
}

function compare(current, operator, target) {
  switch (operator) {
    case ">": return current > target;
    case "<": return current < target;
    case ">=": return current >= target;
    case "<=": return current <= target;
    case "==": return current === target;
    default: return false;
  }
}

module.exports = { evaluateRules };

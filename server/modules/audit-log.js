const fs = require("fs");
const path = require("path");

const AUDIT_PATH = path.join(__dirname, "..", ".audit.log");

function append(event) {
  const row = {
    eventId: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: new Date().toISOString(),
    ...event,
  };
  fs.appendFileSync(AUDIT_PATH, JSON.stringify(row) + "\n", "utf8");
  return row;
}

module.exports = {
  append,
  AUDIT_PATH,
};

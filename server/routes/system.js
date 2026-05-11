const express = require("express");

const state = require("../modules/system-state");

const router = express.Router();

router.get("/state", (req, res) => {
  res.json(state.getState());
});

router.post("/state", (req, res) => {
  const { automationEnabled, safeMode, lockdown } = req.body || {};

  let out = state.getState();

  if (typeof automationEnabled === "boolean") {
    out = state.setAutomationEnabled(automationEnabled);
  }

  if (safeMode === true) {
    out = state.enterSafeMode("manual_request").state;
  }

  if (lockdown === true) {
    out = state.enterLockdown("manual_request").state;
  }

  res.json({
    ok: true,
    state: out,
  });
});

module.exports = router;

const fs = require("fs");
const path = require("path");

const STATE_PATH = path.join(__dirname, "..", ".system-state.json");

const DEFAULT_STATE = {
  version: "1.0",
  execution: {
    automationEnabled: false,
    exceptionOnly: true,
    mode: "OFF",
  },
  guardian: {
    guardianEnabled: true,
    lockdown: false,
    safeMode: false,
    lastIncidentId: null,
  },
  routing: {
    parallelWorkersAllowed: true,
    dynamicRoutingEnabled: true,
    maxParallelWorkers: 2,
    conflictStrategy: "supervisor_resolves",
  },
  audit: {
    appendOnly: true,
    auditRequiredForAutoApproval: true,
    failClosedOnAuditError: true,
  },
  limits: {
    maxTaskTimeoutSec: 1800,
    maxRetries: 2,
    maxParallelFanout: 2,
    maxExternalModelCostUsdPerDay: 5,
  },
};

let state = load();

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function load() {
  try {
    if (fs.existsSync(STATE_PATH)) {
      return JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
    }
  } catch (_) {
    // Fall back to a closed default state.
  }
  fs.writeFileSync(STATE_PATH, JSON.stringify(DEFAULT_STATE, null, 2));
  return clone(DEFAULT_STATE);
}

function save() {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

function getState() {
  return clone(state);
}

function updateState(patch = {}) {
  state = {
    ...state,
    ...patch,
    execution: { ...state.execution, ...(patch.execution || {}) },
    guardian: { ...state.guardian, ...(patch.guardian || {}) },
    routing: { ...state.routing, ...(patch.routing || {}) },
    audit: { ...state.audit, ...(patch.audit || {}) },
    limits: { ...state.limits, ...(patch.limits || {}) },
  };
  save();
  return getState();
}

function setAutomationEnabled(enabled) {
  state.execution.automationEnabled = Boolean(enabled);
  state.execution.mode = enabled ? "ON" : "OFF";
  save();
  return getState();
}

function enterSafeMode(reason = "guardian_request") {
  state.guardian.safeMode = true;
  state.execution.mode = "SAFE_MODE";
  state.guardian.lastIncidentId = String(Date.now());
  save();
  return { state: getState(), reason };
}

function enterLockdown(reason = "guardian_lockdown") {
  state.guardian.lockdown = true;
  state.execution.mode = "GUARDIAN_LOCKDOWN";
  state.guardian.lastIncidentId = String(Date.now());
  save();
  return { state: getState(), reason };
}

module.exports = {
  getState,
  updateState,
  setAutomationEnabled,
  enterSafeMode,
  enterLockdown,
};

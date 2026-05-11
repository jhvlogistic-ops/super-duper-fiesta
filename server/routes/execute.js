const express = require("express");

const registry = require("../stubs/action-registry");
const approvalMatrix = require("../stubs/approval-matrix");
const systemState = require("../modules/system-state");
const guardian = require("../modules/guardian-controller");
const auditLog = require("../modules/audit-log");
const executor = require("../modules/executor");

const router = express.Router();

function getAction(actionId) {
  return registry.actions[actionId] || null;
}

router.post("/", async (req, res) => {
  const {
    actionId,
    source = "user_direct",
    cwd,
    command,
    timeoutSec = 30,
    userConfirmed = false,
    supervisorDecision = "approve",
  } = req.body || {};

  const incident = guardian.detectIncident({
    command,
    containsBlockedToken: executor.containsBlockedToken(command),
    bypassAttempt: false,
    auditFailure: false,
  });

  if (incident.incident) {
    const containment = guardian.contain({
      command,
      containsBlockedToken: true,
    });

    const auditRow = auditLog.append({
      type: "guardian_containment",
      source,
      actionId,
      command,
      cwd,
      reason: containment.reason,
      stateMode: containment.state.execution.mode,
    });

    return res.status(423).json({
      ok: false,
      status: "blocked_by_guardian",
      incident,
      containment,
      audit: auditRow,
    });
  }

  const action = getAction(actionId);

  const ctx = {
    source,
    workspaceAllowed: executor.workspaceAllowed(cwd),
    containsBlockedToken: executor.containsBlockedToken(command),
    userConfirmed,
    incidentSignal: false,
    supervisorDecision,
  };

  const decision = approvalMatrix.resolve({
    action,
    ctx,
    systemState: systemState.getState(),
  });

  const reviewAudit = auditLog.append({
    type: "execution_review",
    source,
    actionId,
    cwd,
    command,
    decision,
  });

  if (decision.status !== "approved") {
    return res.status(400).json({
      ok: false,
      review: decision,
      audit: reviewAudit,
    });
  }

  const state = systemState.getState();

  if (!state.execution.automationEnabled) {
    const holdAudit = auditLog.append({
      type: "execution_hold",
      source,
      actionId,
      cwd,
      command,
      reason: "automation_disabled",
    });

    return res.status(409).json({
      ok: false,
      status: "approved_but_execution_disabled",
      review: decision,
      audit: holdAudit,
    });
  }

  const result = await executor.runPowerShell({
    command,
    cwd,
    timeoutSec,
  });

  const execAudit = auditLog.append({
    type: "execution_result",
    source,
    actionId,
    cwd,
    command,
    resultStatus: result.ok ? "success" : "failed",
    exitCode: result.exitCode,
    artifactPath: result.artifactPath,
  });

  return res.json({
    ok: result.ok,
    review: decision,
    result,
    audit: execAudit,
  });
});

module.exports = router;

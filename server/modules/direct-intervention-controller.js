const path = require("path");

const registry = require("../stubs/action-registry");
const approvalMatrix = require("../stubs/approval-matrix");
const systemState = require("./system-state");

function workspaceAllowed(cwd = "") {
  const normalized = path.normalize(cwd || "");
  return registry.allowedWorkspaces.some((root) => normalized.startsWith(root));
}

function containsBlockedToken(command = "") {
  return registry.blockedTokens.some((token) =>
    command.toLowerCase().includes(token.toLowerCase())
  );
}

function getAction(actionId) {
  return registry.actions[actionId] || null;
}

function reviewDirectOrder({
  actionId,
  source = "user_direct",
  cwd,
  command,
  userConfirmed = false,
  supervisorDecision = "approve",
}) {
  const action = getAction(actionId);

  const ctx = {
    source,
    workspaceAllowed: workspaceAllowed(cwd),
    containsBlockedToken: containsBlockedToken(command),
    userConfirmed,
    incidentSignal: false,
    supervisorDecision,
  };

  const decision = approvalMatrix.resolve({
    action,
    ctx,
    systemState: systemState.getState(),
  });

  return {
    ok: decision.status === "approved",
    action,
    decision,
    command,
    cwd,
    source,
  };
}

module.exports = {
  reviewDirectOrder,
};

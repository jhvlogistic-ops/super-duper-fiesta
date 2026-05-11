const systemState = require("./system-state");

function detectIncident({
  command = "",
  containsBlockedToken = false,
  bypassAttempt = false,
  auditFailure = false,
}) {
  if (containsBlockedToken) return { incident: true, type: "dangerous_token" };
  if (bypassAttempt) return { incident: true, type: "policy_bypass_attempt" };
  if (auditFailure) return { incident: true, type: "audit_failure" };
  if (/Remove-Item|shutdown|Restart-Computer|Set-ExecutionPolicy/i.test(command)) {
    return { incident: true, type: "dangerous_command_pattern" };
  }
  return { incident: false, type: null };
}

function contain(input) {
  const detection = detectIncident(input);
  if (!detection.incident) {
    return {
      contained: false,
      action: null,
      reason: "no_incident_signal",
      state: systemState.getState(),
    };
  }

  const out = systemState.enterSafeMode(detection.type);
  return {
    contained: true,
    action: "system.enter_safe_mode",
    reason: detection.type,
    state: out.state,
  };
}

module.exports = {
  detectIncident,
  contain,
};

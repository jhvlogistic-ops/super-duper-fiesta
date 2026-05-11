module.exports = {
  version: "1.0",
  defaultDecision: "supervisor_review",
  resolve({ action, ctx, systemState }) {
    if (!action) {
      return {
        approvalPolicy: "hard_block",
        status: "blocked",
        decision: "block",
        reason: "action_not_registered",
      };
    }

    if (!action.allowedSources.includes(ctx.source)) {
      return {
        approvalPolicy: "hard_block",
        status: "blocked",
        decision: "block",
        reason: "source_not_allowed",
      };
    }

    if (ctx.workspaceAllowed === false) {
      return {
        approvalPolicy: "hard_block",
        status: "blocked",
        decision: "block",
        reason: "workspace_not_allowed",
      };
    }

    if (ctx.containsBlockedToken) {
      return {
        approvalPolicy: "hard_block",
        status: "blocked",
        decision: "block",
        reason: "dangerous_token",
      };
    }

    switch (action.approvalPolicy) {
      case "human_required":
        return {
          approvalPolicy: "human_required",
          status: "human_required",
          decision: "escalate_to_user",
          reason: "sensitive_action",
        };

      case "guardian_auto":
        if (ctx.incidentSignal) {
          return {
            approvalPolicy: "guardian_auto",
            status: "approved",
            decision: "approve_and_execute",
            approvedBy: "guardian",
            reason: "protective_containment",
          };
        }
        return {
          approvalPolicy: "guardian_auto",
          status: "pending_guardian_signal",
          decision: "hold",
          reason: "incident_signal_missing",
        };

      case "user_direct":
        if (ctx.userConfirmed) {
          return {
            approvalPolicy: "user_direct",
            status: "approved",
            decision: "approve_and_execute",
            approvedBy: "user_direct",
            reason: "user_confirmed",
          };
        }
        return {
          approvalPolicy: "user_direct",
          status: "awaiting_user_confirmation",
          decision: "hold",
          reason: "user_confirmation_required",
        };

      case "safe_auto":
        return {
          approvalPolicy: "safe_auto",
          status: systemState.execution.automationEnabled
            ? "approved"
            : "approved_but_execution_disabled",
          decision: systemState.execution.automationEnabled ? "approve" : "hold",
          approvedBy: "supervisor_auto",
          reason: "supervisor_auto_approved",
        };

      case "supervisor_only":
      default:
        if (ctx.supervisorDecision === "approve") {
          return {
            approvalPolicy: "supervisor_only",
            status: "approved",
            decision: "approve",
            approvedBy: "supervisor",
            reason: "supervisor_approved",
          };
        }
        return {
          approvalPolicy: "supervisor_only",
          status: "pending_supervisor_review",
          decision: "hold",
          reason: "supervisor_review_required",
        };
    }
  },
};

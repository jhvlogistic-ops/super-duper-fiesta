const path = require("path");

const WORKSPACES = [
  "C:\\Users\\Jorge\\quant_lab",
  "C:\\Users\\Jorge\\alphaforge",
].map((workspacePath) => path.normalize(workspacePath));

module.exports = {
  version: "1.0",
  defaultPolicy: "supervisor_only",
  allowedWorkspaces: WORKSPACES,
  blockedTokens: [
    "Remove-Item",
    "del ",
    "rmdir",
    "rd /s",
    "format-",
    "shutdown",
    "Restart-Computer",
    "Stop-Computer",
    "Set-ExecutionPolicy",
    "reg add",
  ],
  actions: {
    "workspace.list_files": {
      approvalPolicy: "safe_auto",
      allowedSources: ["supervisor", "local_worker", "user_direct"],
      allowedCommands: ["Get-ChildItem", "dir", "ls"],
      workspaceOnly: true,
      destructive: false,
    },
    "workspace.show_path": {
      approvalPolicy: "safe_auto",
      allowedSources: ["supervisor", "local_worker", "user_direct"],
      allowedCommands: ["Get-Location", "pwd"],
      workspaceOnly: true,
      destructive: false,
    },
    "repo.git_status": {
      approvalPolicy: "safe_auto",
      allowedSources: ["supervisor", "local_worker", "user_direct"],
      allowedCommands: ["git status"],
      workspaceOnly: true,
      destructive: false,
    },
    "repo.git_diff": {
      approvalPolicy: "safe_auto",
      allowedSources: ["supervisor", "local_worker", "user_direct"],
      allowedCommands: ["git diff"],
      workspaceOnly: true,
      destructive: false,
    },
    "repo.git_pull_ff": {
      approvalPolicy: "supervisor_only",
      allowedSources: ["supervisor", "user_direct"],
      allowedCommands: ["git pull --ff-only"],
      workspaceOnly: true,
      destructive: false,
    },
    "python.quantlab_run": {
      approvalPolicy: "supervisor_only",
      allowedSources: ["supervisor", "local_worker", "user_direct"],
      commandPrefixes: ["python .\\run.py", "python .\\quant_lab\\"],
      workspaceOnly: true,
      destructive: false,
      maxTimeoutSec: 1800,
    },
    "python.alphaforge_run": {
      approvalPolicy: "supervisor_only",
      allowedSources: ["supervisor", "local_worker", "user_direct"],
      commandPrefixes: ["python .\\alphaforge\\"],
      workspaceOnly: true,
      destructive: false,
      maxTimeoutSec: 1800,
    },
    "powershell.script_safe": {
      approvalPolicy: "supervisor_only",
      allowedSources: ["supervisor", "user_direct"],
      commandPrefixes: [".\\scripts\\"],
      workspaceOnly: true,
      destructive: false,
      maxTimeoutSec: 1800,
    },
    "system.toggle_execution": {
      approvalPolicy: "user_direct",
      allowedSources: ["supervisor", "user_direct", "guardian"],
    },
    "system.enter_safe_mode": {
      approvalPolicy: "guardian_auto",
      allowedSources: ["guardian", "supervisor"],
    },
    "system.lockdown": {
      approvalPolicy: "guardian_auto",
      allowedSources: ["guardian", "supervisor"],
    },
    "queue.cancel_pending": {
      approvalPolicy: "guardian_auto",
      allowedSources: ["guardian", "supervisor"],
    },
    "worker.block": {
      approvalPolicy: "guardian_auto",
      allowedSources: ["guardian", "supervisor"],
    },
    "process.kill_child": {
      approvalPolicy: "guardian_auto",
      allowedSources: ["guardian"],
    },
    "evidence.snapshot": {
      approvalPolicy: "guardian_auto",
      allowedSources: ["guardian", "supervisor"],
    },
    "policy.modify_registry": {
      approvalPolicy: "human_required",
      allowedSources: ["supervisor", "user_direct"],
    },
    "secrets.access": {
      approvalPolicy: "human_required",
      allowedSources: ["user_direct"],
    },
    "filesystem.delete_destructive": {
      approvalPolicy: "human_required",
      allowedSources: ["supervisor", "user_direct"],
    },
  },
};

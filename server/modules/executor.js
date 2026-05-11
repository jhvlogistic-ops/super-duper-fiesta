const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const registry = require("../stubs/action-registry");

const ARTIFACTS_DIR = path.join(__dirname, "..", ".artifacts");

if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

function workspaceAllowed(cwd = "") {
  const normalized = path.normalize(cwd || "");
  return registry.allowedWorkspaces.some((root) => normalized.startsWith(root));
}

function containsBlockedToken(command = "") {
  return registry.blockedTokens.some((token) =>
    command.toLowerCase().includes(token.toLowerCase())
  );
}

function resolveShell() {
  if (process.platform === "win32") {
    return {
      bin: "powershell.exe",
      argsPrefix: ["-NoProfile", "-Command"],
    };
  }
  return {
    bin: "pwsh",
    argsPrefix: ["-NoProfile", "-Command"],
  };
}

function runPowerShell({ command, cwd, timeoutSec = 30 }) {
  return new Promise((resolve) => {
    if (!workspaceAllowed(cwd)) {
      return resolve({
        ok: false,
        exitCode: -1,
        error: "workspace_not_allowed",
      });
    }

    if (containsBlockedToken(command)) {
      return resolve({
        ok: false,
        exitCode: -1,
        error: "dangerous_token",
      });
    }

    const shell = resolveShell();
    const startedAt = Date.now();

    let ps;
    try {
      ps = spawn(shell.bin, [...shell.argsPrefix, command], {
        cwd,
        shell: false,
        windowsHide: true,
        env: process.env,
      });
    } catch (err) {
      const artifact = {
        execId: `exec-${Date.now()}`,
        command,
        cwd,
        timeoutSec,
        startedAt: new Date(startedAt).toISOString(),
        endedAt: new Date().toISOString(),
        durationMs: Date.now() - startedAt,
        ok: false,
        exitCode: -1,
        error: err.message,
        stdout: "",
        stderr: "",
      };
      const artifactPath = path.join(ARTIFACTS_DIR, `${artifact.execId}.json`);
      fs.writeFileSync(artifactPath, JSON.stringify(artifact, null, 2), "utf8");
      return resolve({ ...artifact, artifactPath });
    }

    let stdout = "";
    let stderr = "";
    let killed = false;
    let settled = false;

    const finish = (artifact) => {
      if (settled) return;
      settled = true;
      const artifactPath = path.join(ARTIFACTS_DIR, `${artifact.execId}.json`);
      fs.writeFileSync(artifactPath, JSON.stringify(artifact, null, 2), "utf8");
      resolve({ ...artifact, artifactPath });
    };

    const timer = setTimeout(() => {
      killed = true;
      ps.kill();
    }, timeoutSec * 1000);

    ps.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    ps.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    ps.on("error", (err) => {
      clearTimeout(timer);
      finish({
        execId: `exec-${Date.now()}`,
        command,
        cwd,
        timeoutSec,
        startedAt: new Date(startedAt).toISOString(),
        endedAt: new Date().toISOString(),
        durationMs: Date.now() - startedAt,
        ok: false,
        exitCode: -1,
        error: err.message,
        stdout,
        stderr,
      });
    });

    ps.on("close", (code) => {
      clearTimeout(timer);

      finish({
        execId: `exec-${Date.now()}`,
        command,
        cwd,
        timeoutSec,
        startedAt: new Date(startedAt).toISOString(),
        endedAt: new Date().toISOString(),
        durationMs: Date.now() - startedAt,
        exitCode: killed ? -9 : code,
        ok: !killed && code === 0,
        error: killed ? "timeout_killed" : null,
        stdout,
        stderr,
      });
    });
  });
}

module.exports = {
  runPowerShell,
  workspaceAllowed,
  containsBlockedToken,
};

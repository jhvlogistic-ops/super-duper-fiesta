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

function writeArtifact(artifact) {
  const artifactPath = path.join(ARTIFACTS_DIR, `${artifact.execId}.json`);
  fs.writeFileSync(artifactPath, JSON.stringify(artifact, null, 2), "utf8");
  return {
    ...artifact,
    artifactPath,
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

    const startedAt = Date.now();
    const ps = spawn("powershell", ["-NoProfile", "-Command", command], {
      cwd,
      shell: false,
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";
    let killed = false;

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

    ps.on("error", (error) => {
      clearTimeout(timer);
      resolve(writeArtifact({
        execId: `exec-${Date.now()}`,
        command,
        cwd,
        timeoutSec,
        startedAt: new Date(startedAt).toISOString(),
        endedAt: new Date().toISOString(),
        durationMs: Date.now() - startedAt,
        ok: false,
        exitCode: -1,
        error: error.message,
        stdout,
        stderr,
      }));
    });

    ps.on("close", (code) => {
      clearTimeout(timer);

      const artifact = {
        execId: `exec-${Date.now()}`,
        command,
        cwd,
        timeoutSec,
        startedAt: new Date(startedAt).toISOString(),
        endedAt: new Date().toISOString(),
        durationMs: Date.now() - startedAt,
        exitCode: killed ? -9 : code,
        ok: !killed && code === 0,
        stdout,
        stderr,
      };

      resolve(writeArtifact(artifact));
    });
  });
}

module.exports = {
  runPowerShell,
  workspaceAllowed,
  containsBlockedToken,
};

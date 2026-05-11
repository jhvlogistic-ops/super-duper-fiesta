function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function parseJsonResponse(res) {
  const text = await res.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

class LocalWorkerAdapter {
  constructor(opts = {}) {
    this.baseUrl = String(opts.baseUrl || "http://localhost:3000").replace(
      /\/+$/,
      ""
    );
    this.headers = opts.apiToken
      ? { Authorization: `Bearer ${opts.apiToken}` }
      : {};
    this.pollMs = Number(opts.pollMs || 1500);
  }

  async requestJson(path, opts = {}) {
    if (!globalThis.fetch) {
      throw new Error("native_fetch_unavailable");
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      ...opts,
      headers: {
        ...this.headers,
        ...(opts.headers || {}),
      },
    });
    const data = await parseJsonResponse(res);

    if (!res.ok) {
      const err = new Error(`request_failed_${res.status}`);
      err.response = {
        status: res.status,
        data,
      };
      throw err;
    }

    return data;
  }

  async getSystemState() {
    return this.requestJson("/api/system/state");
  }

  async waitUntilAutomationOn(timeoutMs = 30000) {
    const started = Date.now();

    while (Date.now() - started < timeoutMs) {
      const state = await this.getSystemState();
      const mode = state?.execution?.mode;
      const enabled = Boolean(state?.execution?.automationEnabled);

      if (enabled && mode === "ON") {
        return {
          ok: true,
          state,
        };
      }

      await sleep(this.pollMs);
    }

    return {
      ok: false,
      reason: "automation_disabled_timeout",
    };
  }

  async execute(command, opts = {}) {
    const payload = {
      actionId: opts.actionId || "powershell.script_safe",
      source: opts.source || "supervisor",
      cwd: opts.cwd || "C:\\Users\\Jorge\\quant_lab\\server",
      command,
      timeoutSec: Number(opts.timeoutSec || 120),
      userConfirmed: Boolean(opts.userConfirmed ?? true),
      supervisorDecision: opts.supervisorDecision || "approve",
    };

    return this.requestJson("/api/execute", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  }

  async runWhenReady(command, opts = {}) {
    const gate = await this.waitUntilAutomationOn(
      Number(opts.waitTimeoutMs || 30000)
    );

    if (!gate.ok) {
      return {
        ok: false,
        phase: "blocked",
        reason: gate.reason,
      };
    }

    try {
      const result = await this.execute(command, opts);

      return {
        ok: Boolean(result?.ok),
        phase: result?.ok ? "executed" : "failed",
        review: result?.review || null,
        result: result?.result || null,
        audit: result?.audit || null,
      };
    } catch (err) {
      if (err.response?.data) {
        return {
          ok: false,
          phase: "rejected",
          reason: "server_rejected",
          details: err.response.data,
        };
      }

      return {
        ok: false,
        phase: "error",
        reason: err.message,
      };
    }
  }
}

module.exports = LocalWorkerAdapter;

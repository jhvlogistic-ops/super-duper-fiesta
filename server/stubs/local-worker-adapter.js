const axios = require("axios");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

  async getSystemState() {
    const res = await axios.get(`${this.baseUrl}/api/system/state`, {
      headers: this.headers,
    });
    return res.data;
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

    const res = await axios.post(`${this.baseUrl}/api/execute`, payload, {
      headers: this.headers,
    });

    return res.data;
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

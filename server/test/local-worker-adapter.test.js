const assert = require("node:assert/strict");
const { afterEach, test } = require("node:test");

const LocalWorkerAdapter = require("../stubs/local-worker-adapter");

const originalFetch = globalThis.fetch;

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function mockFetch(responses) {
  const calls = [];
  globalThis.fetch = async (url, opts = {}) => {
    calls.push({ url: String(url), opts });
    const next = responses.shift();
    if (!next) {
      throw new Error("unexpected_fetch_call");
    }
    return jsonResponse(next.body, next.status || 200);
  };
  return calls;
}

afterEach(() => {
  globalThis.fetch = originalFetch;
});

test("runWhenReady executes when automation is ON", async () => {
  const calls = mockFetch([
    {
      body: {
        execution: {
          automationEnabled: true,
          mode: "ON",
        },
      },
    },
    {
      body: {
        ok: true,
        review: {
          status: "approved",
        },
        result: {
          ok: true,
          exitCode: 0,
        },
        audit: {
          type: "execution_result",
        },
      },
    },
  ]);

  const worker = new LocalWorkerAdapter({ pollMs: 1 });
  const result = await worker.runWhenReady(".\\scripts\\estimate_pi.ps1", {
    waitTimeoutMs: 10,
  });

  assert.equal(result.ok, true);
  assert.equal(result.phase, "executed");
  assert.equal(result.review.status, "approved");
  assert.equal(result.result.exitCode, 0);
  assert.equal(result.audit.type, "execution_result");
  assert.equal(calls[1].opts.method, "POST");
});

test("runWhenReady blocks before execution when automation is OFF", async () => {
  mockFetch([
    {
      body: {
        execution: {
          automationEnabled: false,
          mode: "OFF",
        },
      },
    },
  ]);

  const worker = new LocalWorkerAdapter({ pollMs: 1 });
  const result = await worker.runWhenReady(".\\scripts\\estimate_pi.ps1", {
    waitTimeoutMs: 1,
  });

  assert.equal(result.ok, false);
  assert.equal(result.phase, "blocked");
  assert.equal(result.reason, "automation_disabled_timeout");
});

test("runWhenReady reports server rejection details", async () => {
  mockFetch([
    {
      body: {
        execution: {
          automationEnabled: true,
          mode: "ON",
        },
      },
    },
    {
      status: 400,
      body: {
        ok: false,
        review: {
          approvalPolicy: "hard_block",
          status: "blocked",
          reason: "workspace_not_allowed",
        },
      },
    },
  ]);

  const worker = new LocalWorkerAdapter({ pollMs: 1 });
  const result = await worker.runWhenReady(".\\scripts\\estimate_pi.ps1", {
    cwd: "C:\\Windows\\System32",
    waitTimeoutMs: 10,
  });

  assert.equal(result.ok, false);
  assert.equal(result.phase, "rejected");
  assert.equal(result.reason, "server_rejected");
  assert.equal(result.details.review.status, "blocked");
  assert.equal(result.details.review.reason, "workspace_not_allowed");
});

test("runWhenReady reports failed execution results", async () => {
  mockFetch([
    {
      body: {
        execution: {
          automationEnabled: true,
          mode: "ON",
        },
      },
    },
    {
      body: {
        ok: false,
        review: {
          status: "approved",
        },
        result: {
          ok: false,
          exitCode: -9,
          error: "timeout_killed",
        },
        audit: {
          type: "execution_result",
        },
      },
    },
  ]);

  const worker = new LocalWorkerAdapter({ pollMs: 1 });
  const result = await worker.runWhenReady("Start-Sleep -Seconds 5", {
    timeoutSec: 1,
    waitTimeoutMs: 10,
  });

  assert.equal(result.ok, false);
  assert.equal(result.phase, "failed");
  assert.equal(result.result.exitCode, -9);
  assert.equal(result.result.error, "timeout_killed");
  assert.equal(result.audit.type, "execution_result");
});

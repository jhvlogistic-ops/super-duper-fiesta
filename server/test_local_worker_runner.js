const LocalWorkerAdapter = require("./stubs/local-worker-adapter");

async function main() {
  const worker = new LocalWorkerAdapter({
    baseUrl: "http://localhost:3000",
    pollMs: 1000,
  });

  const result = await worker.runWhenReady(".\\scripts\\estimate_pi.ps1", {
    actionId: "powershell.script_safe",
    cwd: "C:\\Users\\Jorge\\quant_lab\\server",
    timeoutSec: 120,
    userConfirmed: true,
    supervisorDecision: "approve",
    waitTimeoutMs: 15000,
  });

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const port = process.env.REDRAFT_LOCAL_PORT ?? "5173";
if (!/^\d{1,5}$/.test(port) || Number(port) < 1024 || Number(port) > 65535) {
  throw new Error("REDRAFT_LOCAL_PORT must be a valid unprivileged TCP port.");
}
const child = spawn(
  process.execPath,
  ["scripts/run-framework.mjs", "dev", "--host", "127.0.0.1", "--port", port],
  {
    cwd: root,
    stdio: "inherit",
    env: process.env,
  },
);

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => child.kill(signal));
}
child.on("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exitCode = code ?? 1;
});

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
process.chdir(root);
const config = "dist/server/wrangler.json";
const migration = "drizzle/0000_spotty_patriot.sql";
const wrangler = "node_modules/wrangler/bin/wrangler.js";

if (!existsSync(config)) {
  throw new Error("Build first with `pnpm run build` to generate the local D1 config.");
}
if (!existsSync(wrangler) || !existsSync(migration)) {
  throw new Error("Install dependencies and keep the runtime migration in drizzle/.");
}

const common = [
  wrangler,
  "d1",
  "execute",
  "site-creator-d1",
  "--local",
  "--config",
  config,
  "--persist-to",
  ".wrangler/state",
  "--json",
];
const query = spawnSync(
  process.execPath,
  [...common, "--command", "SELECT name FROM sqlite_master WHERE type='table' AND name='game_runs'"],
  { encoding: "utf8" },
);
if (query.error) throw query.error;
if (query.status !== 0) {
  process.stderr.write(query.stderr);
  process.exit(query.status ?? 1);
}
let existing;
try {
  existing = JSON.parse(query.stdout).some((result) =>
    result.results?.some((row) => row.name === "game_runs"),
  );
} catch {
  throw new Error("Could not read the local D1 schema check response.");
}
if (existing) {
  console.log("Local D1 already has the REDRAFT runtime schema.");
  process.exit(0);
}

const applied = spawnSync(
  process.execPath,
  [...common, "--file", migration],
  { encoding: "utf8" },
);
process.stdout.write(applied.stdout);
process.stderr.write(applied.stderr);
if (applied.error) throw applied.error;
if (applied.status !== 0) process.exit(applied.status ?? 1);
console.log("Initialized local D1 from the runtime migration.");

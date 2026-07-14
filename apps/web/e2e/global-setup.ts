import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);

/** The unit harness isolates per-IP limiter counters per test
 * (conftest.py `flushdb`); an e2e battery registers many accounts from one
 * IP, so the same hygiene applies here — but scoped to the `rl:*` limiter
 * keys only. The limiter itself stays fully active during every test:
 * fresh-signup.spec.ts still proves the 400/duplicate path against it. */
export default async function globalSetup(): Promise<void> {
  const host = process.env.NUR_REDIS_HOST ?? "127.0.0.1";
  const port = process.env.NUR_REDIS_PORT ?? "16379";
  try {
    const { stdout } = await run("redis-cli", ["-h", host, "-p", port, "--scan", "--pattern", "rl:*"]);
    const keys = stdout.split("\n").map(row => row.trim()).filter(Boolean);
    if (keys.length) await run("redis-cli", ["-h", host, "-p", port, "del", ...keys]);
  } catch {
    // Without redis-cli the battery simply runs against live limiter state.
  }
}

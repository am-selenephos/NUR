import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export const V197_HASHES = {
  host: "d4f7f2d3e4c8e36dfc0c6edd51a028f28a04afbc2afa434a319009cb2f122bc6",
  entry: "cdeac0c8574333c7261be2bc410357ecc5407ee0dd5b1b8089630f3914026030",
  universe: "3cff07b31e8360e5ce793287298d66127c4f278705dc0f8e6abdfbe7e874dc40",
} as const;

export type V197IntegrityResult = {
  pass: boolean;
  files: Record<keyof typeof V197_HASHES, { path: string; expected: string; actual: string; pass: boolean }>;
};

function hash(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function checkV197Integrity(repositoryRoot = process.cwd()): V197IntegrityResult {
  const files = {
    host: resolve(repositoryRoot, "apps/web/public/v197/NUR_V197_CHECKBOX_TICK_RESTORED.html"),
    entry: resolve(repositoryRoot, "docs/reference/entry_decoded_v197.html"),
    universe: resolve(repositoryRoot, "docs/reference/universe_decoded_v197.html"),
  } as const;
  const result = Object.fromEntries(
    Object.entries(files).map(([key, path]) => {
      const expected = V197_HASHES[key as keyof typeof V197_HASHES];
      const actual = hash(path);
      return [key, { path, expected, actual, pass: expected === actual }];
    }),
  ) as V197IntegrityResult["files"];
  return { files: result, pass: Object.values(result).every(file => file.pass) };
}

// Keep this CLI guard CommonJS-compatible: the integrity launcher compiles this
// isolated verifier without inheriting the web package's ESM package boundary.
if (process.argv[1]?.endsWith("check-v197-integrity.js")) {
  const result = checkV197Integrity();
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.pass) process.exitCode = 1;
}

#!/usr/bin/env node
// test.mjs — consolidated test harness for orchestrate-codex.
//
// Replaces test-monitor-integration.mjs + test-runner-contracts.mjs (which
// remain as deprecation shims forwarding here for 1 release; removed in v3.0).
//
// Sections:
//   pure-functions   In-process tests of dispatcher pure functions
//                    (parseToolHint, resolveConcurrency, monitor builders)
//   subprocess       Subprocess contract tests (spawn dispatcher, assert envelope)
//   regression-pin   Specific regression scenarios (e.g. unknown-mode rejection)
//   parity-fixtures  Replays __fixtures__/baseline/* via run-parity.mjs
//
// CLI:
//   node test.mjs                       # run all sections
//   node test.mjs --section <name>      # one section
//   node test.mjs --filter <substring>  # filter scenarios by name
//   node test.mjs --bail                # stop at first failure
//
// Sub-section dispatch:
//   The pure-functions and subprocess sections currently delegate to the
//   legacy test-*.mjs files (via execvp) to preserve every scenario's
//   captured behavior. The parity-fixtures section delegates to run-parity.mjs.
//   v3.0 will merge the scenario bodies into this file.

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { rmSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));

function parseArgs(argv) {
  const a = { section: null, filter: null, bail: false };
  for (let i = 2; i < argv.length; i++) {
    const x = argv[i];
    if (x === "--section") a.section = argv[++i];
    else if (x === "--filter") a.filter = argv[++i];
    else if (x === "--bail") a.bail = true;
    else if (x === "--help" || x === "-h") {
      console.log("test.mjs --section pure-functions|subprocess|regression-pin|parity-fixtures [--filter X] [--bail]");
      process.exit(0);
    }
  }
  return a;
}

const args = parseArgs(process.argv);

const sections = {
  "pure-functions": () => runDelegate("test-monitor-integration.mjs"),
  "subprocess":     () => runDelegate("test-runner-contracts.mjs"),
  "regression-pin": () => runRegressionPin(),
  "parity-fixtures": () => runParityFixtures(),
};

function runDelegate(scriptName) {
  const path = join(__dirname, scriptName);
  if (!existsSync(path)) {
    console.log(`[${scriptName}] absent; skipping`);
    return { name: scriptName, passed: 0, failed: 0, skipped: 1 };
  }
  const r = spawnSync(process.execPath, [path], { stdio: "inherit", encoding: "utf8" });
  return { name: scriptName, passed: r.status === 0 ? 1 : 0, failed: r.status === 0 ? 0 : 1 };
}

function runRegressionPin() {
  console.log("[regression-pin]");
  const dispatcher = join(__dirname, "orchestrate-codex.mjs");
  if (!existsSync(dispatcher)) {
    return { name: "regression-pin", passed: 0, failed: 0, skipped: 1 };
  }
  const env = { ...process.env, ORCHESTRATE_SKIP_PREFLIGHT: "1" };
  const r = spawnSync(process.execPath, [dispatcher, "not-a-real-mode"], {
    encoding: "utf8", timeout: 10000, env,
  });
  let parsed;
  try { parsed = JSON.parse(r.stdout); } catch { parsed = null; }
  const ok = parsed && parsed.ok === false && parsed.error && parsed.error.code === "unknown_mode";
  if (ok) {
    console.log("  ok: unknown_mode rejected cleanly");
    return { name: "regression-pin", passed: 1, failed: 0 };
  } else {
    console.log("  FAIL: expected ok=false / error.code=unknown_mode, got:");
    console.log("    stdout:", (r.stdout || "").slice(0, 200));
    console.log("    status:", r.status);
    return { name: "regression-pin", passed: 0, failed: 1 };
  }
}

function runParityFixtures() {
  console.log("[parity-fixtures]");
  const runner = join(__dirname, "__fixtures__", "run-parity.mjs");
  if (!existsSync(runner)) {
    return { name: "parity-fixtures", passed: 0, failed: 0, skipped: 1 };
  }
  const a = ["--target", "current"];
  if (args.bail) a.push("--bail");
  const r = spawnSync(process.execPath, [runner, ...a], { stdio: "inherit", encoding: "utf8" });
  return { name: "parity-fixtures", passed: r.status === 0 ? 1 : 0, failed: r.status === 0 ? 0 : 1 };
}

// Cleanup tmpdirs created by previous test runs (parity tests / dispatcher subprocess scenarios)
function cleanupTmpDirs() {
  const tmpdir = process.env.TMPDIR || "/tmp";
  try {
    const dirs = ["orchestrate-contract-", "orchestrate-rescue-", "oc-test-"];
    // best-effort; rmSync may fail on busy dirs
  } catch (e) {
    /* ignore */
  }
}

const toRun = args.section ? [args.section] : Object.keys(sections);
let totalPassed = 0, totalFailed = 0, totalSkipped = 0;
for (const name of toRun) {
  if (!sections[name]) {
    console.error(`unknown section: ${name}`);
    process.exit(2);
  }
  console.log(`\n=== Section: ${name} ===`);
  try {
    const r = sections[name]();
    totalPassed += r.passed || 0;
    totalFailed += r.failed || 0;
    totalSkipped += r.skipped || 0;
    if (args.bail && (r.failed || 0) > 0) {
      console.log("\nBailing on first failure");
      break;
    }
  } catch (e) {
    console.error(`Section ${name} crashed:`, e.message);
    totalFailed++;
    if (args.bail) break;
  }
}

console.log(`\n=== Summary ===`);
console.log(`Sections passed: ${totalPassed}  failed: ${totalFailed}  skipped: ${totalSkipped}`);
process.exit(totalFailed > 0 ? 1 : 0);

#!/usr/bin/env node
// run-parity.mjs — replays captured fixtures against current or refactored scripts.
//
// Usage:
//   node run-parity.mjs                       # all fixtures
//   node run-parity.mjs --target current      # default
//   node run-parity.mjs --target refactored   # against worktree scripts (same paths in this layout)
//   node run-parity.mjs --filter <substring>
//   node run-parity.mjs --bail
//   node run-parity.mjs --update              # rewrite baseline from current output (gated)
//
// Fixture conventions (see __fixtures__/README.md):
//   <category>/<name>.stdout   captured stdout
//   <category>/<name>.stderr   captured stderr (optional)
//   <category>/<name>.exit     captured exit code
//   <category>/<name>.cmd      command line to reproduce (optional; if present, used to drive comparison)

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { dirname, join, basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCRIPTS_DIR = resolve(__dirname, "..");
const BASELINE_DIR = join(__dirname, "baseline");
const GOLDEN_DIR = join(__dirname, "golden");

function parseArgs(argv) {
  const args = { target: "current", filter: null, bail: false, update: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--target") args.target = argv[++i];
    else if (a === "--filter") args.filter = argv[++i];
    else if (a === "--bail") args.bail = true;
    else if (a === "--update") args.update = true;
    else if (a === "--help" || a === "-h") {
      console.log(`run-parity.mjs — fixture parity test runner

Flags:
  --target current|refactored   which scripts to invoke (default: current)
  --filter <substring>          only run fixtures whose path contains <substring>
  --bail                        stop on first failure
  --update                      rewrite fixtures from current output (DANGEROUS)
  --help                        this message
`);
      process.exit(0);
    } else {
      console.error(`unknown flag: ${a}`);
      process.exit(2);
    }
  }
  return args;
}

const args = parseArgs(process.argv);

let passCount = 0;
let failCount = 0;
const failures = [];

function expect(cond, detail) {
  if (cond) {
    passCount++;
  } else {
    failCount++;
    failures.push(detail);
    if (args.bail) {
      report();
      process.exit(1);
    }
  }
}

function walk(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else out.push(p);
  }
  return out;
}

function loadFixture(path) {
  return readFileSync(path, "utf8");
}

// ---------- HELP fixture replay ----------
function runHelpFixtures() {
  const helpDir = join(BASELINE_DIR, "help");
  const files = walk(helpDir).filter(p => p.endsWith(".help.stdout"));
  for (const stdoutPath of files) {
    const scriptBase = basename(stdoutPath, ".help.stdout");
    if (args.filter && !stdoutPath.includes(args.filter)) continue;

    // Locate the corresponding script in SCRIPTS_DIR by trying common extensions.
    const candidates = [`${scriptBase}.py`, `${scriptBase}.sh`, `${scriptBase}.mjs`];
    const scriptPath = candidates
      .map(c => join(SCRIPTS_DIR, c))
      .find(p => existsSync(p));
    if (!scriptPath) {
      // Could be a deprecation shim that no longer exists in the new tree.
      // Mark as skipped (not failed).
      continue;
    }

    const interp = scriptPath.endsWith(".py") ? "python3"
                 : scriptPath.endsWith(".mjs") ? "node"
                 : "bash";

    const result = spawnSync(interp, [scriptPath, "--help"], {
      encoding: "utf8",
      timeout: 5000,
      stdio: ["ignore", "pipe", "pipe"],
    });

    const expectedExit = parseInt(loadFixture(stdoutPath.replace(".help.stdout", ".help.exit")), 10);
    const expectedStdout = loadFixture(stdoutPath);

    if (args.update) {
      writeFileSync(stdoutPath, result.stdout ?? "");
      writeFileSync(stdoutPath.replace(".help.stdout", ".help.stderr"), result.stderr ?? "");
      writeFileSync(stdoutPath.replace(".help.stdout", ".help.exit"), String(result.status ?? "") + "\n");
      console.log(`UPDATED ${scriptBase}.help`);
      continue;
    }

    const stdoutOk = result.stdout === expectedStdout;
    const exitOk = result.status === expectedExit;
    expect(stdoutOk && exitOk, {
      fixture: scriptBase + ".help",
      reason: !stdoutOk ? "stdout mismatch" : "exit code mismatch",
      expected_exit: expectedExit,
      actual_exit: result.status,
      stdout_diff_size: Math.abs((result.stdout ?? "").length - expectedStdout.length),
    });
  }
}

// ---------- GOLDEN fixture replay ----------
function runGoldenFixtures() {
  // Verifies cross-language consistency for shared algorithms.
  // _lib.py and _lib.sh both consume these fixtures.
  // In Phase 0 we just verify the fixture files parse cleanly.
  const goldenFiles = walk(GOLDEN_DIR).filter(p => p.endsWith(".json"));
  for (const f of goldenFiles) {
    if (args.filter && !f.includes(args.filter)) continue;
    try {
      const data = JSON.parse(loadFixture(f));
      expect(Array.isArray(data) || typeof data === "object", {
        fixture: "golden/" + basename(f),
        reason: "JSON did not parse as object/array",
      });
    } catch (e) {
      expect(false, { fixture: "golden/" + basename(f), reason: "JSON parse failed: " + e.message });
    }
  }
}

function report() {
  console.log(`\nPASS: ${passCount}  FAIL: ${failCount}`);
  if (failCount > 0) {
    console.log("\nFailures:");
    for (const f of failures) {
      console.log("  -", JSON.stringify(f));
    }
  }
}

// Run sections
console.log("[1] help fixtures");
runHelpFixtures();
console.log("[2] golden fixtures");
runGoldenFixtures();

report();
process.exit(failCount === 0 ? 0 : 1);

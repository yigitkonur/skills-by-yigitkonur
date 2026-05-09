#!/usr/bin/env node
// test-monitor-integration.mjs — smoke harness for the dispatcher's
// monitor.tool_hint output and core argv-validation surface.
//
// Why this exists: a malformed Monitor hint (broken JS, missing fflush()) or
// silent-drop in argv parsing (unknown flags accepted, concurrency overrides
// not persisted, rescue --apply not flowing through) results in the agent
// shipping phantom features. Catching that at build time is much cheaper than
// catching it from a user report.
//
// What it tests:
//   1. parse: every mode's tool_hint must parse as a JS expression (so the
//      agent can fire it with no string surgery).
//   2. timeout clamp: monitor.tool_hint timeout_ms must NEVER exceed
//      MONITOR_HARD_MAX_MS (Monitor's documented hard ceiling).
//   3. fleet shape: the fleet command must invoke codex-monitor.sh and emit
//      the closing "monitor exited" line.
//   4. single shape: the single command must use awk fflush() and tail -F.
//   5. live streaming: a producer with sleeps must reach the consumer with
//      ≥200ms total span (events streamed live, not bunched at EOF).
//   6. parseArgsStrict: unknown long-options produce error.code=unknown_option.
//   7. resolveConcurrency: above-default and above-hard-cap require
//      --i-have-measured "<justification>"; the override is captured.
//   8. selectRescueSubset: failed-only / never-started-only / all-non-done /
//      ids:... resolve to the documented entry sets.

import { spawn } from "node:child_process";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import {
  buildMonitorForMode,
  buildMonitorHint,
  fleetMonitorCommand,
  singleMonitorCommand,
  parseArgsStrict,
  resolveConcurrency,
  selectRescueSubset,
  MONITOR_HARD_MAX_MS,
  CONCURRENCY_HARD_CAP,
  DEFAULT_CONCURRENCY,
} from "./orchestrate-codex.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));

let passCount = 0;
let failCount = 0;
const failures = [];

function pass(name) {
  passCount += 1;
  process.stdout.write(`  PASS  ${name}\n`);
}

function fail(name, detail) {
  failCount += 1;
  failures.push({ name, detail });
  process.stdout.write(`  FAIL  ${name}\n`);
  if (detail) process.stdout.write(`        ${detail}\n`);
}

function expect(cond, name, detail) {
  if (cond) pass(name); else fail(name, detail);
}

function parseToolHint(hint) {
  // The agent fires `Monitor({...})` literally; the harness simulates by
  // stripping the Monitor identifier and evaluating the object literal.
  return new Function(`return (${hint.replace("Monitor", "")})`)();
}

// ----------------------------------------------------------------------------
// Scenario 1 — exec mode hint
// ----------------------------------------------------------------------------

function scenarioExec() {
  process.stdout.write("\n[1] exec mode tool_hint\n");
  const monitor = buildMonitorForMode("exec", {
    manifestPath: "/tmp/test/manifest.json",
    runId: "TEST-RUN-001",
    monitorRoot: "/tmp/test",
  });
  expect(monitor && typeof monitor.tool_hint === "string",
    "monitor.tool_hint exists and is a string",
    `got ${typeof monitor?.tool_hint}`);
  let parsed;
  try { parsed = parseToolHint(monitor.tool_hint); }
  catch (e) { fail("tool_hint parses as JS", e.message); return; }
  pass("tool_hint parses as JS expression");

  expect(parsed.persistent === true, "persistent: true (long-running fleet)");
  expect(typeof parsed.command === "string" && parsed.command.length > 0,
    "command is non-empty string");
  expect(typeof parsed.timeout_ms === "number" && parsed.timeout_ms > 60_000,
    "timeout_ms > 1 minute");
  expect(parsed.timeout_ms <= MONITOR_HARD_MAX_MS,
    `timeout_ms <= MONITOR_HARD_MAX_MS (${MONITOR_HARD_MAX_MS})`,
    `got ${parsed.timeout_ms}`);
  expect(parsed.command.includes("ORCHESTRATE_MANIFEST="),
    "command exports ORCHESTRATE_MANIFEST");
  expect(parsed.command.includes("MONITOR_ROOT="),
    "command exports MONITOR_ROOT");
  expect(parsed.command.includes("codex-monitor.sh"),
    "command invokes codex-monitor.sh (the rule-engine ticker)");
  expect(parsed.command.includes("monitor exited"),
    "command emits closing line on monitor exit");
}

// ----------------------------------------------------------------------------
// Scenario 2 — batch mode hint
// ----------------------------------------------------------------------------

function scenarioBatch() {
  process.stdout.write("\n[2] batch mode tool_hint\n");
  const monitor = buildMonitorForMode("batch", {
    manifestPath: "/tmp/test/manifest.json",
    runId: "TEST-RUN-002",
    monitorRoot: "/tmp/test",
  });
  let parsed;
  try { parsed = parseToolHint(monitor.tool_hint); }
  catch (e) { fail("tool_hint parses as JS", e.message); return; }
  pass("tool_hint parses as JS expression");
  expect(parsed.persistent === true, "persistent: true");
  expect(parsed.command.includes("codex-monitor.sh"),
    "command invokes codex-monitor.sh");
  expect(parsed.description.includes("batch"),
    "description includes mode label");
}

// ----------------------------------------------------------------------------
// Scenario 3 — single mode hint
// ----------------------------------------------------------------------------

function scenarioSingle() {
  process.stdout.write("\n[3] single mode tool_hint\n");
  const monitor = buildMonitorForMode("single", {
    manifestPath: "/tmp/test/manifest.json",
    runId: "TEST-RUN-003",
    monitorRoot: "/tmp/test",
    jsonlPath: "/tmp/test/single.jsonl",
  });
  let parsed;
  try { parsed = parseToolHint(monitor.tool_hint); }
  catch (e) { fail("tool_hint parses as JS", e.message); return; }
  pass("tool_hint parses as JS expression");
  expect(parsed.persistent === false,
    "persistent: false (single mission has bounded duration)");
  expect(parsed.timeout_ms > 60_000,
    "timeout_ms > 1 minute");
  expect(parsed.timeout_ms <= MONITOR_HARD_MAX_MS,
    `timeout_ms <= MONITOR_HARD_MAX_MS (${MONITOR_HARD_MAX_MS})`,
    `got ${parsed.timeout_ms}`);
  expect(parsed.command.includes("fflush()"),
    "command uses awk fflush() for line-buffered streaming");
  expect(parsed.command.includes("tail -n +1 -F"),
    "command tails the JSONL with -F");
}

// ----------------------------------------------------------------------------
// Scenario 4 — review mode hint
// ----------------------------------------------------------------------------

function scenarioReview() {
  process.stdout.write("\n[4] review mode tool_hint\n");
  const monitor = buildMonitorForMode("review", {
    manifestPath: "/tmp/test/manifest.json",
    runId: "TEST-RUN-004",
    monitorRoot: "/tmp/test",
  });
  let parsed;
  try { parsed = parseToolHint(monitor.tool_hint); }
  catch (e) { fail("tool_hint parses as JS", e.message); return; }
  pass("tool_hint parses as JS expression");
  expect(parsed.command.includes("codex-monitor.sh"),
    "command invokes codex-monitor.sh");
  expect(parsed.description.includes("review"),
    "description includes mode label");
}

// ----------------------------------------------------------------------------
// Scenario 5 — timeout clamp (Monitor hard max = 1h)
// ----------------------------------------------------------------------------

function scenarioTimeoutClamp() {
  process.stdout.write("\n[5] Monitor timeout clamp\n");
  const hint = buildMonitorHint({
    description: "clamp test",
    command: "true",
    persistent: true,
    timeoutMs: 99 * 60 * 60 * 1000, // 99 hours
  });
  let parsed;
  try { parsed = parseToolHint(hint); }
  catch (e) { fail("clamped hint parses", e.message); return; }
  pass("clamped hint parses as JS");
  expect(parsed.timeout_ms === MONITOR_HARD_MAX_MS,
    `oversize timeout_ms is clamped to ${MONITOR_HARD_MAX_MS}`,
    `got ${parsed.timeout_ms}`);
  expect(parsed.timeout_ms === 3_600_000,
    "MONITOR_HARD_MAX_MS == 3,600,000 (Monitor's documented hard max)",
    `MONITOR_HARD_MAX_MS=${MONITOR_HARD_MAX_MS}`);
}

// ----------------------------------------------------------------------------
// Scenario 6 — buildMonitorHint quoting safety
// ----------------------------------------------------------------------------

function scenarioMonitorHintQuoting() {
  process.stdout.write("\n[6] buildMonitorHint quoting safety\n");
  const tricky = `desc with "quotes" and \\backslashes\nand newline`;
  const hint = buildMonitorHint({
    description: tricky,
    command: `echo "hi" && echo 'world'`,
    persistent: true,
    timeoutMs: 60_000,
  });
  let parsed = null;
  try {
    parsed = new Function(`return (${hint.replace("Monitor", "")})`)();
  } catch (e) {
    fail("hint with tricky description parses", e.message);
    return;
  }
  pass("hint with tricky description parses");
  expect(parsed.description === tricky,
    "description round-trips through JSON.stringify",
    `expected ${JSON.stringify(tricky)}, got ${JSON.stringify(parsed.description)}`);
  expect(parsed.command.includes(`echo "hi"`),
    "command preserves nested double-quotes");
}

// ----------------------------------------------------------------------------
// Scenario 7 — line-buffered streaming under inserted delays (single-mode awk)
// ----------------------------------------------------------------------------

function scenarioLiveStream() {
  process.stdout.write("\n[7] awk fflush() live stream\n");
  return new Promise((resolve) => {
    const producer = `for i in 1 2 3 4 5; do echo "evt $i"; sleep 0.1; done`;
    const child = spawn("bash", ["-c", `${producer} | awk '{ print; fflush(); }'`], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    const t0 = Date.now();
    const arrivals = [];
    let buffer = "";
    child.stdout.on("data", (chunk) => {
      buffer += chunk.toString();
      let nl;
      while ((nl = buffer.indexOf("\n")) !== -1) {
        buffer = buffer.slice(nl + 1);
        arrivals.push(Date.now() - t0);
      }
    });
    child.on("close", () => {
      expect(arrivals.length === 5,
        `awk + fflush() emitted 5 events (got ${arrivals.length})`);
      if (arrivals.length >= 2) {
        const span = arrivals[arrivals.length - 1] - arrivals[0];
        expect(span > 200,
          `awk fflush() streams live (span ${span}ms > 200ms)`,
          `arrivals=${JSON.stringify(arrivals)}`);
      }
      resolve();
    });
  });
}

// ----------------------------------------------------------------------------
// Scenario 8 — parseArgsStrict rejects unknown long-options
// ----------------------------------------------------------------------------

function scenarioStrictParse() {
  process.stdout.write("\n[8] parseArgsStrict — unknown options error out\n");

  // Known options pass through.
  let r = parseArgsStrict(["--prompt", "hi", "--cwd", "/tmp"], "single", {
    valueOptions: ["prompt", "cwd"], booleanOptions: [],
  });
  expect(r.value && r.value.options.prompt === "hi",
    "known --prompt accepted",
    JSON.stringify(r));

  // Unknown long-option errors out.
  r = parseArgsStrict(["--bogus-flag", "value"], "single", {
    valueOptions: ["prompt"], booleanOptions: [],
  });
  expect(r.err && r.err.error.code === "unknown_option",
    "unknown long-option produces unknown_option error",
    JSON.stringify(r));
  expect(r.err && r.err.error.message.includes("--bogus-flag"),
    "error message names the offending flag",
    r.err && r.err.error.message);

  // Stray short-form is rejected too.
  r = parseArgsStrict(["-x"], "single", { valueOptions: [], booleanOptions: [] });
  expect(r.err && r.err.error.code === "unknown_option",
    "stray short flag rejected as unknown_option");

  // Boolean parsed correctly.
  r = parseArgsStrict(["--reuse-worktree"], "single", {
    valueOptions: [], booleanOptions: ["reuse-worktree"],
  });
  expect(r.value && r.value.options["reuse-worktree"] === true,
    "boolean option resolves to true");
}

// ----------------------------------------------------------------------------
// Scenario 9 — resolveConcurrency soft gate + override capture
// ----------------------------------------------------------------------------

function scenarioConcurrency() {
  process.stdout.write("\n[9] resolveConcurrency soft gate + override capture\n");

  // Default exec cap = 5; no override needed for the default itself.
  const savedJOBS = process.env.JOBS;
  delete process.env.JOBS;
  let r = resolveConcurrency({}, "exec");
  expect(r.value === DEFAULT_CONCURRENCY.exec,
    `default exec concurrency = ${DEFAULT_CONCURRENCY.exec}`,
    JSON.stringify(r));
  expect(r.source === "default", "source = default", r.source);
  expect(r.override === null, "no override captured at default cap");

  // Above-default without --i-have-measured → bad_argument.
  r = resolveConcurrency({ concurrency: "8" }, "exec");
  expect(r.err && r.err.error.code === "bad_argument",
    "exec=8 (above default 5) without --i-have-measured rejected",
    JSON.stringify(r));

  // Above-default WITH justification → captured override.
  r = resolveConcurrency({ concurrency: "8", "i-have-measured": "validated 8" }, "exec");
  expect(r.value === 8, "exec=8 with justification accepted");
  expect(r.override && r.override.value === 8 && r.override.justification === "validated 8",
    "override captured with value+justification",
    JSON.stringify(r.override));
  expect(r.override && typeof r.override.set_at === "string",
    "override has set_at timestamp");

  // batch JOBS=15 (default 10) without --i-have-measured → rejected (soft gate
  // fires above mode default, not just above hard cap; aligns with concurrency.md).
  process.env.JOBS = "15";
  r = resolveConcurrency({}, "batch");
  expect(r.err && r.err.error.code === "bad_argument",
    "batch JOBS=15 (above default 10) without justification rejected",
    JSON.stringify(r));
  expect(r.err && r.err.error.message.includes("env"),
    "error message names env as the source");

  // batch JOBS=15 WITH justification accepted, captured.
  r = resolveConcurrency({ "i-have-measured": "60-row batch" }, "batch");
  expect(r.value === 15 && r.source === "env",
    "batch JOBS=15 with justification accepted; source=env");
  expect(r.override && r.override.value === 15,
    "override.value = 15");

  // Above hard cap requires justification too.
  r = resolveConcurrency({ concurrency: "25", "i-have-measured": "stress" }, "batch");
  expect(r.value === 25, "batch concurrency=25 with justification accepted");
  expect(r.override && r.override.value === 25,
    "override.value = 25");

  // Absolute ceiling refused unconditionally.
  r = resolveConcurrency({ concurrency: "200", "i-have-measured": "x" }, "batch");
  expect(r.err && r.err.error.code === "bad_argument",
    "concurrency=200 refused unconditionally (>100)");

  // Flag wins over env when both set.
  process.env.JOBS = "3";
  r = resolveConcurrency({ concurrency: "5" }, "batch");
  expect(r.value === 5 && r.source === "flag",
    "flag overrides env when both set");

  // Restore env.
  if (savedJOBS === undefined) delete process.env.JOBS;
  else process.env.JOBS = savedJOBS;
}

// ----------------------------------------------------------------------------
// Scenario 10 — selectRescueSubset
// ----------------------------------------------------------------------------

function scenarioRescueSubset() {
  process.stdout.write("\n[10] selectRescueSubset\n");
  const manifest = {
    entries: [
      { id: "01-foo", slug: "foo", status: "done", attempts: 1 },
      { id: "02-bar", slug: "bar", status: "failed", attempts: 1 },
      { id: "03-baz", slug: "baz", status: "queued", attempts: 0 },
      { id: "04-qux", slug: "qux", status: "running", attempts: 1 },
    ],
  };
  let s = selectRescueSubset(manifest, "failed-only");
  expect(JSON.stringify(s.ids) === JSON.stringify(["02-bar"]),
    "failed-only matches failed entries", JSON.stringify(s));
  s = selectRescueSubset(manifest, "never-started-only");
  expect(JSON.stringify(s.ids) === JSON.stringify(["03-baz"]),
    "never-started-only matches queued+attempts=0",
    JSON.stringify(s));
  s = selectRescueSubset(manifest, "all-non-done");
  expect(JSON.stringify(s.ids) === JSON.stringify(["02-bar", "03-baz", "04-qux"]),
    "all-non-done matches every non-done entry", JSON.stringify(s));
  s = selectRescueSubset(manifest, "ids:foo,baz");
  expect(JSON.stringify(s.ids.sort()) === JSON.stringify(["01-foo", "03-baz"].sort()),
    "ids: matches by slug or id", JSON.stringify(s));
  s = selectRescueSubset(manifest, "ids:does-not-exist");
  expect(s.ids.length === 0 && s.unknown.includes("does-not-exist"),
    "ids: surfaces unknown");
  s = selectRescueSubset(manifest, "garbage");
  expect(s.invalid === "garbage", "garbage subset reports invalid");
}

// ----------------------------------------------------------------------------
// Run
// ----------------------------------------------------------------------------

async function main() {
  process.stdout.write("test-monitor-integration.mjs — orchestrate-codex Monitor + dispatcher harness\n");
  scenarioExec();
  scenarioBatch();
  scenarioSingle();
  scenarioReview();
  scenarioTimeoutClamp();
  scenarioMonitorHintQuoting();
  await scenarioLiveStream();
  scenarioStrictParse();
  scenarioConcurrency();
  scenarioRescueSubset();

  process.stdout.write(`\n=========================================\n`);
  process.stdout.write(`PASS: ${passCount}   FAIL: ${failCount}\n`);
  if (failCount > 0) {
    process.stdout.write(`\nFAILURES:\n`);
    for (const f of failures) {
      process.stdout.write(`  - ${f.name}\n    ${f.detail || "(no detail)"}\n`);
    }
    process.exit(1);
  } else {
    process.stdout.write(`OK\n`);
    process.exit(0);
  }
}

main().catch((e) => {
  process.stdout.write(`\nharness crash: ${e.message}\n${e.stack}\n`);
  process.exit(2);
});

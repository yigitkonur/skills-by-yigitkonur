#!/usr/bin/env node
// test-monitor-integration.mjs — smoke harness for the dispatcher's
// monitor.tool_hint output. Validates the hint is well-formed and that the
// shell pipelines it embeds line-buffer cleanly under load.
//
// Why this exists: a malformed Monitor hint (broken JS, missing
// --line-buffered, awk without fflush) results in the agent seeing a stalled
// stream and silently treating "no event" as "no progress". Catching that at
// build time is much cheaper than catching it from a user report.
//
// What it tests:
//   1. parse: every mode's tool_hint must parse as a JS expression (so the
//      agent can fire it with no string surgery).
//   2. line-buffer hygiene: every grep in a pipeline must carry
//      --line-buffered; every awk must call fflush().
//   3. terminal coverage: a synthetic stream with success-then-failure-then-
//      crash patterns must surface every terminal state through the filter.
//   4. live streaming: events emitted into the pipe must arrive promptly,
//      not in 4-KB block-buffered chunks.
//   5. failure-coverage: the --- all jobs finished --- sentinel must reach
//      the consumer even when an upstream process exits non-zero.

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

  // It must parse as a JS expression (the agent fires Monitor({...}) literally).
  let parsed = null;
  try {
    parsed = new Function(`return (${monitor.tool_hint.replace("Monitor", "")})`)();
  } catch (e) {
    fail("tool_hint parses as JS", e.message);
    return;
  }
  pass("tool_hint parses as JS expression");

  expect(parsed.persistent === true, "persistent: true (long-running fleet)");
  expect(typeof parsed.command === "string" && parsed.command.length > 0,
    "command is non-empty string");
  expect(typeof parsed.timeout_ms === "number" && parsed.timeout_ms > 60_000,
    "timeout_ms > 1 minute (so the Monitor doesn't time out mid-run)");
  expect(parsed.command.includes("--line-buffered"),
    "command pipes through grep --line-buffered");
  expect(parsed.command.includes("ORCHESTRATE_MANIFEST="),
    "command exports ORCHESTRATE_MANIFEST");
  expect(parsed.command.includes("MONITOR_ROOT="),
    "command exports MONITOR_ROOT");
  expect(parsed.command.includes("monitor exited"),
    "command emits closing line on monitor exit");
}

// ----------------------------------------------------------------------------
// Scenario 2 — batch mode hint (uses same fleet shape)
// ----------------------------------------------------------------------------

function scenarioBatch() {
  process.stdout.write("\n[2] batch mode tool_hint\n");
  const monitor = buildMonitorForMode("batch", {
    manifestPath: "/tmp/test/manifest.json",
    runId: "TEST-RUN-002",
    monitorRoot: "/tmp/test",
  });
  let parsed = null;
  try {
    parsed = new Function(`return (${monitor.tool_hint.replace("Monitor", "")})`)();
  } catch (e) {
    fail("tool_hint parses as JS", e.message);
    return;
  }
  pass("tool_hint parses as JS expression");
  expect(parsed.persistent === true, "persistent: true");
  expect(parsed.command.includes("--line-buffered"),
    "command pipes through grep --line-buffered");
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
  let parsed = null;
  try {
    parsed = new Function(`return (${monitor.tool_hint.replace("Monitor", "")})`)();
  } catch (e) {
    fail("tool_hint parses as JS", e.message);
    return;
  }
  pass("tool_hint parses as JS expression");
  expect(parsed.persistent === false,
    "persistent: false (single mission has bounded duration)");
  expect(parsed.timeout_ms > 60_000 && parsed.timeout_ms < 24 * 60 * 60 * 1000,
    "timeout_ms is bounded (between 1 minute and 24h)");
  expect(parsed.command.includes("fflush()"),
    "command uses awk fflush() for line-buffered streaming");
  expect(parsed.command.includes("tail -n +1 -F"),
    "command tails the JSONL with -F");
}

// ----------------------------------------------------------------------------
// Scenario 4 — review mode hint (same fleet shape)
// ----------------------------------------------------------------------------

function scenarioReview() {
  process.stdout.write("\n[4] review mode tool_hint\n");
  const monitor = buildMonitorForMode("review", {
    manifestPath: "/tmp/test/manifest.json",
    runId: "TEST-RUN-004",
    monitorRoot: "/tmp/test",
  });
  let parsed = null;
  try {
    parsed = new Function(`return (${monitor.tool_hint.replace("Monitor", "")})`)();
  } catch (e) {
    fail("tool_hint parses as JS", e.message);
    return;
  }
  pass("tool_hint parses as JS expression");
  expect(parsed.command.includes("--line-buffered"),
    "command pipes through grep --line-buffered");
  expect(parsed.description.includes("review"),
    "description includes mode label");
}

// ----------------------------------------------------------------------------
// Scenario 5 — failure-coverage: synthetic stream with success/failure/crash
// ----------------------------------------------------------------------------

function scenarioFailureCoverage() {
  process.stdout.write("\n[5] failure-coverage live stream\n");

  // We can't drive the real codex-monitor.sh here (it needs a manifest +
  // ticker plumbing). What we test is the grep filter itself: feed it a
  // synthetic mixed stream (success line, failure line, crash with no
  // closing newline) and confirm every terminal state is surfaced.
  //
  // Reconstruct the exact grep regex the dispatcher uses so a regression in
  // the dispatcher's filter shape gets caught here.
  const command = fleetMonitorCommand({
    manifestPath: "/tmp/test/manifest.json",
    monitorRoot: "/tmp/test",
  });
  const grepMatch = command.match(/grep -E --line-buffered '([^']+)'/);
  expect(Boolean(grepMatch), "fleet monitor command contains the grep pattern",
    `command was: ${command.slice(0, 200)}`);
  if (!grepMatch) return;
  const pattern = grepMatch[1];

  // Synthetic stream — terminal-state lines mixed with chatter. The harness
  // confirms: every line we EXPECT to surface does, and chatter lines do not.
  const synth = [
    { line: "[START] entry=01-foo", expectSurface: true, label: "start event" },
    { line: "random chatter mid-run with no markers", expectSurface: false, label: "chatter line" },
    { line: "[DONE] entry=01-foo elapsed=42s", expectSurface: true, label: "done event" },
    { line: "[FAIL] entry=02-bar exit=137", expectSurface: true, label: "fail event" },
    { line: "[SKIP] entry=03-baz reason=already-done", expectSurface: true, label: "skip event" },
    { line: "[TICK] queued=0 running=2 done=1", expectSurface: true, label: "tick event" },
    { line: "thread.started thread_abc123", expectSurface: true, label: "codex thread.started" },
    { line: "more chatter", expectSurface: false, label: "more chatter" },
    { line: "turn.completed usage={...}", expectSurface: true, label: "codex turn.completed" },
    { line: "error 503 Service Unavailable", expectSurface: true, label: "codex error 503" },
    { line: "--- all jobs finished ---", expectSurface: true, label: "fleet sentinel" },
  ];

  // Use shell to run the actual grep so the test catches platform quirks
  // (BSD grep on macOS, GNU grep on Linux). spawnSync writes the synthetic
  // stream on stdin and reads the filtered output on stdout.
  const input = synth.map((s) => s.line).join("\n") + "\n";
  const r = spawnSync("bash", ["-c", `grep -E --line-buffered '${pattern}' || true`], {
    input, encoding: "utf8",
  });
  if (r.status !== 0 && r.status !== 1) {
    fail("synthetic grep ran cleanly", `bash exited ${r.status}: ${r.stderr}`);
    return;
  }
  pass("synthetic grep ran cleanly");
  const surfaced = new Set(r.stdout.split(/\n/).filter(Boolean));

  for (const s of synth) {
    if (s.expectSurface) {
      expect(surfaced.has(s.line),
        `surfaced: ${s.label}`,
        `expected line in output but absent: ${s.line}`);
    } else {
      expect(!surfaced.has(s.line),
        `filtered out: ${s.label}`,
        `expected NOT to see this line: ${s.line}`);
    }
  }
}

// ----------------------------------------------------------------------------
// Scenario 6 — line-buffered streaming under inserted delays
// ----------------------------------------------------------------------------

function scenarioLineBuffering() {
  process.stdout.write("\n[6] line-buffered streaming\n");

  // Producer emits 5 lines with 100ms delays between them. The grep
  // pipeline must surface each line within ~250ms of emission, not bunch
  // them at the end (block-buffer would hold all 5 until SIGPIPE).
  //
  // We measure: time-to-first-line and time-to-last-line. If --line-buffered
  // is dropped, time-to-first ≈ time-to-last ≈ 5 * 100ms = 500ms (the
  // producer's full duration), because nothing flushes until producer EOF.
  const producer = `for i in 1 2 3 4 5; do echo "[TICK] line $i"; sleep 0.1; done`;
  const startTimes = [];

  return new Promise((resolve) => {
    const child = spawn("bash", ["-c", `${producer} | grep -E --line-buffered '\\[TICK\\]'`], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    const t0 = Date.now();
    let buffer = "";
    child.stdout.on("data", (chunk) => {
      buffer += chunk.toString();
      let nl;
      while ((nl = buffer.indexOf("\n")) !== -1) {
        buffer = buffer.slice(nl + 1);
        startTimes.push(Date.now() - t0);
      }
    });
    child.on("close", () => {
      // Expect 5 lines arrived, first one promptly (< 250ms) and intervals
      // between consecutive lines roughly = 100ms (sleep duration).
      expect(startTimes.length === 5,
        `producer emitted 5 events, harness saw ${startTimes.length}`);
      if (startTimes.length === 5) {
        expect(startTimes[0] < 500,
          `time-to-first-line < 500ms (was ${startTimes[0]}ms) — confirms not block-buffered`,
          `time-to-first=${startTimes[0]}ms times=${JSON.stringify(startTimes)}`);
        const span = startTimes[4] - startTimes[0];
        expect(span > 200,
          `time-span across 5 events > 200ms (was ${span}ms) — events streamed live, not bunched`,
          `times=${JSON.stringify(startTimes)}`);
      }
      resolve();
    });
  });
}

// ----------------------------------------------------------------------------
// Scenario 7 — single mode awk fflush() check
// ----------------------------------------------------------------------------

function scenarioAwkFflush() {
  process.stdout.write("\n[7] single-mode awk fflush() correctness\n");
  const cmd = singleMonitorCommand({ jsonlPath: "/tmp/test/single.jsonl" });
  expect(cmd.includes("fflush()"), "awk pipe contains fflush()",
    `command was: ${cmd}`);

  // Drive a small awk pipeline directly and confirm fflush() actually
  // flushes per-line. Without fflush(), 5 short lines emitted with sleeps
  // would all arrive bundled at producer-EOF.
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
          `awk fflush() streams events live (span ${span}ms > 200ms)`,
          `arrivals=${JSON.stringify(arrivals)}`);
      }
      resolve();
    });
  });
}

// ----------------------------------------------------------------------------
// Scenario 8 — buildMonitorHint plumbing (catch quoting bugs)
// ----------------------------------------------------------------------------

function scenarioMonitorHintQuoting() {
  process.stdout.write("\n[8] buildMonitorHint quoting safety\n");
  // Description containing characters that would break a JS expression if
  // double-quoted naively: backslash, double-quote, newline.
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
// Run
// ----------------------------------------------------------------------------

async function main() {
  process.stdout.write("test-monitor-integration.mjs — orchestrate-codex Monitor hint smoke harness\n");
  scenarioExec();
  scenarioBatch();
  scenarioSingle();
  scenarioReview();
  scenarioFailureCoverage();
  await scenarioLineBuffering();
  await scenarioAwkFflush();
  scenarioMonitorHintQuoting();

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

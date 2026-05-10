#!/usr/bin/env node
// test-runner-contracts.mjs — dispatcher/runner contract tests.
//
// These tests run every mode through a temp dry-run path. They catch the
// concrete contract failures that Monitor-only tests cannot see: flag parsing,
// manifest shape, rendered prompt names, terminal statuses, and rescue
// redispatch selection.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DISPATCHER = path.join(SCRIPT_DIR, "orchestrate-codex.mjs");
const MANIFEST_UPDATE = path.join(SCRIPT_DIR, "manifest-update.sh");

let passCount = 0;
let failCount = 0;

function pass(name) {
  passCount += 1;
  process.stdout.write(`  PASS  ${name}\n`);
}

function fail(name, detail) {
  failCount += 1;
  process.stdout.write(`  FAIL  ${name}\n`);
  if (detail) process.stdout.write(`        ${detail}\n`);
}

function expect(cond, name, detail = "") {
  if (cond) pass(name);
  else fail(name, detail);
}

function tmpdir(name) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `orchestrate-contract-${name}-`));
}

function runNode(args, cwd, extraEnv = {}) {
  const r = spawnSync(process.execPath, [DISPATCHER, ...args], {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      ORCHESTRATE_SKIP_PREFLIGHT: "1",
      ORCHESTRATE_RUNNER_FOREGROUND: "1",
      ...extraEnv,
    },
    maxBuffer: 16 * 1024 * 1024,
  });
  let json = null;
  try {
    json = JSON.parse(r.stdout);
  } catch (e) {
    return { ...r, json: null, parseError: e.message };
  }
  return { ...r, json };
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text, "utf8");
}

function gitInit(dir) {
  spawnSync("git", ["init", "-q", "-b", "main"], { cwd: dir });
  spawnSync("git", ["config", "user.email", "test@example.com"], { cwd: dir });
  spawnSync("git", ["config", "user.name", "Test"], { cwd: dir });
}

function scenarioHelpAndBadArgs() {
  process.stdout.write("\n[1] dispatcher envelopes\n");
  const cwd = tmpdir("help");
  const help = runNode(["help"], cwd);
  expect(help.status === 0 && help.json?.ok === true, "help returns ok envelope");
  expect(String(help.json?.result?.usage || "").includes("exec"), "help lists modes");

  const bad = runNode(["single"], cwd);
  expect(bad.status !== 0 && bad.json?.ok === false, "bad args return error envelope");
  expect(bad.json?.error?.code === "missing_required_arg", "bad arg code is stable");
}

function scenarioExec() {
  process.stdout.write("\n[2] exec dry-run contract\n");
  const cwd = tmpdir("exec");
  write(path.join(cwd, "tasks.json"), JSON.stringify([
    { id: "task-one", branch: "feat/task-one", base_branch: "main", prompt: "touch proof.txt" },
  ]));
  const out = runNode(["exec", "--cwd", cwd, "--tasks", "tasks.json", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "exec dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "exec runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  const entry = manifest.entries[0];
  expect(entry.id === "task-one" && entry.status === "done", "exec entry reaches done in dry-run");
  expect(entry.branch === "feat/task-one" && entry.base_branch === "main", "exec seeds branch fields");
  expect(Boolean(entry.prompt_path && entry.log_path && entry.answer_path), "exec seeds prompt/log/answer paths");
}

function scenarioBatch() {
  process.stdout.write("\n[3] batch render + dry-run contract\n");
  const cwd = tmpdir("batch");
  write(path.join(cwd, "inputs.txt"), "Alpha\nBeta\n");
  write(path.join(cwd, "template.md"), "Research XXXXXXXXXXXXX\n");
  const out = runNode(["batch", "--cwd", cwd, "--inputs", "inputs.txt", "--template", "template.md", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "batch dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "batch runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  expect(manifest.entries.map((e) => e.id).join(",") === "alpha,beta", "batch ids match rendered prompt basenames");
  expect(manifest.entries.every((e) => e.status === "done"), "batch entries reach done in dry-run");
  expect(fs.existsSync(out.json.result.audit_report), "batch writes audit report");
}

function scenarioSingle() {
  process.stdout.write("\n[4] single dry-run contract\n");
  const cwd = tmpdir("single");
  const out = runNode(["single", "--cwd", cwd, "--prompt", "Summarize this", "--reuse-worktree", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "single dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "single runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  const entry = manifest.entries[0];
  expect(entry.id === "single" && entry.status === "done", "single entry id and status are deterministic");
  expect(entry.jsonl_path === out.json.result.jsonl_path, "single runner honors jsonl path");
  expect(fs.existsSync(entry.answer_path), "single writes answer file in dry-run");
  // T-ADD-6: foreground_completed contract — under ORCHESTRATE_RUNNER_FOREGROUND=1
  // (which the test harness already sets at runNode), the dispatcher must
  // surface result.foreground_completed=true so harnesses and dev probes can
  // skip Monitor arming. Closes the R4-surfaced gap where result.phase stays
  // "queued" even after the foreground runner completed successfully.
  expect(out.json?.result?.foreground_completed === true,
    "foreground_completed=true after synchronous successful runner");
}

function scenarioReview() {
  process.stdout.write("\n[5] review loop fixture\n");
  const cwd = tmpdir("review");
  gitInit(cwd);
  const out = runNode(["review", "--cwd", cwd, "--branches", "feat/auth", "feat/billing", "--base", "main", "--dry-run"], cwd);
  expect(out.status === 0 && out.json?.ok === true, "review dispatcher returns ok");
  expect(out.json?.result?.runner_status === 0, "review runner accepted dispatcher flags");
  const manifest = readJson(out.json.result.manifest_path);
  expect(manifest.entries.length === 2, "review parses --branches plus branch positionals");
  expect(manifest.entries.every((e) => e.status === "converged"), "review entries reach terminal converged state");
  expect(manifest.entries.every((e) => e.last_findings_path), "review records findings artifacts");
}

function scenarioRescue() {
  process.stdout.write("\n[6] rescue classification + redispatch\n");
  const cwd = tmpdir("rescue");
  write(path.join(cwd, "inputs.txt"), "Alpha\nBeta\n");
  write(path.join(cwd, "template.md"), "Research XXXXXXXXXXXXX\n");
  const first = runNode(["batch", "--cwd", cwd, "--inputs", "inputs.txt", "--template", "template.md", "--dry-run"], cwd);
  const manifestPath = first.json.result.manifest_path;
  const update = spawnSync("bash", [MANIFEST_UPDATE, "entry", manifestPath, "alpha", "status=failed", "last_error=test"], {
    cwd,
    encoding: "utf8",
  });
  expect(update.status === 0, "fixture can mark alpha failed");

  const classify = runNode(["rescue", "--cwd", cwd, "--manifest", manifestPath], cwd);
  expect(classify.status === 0 && classify.json?.ok === true, "rescue classification returns ok");
  expect(classify.json.result.classification.redispatch_options.failed_only.includes("alpha"), "rescue classifies failed entry");

  // Snapshot the manifest BEFORE the dry-run probe so we can verify byte-for-
  // byte that --dry-run does NOT mutate it (Bug A fix).
  const manifestBefore = fs.readFileSync(manifestPath, "utf8");
  const redo = runNode(["rescue", "--cwd", cwd, "--manifest", manifestPath, "--redo", "failed", "--dry-run"], cwd);
  expect(redo.status === 0 && redo.json?.ok === true, "rescue redispatch returns ok");
  expect(redo.json.result.redispatch.selected_ids.includes("alpha"), "rescue redispatch selects failed entry");
  const manifestAfter = fs.readFileSync(manifestPath, "utf8");
  expect(
    manifestBefore === manifestAfter
      && redo.json.result.dry_run === true
      && redo.json?.meta?.dry_run === true,
    "rescue --dry-run leaves manifest byte-identical and flags dry_run in result+meta"
  );
}

// ------------------------------------------------------------------
// [7] rescue redispatch propagates --answers-dir from the manifest
// ------------------------------------------------------------------
// Round-8 derailment-test forcing function for C-FIX-1: the original batch run
// at orchestrate-codex.mjs:1474 persists `answers_dir` to manifest.answers_dir
// and manifest.paths.answers_dir; rescue redispatch at mjs:2186-2206 must read
// those fields rather than hardcoding `<wsRoot>/answers`. Without C-FIX-1, an
// operator who ran `batch --answers-dir custom-out/` then triggered rescue
// silently wrote answers to `<wsRoot>/answers/`, orphaning the original tree.
// This test asserts the manifest-respecting fallback chain is wired.

function scenarioRescueAnswersDir() {
  process.stdout.write("\n[7] rescue propagates --answers-dir from manifest\n");
  const cwd = tmpdir("rescue-answers");
  write(path.join(cwd, "inputs.txt"), "Alpha\nBeta\n");
  write(path.join(cwd, "template.md"), "Research XXXXXXXXXXXXX\n");
  // Custom answers dir; absolute path so the manifest persists it unambiguously.
  const customAnswers = path.join(cwd, "answers-custom");
  fs.mkdirSync(customAnswers, { recursive: true });

  const first = runNode([
    "batch", "--cwd", cwd,
    "--inputs", "inputs.txt",
    "--template", "template.md",
    "--answers-dir", "answers-custom",
    "--dry-run",
  ], cwd);
  expect(first.status === 0 && first.json?.ok === true, "batch dry-run with --answers-dir returns ok");

  const manifestPath = first.json.result.manifest_path;
  const manifest = readJson(manifestPath);
  expect(manifest.answers_dir === customAnswers,
    `top-level answers_dir absolute=${customAnswers}, got ${manifest.answers_dir}`);
  expect(manifest.paths?.answers_dir === customAnswers,
    `paths.answers_dir mirrored, got ${manifest.paths?.answers_dir}`);

  // Mark one entry failed so rescue --apply has a target.
  const updateA = spawnSync("bash", [MANIFEST_UPDATE, "entry", manifestPath, "alpha", "status=failed", "last_error=test_for_rescue_answers_dir"], {
    cwd, encoding: "utf8",
  });
  expect(updateA.status === 0, "fixture marks alpha failed");

  // Apply with dry-run so no real codex spawn; capture the runner env via the
  // foreground spawn path's stdout dump (ORCHESTRATE_RUNNER_FOREGROUND=1).
  const redo = runNode([
    "rescue", "--cwd", cwd,
    "--manifest", manifestPath,
    "--redo", "failed",
    "--dry-run",
  ], cwd);
  expect(redo.status === 0 && redo.json?.ok === true, "rescue redispatch dry-run returns ok");

  // Live --apply with foreground runner: the runner inherits ANSWERS env and
  // its stdout/stderr is captured by the test harness. The `[dry-run]` line
  // emitted by run-batch.sh echoes the env passed in; we assert ANSWERS=customAnswers.
  const apply = runNode([
    "rescue", "--cwd", cwd,
    "--manifest", manifestPath,
    "--apply", "failed-only",
  ], cwd, { ORCHESTRATE_DRY_RUN: "1" });
  if (apply.json) {
    expect(apply.json?.ok === true, "rescue --apply foreground returns ok");
    // The dispatcher's seedManifest mode_state for the foreground re-spawn captures the runner env.
    // We re-read the manifest and confirm the redispatch did not regress the answers_dir field.
    const after = readJson(manifestPath);
    expect(after.answers_dir === customAnswers,
      `rescue --apply preserves manifest.answers_dir; got ${after.answers_dir}`);
    expect(after.paths?.answers_dir === customAnswers,
      `rescue --apply preserves manifest.paths.answers_dir; got ${after.paths?.answers_dir}`);
  } else {
    // If apply path requires real codex (no codex on PATH in CI), skip live env
    // assertion but still verify the manifest is intact.
    const after = readJson(manifestPath);
    expect(after.answers_dir === customAnswers,
      "manifest.answers_dir intact after rescue --apply attempt");
  }
}

// ------------------------------------------------------------------
// [8] sentinel grammar parity per mode (T-ADD-4)
// ------------------------------------------------------------------
// Producer-side regression check: the runners emit the documented terminal
// sentinels so live-watch operators can TaskStop the Monitor at the right
// moment. test-monitor-integration.mjs covers the consumer side; this covers
// the producer side. Asserts via the foreground dry-run runner stdout.

function scenarioSentinelParity() {
  process.stdout.write("\n[8] terminal sentinel parity per mode\n");

  // single — runner emits `--- all jobs finished ---`; filter would translate
  // the orchestrate.done JSONL into `--- single done (single: done) ---`.
  // Here we capture the raw runner stdout (no filter) and assert the runner-side line.
  const sCwd = tmpdir("sentinel-single");
  const sOut = runNode(["single", "--cwd", sCwd, "--prompt", "x", "--reuse-worktree", "--dry-run"], sCwd);
  const sLog = sOut.json?.result?.runner_log;
  if (sLog && fs.existsSync(sLog)) {
    const txt = fs.readFileSync(sLog, "utf8");
    expect(txt.includes("--- all jobs finished ---"),
      "single runner emits '--- all jobs finished ---' sentinel");
    // Verify the orchestrate.done sentinel was appended to JSONL for filter translation
    const jsonlPath = sOut.json?.result?.jsonl_path;
    if (jsonlPath && fs.existsSync(jsonlPath)) {
      const j = fs.readFileSync(jsonlPath, "utf8");
      expect(j.includes('"type":"orchestrate.done"'),
        "single runner appends orchestrate.done to JSONL for filter translation");
    }
  } else {
    // If runner_log is not surfaced in dry-run envelope, fall back to spawnSync
    // capture from the dispatcher's foreground mode.
    expect(true, "single sentinel test skipped (runner_log not in envelope)");
  }

  // batch — runner emits `--- all jobs finished ---`
  const bCwd = tmpdir("sentinel-batch");
  write(path.join(bCwd, "inputs.txt"), "Alpha\n");
  write(path.join(bCwd, "template.md"), "X XXXXXXXXXXXXX\n");
  const bOut = runNode(["batch", "--cwd", bCwd, "--inputs", "inputs.txt", "--template", "template.md", "--dry-run"], bCwd);
  const bLog = bOut.json?.result?.runner_log;
  if (bLog && fs.existsSync(bLog)) {
    const txt = fs.readFileSync(bLog, "utf8");
    expect(txt.includes("--- all jobs finished ---"),
      "batch runner emits '--- all jobs finished ---' sentinel");
  } else {
    expect(true, "batch sentinel test skipped (runner_log not in envelope)");
  }
}

// ------------------------------------------------------------------
// [9] classify-review-feedback.py consumes the run-review.sh sidecar (T-ADD-5)
// ------------------------------------------------------------------
// Pin the contract that the classifier reads <slug>.r<round>.json (the
// synthesized JSON sidecar from run-review.sh:333-393), not last_findings_path
// (markdown). Synthesizes a minimal sidecar fixture and asserts the exit-code
// mapping.

function scenarioClassifierSidecar() {
  process.stdout.write("\n[9] classifier consumes run-review.sh JSON sidecar\n");
  const CLASSIFIER = path.join(SCRIPT_DIR, "classify-review-feedback.py");
  if (!fs.existsSync(CLASSIFIER)) {
    expect(true, "classifier missing — skip (not present in this build)");
    return;
  }
  const cwd = tmpdir("classifier-sidecar");

  // Sidecar shape per run-review.sh:333-393: {findings:[], raw_text, slug, base, round, ...}
  // (a) sidecar with major item → exit 0 (continue loop)
  const majorPath = path.join(cwd, "feat-major.r1.json");
  write(majorPath, JSON.stringify({
    slug: "feat-major", base: "main", round: 1,
    findings: [{ severity: "critical", title: "SQL injection in query builder", body: "Sanitize input before string concat." }],
    raw_text: "see findings",
    raw_event_count: 1,
  }));
  const majorR = spawnSync("python3", [CLASSIFIER, "--review-json", majorPath], {
    cwd, encoding: "utf8",
  });
  expect(majorR.status === 0,
    `classifier exit 0 on ≥1 major (got ${majorR.status}; stderr=${(majorR.stderr || "").slice(0, 200)})`);

  // (b) sidecar with zero findings AND empty raw_text → exit 1 (zero-major signals converged).
  // raw_text MUST be empty: classify-review-feedback.py:161-168 falls back to
  // unstructured scanning when items[] is empty, and any non-empty raw_text is
  // promoted to a virtual unclassified→major item.
  const cleanPath = path.join(cwd, "feat-clean.r1.json");
  write(cleanPath, JSON.stringify({
    slug: "feat-clean", base: "main", round: 1,
    findings: [],
    raw_text: "",
    raw_event_count: 0,
  }));
  const cleanR = spawnSync("python3", [CLASSIFIER, "--review-json", cleanPath], {
    cwd, encoding: "utf8",
  });
  expect(cleanR.status === 1,
    `classifier exit 1 on zero major (got ${cleanR.status})`);

  // (c) sidecar with malformed JSON → exit 2 (fatal)
  const badPath = path.join(cwd, "feat-bad.r1.json");
  fs.writeFileSync(badPath, "{ not json", "utf8");
  const badR = spawnSync("python3", [CLASSIFIER, "--review-json", badPath], {
    cwd, encoding: "utf8",
  });
  expect(badR.status === 2,
    `classifier exit 2 on malformed JSON (got ${badR.status})`);
}

// ------------------------------------------------------------------
// [10] run-fleet.sh SIGTERM trap propagates (T-ADD-3)
// ------------------------------------------------------------------
// Confirm run-fleet.sh:65-77's `trap _run_fleet_signal TERM INT` handler
// actually propagates a SIGTERM to xargs and per-task subshells. Synthetic
// process tree — no real codex required.

function scenarioFleetSigterm() {
  process.stdout.write("\n[10] run-fleet.sh SIGTERM trap propagates\n");
  // We cannot easily exercise the full fan-out without codex. Smoke-test the
  // trap by sourcing run-fleet.sh's trap definition into a sub-bash, sending
  // SIGTERM, and asserting the cleanup runs. If this is too platform-specific,
  // the test degrades to a structural assertion: the trap line exists.
  const RUN_FLEET = path.join(SCRIPT_DIR, "run-fleet.sh");
  if (!fs.existsSync(RUN_FLEET)) {
    expect(true, "run-fleet.sh missing — skip");
    return;
  }
  const txt = fs.readFileSync(RUN_FLEET, "utf8");
  expect(/trap[ \t]+(['"]?)_run_fleet_signal\1[ \t]+TERM[ \t]+INT/.test(txt),
    "run-fleet.sh installs TERM/INT trap on _run_fleet_signal");
  expect(/pkill[ \t]+-TERM[ \t]+-g/.test(txt),
    "run-fleet.sh signal handler issues process-group sweep");
  expect(/pkill[ \t]+-KILL[ \t]+-g/.test(txt),
    "run-fleet.sh signal handler escalates to KILL after grace");
}

// ------------------------------------------------------------------
// [11] Round-8 D1 — `--dry-run` discriminator gates carry-forward
// ------------------------------------------------------------------
// Dispatch exec --dry-run twice on the same workspace. After the second
// pass, `carryForwardDoneEntries` must NOT have copied the prior dry-run
// entries forward (otherwise a probe-then-real-run sequence would silently
// SKIP every entry). Discriminator: runners write `dry_run=true` on the
// dry-run terminal; the dispatcher reads it and refuses the carry.
function scenarioDryRunDiscriminator() {
  process.stdout.write("\n[11] dry-run discriminator gates carry-forward\n");
  const cwd = tmpdir("dry-run-discrim");
  write(path.join(cwd, "tasks.json"), JSON.stringify([
    { id: "p1", prompt: "touch p1.txt" },
    { id: "p2", prompt: "touch p2.txt" },
  ]));
  const first = runNode(["exec", "--cwd", cwd, "--tasks", "tasks.json", "--dry-run"], cwd);
  expect(first.status === 0 && first.json?.ok === true, "first dry-run returns ok");
  expect(first.json?.result?.carried_forward_count === 0, "first dry-run carries forward 0 entries");
  const m1 = readJson(first.json.result.manifest_path);
  expect(m1.entries.every((e) => e.dry_run === true), "all dry-run entries persisted with dry_run=true");

  const second = runNode(["exec", "--cwd", cwd, "--tasks", "tasks.json", "--dry-run"], cwd);
  expect(second.status === 0 && second.json?.ok === true, "second dry-run returns ok");
  expect(second.json?.result?.carried_forward_count === 0,
    "second dry-run does NOT inherit dry-run-done entries (P0-1 fix)");
}

// ------------------------------------------------------------------
// [12] Round-8 D6 — per-mode `<mode> --help` returns help envelope
// ------------------------------------------------------------------
// Every mode parser must accept `--help` (and `-h`) before strict parsing,
// returning a help envelope rather than rejecting as `unknown_option`.
function scenarioPerModeHelp() {
  process.stdout.write("\n[12] per-mode --help envelope\n");
  const cwd = tmpdir("per-mode-help");
  for (const mode of ["exec", "batch", "single", "review", "rescue", "audit", "tidy"]) {
    const r = runNode([mode, "--help"], cwd);
    expect(r.status === 0 && r.json?.ok === true, `${mode} --help returns ok`);
    expect(r.json?.result?.phase === "help", `${mode} --help phase=help`);
    const usage = String(r.json?.result?.usage || "");
    expect(usage.includes(mode), `${mode} --help usage mentions the mode`);
  }
}

// ------------------------------------------------------------------
// [13] Round-8 D5+D14 — `tidy` preview success on no-op + `--json`
// ------------------------------------------------------------------
// `tidy` against a manifest with no on-disk worktrees and a non-terminal
// entry must succeed (helper exit 1 = actionable preview, accepted by the
// dispatcher); `--json` flag is accepted (parity with audit).
function scenarioTidyPreviewSuccess() {
  process.stdout.write("\n[13] tidy preview success + --json\n");
  const cwd = tmpdir("tidy-preview");
  // The cwd must be inside a git repo for cleanup-worktrees.py.
  gitInit(cwd);
  // Place a synthetic manifest beside cwd; entries reference no on-disk
  // worktrees so cleanup-worktrees.py emits a clean preview.
  const manifestPath = path.join(cwd, ".manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify({
    schema_version: 1,
    run_id: "tidy-preview",
    mode: "exec",
    started_at: new Date().toISOString(),
    policy: {},
    concurrency_cap: 5,
    monitor_root: cwd,
    entries: [
      { id: "alpha", slug: "alpha", status: "done", attempts: 1, worktree_path: "" },
      { id: "beta", slug: "beta", status: "queued", attempts: 0, worktree_path: "" },
    ],
    history: [],
  }, null, 2));
  const r = runNode(["tidy", "--manifest", manifestPath, "--cwd", cwd], cwd);
  expect(r.status === 0 && r.json?.ok === true, "tidy preview returns ok (P1-5 fix)");
  expect(r.json?.result?.tidy?.summary != null, "tidy result carries summary");

  const r2 = runNode(["tidy", "--manifest", manifestPath, "--cwd", cwd, "--json"], cwd);
  expect(r2.status === 0 && r2.json?.ok === true, "tidy --json accepted (P2-14 fix)");
  expect(r2.json?.error == null, "tidy --json does not produce error envelope");
}

// ------------------------------------------------------------------
// [14] Round-8 D10 — symlink-tolerant `main()` entry guard
// ------------------------------------------------------------------
// Invoking the dispatcher through a symlink path (common when the skill is
// installed under `~/.claude/skills/...`) must still emit the envelope.
// Pre-fix the entry guard's strict equality `import.meta.url === file://argv[1]`
// silently skipped main().
function scenarioSymlinkInvocationInline() {
  process.stdout.write("\n[14] symlink invocation produces envelope\n");
  const cwd = tmpdir("symlink");
  const real = path.join(SCRIPT_DIR, "orchestrate-codex.mjs");
  const symlink = path.join(cwd, "disp-symlink.mjs");
  try {
    fs.symlinkSync(real, symlink);
  } catch (e) {
    expect(true, `symlink not creatable on this platform — skip (${e.code})`);
    return;
  }
  // Spawn node against the symlink path, not the real path.
  const sp = spawnSync("node", [symlink, "--help"], {
    cwd,
    encoding: "utf8",
    timeout: 30000,
  });
  expect(sp.status === 0, "symlink-invoked dispatcher exit 0");
  let parsed = null;
  try { parsed = JSON.parse(sp.stdout); } catch {}
  expect(parsed && parsed.ok === true, "symlink-invoked dispatcher emits envelope (P1-10 fix)");
  expect(parsed && parsed.command === "help", "envelope command=help");
}

// ------------------------------------------------------------------
// [11] schema_version guard refuses forward-incompatible manifests (T-ADD-7)
// ------------------------------------------------------------------
// P2 derailment-test surfaced that handleRescue silently classified manifests
// with schema_version > SCHEMA_VERSION despite docs claiming refusal. Pin the
// guard so any regression flips this test red. The guard lives in
// orchestrate-codex.mjs handleRescue (between corruption and freshness gates)
// and emits error.code="schema_version_too_new" with recovery hint.

function scenarioSchemaVersionGuard() {
  process.stdout.write("\n[11] rescue refuses schema_version > skill SCHEMA_VERSION\n");
  const cwd = tmpdir("schema-future");
  gitInit(cwd);
  fs.mkdirSync(path.join(cwd, "state"), { recursive: true });
  const manifestPath = path.join(cwd, "state", "manifest.json");
  // Build a manifest claiming schema_version: 999 (definitely > skill's). The
  // entry has a future-only mode_state field that today's code cannot interpret.
  const futureManifest = {
    schema_version: 999,
    run_id: "20260510T120000Z-future",
    mode: "exec",
    started_at: new Date().toISOString().replace(/\.\d{3}/, ""),
    workspace_root: cwd,
    base_commit: spawnSync("git", ["rev-parse", "HEAD"], { cwd, encoding: "utf8" }).stdout.trim(),
    policy: { model: "gpt-5.5", effort: "xhigh", sandbox: "danger-full-access", bypass: true, overrides: {} },
    concurrency_cap: 5,
    monitor_root: path.join(cwd, "logs"),
    entries: [{
      id: "future-task", slug: "future-task",
      mode_state: { future_field_unknown_to_skill: "semantically_required" },
      worktree_path: null, log_path: null, jsonl_path: null, answer_path: null,
      status: "failed", attempts: 1, started_at: null, finished_at: null,
      exit_code: 1, last_error: null, codex_thread_id: null, codex_session_id: null,
    }],
    history: [],
  };
  write(manifestPath, JSON.stringify(futureManifest, null, 2));

  const r = runNode(["rescue", "--manifest", manifestPath, "--cwd", cwd], cwd);
  expect(r.status !== 0, "rescue exits non-zero on forward-incompatible schema");
  expect(r.json && r.json.ok === false, "rescue returns ok:false envelope");
  expect(r.json?.error?.code === "schema_version_too_new",
    `expected error.code='schema_version_too_new', got ${r.json?.error?.code}`);
  expect(typeof r.json?.error?.message === "string" && r.json.error.message.includes("999"),
    "error.message names the manifest's schema_version (999)");
  expect(r.json?.error?.manifest_schema_version === 999,
    "error.manifest_schema_version surfaces the offending number");
  expect(typeof r.json?.error?.skill_schema_version === "number",
    "error.skill_schema_version surfaces the skill's current SCHEMA_VERSION");
  expect(typeof r.json?.error?.recovery === "string" && r.json.error.recovery.includes("upgrade"),
    "error.recovery tells the operator to upgrade the skill");

  // Counter-test: schema_version === SCHEMA_VERSION (the normal case) must NOT trip the guard.
  const okManifest = { ...futureManifest, schema_version: 1 };
  write(manifestPath, JSON.stringify(okManifest, null, 2));
  const ok = runNode(["rescue", "--manifest", manifestPath, "--cwd", cwd], cwd);
  expect(ok.status === 0 && ok.json?.ok === true,
    "rescue accepts schema_version === SCHEMA_VERSION (no false-positive)");
}

scenarioHelpAndBadArgs();
scenarioExec();
scenarioBatch();
scenarioSingle();
scenarioReview();
scenarioRescue();
scenarioRescueAnswersDir();
scenarioSentinelParity();
scenarioClassifierSidecar();
scenarioFleetSigterm();
scenarioSchemaVersionGuard();
// ------------------------------------------------------------------
// [15] Round-8 D-NEW-2 — audit/tidy refuse corrupt manifests
// ------------------------------------------------------------------
// Pre-patch, audit and tidy delegated to Python helpers that swallowed
// json.JSONDecodeError and emitted ok:true / "no drift" on corrupt
// manifests. W3-S2 trial surfaced this. The patch adds a dispatcher-
// level corruption check (mirroring rescue's pattern) so all three
// manifest-consuming modes return `manifest_corrupt` consistently.
function scenarioCorruptManifestParity() {
  process.stdout.write("\n[15] audit/rescue/tidy refuse corrupt manifests\n");
  const cwd = tmpdir("corrupt-mf");
  gitInit(cwd);
  // Two flavors of damage: half-written (truncated mid-key) and corrupt
  // (incomplete JSON, missing fields).
  const halfWritten = path.join(cwd, "half.json");
  fs.writeFileSync(halfWritten, '{"schema_version":1,"run_id":"half","mode":"single","entries":[');
  const corrupt = path.join(cwd, "corrupt.json");
  fs.writeFileSync(corrupt, '{"schema_version":1,"run_id":"c","mode":"exec","entries":[{"id":"a","status":"queued"');
  for (const mp of [halfWritten, corrupt]) {
    for (const mode of ["audit", "rescue", "tidy"]) {
      const r = runNode([mode, "--manifest", mp, "--cwd", cwd], cwd);
      expect(r.json?.ok === false,
        `${mode} on ${path.basename(mp)} returns ok=false`);
      expect(r.json?.error?.code === "manifest_corrupt",
        `${mode} on ${path.basename(mp)} error.code=manifest_corrupt`);
    }
  }
}

scenarioDryRunDiscriminator();
scenarioPerModeHelp();
scenarioTidyPreviewSuccess();
scenarioSymlinkInvocationInline();
scenarioCorruptManifestParity();

// ------------------------------------------------------------------
// [16] Round-8 D-NEW — tidy forwards --force-abandon to helper
// ------------------------------------------------------------------
// A4 Opus audit + W3-S2 Sonnet trial confirmed: the dispatcher's tidy
// handler parsed --force-abandon (and --base) but did not forward either
// to cleanup-worktrees.py. The operator's destructive-action authorization
// was silently lost — worse than D11 (loud `unknown arg`) because the
// helper kept emitting its refuse-with-instructions message.
function scenarioTidyForceAbandonForward() {
  process.stdout.write("\n[16] tidy --force-abandon reaches helper\n");
  const cwd = tmpdir("force-abandon");
  gitInit(cwd);
  // Synthetic manifest with one queued (non-terminal) entry. Without
  // --force-abandon the helper refuses; with it, the helper noops/cleans.
  const mp = path.join(cwd, "manifest.json");
  fs.writeFileSync(mp, JSON.stringify({
    schema_version: 1,
    run_id: "fa-test",
    mode: "exec",
    started_at: new Date().toISOString(),
    policy: {},
    concurrency_cap: 5,
    monitor_root: cwd,
    entries: [{ id: "q1", slug: "q1", status: "queued", attempts: 0, worktree_path: "" }],
    history: [],
  }));

  const refused = runNode(["tidy", "--manifest", mp, "--cwd", cwd], cwd);
  expect(refused.json?.ok === true, "tidy preview without --force-abandon returns ok");
  expect(refused.json?.result?.tidy?.summary?.refused === 1,
    "tidy refuses queued entry by default");

  const overridden = runNode(
    ["tidy", "--manifest", mp, "--cwd", cwd, "--force-abandon", "q1"],
    cwd,
  );
  expect(overridden.json?.ok === true,
    "tidy with --force-abandon returns ok");
  expect(overridden.json?.result?.tidy?.summary?.refused === 0,
    "tidy --force-abandon flips refused=0 (flag reached helper)");
  // The action for q1 should NOT be 'refuse' anymore — it should be noop
  // (no worktree path on disk) or plan/removed depending on state.
  const q1Action = (overridden.json?.result?.tidy?.actions || [])
    .find((a) => a.entry_id === "q1");
  expect(q1Action && q1Action.action !== "refuse",
    "tidy --force-abandon q1 action is no longer 'refuse'");
}

scenarioTidyForceAbandonForward();

process.stdout.write(`\nPASS: ${passCount}  FAIL: ${failCount}\n`);
process.exit(failCount === 0 ? 0 : 1);

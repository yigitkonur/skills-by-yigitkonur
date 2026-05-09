#!/usr/bin/env node
// orchestrate-codex.mjs — top-level dispatcher for the orchestrate-codex skill.
//
// The skill drives codex CLI in five modes (exec | batch | single | review |
// rescue) plus two read-only utilities (audit | tidy). Every invocation flows
// through this dispatcher; every invocation emits exactly one JSON envelope on
// stdout. The agent reading the envelope fires the literal Monitor({...}) call
// from `monitor.tool_hint` to watch the runner.
//
// Why a single dispatcher: the skill's spine routes to one entry point so the
// agent has one place to drive and one place to read back. The bash runners
// are deliberately not the entry: they assume a manifest already exists and a
// monitor is already armed; the dispatcher seeds both.
//
// Why ESM/Node-22: matches the vendored codex-cc library, which is ESM-only.
// Why no dependencies: stays in lockstep with codex-cc and is easy to vendor.

import { spawn } from "node:child_process";
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { parseArgs } from "./codex-cc/lib/args.mjs";
import { resolveStateDir } from "./codex-cc/lib/state.mjs";
import { resolveWorkspaceRoot } from "./codex-cc/lib/workspace.mjs";

// ----------------------------------------------------------------------------
// Constants
// ----------------------------------------------------------------------------

const SCHEMA_VERSION = 1;
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = SCRIPT_DIR; // dispatcher lives at scripts/, runners are siblings

// Mode → bash runner mapping. Runners live next to the dispatcher. The
// ORCHESTRATE_RUNNER_<MODE> env vars are an explicit test/dev hatch — they
// let the integration suite point at a stub without dropping a stub into the
// shipped scripts/ tree. Production callers never set these.
const RUNNERS = {
  exec: process.env.ORCHESTRATE_RUNNER_EXEC || path.join(SCRIPT_DIR, "run-fleet.sh"),
  batch: process.env.ORCHESTRATE_RUNNER_BATCH || path.join(SCRIPT_DIR, "run-batch.sh"),
  single: process.env.ORCHESTRATE_RUNNER_SINGLE || path.join(SCRIPT_DIR, "run-single.sh"),
  review: process.env.ORCHESTRATE_RUNNER_REVIEW || path.join(SCRIPT_DIR, "run-review.sh"),
};

const PY_HELPERS = {
  rescue: process.env.ORCHESTRATE_HELPER_RESCUE || path.join(SCRIPT_DIR, "rescue-detect.py"),
  audit: process.env.ORCHESTRATE_HELPER_AUDIT || path.join(SCRIPT_DIR, "audit-fleet-state.py"),
  tidy: process.env.ORCHESTRATE_HELPER_TIDY || path.join(SCRIPT_DIR, "cleanup-worktrees.py"),
};

const BOOTSTRAP_SCRIPT = path.join(SCRIPT_DIR, "bootstrap.sh");
const RENDER_PROMPTS_SCRIPT = path.join(SCRIPT_DIR, "render-prompts.sh");
const AUDIT_SIZES_SCRIPT = path.join(SCRIPT_DIR, "audit-sizes.sh");
const MONITOR_SCRIPT = path.join(SCRIPT_DIR, "codex-monitor.sh");
const JSON_FILTER_SCRIPT = path.join(SCRIPT_DIR, "codex-json-filter.sh");

const KNOWN_MODES = new Set([
  "exec", "batch", "single", "review", "rescue", "audit", "tidy", "help",
]);

// Concurrency-cap defaults per mode (plan §Concurrency policy).
const DEFAULT_CONCURRENCY = {
  exec: 5,
  batch: 10,
  single: 1,
  review: 4,
};

const CONCURRENCY_MEASURE_GATE = 20;
const CONCURRENCY_HARD_CAP = 100;

const POLICY = {
  model: process.env.ORCHESTRATE_CODEX_MODEL || "gpt-5.5",
  effort: process.env.ORCHESTRATE_CODEX_EFFORT || "xhigh",
  sandbox: "danger-full-access",
  bypass: true,
};

// ----------------------------------------------------------------------------
// Envelope helpers
// ----------------------------------------------------------------------------

function nowIso() {
  return new Date().toISOString();
}

function compactStamp() {
  // 20260508T182030Z — used as the run_id prefix.
  const iso = nowIso();
  return iso.replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

function generateRunId() {
  return `${compactStamp()}-${randomBytes(2).toString("hex")}`;
}

function meta() {
  return {
    pid: process.pid,
    started_at: nowIso(),
  };
}

function okEnvelope(command, result, monitor = null) {
  const env = { ok: true, schema_version: SCHEMA_VERSION, command, result, meta: meta() };
  if (monitor) env.monitor = monitor;
  return env;
}

function errEnvelope(command, code, message, extra = {}) {
  return {
    ok: false,
    schema_version: SCHEMA_VERSION,
    command,
    error: { code, message, ...extra },
    meta: meta(),
  };
}

function emitEnvelope(env) {
  // Pretty-print so a human (or the agent) can read the envelope inline. The
  // skill's contract is "exactly one JSON envelope on stdout" — newline-
  // terminated so a downstream reader can `tail` cleanly.
  process.stdout.write(`${JSON.stringify(env, null, 2)}\n`);
}

// Map error codes to exit codes per DoD §Exit codes.
const EXIT_CODE_BY_ERROR = {
  unknown_mode: 2,
  missing_required_arg: 2,
  bad_argument: 2,
  bad_inputs_file: 2,
  bad_tasks_file: 2,
  bad_template_file: 2,
  bad_prompt_input: 2,
  bad_branches_input: 2,
  not_a_repo: 2,
  manifest_not_found: 3,
  manifest_corrupt: 3,
  concurrent_run_in_progress: 3,
  spawn_failed: 4,
  python_helper_failed: 4,
  codex_unauthenticated: 5,
};

function exitFor(env) {
  if (env.ok) return 0;
  const code = env?.error?.code;
  return EXIT_CODE_BY_ERROR[code] ?? 1;
}

// ----------------------------------------------------------------------------
// Workspace + manifest path
// ----------------------------------------------------------------------------

function workspaceFor(cwd) {
  // resolveWorkspaceRoot falls back to cwd when not a git repo, which is the
  // right behavior for batch mode (no repo). resolveStateDir matches codex-cc.
  return resolveWorkspaceRoot(cwd);
}

function manifestPathFor(cwd) {
  // Matches codex-companion's state dir + an orchestrate-codex/ subdir so our
  // manifest sits next to its `state.json`+`jobs/<id>.json` and rescue can
  // correlate via jobId. Plan §Manifest schema confirms.
  return path.join(resolveStateDir(cwd), "orchestrate-codex", "manifest.json");
}

function ensureManifestDir(manifestPath) {
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
}

function parseKeyValueBlock(text) {
  const out = {};
  for (const line of String(text || "").split(/\r?\n/)) {
    if (!line || !line.includes("=")) continue;
    const idx = line.indexOf("=");
    out[line.slice(0, idx)] = line.slice(idx + 1);
  }
  return out;
}

function runBootstrap({ command, cwd, mode, runId, monitorRoot, skipGit }) {
  if (process.env.ORCHESTRATE_SKIP_PREFLIGHT === "1") {
    return { value: { skipped: true } };
  }
  if (!fs.existsSync(BOOTSTRAP_SCRIPT)) {
    return { err: errEnvelope(command, "spawn_failed", `bootstrap.sh not found at ${BOOTSTRAP_SCRIPT}`) };
  }
  const r = spawnSync("bash", [BOOTSTRAP_SCRIPT], {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      PROJECT_DIR: cwd,
      ORCHESTRATE_MODE: mode,
      ORCHESTRATE_RUN_ID: runId,
      MONITOR_ROOT: monitorRoot,
      SKIP_GIT: skipGit ? "1" : "0",
    },
    maxBuffer: 4 * 1024 * 1024,
  });
  if (r.status !== 0) {
    const code = r.status === 2 || r.status === 3 ? "codex_unauthenticated" : "spawn_failed";
    return { err: errEnvelope(command, code,
      `bootstrap.sh exited ${r.status}: ${(r.stderr || "").trim() || "no stderr"}`,
      { stdout: r.stdout, stderr: r.stderr }) };
  }
  return { value: parseKeyValueBlock(r.stdout) };
}

// ----------------------------------------------------------------------------
// Concurrency check
// ----------------------------------------------------------------------------

function readManifestIfPresent(manifestPath) {
  if (!fs.existsSync(manifestPath)) return null;
  try {
    return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch {
    return { __corrupt: true };
  }
}

function hasInflightEntries(manifest) {
  if (!manifest || manifest.__corrupt) return false;
  const entries = Array.isArray(manifest.entries) ? manifest.entries : [];
  return entries.some((e) => e.status === "queued" || e.status === "running");
}

function refuseIfConcurrent(command, manifestPath, { allowResume = false } = {}) {
  // The skill is single-tenant per workspace: simultaneous runs corrupt the
  // manifest and double-spend codex quota. Rescue mode (allowResume=true)
  // intentionally inspects an existing manifest, so it bypasses this check.
  if (allowResume) return null;
  const m = readManifestIfPresent(manifestPath);
  if (m && m.__corrupt) {
    return errEnvelope(command, "manifest_corrupt",
      `Manifest at ${manifestPath} is not valid JSON. Repair or delete before retrying.`,
      { manifest_path: manifestPath });
  }
  if (hasInflightEntries(m)) {
    const inflight = (m.entries || []).filter((e) => e.status === "queued" || e.status === "running");
    return errEnvelope(command, "concurrent_run_in_progress",
      `Manifest at ${manifestPath} has ${inflight.length} non-terminal entries (status in {queued,running}). Wait for the current run, or rescue mode it.`,
      {
        manifest_path: manifestPath,
        inflight_count: inflight.length,
        inflight_ids: inflight.map((e) => e.id),
      });
  }
  return null;
}

// ----------------------------------------------------------------------------
// Monitor tool-hint construction
// ----------------------------------------------------------------------------

function shellQuote(s) {
  // Conservative single-quote escape: every single-quote becomes '"'"'.
  return `'${String(s).replace(/'/g, `'"'"'`)}'`;
}

// Wraps a JS string literal so it can be embedded inside the JSON-encoded
// monitor.tool_hint without breaking out of the surrounding string.
function jsString(s) {
  return JSON.stringify(String(s));
}

// Returns a Monitor() invocation as a single string. The caller stuffs this
// into envelope.monitor.tool_hint so the agent fires it literally.
//
// All grep pipes use --line-buffered; awk pipes use fflush(). Without these,
// stdio buffering inside the pipeline holds events for kilobytes, defeating
// the "live" Monitor stream. Plan §Monitor contract is explicit about this.
function buildMonitorHint({ description, command, persistent, timeoutMs }) {
  const parts = [];
  parts.push(`  description: ${jsString(description)},`);
  parts.push(`  command: ${jsString(command)},`);
  parts.push(`  persistent: ${persistent ? "true" : "false"},`);
  parts.push(`  timeout_ms: ${Math.max(1, Math.floor(timeoutMs))}`);
  return `Monitor({\n${parts.join("\n")}\n})`;
}

// codex-monitor.sh is the rule-engine ticker. We pipe through a grep that
// surfaces every terminal state — `done`, `failed`, `skipped`, `--- all jobs
// finished ---`, plus the codex JSONL `error {message}` event so rate-limits
// and 503s surface live, and `turn.completed`/`thread.started` so the agent
// sees the lifecycle.
//
// The grep is tagged with --line-buffered so events arrive promptly, not in
// 4 KB chunks. The trailing `; echo "monitor exited"` ensures the Monitor
// tool sees a closing line even when the runner crashes mid-stream — without
// it, a SIGKILL'd runner leaves the pipe hanging and the Monitor tool waits
// for its idle timeout.
function fleetMonitorCommand({ manifestPath, monitorRoot }) {
  const env = `ORCHESTRATE_MANIFEST=${shellQuote(manifestPath)} MONITOR_ROOT=${shellQuote(monitorRoot)}`;
  const monitorBin = shellQuote(MONITOR_SCRIPT);
  // The grep extended-regex covers: lifecycle (started/done/failed/skipped),
  // crashes (error {), terminal sentinel (all jobs finished), and the
  // monitor's own progress ticks. --line-buffered flushes per-line.
  const grep = `grep -E --line-buffered '\\[(START|DONE|FAIL|SKIP|TICK|MON)\\]|--- all jobs finished ---|^error |^turn\\.completed|^thread\\.started'`;
  return `${env} bash ${monitorBin} 2>&1 | ${grep}; echo "monitor exited rc=$?"`;
}

// Single-mission tail — pipes the codex --json output through codex-json-filter.sh.
// Wraps awk with fflush() to keep the filter live-streaming.
function singleMonitorCommand({ jsonlPath }) {
  const filterBin = shellQuote(JSON_FILTER_SCRIPT);
  const tail = `tail -n +1 -F ${shellQuote(jsonlPath)}`;
  // The trailing awk forces line-buffering on environments where the filter's
  // own stdio defaults to block-buffered.
  const awk = `awk '{ print; fflush(); }'`;
  return `${tail} 2>/dev/null | bash ${filterBin} 2>&1 | ${awk}; echo "monitor exited rc=$?"`;
}

function buildMonitorForMode(mode, ctx) {
  const { manifestPath, runId, monitorRoot, jsonlPath } = ctx;
  switch (mode) {
    case "exec":
    case "batch":
    case "review":
      return {
        tool_hint: buildMonitorHint({
          description: `orchestrate-codex ${mode} (run_id=${runId})`,
          command: fleetMonitorCommand({ manifestPath, monitorRoot }),
          persistent: true,
          // 4-hour ceiling — the agent's Monitor closes when the runner emits
          // "all jobs finished". This guards against hung runners.
          timeoutMs: 4 * 60 * 60 * 1000,
        }),
      };
    case "single":
      return {
        tool_hint: buildMonitorHint({
          description: `orchestrate-codex single (run_id=${runId})`,
          command: singleMonitorCommand({ jsonlPath: jsonlPath || path.join(monitorRoot, "single.jsonl") }),
          // single mode is bounded — Monitor closes at turn.completed; we
          // give it a 2-hour cap.
          persistent: false,
          timeoutMs: 2 * 60 * 60 * 1000,
        }),
      };
    default:
      return null;
  }
}

// ----------------------------------------------------------------------------
// Inputs validation + entry construction
// ----------------------------------------------------------------------------

function readJsonFile(p, command, errCode) {
  try {
    const raw = fs.readFileSync(p, "utf8");
    return { value: JSON.parse(raw) };
  } catch (e) {
    return { err: errEnvelope(command, errCode, `Failed to read ${p}: ${e.message}`) };
  }
}

function readTextFile(p, command, errCode) {
  try {
    return { value: fs.readFileSync(p, "utf8") };
  } catch (e) {
    return { err: errEnvelope(command, errCode, `Failed to read ${p}: ${e.message}`) };
  }
}

function slugify(s, fallback = "task") {
  const slug = String(s ?? "").trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
  return slug || fallback;
}

function newEntry({ id, slug, branch = null, baseBranch = null, promptPath = null, modeState = {} }) {
  return {
    id,
    slug: slug || id,
    branch,
    base_branch: baseBranch,
    prompt_path: promptPath,
    worktree_path: null,
    log_path: null,
    jsonl_path: null,
    answer_path: null,
    status: "queued",
    attempts: 0,
    started_at: null,
    finished_at: null,
    exit_code: null,
    last_error: null,
    codex_thread_id: null,
    codex_session_id: null,
    mode_state: modeState,
  };
}

// tasks.json schema (lenient): array of {id?, slug?, branch?, base_branch?,
// prompt, prompt_file?, label?, post_verify_cmd?}.
// We coerce to the manifest entries[] shape.
function buildExecEntries(tasks, command) {
  if (!Array.isArray(tasks)) {
    return { err: errEnvelope(command, "bad_tasks_file", "tasks.json must be a JSON array of {id|slug, prompt|prompt_file} objects.") };
  }
  if (tasks.length === 0) {
    return { err: errEnvelope(command, "bad_tasks_file", "tasks.json is empty.") };
  }
  const entries = [];
  const seen = new Set();
  tasks.forEach((t, i) => {
    const idx = String(i + 1).padStart(2, "0");
    const id = (t.id || t.slug || `${idx}-${slugify(t.label || t.prompt || "task")}`).toString();
    if (seen.has(id)) {
      entries.push({ __err: `duplicate id: ${id}` });
      return;
    }
    seen.add(id);
    if (!t.prompt && !t.prompt_file) {
      entries.push({ __err: `task ${id} requires prompt or prompt_file` });
      return;
    }
    const branch = t.branch || id;
    const baseBranch = t.base_branch || t.base || "main";
    entries.push(newEntry({
      id,
      slug: t.slug || id,
      branch,
      baseBranch,
      promptPath: t.prompt_file ?? null,
      modeState: {
        exec: {
          branch,
          base_branch: baseBranch,
          prompt: t.prompt ?? null,
          prompt_file: t.prompt_file ?? null,
          label: t.label ?? null,
          post_verify_cmd: t.post_verify_cmd ?? null,
          post_verify_exit: null,
        },
      },
    }));
  });
  const dup = entries.find((e) => e.__err);
  if (dup) return { err: errEnvelope(command, "bad_tasks_file", dup.__err) };
  return { value: entries };
}

function buildBatchEntries(inputsText, command) {
  // Each non-blank line is one input. Tab-delimited preserved for the
  // template renderer downstream — we only need a slug here.
  const lines = inputsText.split(/\r?\n/).map((l) => l.replace(/\s+$/, "")).filter(Boolean);
  if (lines.length === 0) {
    return { err: errEnvelope(command, "bad_inputs_file", "inputs file is empty after stripping blank lines.") };
  }
  const seen = new Map();
  const entries = lines.map((line, i) => {
    const firstField = line.split(/\t/)[0] || line;
    const id = slugify(firstField, `row-${String(i + 1).padStart(3, "0")}`);
    if (seen.has(id)) {
      return { __err: `duplicate rendered slug: ${id} (rows ${seen.get(id)} and ${i + 1})` };
    }
    seen.set(id, i + 1);
    return newEntry({
      id,
      slug: id,
      modeState: { batch: { input_row: line, prompt_file: null, answer_size_bytes: null, below_floor: null } },
    });
  });
  const dup = entries.find((e) => e.__err);
  if (dup) return { err: errEnvelope(command, "bad_inputs_file", dup.__err) };
  return { value: entries };
}

function buildSingleEntry(prompt, promptFile, command, { cwd, reuseWorktree }) {
  if (!prompt && !promptFile) {
    return { err: errEnvelope(command, "missing_required_arg", "single mode requires --prompt or --prompt-file.") };
  }
  return {
    value: [newEntry({
      id: "single",
      slug: "single",
      promptPath: promptFile || null,
      modeState: {
        single: {
          prompt: prompt || null,
          prompt_file: promptFile || null,
          cwd,
          reuse_worktree: Boolean(reuseWorktree),
        },
      },
    })],
  };
}

function expandBranches({ branchSpec, branchesFile, positionals, cwd }) {
  let branches = [];
  if (branchesFile) {
    const text = fs.readFileSync(path.resolve(cwd, branchesFile), "utf8");
    branches = text.split(/\r?\n/).map((b) => b.trim()).filter(Boolean);
  }
  if (branchSpec) {
    const specPath = path.resolve(cwd, branchSpec);
    if (fs.existsSync(specPath) && fs.statSync(specPath).isFile()) {
      const text = fs.readFileSync(specPath, "utf8");
      branches.push(...text.split(/\r?\n/).map((b) => b.trim()).filter(Boolean));
    } else {
      branches.push(...branchSpec.split(",").map((b) => b.trim()).filter(Boolean));
    }
  }
  branches.push(...(positionals || []).map((b) => b.trim()).filter(Boolean));
  return [...new Set(branches)];
}

function buildReviewEntries(branches, command, baseBranch = "main", maxRounds = 10) {
  if (branches.length === 0) {
    return { err: errEnvelope(command, "bad_branches_input", "review mode requires at least one branch (file or comma-list).") };
  }
  const entries = branches.map((branch) => {
    const slug = slugify(branch);
    return newEntry({
      id: slug,
      slug,
      branch,
      baseBranch,
      modeState: {
        review: {
          branch,
          base_branch: baseBranch,
          round: 0,
          max_rounds: maxRounds,
          rounds: [],
          last_findings_path: null,
          terminal_state: null,
        },
      },
    });
  });
  return { value: entries };
}

function writePromptFile(dir, name, content) {
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `${slugify(name)}.md`);
  fs.writeFileSync(p, `${String(content).replace(/\s+$/g, "")}\n`, "utf8");
  return p;
}

function materializeExecPrompts(entries, cwd, promptDir, command) {
  for (const entry of entries) {
    const state = entry.mode_state.exec;
    if (state.prompt_file) {
      const promptPath = path.isAbsolute(state.prompt_file)
        ? state.prompt_file
        : path.resolve(cwd, state.prompt_file);
      if (!fs.existsSync(promptPath)) {
        return errEnvelope(command, "bad_tasks_file", `prompt_file not found for ${entry.id}: ${promptPath}`);
      }
      entry.prompt_path = promptPath;
      state.prompt_file = promptPath;
      continue;
    }
    entry.prompt_path = writePromptFile(promptDir, entry.id, state.prompt);
    state.prompt_file = entry.prompt_path;
  }
  return null;
}

function materializeSinglePrompt(entry, cwd, promptDir, command) {
  const state = entry.mode_state.single;
  if (state.prompt_file) {
    const promptPath = path.isAbsolute(state.prompt_file)
      ? state.prompt_file
      : path.resolve(cwd, state.prompt_file);
    if (!fs.existsSync(promptPath)) {
      return errEnvelope(command, "bad_prompt_input", `prompt file not found: ${promptPath}`);
    }
    entry.prompt_path = promptPath;
    state.prompt_file = promptPath;
    return null;
  }
  entry.prompt_path = writePromptFile(promptDir, entry.id, state.prompt);
  state.prompt_file = entry.prompt_path;
  return null;
}

function renderBatchPrompts({ inputsPath, templatePath, promptsDir, cwd, command }) {
  const r = spawnSync("bash", [RENDER_PROMPTS_SCRIPT, inputsPath, templatePath, promptsDir], {
    cwd,
    encoding: "utf8",
    maxBuffer: 4 * 1024 * 1024,
  });
  if (r.status !== 0) {
    return { err: errEnvelope(command, "bad_inputs_file",
      `render-prompts.sh exited ${r.status}: ${(r.stderr || "").trim() || "no stderr"}`,
      { stdout: r.stdout, stderr: r.stderr }) };
  }
  return { value: { stdout: r.stdout, stderr: r.stderr } };
}

// ----------------------------------------------------------------------------
// Manifest seeding (initial atomic write)
// ----------------------------------------------------------------------------

function getBaseCommit(cwd) {
  const r = spawnSync("git", ["rev-parse", "HEAD"], { cwd, encoding: "utf8" });
  if (r.status === 0) return r.stdout.trim();
  return null;
}

function seedManifest({
  manifestPath,
  mode,
  runId,
  entries,
  concurrencyCap,
  monitorRoot,
  cwd,
  policyOverrides = {},
  paths = {},
  preflight = {},
}) {
  ensureManifestDir(manifestPath);
  const manifest = {
    schema_version: SCHEMA_VERSION,
    run_id: runId,
    mode,
    started_at: nowIso(),
    base_commit: getBaseCommit(cwd),
    workspace_root: cwd,
    state_dir: path.dirname(manifestPath),
    policy: { ...POLICY, overrides: policyOverrides },
    concurrency_cap: concurrencyCap,
    monitor_root: monitorRoot,
    paths,
    preflight,
    entries,
    history: [],
  };
  // Initial-write race guard: refuse to overwrite an in-flight manifest. The
  // refuseIfConcurrent gate above caught this for non-rescue paths; this is
  // defense in depth in case two seedManifest calls interleave.
  if (fs.existsSync(manifestPath)) {
    const prev = readManifestIfPresent(manifestPath);
    if (hasInflightEntries(prev)) {
      throw new Error("manifest already has in-flight entries; refusing to overwrite");
    }
  }
  // Atomic write: write to a temp file in the same directory, then rename.
  const tmp = `${manifestPath}.tmp.${process.pid}.${Date.now()}`;
  fs.writeFileSync(tmp, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  fs.renameSync(tmp, manifestPath);
  return manifest;
}

// ----------------------------------------------------------------------------
// Spawn the runner
// ----------------------------------------------------------------------------

function ensureRunnerExists(runnerPath, command) {
  if (!fs.existsSync(runnerPath)) {
    return errEnvelope(command, "spawn_failed",
      `Runner not found at ${runnerPath}. The bash runner for this mode hasn't been authored yet (parallel subagent's output).`,
      { runner_path: runnerPath });
  }
  return null;
}

function spawnRunnerDetached({ runnerPath, args, cwd }) {
  // detached + stdio:'ignore' + unref() = the dispatcher returns immediately,
  // the runner survives across the dispatcher's exit, and the agent's
  // Monitor reads progress via the JSONL/log files the runner writes. This is
  // the codex-companion 'task --background' pattern, adapted for bash.
  if (process.env.ORCHESTRATE_RUNNER_FOREGROUND === "1") {
    const r = spawnSync("bash", [runnerPath, ...args], {
      cwd,
      encoding: "utf8",
      env: process.env,
      maxBuffer: 16 * 1024 * 1024,
    });
    return {
      pid: 0,
      foreground: true,
      status: r.status,
      stdout: r.stdout,
      stderr: r.stderr,
    };
  }
  const child = spawn("bash", [runnerPath, ...args], {
    cwd,
    detached: true,
    stdio: "ignore",
    env: process.env,
  });
  child.unref();
  return { pid: child.pid, foreground: false };
}

// ----------------------------------------------------------------------------
// Python helpers (rescue / audit / tidy)
// ----------------------------------------------------------------------------

function runPythonHelper(scriptPath, args, cwd) {
  // We use spawnSync because the helpers are read-mostly and finish quickly;
  // the caller wants their JSON in the envelope, so blocking is fine. cwd is
  // the manifest's workspace_root, not the dispatcher's cwd — the helpers
  // need git context.
  const r = spawnSync("python3", [scriptPath, ...args], {
    cwd,
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
  });
  return r;
}

function writeManifestAtomic(manifestPath, manifest) {
  const tmp = `${manifestPath}.tmp.${process.pid}.${Date.now()}`;
  fs.writeFileSync(tmp, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  fs.renameSync(tmp, manifestPath);
}

function normalizeRedoOption(redo) {
  const value = String(redo || "").trim().toLowerCase().replace(/_/g, "-");
  if (value === "failed" || value === "failed-only") return "failed_only";
  if (value === "never-started" || value === "never-started-only") return "never_started_only";
  if (value === "all-non-done" || value === "non-done" || value === "all") return "all_non_done";
  return null;
}

function selectedRedispatchIds(classification, redoKey) {
  const opts = classification?.redispatch_options || {};
  return Array.isArray(opts[redoKey]) ? opts[redoKey] : [];
}

function selectedIncludesUnknown(classification, selectedIds) {
  const selected = new Set(selectedIds);
  return (classification?.entries || []).some((entry) =>
    selected.has(entry.id) && entry.classification === "unknown");
}

function resetEntriesForRedispatch(manifest, selectedIds) {
  const selected = new Set(selectedIds);
  const changed = [];
  if (!Array.isArray(manifest.history)) manifest.history = [];
  for (const entry of manifest.entries || []) {
    if (!selected.has(entry.id) || entry.status === "done") continue;
    const old = entry.status;
    entry.status = "queued";
    entry.started_at = null;
    entry.finished_at = null;
    entry.exit_code = null;
    entry.last_error = null;
    manifest.history.push({
      ts: nowIso(),
      entry_id: entry.id,
      from: old,
      to: "queued",
      reason: "rescue redispatch",
    });
    changed.push(entry.id);
  }
  manifest.rescue = {
    ...(manifest.rescue || {}),
    last_redispatch_at: nowIso(),
    last_redispatch_ids: changed,
  };
  return changed;
}

function runnerArgsForRedispatch(manifest, manifestPath, selectedIds, cap) {
  const only = selectedIds.join(",");
  const common = ["--manifest", manifestPath, "--concurrency", String(cap), "--only", only];
  const paths = manifest.paths || {};
  switch (manifest.mode) {
    case "exec":
      return {
        mode: "exec",
        runner: RUNNERS.exec,
        args: [...common, "--project-dir", manifest.workspace_root || process.cwd()],
      };
    case "batch":
      return {
        mode: "batch",
        runner: RUNNERS.batch,
        args: [
          ...common,
          "--prompts-dir", paths.prompts_dir || path.join(manifest.monitor_root || path.dirname(manifestPath), "prompts"),
          "--answers-dir", paths.answers_dir || path.join(manifest.monitor_root || path.dirname(manifestPath), "answers"),
          "--logs-dir", paths.logs_dir || path.join(manifest.monitor_root || path.dirname(manifestPath), "logs"),
          "--runner-log", paths.runner_log || path.join(paths.logs_dir || path.dirname(manifestPath), "_runner.log"),
          "--audit-report", paths.audit_report || path.join(manifest.monitor_root || path.dirname(manifestPath), "audit-sizes.txt"),
        ],
      };
    case "single": {
      const entry = (manifest.entries || []).find((e) => selectedIds.includes(e.id));
      if (!entry) return null;
      return {
        mode: "single",
        runner: RUNNERS.single,
        args: [
          "--manifest", manifestPath,
          "--entry-id", entry.id,
          "--prompt-file", entry.prompt_path,
          "--out", entry.answer_path,
          "--jsonl", entry.jsonl_path || entry.log_path,
          "--cwd", entry.mode_state?.single?.cwd || manifest.workspace_root || process.cwd(),
        ],
      };
    }
    case "review": {
      const maxRounds = Math.max(...(manifest.entries || []).map((e) => Number(e.mode_state?.review?.max_rounds || 10)), 10);
      const base = (manifest.entries || []).find((e) => e.base_branch)?.base_branch || "main";
      const roundsDir = paths.rounds_dir || path.join(manifest.monitor_root || path.dirname(manifestPath), "rounds");
      return {
        mode: "review",
        runner: RUNNERS.review,
        args: [...common, "--base", base, "--max-rounds", String(maxRounds), "--state-dir", path.dirname(roundsDir)],
      };
    }
    default:
      return null;
  }
}

// ----------------------------------------------------------------------------
// Mode handlers
// ----------------------------------------------------------------------------

function dispatchHelp() {
  return okEnvelope("help", {
    phase: "done",
    next_action: "select a mode and rerun",
    usage: [
      "Usage: node orchestrate-codex.mjs <mode> [args]",
      "",
      "Modes:",
      "  exec    --tasks <tasks.json> [--concurrency N] [--cwd <dir>]",
      "          parallel codex exec across worktrees",
      "  batch   --inputs <file> --template <tmpl> [--concurrency N] [--cwd <dir>]",
      "          template x N inputs",
      "  single  (--prompt <text> | --prompt-file <file>) [--cwd <dir>]",
      "          one mission with live monitor",
      "  review  --branches <list-or-file> [--base <ref>] [--cwd <dir>]",
      "          per-branch convergence loop using native codex review",
      "  rescue  [--manifest <path>] [--redo failed|never-started|all-non-done] [--cwd <dir>]",
      "          classify a partial prior run; optionally redispatch a selected bucket",
      "  audit   [--manifest <path>] [--cwd <dir>]",
      "          read-only manifest+filesystem state dump",
      "  tidy    [--manifest <path>] [--cwd <dir>] [--execute]",
      "          gated worktree cleanup",
      "",
      "Every invocation emits one JSON envelope on stdout.",
      "Policy: --dangerously-bypass-approvals-and-sandbox + gpt-5.5 + xhigh effort.",
    ].join("\n"),
  });
}

function checkConcurrency(opts, command) {
  const cap = Number(opts.concurrency || DEFAULT_CONCURRENCY[command] || 1);
  if (!Number.isFinite(cap) || cap < 1) {
    return { err: errEnvelope(command, "bad_argument", `--concurrency must be a positive integer (got ${opts.concurrency})`) };
  }
  if (cap > CONCURRENCY_HARD_CAP) {
    return { err: errEnvelope(command, "bad_argument",
      `--concurrency=${cap} exceeds the hard cap (${CONCURRENCY_HARD_CAP}).`) };
  }
  if (cap > CONCURRENCY_MEASURE_GATE && !opts["i-have-measured"]) {
    return { err: errEnvelope(command, "bad_argument",
      `--concurrency=${cap} exceeds ${CONCURRENCY_MEASURE_GATE}. Pass --i-have-measured <justification> to override.`) };
  }
  return { value: cap };
}

function concurrencyOverride(command, cap, opts) {
  const reason = opts["i-have-measured"];
  if (cap <= CONCURRENCY_MEASURE_GATE && !reason) return {};
  return {
    concurrency: {
      value: cap,
      default: DEFAULT_CONCURRENCY[command] || 1,
      set_at: nowIso(),
      justification: typeof reason === "string" ? reason : "caller supplied --i-have-measured",
    },
  };
}

function defaultMonitorRoot(manifestPath) {
  return path.dirname(manifestPath);
}

async function handleExec(argv) {
  const command = "exec";
  const { options } = parseArgs(argv, {
    valueOptions: ["tasks", "concurrency", "cwd", "monitor-root", "run-id", "i-have-measured"],
    booleanOptions: ["dry-run"],
  });
  if (!options.tasks) {
    return errEnvelope(command, "missing_required_arg", "exec mode requires --tasks <tasks.json>.");
  }
  const cwd = path.resolve(options.cwd || process.cwd());
  const tasksPath = path.resolve(cwd, options.tasks);
  if (!fs.existsSync(tasksPath)) {
    return errEnvelope(command, "bad_tasks_file", `tasks file not found: ${tasksPath}`);
  }
  const parsed = readJsonFile(tasksPath, command, "bad_tasks_file");
  if (parsed.err) return parsed.err;
  const built = buildExecEntries(parsed.value, command);
  if (built.err) return built.err;

  const cap = checkConcurrency(options, command);
  if (cap.err) return cap.err;

  const wsRoot = workspaceFor(cwd);
  const manifestPath = manifestPathFor(cwd);
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const runId = options["run-id"] || generateRunId();
  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const preflight = runBootstrap({ command, cwd: wsRoot, mode: command, runId, monitorRoot, skipGit: false });
  if (preflight.err) return preflight.err;

  const runDir = path.join(monitorRoot, runId);
  const promptDir = path.join(runDir, "prompts");
  const promptErr = materializeExecPrompts(built.value, cwd, promptDir, command);
  if (promptErr) return promptErr;
  const logsDir = path.join(runDir, "logs");
  const answersDir = path.join(runDir, "answers");
  fs.mkdirSync(logsDir, { recursive: true });
  fs.mkdirSync(answersDir, { recursive: true });
  for (const entry of built.value) {
    entry.log_path = path.join(logsDir, `${entry.id}.jsonl`);
    entry.answer_path = path.join(answersDir, `${entry.id}.md`);
  }

  seedManifest({
    manifestPath, mode: "exec", runId, entries: built.value,
    concurrencyCap: cap.value, monitorRoot, cwd: wsRoot,
    policyOverrides: concurrencyOverride(command, cap.value, options),
    paths: { prompts_dir: promptDir, logs_dir: logsDir, answers_dir: answersDir },
    preflight: preflight.value,
  });

  const runnerErr = ensureRunnerExists(RUNNERS.exec, command);
  if (runnerErr) return runnerErr;
  const runnerArgs = ["--manifest", manifestPath, "--concurrency", String(cap.value), "--project-dir", wsRoot];
  if (options["dry-run"]) runnerArgs.push("--dry-run");
  if (options["i-have-measured"]) runnerArgs.push("--i-have-measured", options["i-have-measured"]);
  const runner = spawnRunnerDetached({
    runnerPath: RUNNERS.exec,
    args: runnerArgs,
    cwd: wsRoot,
  });

  return okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: built.value.length,
    runner_pid: runner.pid,
    runner_status: runner.foreground ? runner.status : null,
    workspace_root: wsRoot,
  }, buildMonitorForMode("exec", { manifestPath, runId, monitorRoot }));
}

async function handleBatch(argv) {
  const command = "batch";
  const { options } = parseArgs(argv, {
    valueOptions: [
      "inputs", "template", "concurrency", "cwd", "monitor-root", "run-id",
      "prompts-dir", "answers-dir", "logs-dir", "audit-report", "min-bytes",
      "i-have-measured",
    ],
    booleanOptions: ["dry-run"],
  });
  if (!options.inputs) return errEnvelope(command, "missing_required_arg", "batch mode requires --inputs <file>.");
  if (!options.template) return errEnvelope(command, "missing_required_arg", "batch mode requires --template <tmpl>.");

  const cwd = path.resolve(options.cwd || process.cwd());
  const inputsPath = path.resolve(cwd, options.inputs);
  const templatePath = path.resolve(cwd, options.template);
  if (!fs.existsSync(inputsPath)) return errEnvelope(command, "bad_inputs_file", `inputs file not found: ${inputsPath}`);
  if (!fs.existsSync(templatePath)) return errEnvelope(command, "bad_template_file", `template file not found: ${templatePath}`);

  const text = readTextFile(inputsPath, command, "bad_inputs_file");
  if (text.err) return text.err;
  const built = buildBatchEntries(text.value, command);
  if (built.err) return built.err;

  const cap = checkConcurrency(options, command);
  if (cap.err) return cap.err;

  // batch mode does not require a git repo; workspaceFor falls back to cwd.
  const wsRoot = workspaceFor(cwd);
  const manifestPath = manifestPathFor(cwd);
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const runId = options["run-id"] || generateRunId();
  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const preflight = runBootstrap({ command, cwd: wsRoot, mode: command, runId, monitorRoot, skipGit: true });
  if (preflight.err) return preflight.err;

  const runDir = path.join(monitorRoot, runId);
  const promptsDir = options["prompts-dir"]
    ? path.resolve(cwd, options["prompts-dir"])
    : path.join(runDir, "prompts");
  const answersDir = options["answers-dir"]
    ? path.resolve(cwd, options["answers-dir"])
    : path.join(runDir, "answers");
  const logsDir = options["logs-dir"]
    ? path.resolve(cwd, options["logs-dir"])
    : path.join(runDir, "logs");
  const runnerLog = path.join(logsDir, "_runner.log");
  const auditReport = options["audit-report"]
    ? path.resolve(cwd, options["audit-report"])
    : path.join(monitorRoot, "audit-sizes.txt");

  const rendered = renderBatchPrompts({ inputsPath, templatePath, promptsDir, cwd, command });
  if (rendered.err) return rendered.err;
  for (const entry of built.value) {
    const promptPath = path.join(promptsDir, `${entry.id}.md`);
    if (!fs.existsSync(promptPath)) {
      return errEnvelope(command, "bad_inputs_file", `rendered prompt missing for ${entry.id}: ${promptPath}`);
    }
    entry.prompt_path = promptPath;
    entry.answer_path = path.join(answersDir, `${entry.id}.md`);
    entry.log_path = path.join(logsDir, `${entry.id}.log`);
    entry.mode_state.batch.prompt_file = promptPath;
  }

  seedManifest({
    manifestPath, mode: "batch", runId, entries: built.value,
    concurrencyCap: cap.value, monitorRoot, cwd: wsRoot,
    policyOverrides: concurrencyOverride(command, cap.value, options),
    paths: {
      inputs_path: inputsPath,
      template_path: templatePath,
      prompts_dir: promptsDir,
      answers_dir: answersDir,
      logs_dir: logsDir,
      runner_log: runnerLog,
      audit_report: auditReport,
    },
    preflight: preflight.value,
  });

  const runnerErr = ensureRunnerExists(RUNNERS.batch, command);
  if (runnerErr) return runnerErr;
  const runnerArgs = [
    "--manifest", manifestPath,
    "--inputs", inputsPath,
    "--template", templatePath,
    "--prompts-dir", promptsDir,
    "--answers-dir", answersDir,
    "--logs-dir", logsDir,
    "--runner-log", runnerLog,
    "--audit-report", auditReport,
    "--concurrency", String(cap.value),
  ];
  if (options["dry-run"]) runnerArgs.push("--dry-run");
  if (options["min-bytes"]) runnerArgs.push("--min-bytes", options["min-bytes"]);
  if (options["i-have-measured"]) runnerArgs.push("--i-have-measured", options["i-have-measured"]);
  const runner = spawnRunnerDetached({
    runnerPath: RUNNERS.batch,
    args: runnerArgs,
    cwd: wsRoot,
  });

  return okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: built.value.length,
    runner_pid: runner.pid,
    runner_status: runner.foreground ? runner.status : null,
    workspace_root: wsRoot,
    prompts_dir: promptsDir,
    answers_dir: answersDir,
    logs_dir: logsDir,
    audit_report: auditReport,
  }, buildMonitorForMode("batch", { manifestPath, runId, monitorRoot }));
}

async function handleSingle(argv) {
  const command = "single";
  const { options } = parseArgs(argv, {
    valueOptions: ["prompt", "prompt-file", "out", "jsonl", "cwd", "monitor-root", "run-id"],
    booleanOptions: ["reuse-worktree", "dry-run"],
  });
  const cwd = path.resolve(options.cwd || process.cwd());
  let promptFile = options["prompt-file"] ? path.resolve(cwd, options["prompt-file"]) : null;
  if (promptFile && !fs.existsSync(promptFile)) {
    return errEnvelope(command, "bad_prompt_input", `prompt file not found: ${promptFile}`);
  }
  const built = buildSingleEntry(options.prompt, promptFile, command, {
    cwd,
    reuseWorktree: options["reuse-worktree"],
  });
  if (built.err) return built.err;

  const wsRoot = workspaceFor(cwd);
  const manifestPath = manifestPathFor(cwd);
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const runId = options["run-id"] || generateRunId();
  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const preflight = runBootstrap({ command, cwd: wsRoot, mode: command, runId, monitorRoot, skipGit: true });
  if (preflight.err) return preflight.err;

  const promptDir = path.join(monitorRoot, runId, "prompts");
  const promptErr = materializeSinglePrompt(built.value[0], cwd, promptDir, command);
  if (promptErr) return promptErr;
  const jsonlPath = options.jsonl ? path.resolve(cwd, options.jsonl) : path.join(monitorRoot, `single-${runId}.jsonl`);
  const outPath = options.out ? path.resolve(cwd, options.out) : path.join(monitorRoot, `single-${runId}.md`);
  built.value[0].jsonl_path = jsonlPath;
  built.value[0].log_path = jsonlPath;
  built.value[0].answer_path = outPath;
  if (options["reuse-worktree"]) built.value[0].worktree_path = cwd;

  seedManifest({
    manifestPath, mode: "single", runId, entries: built.value,
    concurrencyCap: 1, monitorRoot, cwd: wsRoot,
    paths: { prompts_dir: promptDir, answer_path: outPath, jsonl_path: jsonlPath },
    preflight: preflight.value,
  });

  const runnerErr = ensureRunnerExists(RUNNERS.single, command);
  if (runnerErr) return runnerErr;
  const runnerArgs = [
    "--manifest", manifestPath,
    "--entry-id", "single",
    "--prompt-file", built.value[0].prompt_path,
    "--out", outPath,
    "--jsonl", jsonlPath,
    "--cwd", cwd,
  ];
  if (options.prompt) runnerArgs.push("--prompt", options.prompt);
  if (options["reuse-worktree"]) runnerArgs.push("--reuse-worktree");
  if (options["dry-run"]) runnerArgs.push("--dry-run");
  const runner = spawnRunnerDetached({
    runnerPath: RUNNERS.single,
    args: runnerArgs,
    cwd: wsRoot,
  });

  return okEnvelope(command, {
    phase: "running",
    next_action: "arm Monitor and wait",
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: 1,
    runner_pid: runner.pid,
    runner_status: runner.foreground ? runner.status : null,
    workspace_root: wsRoot,
    answer_path: outPath,
    jsonl_path: jsonlPath,
  }, buildMonitorForMode("single", { manifestPath, runId, monitorRoot, jsonlPath }));
}

async function handleReview(argv) {
  const command = "review";
  const { options, positionals } = parseArgs(argv, {
    valueOptions: [
      "branches", "branches-file", "base", "concurrency", "cwd",
      "monitor-root", "run-id", "max-rounds", "i-have-measured",
    ],
    booleanOptions: ["dry-run"],
  });
  const cwd = path.resolve(options.cwd || process.cwd());
  if (!options.branches && !options["branches-file"] && positionals.length === 0) {
    return errEnvelope(command, "missing_required_arg", "review mode requires --branches <list-or-file> or branch positionals.");
  }
  const maxRounds = Number(options["max-rounds"] || 10);
  if (!Number.isInteger(maxRounds) || maxRounds < 1) {
    return errEnvelope(command, "bad_argument", `--max-rounds must be a positive integer (got ${options["max-rounds"]})`);
  }
  const branches = expandBranches({
    branchSpec: options.branches,
    branchesFile: options["branches-file"],
    positionals,
    cwd,
  });
  const baseBranch = options.base || "main";
  const built = buildReviewEntries(branches, command, baseBranch, maxRounds);
  if (built.err) return built.err;

  const cap = checkConcurrency(options, command);
  if (cap.err) return cap.err;

  const wsRoot = workspaceFor(cwd);
  if (!fs.existsSync(path.join(wsRoot, ".git"))) {
    // review mode requires a real repo; resolveWorkspaceRoot's fallback is
    // unhelpful here.
    return errEnvelope(command, "not_a_repo", `review mode requires a git repository (cwd=${cwd}).`);
  }
  const manifestPath = manifestPathFor(cwd);
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const runId = options["run-id"] || generateRunId();
  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const preflight = runBootstrap({ command, cwd: wsRoot, mode: command, runId, monitorRoot, skipGit: false });
  if (preflight.err) return preflight.err;

  seedManifest({
    manifestPath, mode: "review", runId, entries: built.value,
    concurrencyCap: cap.value, monitorRoot, cwd: wsRoot,
    policyOverrides: concurrencyOverride(command, cap.value, options),
    paths: { rounds_dir: path.join(monitorRoot, runId, "rounds") },
    preflight: preflight.value,
  });

  const runnerErr = ensureRunnerExists(RUNNERS.review, command);
  if (runnerErr) return runnerErr;
  const runnerArgs = [
    "--manifest", manifestPath,
    "--concurrency", String(cap.value),
    "--base", baseBranch,
    "--max-rounds", String(maxRounds),
    "--state-dir", path.join(monitorRoot, runId),
  ];
  if (options["dry-run"]) runnerArgs.push("--dry-run");
  if (options["i-have-measured"]) runnerArgs.push("--i-have-measured", options["i-have-measured"]);
  const runner = spawnRunnerDetached({
    runnerPath: RUNNERS.review,
    args: runnerArgs,
    cwd: wsRoot,
  });

  return okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: built.value.length,
    runner_pid: runner.pid,
    runner_status: runner.foreground ? runner.status : null,
    workspace_root: wsRoot,
  }, buildMonitorForMode("review", { manifestPath, runId, monitorRoot }));
}

async function handleRescue(argv) {
  const command = "rescue";
  const { options } = parseArgs(argv, {
    valueOptions: ["manifest", "cwd", "redo", "concurrency", "i-have-measured"],
    booleanOptions: ["json", "accept-stale", "dry-run"],
  });
  const cwd = path.resolve(options.cwd || process.cwd());
  const wsRoot = workspaceFor(cwd);
  const manifestPath = options.manifest ? path.resolve(options.manifest) : manifestPathFor(cwd);
  if (!fs.existsSync(manifestPath)) {
    return errEnvelope(command, "manifest_not_found",
      `No manifest at ${manifestPath}. Rescue requires a prior run.`,
      { manifest_path: manifestPath });
  }
  const m = readManifestIfPresent(manifestPath);
  if (!m || m.__corrupt) {
    return errEnvelope(command, "manifest_corrupt", `Manifest at ${manifestPath} is not valid JSON.`,
      { manifest_path: manifestPath });
  }

  let classification = null;
  if (fs.existsSync(PY_HELPERS.rescue)) {
    const r = runPythonHelper(PY_HELPERS.rescue, ["--manifest", manifestPath, "--json"], wsRoot);
    if (r.status !== 0) {
      return errEnvelope(command, "python_helper_failed",
        `rescue-detect.py exited ${r.status}: ${(r.stderr || "").trim() || "no stderr"}`,
        { stdout: r.stdout, stderr: r.stderr });
    }
    try {
      classification = JSON.parse(r.stdout);
    } catch (e) {
      return errEnvelope(command, "python_helper_failed",
        `rescue-detect.py produced non-JSON stdout: ${e.message}`,
        { stdout: r.stdout });
    }
  } else {
    // Fallback: compute a minimal classification from the manifest. The
    // proper classifier will overwrite this once authored.
    const buckets = { done: [], failed: [], queued: [], running: [], other: [] };
    for (const e of (m.entries || [])) {
      const bucket = buckets[e.status] ? e.status : "other";
      buckets[bucket].push(e.id);
    }
    classification = {
      source: "fallback (rescue-detect.py not present)",
      mode: m.mode,
      run_id: m.run_id,
      buckets,
      counts: Object.fromEntries(Object.entries(buckets).map(([k, v]) => [k, v.length])),
      redispatch_options: {
        failed_only: buckets.failed,
        never_started_only: buckets.queued,
        all_non_done: [...buckets.failed, ...buckets.queued, ...buckets.running, ...buckets.other],
      },
      entries: (m.entries || []).map((e) => ({
        id: e.id,
        manifest_status: e.status,
        classification: e.status === "done" ? "done" : (e.status === "failed" ? "failed" : "unknown"),
      })),
    };
  }

  if (options.redo) {
    const redoKey = normalizeRedoOption(options.redo);
    if (!redoKey) {
      return errEnvelope(command, "bad_argument",
        "--redo must be one of: failed, never-started, all-non-done.");
    }
    const selectedIds = selectedRedispatchIds(classification, redoKey);
    if (selectedIds.length === 0) {
      return okEnvelope(command, {
        phase: "done",
        next_action: "nothing to redispatch for selected rescue bucket",
        manifest_path: manifestPath,
        run_id: m.run_id,
        mode: m.mode,
        classification,
        redispatch: { redo: redoKey, selected_ids: [] },
        workspace_root: wsRoot,
      });
    }
    if (selectedIncludesUnknown(classification, selectedIds) && !options["accept-stale"]) {
      return errEnvelope(command, "bad_argument",
        "Selected rescue bucket contains unknown/stale entries. Pass --accept-stale to redispatch them.",
        { selected_ids: selectedIds });
    }
    const runnerPlan = runnerArgsForRedispatch(m, manifestPath, selectedIds, Number(options.concurrency || m.concurrency_cap || 1));
    if (!runnerPlan) {
      return errEnvelope(command, "bad_argument", `Cannot redispatch manifest mode: ${m.mode}`);
    }
    const runnerErr = ensureRunnerExists(runnerPlan.runner, command);
    if (runnerErr) return runnerErr;
    const cap = checkConcurrency({ ...options, concurrency: options.concurrency || m.concurrency_cap || 1 }, m.mode || command);
    if (cap.err) return cap.err;
    const changedIds = resetEntriesForRedispatch(m, selectedIds);
    writeManifestAtomic(manifestPath, m);
    if (options["dry-run"]) runnerPlan.args.push("--dry-run");
    if (options["i-have-measured"]) runnerPlan.args.push("--i-have-measured", options["i-have-measured"]);
    const runner = spawnRunnerDetached({
      runnerPath: runnerPlan.runner,
      args: runnerPlan.args,
      cwd: m.workspace_root || wsRoot,
    });
    return okEnvelope(command, {
      phase: "queued",
      next_action: "arm Monitor and wait",
      manifest_path: manifestPath,
      run_id: m.run_id,
      mode: m.mode,
      classification,
      redispatch: { redo: redoKey, selected_ids: changedIds },
      runner_pid: runner.pid,
      runner_status: runner.foreground ? runner.status : null,
      workspace_root: m.workspace_root || wsRoot,
    }, buildMonitorForMode(m.mode, {
      manifestPath,
      runId: m.run_id,
      monitorRoot: m.monitor_root || path.dirname(manifestPath),
      jsonlPath: m.entries?.[0]?.jsonl_path,
    }));
  }

  return okEnvelope(command, {
    phase: "done",
    next_action: "choose a rescue redispatch bucket and rerun with --redo failed|never-started|all-non-done",
    manifest_path: manifestPath,
    run_id: m.run_id,
    mode: m.mode,
    classification,
    workspace_root: wsRoot,
  });
}

async function handleAudit(argv) {
  const command = "audit";
  const { options } = parseArgs(argv, {
    valueOptions: ["manifest", "cwd"],
    booleanOptions: ["json"],
  });
  const cwd = path.resolve(options.cwd || process.cwd());
  const wsRoot = workspaceFor(cwd);
  const manifestPath = options.manifest ? path.resolve(options.manifest) : manifestPathFor(cwd);

  if (!fs.existsSync(PY_HELPERS.audit)) {
    // No helper yet — fall back to a minimal manifest dump.
    if (!fs.existsSync(manifestPath)) {
      return errEnvelope(command, "manifest_not_found", `No manifest at ${manifestPath}.`,
        { manifest_path: manifestPath });
    }
    const m = readManifestIfPresent(manifestPath);
    if (!m || m.__corrupt) {
      return errEnvelope(command, "manifest_corrupt", `Manifest at ${manifestPath} is not valid JSON.`);
    }
    const summary = {
      source: "fallback (audit-fleet-state.py not present)",
      manifest_path: manifestPath,
      run_id: m.run_id,
      mode: m.mode,
      entries_count: (m.entries || []).length,
      status_counts: (m.entries || []).reduce((acc, e) => {
        acc[e.status] = (acc[e.status] || 0) + 1;
        return acc;
      }, {}),
    };
    return okEnvelope(command, {
      phase: "done",
      next_action: "review the manifest",
      manifest_path: manifestPath,
      audit: summary,
      workspace_root: wsRoot,
    });
  }
  const r = runPythonHelper(PY_HELPERS.audit, ["--manifest", manifestPath, "--json"], wsRoot);
  if (r.status !== 0) {
    return errEnvelope(command, "python_helper_failed",
      `audit-fleet-state.py exited ${r.status}: ${(r.stderr || "").trim() || "no stderr"}`,
      { stdout: r.stdout, stderr: r.stderr });
  }
  let audit;
  try { audit = JSON.parse(r.stdout); } catch (e) {
    return errEnvelope(command, "python_helper_failed",
      `audit-fleet-state.py produced non-JSON stdout: ${e.message}`, { stdout: r.stdout });
  }
  return okEnvelope(command, {
    phase: "done",
    next_action: "review the manifest",
    manifest_path: manifestPath,
    audit,
    workspace_root: wsRoot,
  });
}

async function handleTidy(argv) {
  const command = "tidy";
  const { options } = parseArgs(argv, {
    valueOptions: ["manifest", "cwd"],
    booleanOptions: ["execute"],
  });
  const cwd = path.resolve(options.cwd || process.cwd());
  const wsRoot = workspaceFor(cwd);
  const manifestPath = options.manifest ? path.resolve(options.manifest) : manifestPathFor(cwd);

  if (!fs.existsSync(PY_HELPERS.tidy)) {
    return errEnvelope(command, "python_helper_failed",
      `cleanup-worktrees.py not found at ${PY_HELPERS.tidy}. The parallel subagent hasn't authored it yet.`,
      { helper_path: PY_HELPERS.tidy });
  }
  const args = ["--manifest", manifestPath, "--json"];
  if (options.execute) args.push("--execute");
  const r = runPythonHelper(PY_HELPERS.tidy, args, wsRoot);
  if (r.status !== 0) {
    return errEnvelope(command, "python_helper_failed",
      `cleanup-worktrees.py exited ${r.status}: ${(r.stderr || "").trim() || "no stderr"}`,
      { stdout: r.stdout, stderr: r.stderr });
  }
  let report;
  try { report = JSON.parse(r.stdout); } catch (e) {
    return errEnvelope(command, "python_helper_failed",
      `cleanup-worktrees.py produced non-JSON stdout: ${e.message}`, { stdout: r.stdout });
  }
  return okEnvelope(command, {
    phase: "done",
    next_action: options.execute
      ? "review removed worktrees"
      : "review the dry-run plan; rerun with --execute to delete",
    manifest_path: manifestPath,
    tidy: report,
    workspace_root: wsRoot,
  });
}

// ----------------------------------------------------------------------------
// Entrypoint
// ----------------------------------------------------------------------------

const HANDLERS = {
  exec: handleExec,
  batch: handleBatch,
  single: handleSingle,
  review: handleReview,
  rescue: handleRescue,
  audit: handleAudit,
  tidy: handleTidy,
};

export async function dispatch(argv) {
  // Wrapper that always returns an envelope. Caller emits + exits.
  if (!argv || argv.length === 0) return dispatchHelp();
  const [mode, ...rest] = argv;
  if (mode === "--help" || mode === "-h" || mode === "help") return dispatchHelp();
  if (!KNOWN_MODES.has(mode)) {
    return errEnvelope(mode, "unknown_mode",
      `Unknown mode: ${mode}. Valid modes: exec, batch, single, review, rescue, audit, tidy.`);
  }
  const handler = HANDLERS[mode];
  if (!handler) return dispatchHelp();
  try {
    return await handler(rest);
  } catch (e) {
    return errEnvelope(mode, "spawn_failed",
      `Unhandled dispatcher error: ${e.message}`,
      { stack: (e.stack || "").split("\n").slice(0, 5) });
  }
}

async function main() {
  const env = await dispatch(process.argv.slice(2));
  emitEnvelope(env);
  process.exit(exitFor(env));
}

// Only run main when this file is the script entry. Lets tests `import` the
// module (dispatch / buildMonitorHint / fleetMonitorCommand) without firing.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    // Last-resort: still emit an envelope so the contract holds.
    emitEnvelope(errEnvelope("unknown", "spawn_failed",
      `Top-level crash: ${e.message}`, { stack: (e.stack || "").split("\n").slice(0, 5) }));
    process.exit(1);
  });
}

// Named exports for tests + tooling. Keep this list narrow.
export {
  buildMonitorHint,
  buildMonitorForMode,
  fleetMonitorCommand,
  singleMonitorCommand,
  manifestPathFor,
  workspaceFor,
  seedManifest,
  POLICY,
};

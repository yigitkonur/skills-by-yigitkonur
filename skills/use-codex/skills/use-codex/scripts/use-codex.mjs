#!/usr/bin/env node
// use-codex.mjs — top-level dispatcher for the use-codex skill.
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
// USE_CODEX_RUNNER_<MODE> env vars are an explicit test/dev hatch — they
// let the integration suite point at a stub without dropping a stub into the
// shipped scripts/ tree. Production callers never set these.
const RUNNERS = {
  exec: process.env.USE_CODEX_RUNNER_EXEC || path.join(SCRIPT_DIR, "run-fleet.sh"),
  batch: process.env.USE_CODEX_RUNNER_BATCH || path.join(SCRIPT_DIR, "run-batch.sh"),
  single: process.env.USE_CODEX_RUNNER_SINGLE || path.join(SCRIPT_DIR, "run-single.sh"),
  review: process.env.USE_CODEX_RUNNER_REVIEW || path.join(SCRIPT_DIR, "run-review.sh"),
};

const PY_HELPERS = {
  rescue: process.env.USE_CODEX_HELPER_RESCUE || path.join(SCRIPT_DIR, "rescue-detect.py"),
  audit: process.env.USE_CODEX_HELPER_AUDIT || path.join(SCRIPT_DIR, "audit-fleet-state.py"),
  tidy: process.env.USE_CODEX_HELPER_TIDY || path.join(SCRIPT_DIR, "cleanup-worktrees.py"),
  manifestUpdate: process.env.USE_CODEX_HELPER_MANIFEST_UPDATE
    || path.join(SCRIPT_DIR, "manifest-update.py"),
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

// Soft gate: above this requires --i-have-measured "<justification>".
// Aligns with references/universal/concurrency.md.
const CONCURRENCY_HARD_CAP = 20;
// Hard ceiling: refused unconditionally — assumes a single user's auth tier.
const CONCURRENCY_ABSOLUTE_CEILING = 100;
// Legacy alias retained for any external code that imported the old name.
const CONCURRENCY_MEASURE_GATE = CONCURRENCY_HARD_CAP;

// Monitor's hard timeout ceiling — Claude Code's Monitor tool refuses
// timeout_ms > 1h. Any larger value is silently clamped. We clamp here so the
// envelope value reflects what Monitor will actually honor.
const MONITOR_HARD_MAX_MS = 60 * 60 * 1000;

// Subsets recognised by `rescue --apply <subset>` (S8 rescue redispatch UI).
const RESCUE_APPLY_SUBSETS = new Set([
  "failed-only",
  "never-started-only",
  "all-non-done",
]);

const POLICY = {
  model: process.env.USE_CODEX_CODEX_MODEL || "gpt-5.5",
  effort: process.env.USE_CODEX_CODEX_EFFORT || "xhigh",
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
  unknown_option: 2,
  missing_required_arg: 2,
  bad_argument: 2,
  bad_inputs_file: 2,
  bad_tasks_file: 2,
  bad_template_file: 2,
  bad_prompt_input: 2,
  bad_branches_input: 2,
  bad_schema_file: 2,
  not_a_repo: 2,
  manifest_not_found: 3,
  manifest_corrupt: 3,
  manifest_stale: 3,
  schema_version_too_new: 3,
  concurrent_run_in_progress: 3,
  manifest_inflight_race: 3,
  spawn_failed: 4,
  python_helper_failed: 4,
  codex_unauthenticated: 5,
  codex_unavailable: 5,
};

function exitFor(env) {
  if (env.ok) return 0;
  const code = env?.error?.code;
  return EXIT_CODE_BY_ERROR[code] ?? 1;
}

// ----------------------------------------------------------------------------
// Strict argv parsing — wrap parseArgs so unknown long-options error out
// instead of being silently shoved into `positionals`.
// ----------------------------------------------------------------------------

// P1-6: per-mode usage strings — short-circuit `<mode> --help` (or `-h`) at
// parseArgsStrict so each mode handler returns a help envelope instead of
// rejecting `--help` as unknown_option. Calling top-level `--help` keeps
// returning the full multi-mode usage via dispatchHelp.
const MODE_USAGE = {
  exec: [
    "Usage: node use-codex.mjs exec --tasks <tasks.json> [args]",
    "",
    "Required:",
    "  --tasks <tasks.json>             JSON array of {id|slug, prompt|prompt_file, ...}",
    "",
    "Optional:",
    "  --cwd <dir>                      workspace cwd (default: process.cwd)",
    "  --concurrency N                  jobs (default 5; >20 needs --i-have-measured)",
    "  --i-have-measured \"<reason>\"     justification for raised concurrency",
    "  --force-redo <slug[,slug2,...]>  archive answers + flip selected entries to queued",
    "  --force-redo-all                 archive + flip every entry in the manifest",
    "  --force-new-run --run-id <id>    write to manifest.<id>.json (sibling run)",
    "  --monitor-root <dir>             override monitor/state root",
    "  --dry-run                        seed manifest + print runner cmd; no codex spawn",
    "",
    "Spawns N parallel codex exec workers in per-entry worktrees with auto-commit.",
  ].join("\n"),
  batch: [
    "Usage: node use-codex.mjs batch --inputs <file> --template <tmpl> [args]",
    "",
    "Required:",
    "  --inputs <file>                  newline- or tab-delimited input list",
    "  --template <tmpl>                template file containing literal XXXXXXXXXXXXX",
    "",
    "Optional:",
    "  --cwd <dir>                      workspace cwd (default: process.cwd)",
    "  --concurrency N                  jobs (default 10; >20 needs --i-have-measured)",
    "  --i-have-measured \"<reason>\"     justification for raised concurrency",
    "  --answers-dir <dir>              override default <cwd>/answers/",
    "  --force-redo <slug[,...]>        archive answers + flip selected entries",
    "  --force-redo-all                 archive + flip every entry",
    "  --force-new-run --run-id <id>    sibling run (manifest.<id>.json)",
    "  --monitor-root <dir>             override monitor/state root",
    "  --dry-run                        seed + plan-print; no codex spawn",
    "",
    "Renders one prompt per input row and writes one answer file per slug.",
  ].join("\n"),
  single: [
    "Usage: node use-codex.mjs single (--prompt <text> | --prompt-file <file>) [args]",
    "",
    "Required (exactly one):",
    "  --prompt <text>                  inline prompt",
    "  --prompt-file <file>             prompt file path",
    "",
    "Optional:",
    "  --cwd <dir>                      workspace cwd (default: process.cwd)",
    "  --out <file>                     codex -o final-message file (default: <cwd>/.use-codex/single.last.md)",
    "  --output-schema <schema.json>    record schema path in manifest entry",
    "  --reuse-worktree                 record reuse intent (single mode runs in cwd; no worktree creation)",
    "  --resume-last                    pick up codex's last session",
    "  --resume-thread <id>             resume a specific codex thread",
    "  --force-new-run --run-id <id>    sibling run (manifest.<id>.json)",
    "  --monitor-root <dir>             override monitor/state root",
    "  --dry-run                        seed + plan-print; no codex spawn",
    "",
    "One mission with live monitor; -o file is the source of truth.",
  ].join("\n"),
  review: [
    "Usage: node use-codex.mjs review --branches <list-or-file> [--base <ref>] [args]",
    "",
    "Required:",
    "  --branches <list|file|positionals>  comma-list, file path, or bare branch tokens",
    "",
    "Optional:",
    "  --base <ref>                     base for codex review --base (default: main)",
    "  --cwd <dir>                      git workspace (must be a repo)",
    "  --concurrency N                  jobs (default 4; >20 needs --i-have-measured)",
    "  --i-have-measured \"<reason>\"     justification for raised concurrency",
    "  --force-new-run --run-id <id>    sibling run (manifest.<id>.json)",
    "  --monitor-root <dir>             override monitor/state root",
    "  --dry-run                        seed + plan-print; no codex spawn",
    "",
    "Per-branch convergence loop using native `codex review`. Single round per",
    "invocation; orchestrator decides next round. Auto-loop is documented as",
    "Planned-but-not-yet-wired.",
  ].join("\n"),
  rescue: [
    "Usage: node use-codex.mjs rescue [--manifest <path>] [--cwd <dir>] [--apply <subset>]",
    "",
    "Optional:",
    "  --manifest <path>                explicit manifest (else derived from --cwd)",
    "  --cwd <dir>                      workspace cwd",
    "  --apply <subset>                 redispatch subset:",
    "                                     failed-only        — entries with status=failed",
    "                                     never-started-only — status=queued AND attempts=0",
    "                                     all-non-done       — every non-done entry",
    "                                     ids:s1,s2,...      — explicit slug/id list (operator override)",
    "  --accept-stale                   override the 7-day freshness gate",
    "  --dry-run                        with --apply: preview-only (does not flip or spawn)",
    "",
    "Without --apply: read-only classification (done/failed/never_started/in_flight/unknown).",
  ].join("\n"),
  audit: [
    "Usage: node use-codex.mjs audit [--manifest <path>] [--cwd <dir>] [--json]",
    "",
    "Optional:",
    "  --manifest <path>                explicit manifest",
    "  --cwd <dir>                      workspace cwd",
    "  --json                           emit machine-readable report (always on within envelope)",
    "",
    "Read-only state dump: status counts, drift_kinds, orphan_worktrees[].",
  ].join("\n"),
  tidy: [
    "Usage: node use-codex.mjs tidy [--manifest <path>] [--cwd <dir>] [--execute] [--json]",
    "",
    "Optional:",
    "  --manifest <path>                explicit manifest",
    "  --cwd <dir>                      workspace cwd (must be inside a git repo)",
    "  --execute                        actually remove (default: dry-run preview)",
    "  --force-abandon <id>             remove a refused entry (per-id escape hatch)",
    "  --base <ref>                     branch-merged check base (default: main)",
    "  --json                           machine-readable report",
    "",
    "Refuses dirty/unmerged/non-terminal worktrees unless --force-abandon names them.",
  ].join("\n"),
};

function modeHelpEnvelope(command) {
  return okEnvelope(command, {
    phase: "help",
    next_action: "select arguments and rerun",
    usage: MODE_USAGE[command] ?? `No per-mode usage available for: ${command}`,
  });
}

function argvHasHelp(argv) {
  if (!Array.isArray(argv)) return false;
  return argv.some((t) => t === "--help" || t === "-h");
}

function parseArgsStrict(argv, command, config) {
  // P1-6: short-circuit per-mode --help / -h before strict parsing so the
  // unknown-option guard does not reject these as typos. Top-level --help
  // is still handled by dispatchHelp() in dispatch().
  if (argvHasHelp(argv) && MODE_USAGE[command]) {
    return { err: modeHelpEnvelope(command) };
  }
  // Underlying parseArgs is permissive: unknown long-options end up in
  // positionals (token starts with "--" but didn't match valueOptions or
  // booleanOptions). Catch those here.
  let parsed;
  try {
    parsed = parseArgs(argv, config);
  } catch (e) {
    return { err: errEnvelope(command, "bad_argument", e.message) };
  }
  const unknownLong = parsed.positionals.filter((t) => typeof t === "string" && t.startsWith("--"));
  if (unknownLong.length > 0) {
    return {
      err: errEnvelope(command, "unknown_option",
        `Unknown option: ${unknownLong[0]}. ` +
        `Run \`node use-codex.mjs help\` for the supported flags.`,
        { unknown_options: unknownLong }),
    };
  }
  // Strip stray short-form flags too — the dispatcher uses long-form
  // exclusively, and a stray `-x` is almost certainly a typo.
  const unknownShort = parsed.positionals.filter(
    (t) => typeof t === "string" && t.startsWith("-") && t.length > 1 && t !== "-",
  );
  if (unknownShort.length > 0) {
    return {
      err: errEnvelope(command, "unknown_option",
        `Unknown option: ${unknownShort[0]}. ` +
        `The dispatcher only accepts long-form flags (--name).`,
        { unknown_options: unknownShort }),
    };
  }
  return { value: parsed };
}

// ----------------------------------------------------------------------------
// Workspace + manifest path
// ----------------------------------------------------------------------------

function workspaceFor(cwd) {
  // resolveWorkspaceRoot falls back to cwd when not a git repo, which is the
  // right behavior for batch mode (no repo). resolveStateDir matches codex-cc.
  return resolveWorkspaceRoot(cwd);
}

function manifestPathFor(cwd, runId = null) {
  // Matches codex-companion's state dir + a use-codex/ subdir so our
  // manifest sits next to its `state.json`+`jobs/<id>.json` and rescue can
  // correlate via jobId. Plan §Manifest schema confirms.
  //
  // When runId is provided (force-new-run), the manifest is named
  // `manifest.<run_id>.json` so a concurrent second run on the same workspace
  // gets its own file and doesn't collide with the live manifest. See
  // references/universal/idempotency.md "force-new-run".
  const base = path.join(resolveStateDir(cwd), "use-codex");
  return runId
    ? path.join(base, `manifest.${runId}.json`)
    : path.join(base, "manifest.json");
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
  if (process.env.USE_CODEX_SKIP_PREFLIGHT === "1") {
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
      USE_CODEX_MODE: mode,
      USE_CODEX_RUN_ID: runId,
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
      `Manifest at ${manifestPath} has ${inflight.length} non-terminal entries (status in {queued,running}). ` +
      `Recovery options: (1) wait for the current run to finish; (2) run \`rescue\` mode to redispatch the partial run; ` +
      `(3) force a parallel run with \`--force-new-run --run-id <custom>\` (writes to manifest.<custom>.json).`,
      {
        manifest_path: manifestPath,
        inflight_count: inflight.length,
        inflight_ids: inflight.map((e) => e.id),
        recovery_options: [
          "wait",
          "rescue",
          "--force-new-run --run-id <custom>",
        ],
      });
  }
  return null;
}

// ----------------------------------------------------------------------------
// Codex CLI pre-flight
// ----------------------------------------------------------------------------

function ensureCodexAvailable(command) {
  // The dispatcher must NOT seed a manifest if `codex` is missing — the
  // detached runner would exit immediately, leaving every entry `queued`
  // forever, and every subsequent run would hit `concurrent_run_in_progress`
  // until the operator nuked the manifest by hand.
  //
  // Test/dev hatch: setting USE_CODEX_RUNNER_<MODE> to a stub means the
  // operator is running the integration suite without a real codex binary;
  // skip the check in that case. We detect "any RUNNER override is set" as
  // the integration-test signal.
  if (
    process.env.USE_CODEX_RUNNER_EXEC ||
    process.env.USE_CODEX_RUNNER_BATCH ||
    process.env.USE_CODEX_RUNNER_SINGLE ||
    process.env.USE_CODEX_RUNNER_REVIEW ||
    process.env.USE_CODEX_SKIP_CODEX_PREFLIGHT === "1"
  ) {
    return null;
  }
  const r = spawnSync("command", ["-v", "codex"], { shell: true, encoding: "utf8" });
  if (r.status === 0 && (r.stdout || "").trim()) return null;
  return errEnvelope(command, "codex_unavailable",
    "codex CLI not found on PATH. Install codex-cli before invoking the dispatcher; " +
    "the detached runner would otherwise exit immediately and strand the manifest in `queued` state. " +
    "Verify with `command -v codex && codex --version`.",
    { hint: "https://github.com/openai/codex" });
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
  // Monitor's hard ceiling is 1h. Larger values are silently clamped, which
  // means the envelope lies about how long Monitor will watch. Clamp here.
  const clamped = Math.max(1, Math.min(MONITOR_HARD_MAX_MS, Math.floor(timeoutMs)));
  const parts = [];
  parts.push(`  description: ${jsString(description)},`);
  parts.push(`  command: ${jsString(command)},`);
  parts.push(`  persistent: ${persistent ? "true" : "false"},`);
  parts.push(`  timeout_ms: ${clamped}`);
  return `Monitor({\n${parts.join("\n")}\n})`;
}

// codex-monitor.sh is the rule-engine ticker. It already emits one
// line-buffered progress row per tick plus terminal markers such as
// `--- fleet quiet ---`; do not grep-filter it or real progress disappears.
function fleetMonitorCommand({ manifestPath, monitorRoot }) {
  const env = [
    `USE_CODEX_MANIFEST=${shellQuote(manifestPath)}`,
    `MONITOR_ROOT=${shellQuote(monitorRoot)}`,
    `USE_CODEX_QUIET_AFTER=${shellQuote(process.env.USE_CODEX_QUIET_AFTER || "1")}`,
  ].join(" ");
  const monitorBin = shellQuote(MONITOR_SCRIPT);
  return `${env} bash ${monitorBin} 2>&1; echo "monitor exited rc=$?"`;
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
          description: `use-codex ${mode} (run_id=${runId})`,
          command: fleetMonitorCommand({ manifestPath, monitorRoot }),
          persistent: true,
          // Hard-clamped to MONITOR_HARD_MAX_MS by buildMonitorHint. The
          // long-running fleet monitor closes when codex-monitor.sh emits
          // `--- fleet quiet ---`, which the agent's Monitor sees and stops.
          timeoutMs: MONITOR_HARD_MAX_MS,
        }),
      };
    case "single":
      return {
        tool_hint: buildMonitorHint({
          description: `use-codex single (run_id=${runId})`,
          command: singleMonitorCommand({ jsonlPath: jsonlPath || path.join(monitorRoot, "single.jsonl") }),
          // single mode is bounded — Monitor closes at turn.completed; we
          // give it the platform max (1h, see MONITOR_HARD_MAX_MS).
          persistent: false,
          timeoutMs: MONITOR_HARD_MAX_MS,
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
    // Per-task post_verify_cmd: thread through to mode_state so the runner
    // (run-fleet.sh) can prefer it over auto-detect (B4 from S8 fix wave).
    const postVerify = (typeof t.post_verify_cmd === "string" && t.post_verify_cmd.trim())
      ? t.post_verify_cmd.trim()
      : (t.post_verify_cmd ?? null);
    entries.push(newEntry({
      id,
      slug: t.slug || id,
      branch,
      baseBranch,
      promptPath: t.prompt_file ?? null,
      modeState: {
        // `task` is the canonical per-task shape the runner reads first
        // (`mode_state.post_verify_cmd` first, then `mode_state.task.post_verify_cmd`).
        task: {
          prompt: t.prompt ?? null,
          prompt_file: t.prompt_file ?? null,
          label: t.label ?? null,
        },
        // Yigit's `exec` shape is preserved for code that grew up reading
        // mode_state.exec.* — both are populated so neither path breaks.
        exec: {
          branch,
          base_branch: baseBranch,
          prompt: t.prompt ?? null,
          prompt_file: t.prompt_file ?? null,
          label: t.label ?? null,
          post_verify_cmd: postVerify,
          post_verify_exit: null,
        },
        post_verify_cmd: postVerify,
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
      // Bug 4 fix: do NOT seed nested `mode_state.batch.{answer_size_bytes,
      // below_floor}` keys — the runner writes those to the TOP LEVEL
      // (`mode_state.answer_size_bytes` / `mode_state.below_floor`), and the
      // dual shape left null fields hanging that downstream readers couldn't
      // disambiguate. The nested `mode_state.batch.input` row content remains
      // canonical per references/modes/batch.md.
      modeState: { batch: { input: line, input_row: line, prompt_file: null } },
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
  const entries = branches.map((branch, i) => {
    const idx = String(i + 1).padStart(2, "0");
    const slug = slugify(branch);
    return newEntry({
      id: `${idx}-${slug}`,
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
    // Read prompt content from either mode_state.exec.* (Yigit's shape) or
    // mode_state.task.* (S8's shape). buildExecEntries populates both, but
    // older manifests may only carry one.
    const state = entry.mode_state?.exec || entry.mode_state?.task || {};
    if (state.prompt_file) {
      const promptPath = path.isAbsolute(state.prompt_file)
        ? state.prompt_file
        : path.resolve(cwd, state.prompt_file);
      if (!fs.existsSync(promptPath)) {
        return errEnvelope(command, "bad_tasks_file", `prompt_file not found for ${entry.id}: ${promptPath}`);
      }
      entry.prompt_path = promptPath;
      // Mirror to both shapes so downstream readers don't have to choose.
      if (entry.mode_state?.task) entry.mode_state.task.prompt_file = promptPath;
      if (entry.mode_state?.exec) entry.mode_state.exec.prompt_file = promptPath;
      continue;
    }
    if (state.prompt) {
      entry.prompt_path = writePromptFile(promptDir, entry.id, state.prompt);
      if (entry.mode_state?.task) entry.mode_state.task.prompt_file = entry.prompt_path;
      if (entry.mode_state?.exec) entry.mode_state.exec.prompt_file = entry.prompt_path;
      continue;
    }
    return errEnvelope(command, "bad_tasks_file", `task ${entry.id} requires prompt or prompt_file`);
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
  // Yigit's path: shell out to render-prompts.sh (preserves the bare-slug
  // standalone-runner workflow). S8's renderBatchPromptFiles below renders
  // inline in Node for the dispatcher path. handleBatch decides which to call.
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

function renderBatchPromptFiles(entries, templatePath, promptDir, command, placeholder = "XXXXXXXXXXXXX") {
  // S8 dispatcher path: renders inline for the NNN-prefixed slug space.
  // See references/modes/batch.md "Two slug spaces".
  const template = readTextFile(templatePath, command, "bad_template_file");
  if (template.err) return template.err;
  fs.mkdirSync(promptDir, { recursive: true });
  for (const entry of entries) {
    const input = entry.mode_state?.batch?.input ?? "";
    const content = input.includes("\t") ? input.slice(input.indexOf("\t") + 1) : input;
    const prompt = template.value.split(placeholder).join(content);
    const promptPath = path.join(promptDir, `${entry.id}.md`);
    fs.writeFileSync(promptPath, `${prompt.replace(/\s+$/g, "")}\n`, "utf8");
    entry.prompt_path = promptPath;
  }
  return null;
}

// ----------------------------------------------------------------------------
// Manifest seeding (initial atomic write)
// ----------------------------------------------------------------------------

function getBaseCommit(cwd) {
  const r = spawnSync("git", ["rev-parse", "HEAD"], { cwd, encoding: "utf8" });
  if (r.status === 0) return r.stdout.trim();
  return null;
}

// Bug 1 fix — carry forward terminal `done` entries from a prior manifest so
// re-running the dispatcher (e.g. to retry one failure) does not silently
// demote successful entries back to `queued` (which the runner would then
// flip to `skipped`, rewriting history). The fresh entry list is mutated
// in place: any element whose id matches a prior `done` entry has its
// terminal-state fields (status, timing, paths, mode_state, etc.) restored
// from the prior manifest.
//
// Edge cases:
//   - prior entry exists but status !== "done": no-op (let the runner re-run).
//   - prior entry has stale paths (e.g. worktree deleted between runs):
//     carry forward anyway; the runner's idempotency guard handles re-creation
//     and audit will surface the drift.
//   - no prior manifest: no-op (fresh seed behaviour).
//   - older manifest schema lacks some fields: read with `??` defaults so the
//     merge is forward-compatible.
// Returns the count of entries whose terminal-state was carried forward.
// Surfaced via result.carried_forward_count so operators can tell when a
// re-invocation is overlaying a prior real run rather than starting fresh
// (P0-3 — defensive envelope diagnostic).
function carryForwardDoneEntries(priorManifestPath, freshEntries) {
  if (!Array.isArray(freshEntries) || freshEntries.length === 0) return 0;
  const prior = readManifestIfPresent(priorManifestPath);
  if (!prior || prior.__corrupt) return 0;
  const priorEntries = Array.isArray(prior.entries) ? prior.entries : [];
  if (priorEntries.length === 0) return 0;
  const priorById = new Map();
  for (const entry of priorEntries) {
    if (entry && typeof entry.id === "string") priorById.set(entry.id, entry);
  }
  let carried = 0;
  for (const entry of freshEntries) {
    if (!entry || typeof entry.id !== "string") continue;
    const prev = priorById.get(entry.id);
    if (!prev) continue;
    // Carry forward terminal real-run state only. Skip:
    //   - non-terminal statuses (handled by skip-existing in the runner)
    //   - dry-run terminal entries (P0-1: a probe must not poison the next
    //     real run via filesystem-keyed or status-keyed skip-existing).
    //     `dry_run === true` is the runner-side discriminator (run-fleet.sh,
    //     run-batch.sh, run-single.sh, run-review.sh emit this field on the
    //     dry-run terminal write); `verify_status === "dry-run"` is the
    //     audit-side mirror. Either signal disqualifies the carry.
    const isTerminal = prev.status === "done" || prev.status === "converged";
    if (!isTerminal) continue;
    if (prev.dry_run === true || prev.verify_status === "dry-run") continue;
    const priorWorktreePath = prev.worktree_path ?? entry.worktree_path;
    const safeWorktreePath = priorWorktreePath && fs.existsSync(priorWorktreePath)
      ? priorWorktreePath
      : null;
    // Restore terminal-state fields. mode_state is shallow-merged so the
    // freshly-seeded shape (e.g. mode_state.batch.input from the new inputs
    // file) wins for keys absent in the prior, and prior-run signals
    // (answer_size_bytes / below_floor / post_verify_cmd / task.*) win where
    // present. Unknown fields on the prior side are tolerated via `??`.
    entry.status = prev.status ?? entry.status;
    entry.started_at = prev.started_at ?? entry.started_at;
    entry.finished_at = prev.finished_at ?? entry.finished_at;
    entry.exit_code = prev.exit_code ?? entry.exit_code;
    entry.attempts = prev.attempts ?? entry.attempts;
    entry.log_path = prev.log_path ?? entry.log_path;
    entry.jsonl_path = prev.jsonl_path ?? entry.jsonl_path;
    entry.answer_path = prev.answer_path ?? entry.answer_path;
    entry.worktree_path = safeWorktreePath;
    entry.codex_thread_id = prev.codex_thread_id ?? entry.codex_thread_id;
    entry.codex_session_id = prev.codex_session_id ?? entry.codex_session_id;
    entry.last_error = prev.last_error ?? entry.last_error;
    if (prev.mode_state && typeof prev.mode_state === "object") {
      entry.mode_state = { ...(entry.mode_state || {}), ...prev.mode_state };
    }
    carried += 1;
  }
  return carried;
}

function seedManifest({
  manifestPath,
  mode,
  runId,
  entries,
  concurrencyCap,
  monitorRoot,
  cwd,
  // Both names accepted: HEAD uses `policyOverrides`, S8 uses `overrides`.
  policyOverrides,
  overrides,
  paths = {},
  preflight = {},
  // Top-level answers_dir is the canonical post-run audit hint. The dispatcher
  // surfaces this so `audit-sizes.sh --manifest <path>` finds outputs even
  // when the operator passed `--answers-dir <override>`. Also mirrored into
  // paths.answers_dir for the rerun-from-manifest path that reads paths[].
  answersDir = null,
}) {
  ensureManifestDir(manifestPath);
  const overridesMerged = { ...(policyOverrides || {}), ...(overrides || {}) };
  const policy = { ...POLICY, overrides: overridesMerged };
  const pathsWithAnswers = answersDir
    ? { ...paths, answers_dir: paths.answers_dir || answersDir }
    : paths;
  const manifest = {
    schema_version: SCHEMA_VERSION,
    run_id: runId,
    mode,
    started_at: nowIso(),
    base_commit: getBaseCommit(cwd),
    workspace_root: cwd,
    state_dir: path.dirname(manifestPath),
    policy,
    concurrency_cap: concurrencyCap,
    monitor_root: monitorRoot,
    paths: pathsWithAnswers,
    preflight,
    entries,
    history: [],
  };
  if (answersDir) {
    // Top-level field — what audit-sizes.sh --manifest reads first. Persisted
    // before paths so jq's `.answers_dir // .paths.answers_dir` picks it up.
    manifest.answers_dir = answersDir;
  }
  // Initial-write race guard: refuse to overwrite an in-flight manifest. The
  // refuseIfConcurrent gate above caught this for non-rescue paths; this is
  // defense in depth in case two seedManifest calls interleave. Surfaces as
  // the same error envelope shape the operator sees from the primary gate.
  if (fs.existsSync(manifestPath)) {
    const prev = readManifestIfPresent(manifestPath);
    if (hasInflightEntries(prev)) {
      return {
        err: errEnvelope("seed", "manifest_inflight_race",
          `Another writer seeded ${manifestPath} with in-flight entries between the concurrent-run gate and seedManifest. Re-run after the existing run finishes, or run rescue to redispatch.`,
          { manifest_path: manifestPath }),
      };
    }
  }
  // Atomic write: write to a temp file in the same directory, then rename.
  const tmp = `${manifestPath}.tmp.${process.pid}.${Date.now()}`;
  fs.writeFileSync(tmp, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  fs.renameSync(tmp, manifestPath);
  return { value: manifest };
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

function ensureLogPath(monitorRoot, runId) {
  // Per DoD: redirect runner stdout+stderr to ${monitor_root}/logs/<run_id>/_runner.log
  // so codex-monitor.sh / audit-sizes.sh can rediscover the runner's
  // START/DONE/FAIL/SKIP lines after the dispatcher exits.
  const logDir = path.join(monitorRoot, "logs", runId);
  fs.mkdirSync(logDir, { recursive: true });
  return path.join(logDir, "_runner.log");
}

function spawnRunnerDetached({ runnerPath, args, cwd, env = {}, runnerLogPath = null }) {
  // detached + unref() = the dispatcher returns immediately, the runner
  // survives across the dispatcher's exit, and the agent's Monitor reads
  // progress via the JSONL/log files the runner writes. This is the
  // codex-companion 'task --background' pattern, adapted for bash.
  //
  // USE_CODEX_RUNNER_FOREGROUND=1 is a test/dev escape hatch — runs the
  // runner in the foreground via spawnSync so integration tests can assert on
  // the runner's exit status without scraping the runner log.
  if (process.env.USE_CODEX_RUNNER_FOREGROUND === "1") {
    const foregroundAllowed = process.env.NODE_ENV === "test"
      || process.env.USE_CODEX_ALLOW_FOREGROUND === "1";
    if (!foregroundAllowed) {
      return {
        pid: 0,
        foreground: true,
        status: 2,
        stdout: "",
        stderr: "USE_CODEX_RUNNER_FOREGROUND=1 is test-only; set NODE_ENV=test or USE_CODEX_ALLOW_FOREGROUND=1 to use it.",
        foreground_rejected: true,
      };
    }
    const r = spawnSync("bash", [runnerPath, ...args], {
      cwd,
      encoding: "utf8",
      env: { ...process.env, ...env },
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
  // stdout+stderr go to <monitor_root>/logs/<run_id>/_runner.log (B5/B7).
  // Without the redirect, audit-sizes.sh and codex-monitor.sh have nothing
  // to grep for the runner's START/DONE/FAIL/SKIP markers.
  let stdio = "ignore";
  let logFd = null;
  if (runnerLogPath) {
    logFd = fs.openSync(runnerLogPath, "a");
    stdio = ["ignore", logFd, logFd];
  }
  const child = spawn("bash", [runnerPath, ...args], {
    cwd,
    detached: true,
    stdio,
    env: { ...process.env, ...env },
  });
  if (logFd !== null) {
    // Close our handle now that the child owns the fd. Matters on macOS where
    // unclosed parent fds keep the file open even after the child exits.
    try { fs.closeSync(logFd); } catch { /* ignore */ }
  }
  child.unref();
  return { pid: child.pid, foreground: false };
}

function foregroundRejectedEnvelope(command, pid) {
  if (!pid?.foreground_rejected) return null;
  return errEnvelope(command, "bad_argument", pid.stderr, {
    env: "USE_CODEX_RUNNER_FOREGROUND",
  });
}

// ----------------------------------------------------------------------------
// Python helpers (rescue / audit / tidy / manifest-update)
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

// runnerArgsForRedispatch was removed in the round-8 fix pass. It was dead code
// (never called; rescue redispatch builds args inline at handleRescue) and it
// referenced flags (--manifest, --base, --concurrency, --max-rounds, --state-dir,
// --only) that none of the bash runners actually accept. Wiring those flags is
// a feature, not a fix; until that's done the rescue-redispatch path inside
// handleRescue (below) is the canonical surface.

function flipEntryToQueued(manifestPath, entryId, wsRoot) {
  // manifest-update.py defaults to dry-run; --execute writes. We blank
  // exit_code/finished_at/last_error so audit doesn't carry stale failure
  // signals into the next attempt.
  //
  // Bug 5 fix: also clear started_at and increment attempts. references/modes/
  // rescue.md documents that rescue should "increment attempts" and "clear
  // started_at"; the runner only increments on the START path, so dry-run
  // and stub-runner code paths previously left attempts stuck at the prior
  // value. Bumping here covers every redispatch entry (rescue + force-redo).
  const args = [
    "entry",
    "--manifest", manifestPath,
    "--entry", entryId,
    "--set", "status=queued",
    "--set", "exit_code=null",
    "--set", "finished_at=null",
    "--set", "last_error=null",
    "--set", "started_at=null",
    "--set", "attempts=+1",
    "--execute",
  ];
  return runPythonHelper(PY_HELPERS.manifestUpdate, args, wsRoot);
}

// ----------------------------------------------------------------------------
// Concurrency resolution + override persistence
// ----------------------------------------------------------------------------

function resolveConcurrency(opts, command) {
  // Precedence: --concurrency flag > JOBS env > mode default.
  // The user's JOBS=10 must win when no --concurrency flag is set; the flag
  // wins when both are set. (Documented in references/universal/concurrency.md.)
  const flagVal = opts.concurrency != null && opts.concurrency !== "" ? opts.concurrency : null;
  const envVal = process.env.JOBS && process.env.JOBS !== "" ? process.env.JOBS : null;
  const defaultVal = DEFAULT_CONCURRENCY[command] || 1;
  const sourceRaw = flagVal != null ? flagVal : (envVal != null ? envVal : String(defaultVal));
  const source = flagVal != null ? "flag" : (envVal != null ? "env" : "default");
  const cap = Number(sourceRaw);
  if (!Number.isFinite(cap) || cap < 1 || !Number.isInteger(cap)) {
    return {
      err: errEnvelope(command, "bad_argument",
        `concurrency must be a positive integer (got ${JSON.stringify(sourceRaw)} from ${source}).`),
    };
  }
  if (cap > CONCURRENCY_ABSOLUTE_CEILING) {
    return {
      err: errEnvelope(command, "bad_argument",
        `concurrency=${cap} exceeds the absolute ceiling (${CONCURRENCY_ABSOLUTE_CEILING}). ` +
        `references/universal/concurrency.md §Hard ceiling: this skill assumes a single user's auth tier; ` +
        `concurrency above ${CONCURRENCY_ABSOLUTE_CEILING} is structurally pathological.`),
    };
  }
  // Soft gate: above mode default OR above hard cap (whichever lower) requires
  // --i-have-measured "<justification>". Aligns with references/universal/concurrency.md.
  const overDefault = cap > defaultVal;
  const overHardCap = cap > CONCURRENCY_HARD_CAP;
  const measured = opts["i-have-measured"];
  if (overDefault || overHardCap) {
    if (typeof measured !== "string" || !measured.trim()) {
      const which = overHardCap
        ? `the hard cap (${CONCURRENCY_HARD_CAP})`
        : `the ${command} default (${defaultVal})`;
      return {
        err: errEnvelope(command, "bad_argument",
          `concurrency=${cap} (source=${source}) exceeds ${which}. ` +
          `Pass \`--i-have-measured "<justification>"\` to override (the justification is recorded in ` +
          `manifest.policy.overrides.concurrency for audit). See references/universal/concurrency.md.`,
          { source, default: defaultVal, requested: cap, hard_cap: CONCURRENCY_HARD_CAP }),
      };
    }
  }
  const override = (overDefault || overHardCap)
    ? { value: cap, justification: measured.trim(), set_at: nowIso() }
    : null;
  return { value: cap, source, override };
}

function defaultMonitorRoot(manifestPath) {
  return path.dirname(manifestPath);
}

// ----------------------------------------------------------------------------
// Force-redo helpers (exec/batch)
// ----------------------------------------------------------------------------

function listForceRedoSlugs(opts) {
  // --force-redo is value-or-comma-list. parseArgs only takes one value per
  // invocation; document `--force-redo a,b,c` as the supported form.
  const raw = opts["force-redo"];
  if (!raw) return [];
  return String(raw).split(",").map((s) => s.trim()).filter(Boolean);
}

function archiveAnswerToPrev(answerDir, slug) {
  // answer dir layout: <answers>/<slug>.md ; archive moves to .prev/<slug>-<ts>.md.
  const src = path.join(answerDir, `${slug}.md`);
  if (!fs.existsSync(src)) return { archived: false, reason: "no answer file" };
  const prevDir = path.join(answerDir, ".prev");
  fs.mkdirSync(prevDir, { recursive: true });
  const ts = compactStamp();
  const dest = path.join(prevDir, `${slug}-${ts}.md`);
  fs.renameSync(src, dest);
  return { archived: true, dest };
}

function applyForceRedo({ manifestPath, manifest, slugs, answerDir, wsRoot, all = false }) {
  const out = { archived: [], flipped: [], unknown: [] };
  const entries = manifest.entries || [];
  const targetIds = all
    ? entries.map((e) => e.id)
    : entries.filter((e) => slugs.includes(e.id) || slugs.includes(e.slug)).map((e) => e.id);
  if (!all) {
    for (const slug of slugs) {
      const found = entries.find((e) => e.id === slug || e.slug === slug);
      if (!found) out.unknown.push(slug);
    }
  }
  if (out.unknown.length > 0 && !all) {
    return {
      err: errEnvelope("force-redo", "bad_argument",
        `--force-redo: unknown slug(s): ${out.unknown.join(", ")}. ` +
        `Run \`audit\` to list known entries.`,
        { unknown_slugs: out.unknown }),
    };
  }
  for (const id of targetIds) {
    if (answerDir) {
      const slug = entries.find((e) => e.id === id)?.slug || id;
      const arch = archiveAnswerToPrev(answerDir, slug);
      if (arch.archived) out.archived.push({ slug, dest: arch.dest });
    }
    const r = flipEntryToQueued(manifestPath, id, wsRoot);
    if (r.status !== 0) {
      return {
        err: errEnvelope("force-redo", "python_helper_failed",
          `manifest-update.py failed for ${id}: ${(r.stderr || "").trim() || "no stderr"}`,
          { stdout: r.stdout, stderr: r.stderr }),
      };
    }
    out.flipped.push(id);
  }
  return { value: out };
}

// ----------------------------------------------------------------------------
// Mode handlers
// ----------------------------------------------------------------------------

function dispatchHelp() {
  return okEnvelope("help", {
    phase: "done",
    next_action: "select a mode and rerun",
    usage: [
      "Usage: node use-codex.mjs <mode> [args]",
      "",
      "Modes:",
      "  exec    --tasks <tasks.json> [--concurrency N] [--cwd <dir>]",
      "          [--i-have-measured \"<justification>\"]",
      "          [--force-redo <slug[,slug2,...]> | --force-redo-all]",
      "          [--force-new-run --run-id <custom>]",
      "          parallel codex exec across worktrees",
      "  batch   --inputs <file> --template <tmpl> [--concurrency N] [--cwd <dir>]",
      "          [--i-have-measured \"<justification>\"]",
      "          [--force-redo <slug[,slug2,...]> | --force-redo-all]",
      "          [--force-new-run --run-id <custom>] [--answers-dir <dir>]",
      "          template x N inputs",
      "  single  (--prompt <text> | --prompt-file <file>) [--cwd <dir>] [--out <file>]",
      "          [--reuse-worktree] [--output-schema <schema.json>]",
      "          [--resume-last | --resume-thread <id>]",
      "          [--force-new-run --run-id <custom>]",
      "          one mission with live monitor",
      "  review  --branches <list-or-file> [--base <ref>] [--cwd <dir>] [--concurrency N]",
      "          [--i-have-measured \"<justification>\"]",
      "          per-branch convergence loop using native codex review",
      "  rescue  [--manifest <path>] [--cwd <dir>]",
      "          [--apply failed-only|never-started-only|all-non-done|ids:s1,s2]",
      "          classify a partial prior run; with --apply, re-spawn the runner",
      "  audit   [--manifest <path>] [--cwd <dir>] [--json]",
      "          read-only manifest+filesystem state dump",
      "  tidy    [--manifest <path>] [--cwd <dir>] [--execute]",
      "          gated worktree cleanup",
      "",
      "Every invocation emits one JSON envelope on stdout.",
      "Unknown long-options are rejected with error.code=\"unknown_option\".",
      "Policy: --dangerously-bypass-approvals-and-sandbox + gpt-5.5 + xhigh effort.",
    ].join("\n"),
  });
}

async function handleExec(argv) {
  const command = "exec";
  const parsed = parseArgsStrict(argv, command, {
    valueOptions: ["tasks", "concurrency", "cwd", "monitor-root", "run-id",
                   "i-have-measured", "force-redo"],
    booleanOptions: ["force-redo-all", "force-new-run", "dry-run"],
  });
  if (parsed.err) return parsed.err;
  const { options } = parsed.value;
  if (!options.tasks) {
    return errEnvelope(command, "missing_required_arg", "exec mode requires --tasks <tasks.json>.");
  }
  const cwd = path.resolve(options.cwd || process.cwd());
  const tasksPath = path.resolve(cwd, options.tasks);
  if (!fs.existsSync(tasksPath)) {
    return errEnvelope(command, "bad_tasks_file", `tasks file not found: ${tasksPath}`);
  }
  const parsedJson = readJsonFile(tasksPath, command, "bad_tasks_file");
  if (parsedJson.err) return parsedJson.err;
  const built = buildExecEntries(parsedJson.value, command);
  if (built.err) return built.err;

  const cap = resolveConcurrency(options, command);
  if (cap.err) return cap.err;

  const codexErr = ensureCodexAvailable(command);
  if (codexErr) return codexErr;

  const wsRoot = workspaceFor(cwd);

  // --force-new-run: write to manifest.<run_id>.json instead of manifest.json
  // so a second concurrent run on the same workspace doesn't collide.
  const runId = options["run-id"] || generateRunId();
  const useCustomManifest = !!options["force-new-run"];
  if (options["force-new-run"] && !options["run-id"]) {
    return errEnvelope(command, "missing_required_arg",
      "--force-new-run requires an explicit --run-id <custom> so the resulting manifest.<run_id>.json is discoverable.");
  }
  const manifestPath = manifestPathFor(cwd, useCustomManifest ? runId : null);

  // --force-redo / --force-redo-all are dispatcher conveniences that operate
  // on a PRIOR manifest, not the seeded one. They run BEFORE seedManifest
  // (and BEFORE the concurrent-run gate, since the operator's intent is to
  // pick up an in-flight manifest deliberately). If the operator wants to
  // re-run a partial fleet, they pass --force-redo against the existing
  // manifest, then this branch flips entries and exits before seeding.
  const forceRedoSlugs = listForceRedoSlugs(options);
  const wantsForceRedoAll = !!options["force-redo-all"];
  if (forceRedoSlugs.length > 0 && wantsForceRedoAll) {
    return errEnvelope(command, "bad_argument",
      "Pass either `--force-redo <slug,…>` for named slugs OR `--force-redo-all` for the full fleet — not both. The named-list and fleet-wide modes are mutually exclusive.",
      { force_redo_slugs: forceRedoSlugs, force_redo_all: true });
  }
  if (forceRedoSlugs.length > 0 || wantsForceRedoAll) {
    const m = readManifestIfPresent(manifestPath);
    if (!m || m.__corrupt) {
      return errEnvelope(command, "manifest_not_found",
        `--force-redo requires an existing manifest at ${manifestPath}; none found.`,
        { manifest_path: manifestPath });
    }
    const answerDir = null; // exec mode doesn't have a single answer dir
    const out = applyForceRedo({
      manifestPath, manifest: m, slugs: forceRedoSlugs,
      answerDir, wsRoot, all: wantsForceRedoAll,
    });
    if (out.err) return out.err;
    // After flipping entries, fall through to spawn the runner. We do NOT
    // re-seed the manifest — the existing one's entries / overrides / monitor
    // root remain authoritative; we only flipped status fields.
    const runnerErr = ensureRunnerExists(RUNNERS.exec, command);
    if (runnerErr) return runnerErr;
    const runnerLogPath = ensureLogPath(m.monitor_root || defaultMonitorRoot(manifestPath), m.run_id || runId);
    const pid = spawnRunnerDetached({
      runnerPath: RUNNERS.exec,
      args: [manifestPath],
      cwd: wsRoot,
      env: { JOBS: String(cap.value), PROJECT_DIR: wsRoot },
      runnerLogPath,
    });
    const foregroundErr = foregroundRejectedEnvelope(command, pid);
    if (foregroundErr) return foregroundErr;
    return okEnvelope(command, {
      phase: "queued",
      next_action: "arm Monitor and wait",
      foreground_completed: pid?.foreground === true && pid?.status === 0,
      manifest_path: manifestPath,
      run_id: m.run_id || runId,
      entries_count: out.value.flipped.length,
      flipped_entries: out.value.flipped,
      runner_pid: pid,
      runner_log_path: runnerLogPath,
      workspace_root: wsRoot,
      mode: "force-redo",
    }, buildMonitorForMode("exec", { manifestPath, runId: m.run_id || runId, monitorRoot: m.monitor_root || defaultMonitorRoot(manifestPath) }));
  }

  // Concurrent-run gate runs AFTER force-redo (which deliberately re-uses
  // an in-flight manifest) but BEFORE seedManifest (which would overwrite it).
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const promptDir = path.join(monitorRoot, "prompts", runId);
  const promptErr = materializeExecPrompts(built.value, cwd, promptDir, command);
  if (promptErr) return promptErr;

  // Bug 1 fix: carry forward real-run terminal entries from a prior manifest
  // at the same path so a re-run does not demote successful entries back to
  // queued. Dry-run terminal entries are skipped (P0-1).
  const carriedForward = carryForwardDoneEntries(manifestPath, built.value);

  const seeded = seedManifest({
    manifestPath, mode: "exec", runId, entries: built.value,
    concurrencyCap: cap.value, monitorRoot, cwd: wsRoot,
    overrides: cap.override ? { concurrency: cap.override } : {},
  });
  if (seeded.err) return seeded.err;

  const runnerErr = ensureRunnerExists(RUNNERS.exec, command);
  if (runnerErr) return runnerErr;
  const runnerLogPath = ensureLogPath(monitorRoot, runId);
  const execEnv = {
    JOBS: String(cap.value),
    PROJECT_DIR: wsRoot,
  };
  if (options["dry-run"]) execEnv.DRY_RUN = "1";
  const pid = spawnRunnerDetached({
    runnerPath: RUNNERS.exec,
    args: [manifestPath],
    cwd: wsRoot,
    env: execEnv,
    runnerLogPath,
  });
  const foregroundErr = foregroundRejectedEnvelope(command, pid);
  if (foregroundErr) return foregroundErr;

  const env = okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    foreground_completed: pid?.foreground === true && pid?.status === 0,
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: built.value.length,
    runner_pid: pid,
    runner_status: pid.foreground ? pid.status : null,
    runner_log_path: runnerLogPath,
    workspace_root: wsRoot,
    concurrency_cap: cap.value,
    concurrency_source: cap.source,
    // P0-3: surface how many entries were inherited from a prior real run.
    // 0 = fresh run; >0 = re-invocation overlaying real results (the runner's
    // skip-existing guard will not redo those). Operators read this to detect
    // accidental clobbering before arming Monitor.
    carried_forward_count: carriedForward,
    dry_run: !!options["dry-run"],
  }, buildMonitorForMode("exec", { manifestPath, runId, monitorRoot }));
  env.meta.dry_run = !!options["dry-run"];
  return env;
}

async function handleBatch(argv) {
  const command = "batch";
  const parsed = parseArgsStrict(argv, command, {
    valueOptions: ["inputs", "template", "concurrency", "cwd", "monitor-root", "run-id",
                   "answers-dir", "i-have-measured", "force-redo"],
    booleanOptions: ["force-redo-all", "force-new-run", "dry-run"],
  });
  if (parsed.err) return parsed.err;
  const { options } = parsed.value;
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

  const cap = resolveConcurrency(options, command);
  if (cap.err) return cap.err;

  const codexErr = ensureCodexAvailable(command);
  if (codexErr) return codexErr;

  // batch mode does not require a git repo; workspaceFor falls back to cwd.
  const wsRoot = workspaceFor(cwd);

  const runId = options["run-id"] || generateRunId();
  const useCustomManifest = !!options["force-new-run"];
  if (options["force-new-run"] && !options["run-id"]) {
    return errEnvelope(command, "missing_required_arg",
      "--force-new-run requires an explicit --run-id <custom>.");
  }
  const manifestPath = manifestPathFor(cwd, useCustomManifest ? runId : null);

  const answersDir = options["answers-dir"] ? path.resolve(cwd, options["answers-dir"]) : path.join(cwd, "answers");

  // Force-redo pre-flight (operates on existing manifest).
  const forceRedoSlugs = listForceRedoSlugs(options);
  const wantsForceRedoAll = !!options["force-redo-all"];
  if (forceRedoSlugs.length > 0 && wantsForceRedoAll) {
    return errEnvelope(command, "bad_argument",
      "Pass either `--force-redo <slug,…>` for named slugs OR `--force-redo-all` for the full fleet — not both. The named-list and fleet-wide modes are mutually exclusive.",
      { force_redo_slugs: forceRedoSlugs, force_redo_all: true });
  }
  if (forceRedoSlugs.length > 0 || wantsForceRedoAll) {
    const m = readManifestIfPresent(manifestPath);
    if (!m || m.__corrupt) {
      return errEnvelope(command, "manifest_not_found",
        `--force-redo requires an existing manifest at ${manifestPath}; none found.`,
        { manifest_path: manifestPath });
    }
    const out = applyForceRedo({
      manifestPath, manifest: m, slugs: forceRedoSlugs,
      answerDir: answersDir, wsRoot, all: wantsForceRedoAll,
    });
    if (out.err) return out.err;
    const monitorRootExisting = m.monitor_root || defaultMonitorRoot(manifestPath);
    const runnerErr = ensureRunnerExists(RUNNERS.batch, command);
    if (runnerErr) return runnerErr;
    const promptsDir = path.join(monitorRootExisting, "prompts", m.run_id || runId);
    const logsDir = path.join(monitorRootExisting, "logs", m.run_id || runId);
    const runnerLogPath = ensureLogPath(monitorRootExisting, m.run_id || runId);
    const pid = spawnRunnerDetached({
      runnerPath: RUNNERS.batch,
      args: [],
      cwd: wsRoot,
      env: {
        JOBS: String(cap.value),
        PROMPTS: promptsDir,
        ANSWERS: answersDir,
        LOGS: logsDir,
        USE_CODEX_MANIFEST: manifestPath,
      },
      runnerLogPath,
    });
    const foregroundErr = foregroundRejectedEnvelope(command, pid);
    if (foregroundErr) return foregroundErr;
    return okEnvelope(command, {
      phase: "queued",
      next_action: "arm Monitor and wait",
      foreground_completed: pid?.foreground === true && pid?.status === 0,
      manifest_path: manifestPath,
      run_id: m.run_id || runId,
      entries_count: out.value.flipped.length,
      flipped_entries: out.value.flipped,
      archived_answers: out.value.archived,
      runner_pid: pid,
      runner_log_path: runnerLogPath,
      workspace_root: wsRoot,
      answers_dir: answersDir,
      // Post-run audit hint: manifest-aware form is correct under
      // `--answers-dir <override>` (D2 fix; same rationale as the seed envelope).
      post_run_audit_cmd: `bash ${AUDIT_SIZES_SCRIPT} --manifest ${manifestPath}`,
      mode: "force-redo",
    }, buildMonitorForMode("batch", { manifestPath, runId: m.run_id || runId, monitorRoot: monitorRootExisting }));
  }

  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const promptsDir = path.join(monitorRoot, "prompts", runId);
  const logsDir = path.join(monitorRoot, "logs", runId);
  const renderErr = renderBatchPromptFiles(built.value, templatePath, promptsDir, command);
  if (renderErr) return renderErr;

  // Bug 1 fix: preserve real-run terminal entries from the prior manifest;
  // dry-run terminal entries are skipped (P0-1).
  const carriedForward = carryForwardDoneEntries(manifestPath, built.value);

  const seeded = seedManifest({
    manifestPath, mode: "batch", runId, entries: built.value,
    concurrencyCap: cap.value, monitorRoot, cwd: wsRoot,
    overrides: cap.override ? { concurrency: cap.override } : {},
    // Persist `answers_dir` at top-level so `audit-sizes.sh --manifest <path>`
    // finds the right directory even when the operator passed
    // `--answers-dir <override>`. Without this, the post-run audit defaults
    // to `./answers/` and silently inspects the wrong directory (D2 fix).
    answersDir,
  });
  if (seeded.err) return seeded.err;

  const runnerErr = ensureRunnerExists(RUNNERS.batch, command);
  if (runnerErr) return runnerErr;
  const runnerLogPath = ensureLogPath(monitorRoot, runId);
  const auditReportPath = path.join(monitorRoot, "logs", runId, "audit-sizes.txt");
  const batchEnv = {
    JOBS: String(cap.value),
    PROMPTS: promptsDir,
    ANSWERS: answersDir,
    LOGS: logsDir,
    USE_CODEX_MANIFEST: manifestPath,
    AUDIT_REPORT: auditReportPath,
    RUNNER_LOG: runnerLogPath,
  };
  if (options["dry-run"]) batchEnv.DRY_RUN = "1";
  const pid = spawnRunnerDetached({
    runnerPath: RUNNERS.batch,
    args: [],
    cwd: wsRoot,
    env: batchEnv,
    runnerLogPath,
  });
  const foregroundErr = foregroundRejectedEnvelope(command, pid);
  if (foregroundErr) return foregroundErr;

  const env = okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    foreground_completed: pid?.foreground === true && pid?.status === 0,
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: built.value.length,
    runner_pid: pid,
    runner_status: pid.foreground ? pid.status : null,
    runner_log_path: runnerLogPath,
    workspace_root: wsRoot,
    prompts_dir: promptsDir,
    answers_dir: answersDir,
    audit_report: auditReportPath,
    // Post-run audit hint: the manifest-aware form is correct under
    // `--answers-dir <override>` (D2 fix). The legacy positional form
    // `bash audit-sizes.sh <answers-dir> <min-bytes>` defaults to ./answers/
    // and silently inspects the wrong directory when the operator overrode it.
    post_run_audit_cmd: `bash ${AUDIT_SIZES_SCRIPT} --manifest ${manifestPath}`,
    concurrency_cap: cap.value,
    concurrency_source: cap.source,
    // P0-3: see handleExec for rationale.
    carried_forward_count: carriedForward,
    dry_run: !!options["dry-run"],
  }, buildMonitorForMode("batch", { manifestPath, runId, monitorRoot }));
  env.meta.dry_run = !!options["dry-run"];
  return env;
}

async function handleSingle(argv) {
  const command = "single";
  const parsed = parseArgsStrict(argv, command, {
    valueOptions: ["prompt", "prompt-file", "out", "cwd", "monitor-root", "run-id",
                   "output-schema", "resume-thread"],
    booleanOptions: ["reuse-worktree", "resume-last", "force-new-run", "dry-run"],
  });
  if (parsed.err) return parsed.err;
  const { options } = parsed.value;
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

  // Validate --output-schema (DoD #2).
  let outputSchema = null;
  if (options["output-schema"]) {
    outputSchema = path.isAbsolute(options["output-schema"])
      ? options["output-schema"]
      : path.resolve(cwd, options["output-schema"]);
    if (!fs.existsSync(outputSchema)) {
      return errEnvelope(command, "bad_schema_file",
        `--output-schema file not found: ${outputSchema}`);
    }
    // Lightweight JSON validity check — codex itself enforces JSON-Schema
    // semantics; here we only catch typos that would otherwise silently fail.
    try { JSON.parse(fs.readFileSync(outputSchema, "utf8")); }
    catch (e) {
      return errEnvelope(command, "bad_schema_file",
        `--output-schema file is not valid JSON: ${e.message}`,
        { schema_path: outputSchema });
    }
  }

  // --resume-last and --resume-thread <id> are mutually exclusive.
  if (options["resume-last"] && options["resume-thread"]) {
    return errEnvelope(command, "bad_argument",
      "--resume-last and --resume-thread are mutually exclusive; pick one.");
  }

  const codexErr = ensureCodexAvailable(command);
  if (codexErr) return codexErr;

  const wsRoot = workspaceFor(cwd);
  const runId = options["run-id"] || generateRunId();
  const useCustomManifest = !!options["force-new-run"];
  if (options["force-new-run"] && !options["run-id"]) {
    return errEnvelope(command, "missing_required_arg",
      "--force-new-run requires an explicit --run-id <custom>.");
  }
  const manifestPath = manifestPathFor(cwd, useCustomManifest ? runId : null);
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const outPath = options.out ? path.resolve(cwd, options.out) : path.join(monitorRoot, `single-${runId}.md`);
  const jsonlPath = path.join(path.dirname(outPath), `${built.value[0].id}.jsonl`);
  if (!promptFile && options.prompt) {
    promptFile = writePromptFile(path.join(monitorRoot, "prompts", runId), "single", options.prompt);
    built.value[0].prompt_path = promptFile;
    built.value[0].mode_state.single.prompt_file = promptFile;
  }
  built.value[0].jsonl_path = jsonlPath;
  built.value[0].log_path = jsonlPath;
  built.value[0].answer_path = outPath;
  // Persist the single-mode flags so audit + rescue can see them.
  if (outputSchema) built.value[0].mode_state.single.output_schema = outputSchema;
  if (options["reuse-worktree"]) built.value[0].mode_state.single.reuse_worktree = true;
  if (options["resume-last"]) built.value[0].mode_state.single.resume_last = true;
  if (options["resume-thread"]) built.value[0].mode_state.single.resume_thread = String(options["resume-thread"]);

  // Bug 1 fix: preserve real-run terminal entries from the prior manifest;
  // dry-run terminal entries are skipped (P0-1).
  const carriedForward = carryForwardDoneEntries(manifestPath, built.value);

  const seeded = seedManifest({
    manifestPath, mode: "single", runId, entries: built.value,
    concurrencyCap: 1, monitorRoot, cwd: wsRoot,
    overrides: {},
  });
  if (seeded.err) return seeded.err;

  const runnerErr = ensureRunnerExists(RUNNERS.single, command);
  if (runnerErr) return runnerErr;
  const runnerArgs = [
    "--prompt-file", promptFile,
    "--cwd", wsRoot,
    "--out", outPath,
    "--manifest", manifestPath,
    "--entry-id", built.value[0].id,
  ];
  if (outputSchema) {
    runnerArgs.push("--output-schema", outputSchema);
  }
  if (options["reuse-worktree"]) runnerArgs.push("--reuse-worktree");
  if (options["resume-last"]) runnerArgs.push("--resume-last");
  if (options["resume-thread"]) runnerArgs.push("--resume-thread", String(options["resume-thread"]));
  if (options["dry-run"]) runnerArgs.push("--dry-run");

  const runnerLogPath = ensureLogPath(monitorRoot, runId);
  const pid = spawnRunnerDetached({
    runnerPath: RUNNERS.single,
    args: runnerArgs,
    cwd: wsRoot,
    runnerLogPath,
  });
  const foregroundErr = foregroundRejectedEnvelope(command, pid);
  if (foregroundErr) return foregroundErr;

  const env = okEnvelope(command, {
    phase: "running",
    next_action: "arm Monitor and wait",
    foreground_completed: pid?.foreground === true && pid?.status === 0,
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: 1,
    runner_pid: pid,
    runner_status: pid.foreground ? pid.status : null,
    runner_log_path: runnerLogPath,
    workspace_root: wsRoot,
    answer_path: outPath,
    jsonl_path: jsonlPath,
    output_schema: outputSchema,
    reuse_worktree: !!options["reuse-worktree"],
    resume: options["resume-last"] ? { kind: "last" } :
            options["resume-thread"] ? { kind: "thread", thread_id: String(options["resume-thread"]) } :
            null,
    // P0-3: see handleExec for rationale.
    carried_forward_count: carriedForward,
    dry_run: !!options["dry-run"],
  }, buildMonitorForMode("single", { manifestPath, runId, monitorRoot, jsonlPath }));
  env.meta.dry_run = !!options["dry-run"];
  return env;
}

async function handleReview(argv) {
  const command = "review";
  const parsed = parseArgsStrict(argv, command, {
    valueOptions: ["branches", "base", "concurrency", "cwd", "monitor-root", "run-id",
                   "i-have-measured"],
    booleanOptions: ["force-new-run", "dry-run"],
  });
  if (parsed.err) return parsed.err;
  const { options, positionals } = parsed.value;
  const cwd = path.resolve(options.cwd || process.cwd());
  // --branches accepts a single token (file path OR comma-list); additional
  // bare branch tokens may be supplied as positionals (e.g.
  // `review --branches feat/auth feat/billing`).
  const branchPositionals = (positionals || []).filter((t) => typeof t === "string" && !t.startsWith("-"));
  const branches = expandBranches({
    branchSpec: options.branches || null,
    branchesFile: null,
    positionals: branchPositionals,
    cwd,
  });
  if (!options.branches && branches.length === 0) {
    return errEnvelope(command, "missing_required_arg", "review mode requires --branches <list-or-file>.");
  }
  const built = buildReviewEntries(branches, command, options.base || "main");
  if (built.err) return built.err;

  const cap = resolveConcurrency(options, command);
  if (cap.err) return cap.err;

  const codexErr = ensureCodexAvailable(command);
  if (codexErr) return codexErr;

  const wsRoot = workspaceFor(cwd);
  if (!fs.existsSync(path.join(wsRoot, ".git"))) {
    // review mode requires a real repo; resolveWorkspaceRoot's fallback is
    // unhelpful here.
    return errEnvelope(command, "not_a_repo", `review mode requires a git repository (cwd=${cwd}).`);
  }

  const runId = options["run-id"] || generateRunId();
  const useCustomManifest = !!options["force-new-run"];
  if (options["force-new-run"] && !options["run-id"]) {
    return errEnvelope(command, "missing_required_arg",
      "--force-new-run requires an explicit --run-id <custom>.");
  }
  const manifestPath = manifestPathFor(cwd, useCustomManifest ? runId : null);
  const concurrent = refuseIfConcurrent(command, manifestPath);
  if (concurrent) return concurrent;

  const monitorRoot = options["monitor-root"] || defaultMonitorRoot(manifestPath);
  fs.mkdirSync(monitorRoot, { recursive: true });
  const preflight = runBootstrap({ command, cwd: wsRoot, mode: command, runId, monitorRoot, skipGit: false });
  if (preflight.err) return preflight.err;

  // Bug 1 fix: preserve real-run terminal entries from the prior manifest;
  // dry-run terminal entries are skipped (P0-1).
  const carriedForward = carryForwardDoneEntries(manifestPath, built.value);

  const seeded = seedManifest({
    manifestPath, mode: "review", runId, entries: built.value,
    concurrencyCap: cap.value, monitorRoot, cwd: wsRoot,
    overrides: cap.override ? { concurrency: cap.override } : {},
  });
  if (seeded.err) return seeded.err;

  const runnerErr = ensureRunnerExists(RUNNERS.review, command);
  if (runnerErr) return runnerErr;
  // run-review.sh accepts --dry-run as the FIRST positional flag, then
  // <manifest> <round-number>.
  const runnerArgs = options["dry-run"]
    ? ["--dry-run", manifestPath, "1"]
    : [manifestPath, "1"];
  const runnerLogPath = ensureLogPath(monitorRoot, runId);
  const pid = spawnRunnerDetached({
    runnerPath: RUNNERS.review,
    args: runnerArgs,
    cwd: wsRoot,
    env: {
      JOBS: String(cap.value),
      PROJECT_DIR: wsRoot,
    },
    runnerLogPath,
  });
  const foregroundErr = foregroundRejectedEnvelope(command, pid);
  if (foregroundErr) return foregroundErr;

  const env = okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    foreground_completed: pid?.foreground === true && pid?.status === 0,
    manifest_path: manifestPath,
    run_id: runId,
    entries_count: built.value.length,
    runner_pid: pid,
    runner_status: pid.foreground ? pid.status : null,
    runner_log_path: runnerLogPath,
    workspace_root: wsRoot,
    concurrency_cap: cap.value,
    concurrency_source: cap.source,
    // P0-3: see handleExec for rationale.
    carried_forward_count: carriedForward,
    dry_run: !!options["dry-run"],
  }, buildMonitorForMode("review", { manifestPath, runId, monitorRoot }));
  env.meta.dry_run = !!options["dry-run"];
  return env;
}

// ----------------------------------------------------------------------------
// Rescue helpers
// ----------------------------------------------------------------------------

function selectRescueSubset(manifest, applySpec) {
  // applySpec ∈ failed-only | never-started-only | all-non-done | ids:s1,s2,...
  const entries = manifest.entries || [];
  if (applySpec.startsWith("ids:")) {
    const wanted = applySpec.slice(4).split(",").map((s) => s.trim()).filter(Boolean);
    const matched = entries.filter((e) => {
      const wantedEntry = wanted.includes(e.id) || wanted.includes(e.slug);
      return wantedEntry && e.status !== "done" && e.status !== "converged";
    });
    const unknown = wanted.filter((w) => !entries.find((e) => e.id === w || e.slug === w));
    return { ids: matched.map((e) => e.id), unknown };
  }
  switch (applySpec) {
    case "failed-only":
      return { ids: entries.filter((e) => e.status === "failed").map((e) => e.id), unknown: [] };
    case "never-started-only":
      return { ids: entries.filter((e) => e.status === "queued" && (e.attempts || 0) === 0).map((e) => e.id), unknown: [] };
    case "all-non-done":
      return { ids: entries.filter((e) => e.status !== "done").map((e) => e.id), unknown: [] };
    default:
      return { ids: [], unknown: [], invalid: applySpec };
  }
}

function killStalePid(pid) {
  if (!pid) return { killed: false, reason: "no pid" };
  try {
    process.kill(pid, 0); // probe
  } catch { return { killed: false, reason: "not alive" }; }
  try { process.kill(pid, "SIGTERM"); } catch { /* ignore */ }
  // Brief wait; if still alive after, SIGKILL.
  const deadline = Date.now() + 2000;
  while (Date.now() < deadline) {
    try { process.kill(pid, 0); } catch { return { killed: true, signal: "SIGTERM" }; }
  }
  try { process.kill(pid, "SIGKILL"); } catch { /* ignore */ }
  return { killed: true, signal: "SIGKILL" };
}

function preRescueCleanup(manifest, ids, wsRoot) {
  // Per references/modes/rescue.md "Pre-rescue cleanup":
  //   1. Kill stale pids on entries whose status is `running`.
  //   2. Stash dirty worktrees (record stash ref into mode_state).
  //   3. Best-effort prune missing worktrees.
  // We do (1) here directly; (2)+(3) are best-effort via git CLI.
  const report = { killed: [], stashed: [], pruned_worktrees: false };
  const entries = manifest.entries || [];
  for (const id of ids) {
    const entry = entries.find((e) => e.id === id);
    if (!entry) continue;
    if (entry.status === "running" && entry.runner_pid) {
      const r = killStalePid(entry.runner_pid);
      if (r.killed) report.killed.push({ id, pid: entry.runner_pid, signal: r.signal });
    }
    const wt = entry.worktree_path;
    if (wt && fs.existsSync(wt)) {
      // Stash dirty work, recording the stash ref so the operator can recover.
      const status = spawnSync("git", ["-C", wt, "status", "--porcelain"], { encoding: "utf8" });
      if (status.status === 0 && (status.stdout || "").trim().length > 0) {
        const stash = spawnSync("git", ["-C", wt, "stash", "push", "--include-untracked",
          "-m", `pre-rescue stash ${id}`], { encoding: "utf8" });
        if (stash.status === 0) {
          const ref = spawnSync("git", ["-C", wt, "rev-parse", "stash@{0}"], { encoding: "utf8" });
          report.stashed.push({ id, worktree_path: wt, stash_ref: (ref.stdout || "").trim() });
        }
      }
    }
  }
  // Prune any worktrees the manifest references that no longer exist on disk.
  if (entries.some((e) => e.worktree_path && !fs.existsSync(e.worktree_path))) {
    spawnSync("git", ["-C", wsRoot, "worktree", "prune"], { encoding: "utf8" });
    report.pruned_worktrees = true;
  }
  return report;
}

async function handleRescue(argv) {
  const command = "rescue";
  const parsed = parseArgsStrict(argv, command, {
    // `--redo` is HEAD/Yigit's flag name (failed | never-started | all-non-done).
    // `--apply` is S8's flag name (failed-only | never-started-only | all-non-done | ids:s1,s2).
    // We accept both; --redo is normalized into --apply below so the rest of the
    // handler has one code path. The docs reference --redo; --apply is the new
    // structured form. References: rescue.md, SKILL.md.
    valueOptions: ["manifest", "cwd", "apply", "redo", "concurrency", "i-have-measured"],
    booleanOptions: ["json", "accept-stale", "dry-run"],
  });
  if (parsed.err) return parsed.err;
  const { options } = parsed.value;
  // Normalize --redo into --apply (HEAD's bucket names → S8's bucket names).
  if (options.redo && !options.apply) {
    const redoMap = {
      "failed": "failed-only",
      "failed-only": "failed-only",
      "never-started": "never-started-only",
      "never-started-only": "never-started-only",
      "all-non-done": "all-non-done",
      "non-done": "all-non-done",
      "all": "all-non-done",
    };
    const normalized = redoMap[String(options.redo).trim().toLowerCase()];
    if (!normalized) {
      return errEnvelope(command, "bad_argument",
        `--redo must be one of: failed, never-started, all-non-done. Got: ${options.redo}`);
    }
    options.apply = normalized;
  }
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

  // Schema-version guard: rescue.md:70-72, failure-modes.md:179, manifest-contract.md:74.
  // Refuse forward-incompatible manifests (newer schema than the skill knows). The
  // refusal is the contract — newer schemas can carry semantically-required fields
  // (e.g. mode_state.* additions) that this version cannot reason about safely.
  // The user must upgrade the skill (or pull the latest pack) before resuming.
  // Do NOT silently downgrade or strip unknown fields. P2 derailment fix.
  const manifestSchema = typeof m.schema_version === "number" ? m.schema_version : 1;
  if (manifestSchema > SCHEMA_VERSION) {
    return errEnvelope(command, "schema_version_too_new",
      `Manifest schema_version=${manifestSchema} is newer than this skill's ` +
      `SCHEMA_VERSION=${SCHEMA_VERSION}. Upgrade the skill before resuming. ` +
      `Newer manifests may carry semantically-required fields (mode_state.* additions, ` +
      `policy fields) the older code cannot reason about; silent proceed risks corruption.`,
      {
        manifest_path: manifestPath,
        manifest_schema_version: manifestSchema,
        skill_schema_version: SCHEMA_VERSION,
        recovery: "upgrade the skill (or its installed pack) to a version with schema_version >= " + manifestSchema,
      });
  }

  // Freshness gate: rescue.md:51 contracts "≤ 7 days OR --accept-stale".
  // Older manifests may reference deleted branches, removed files, or codex-
  // companion job records aged out by MAX_JOBS=50 prune.
  const acceptStale = !!options["accept-stale"];
  const startedAt = m.started_at ? Date.parse(m.started_at) : NaN;
  if (Number.isFinite(startedAt)) {
    const ageMs = Date.now() - startedAt;
    const ageDays = ageMs / (24 * 60 * 60 * 1000);
    if (ageDays > 7 && !acceptStale) {
      return errEnvelope(command, "manifest_stale",
        `Manifest is ${ageDays.toFixed(1)} days old (started_at=${m.started_at}); ` +
        `rescue refuses manifests older than 7 days. ` +
        `Re-run with --accept-stale to override.`,
        { manifest_path: manifestPath, started_at: m.started_at, age_days: Number(ageDays.toFixed(2)) });
    }
    if (ageDays > 7 && acceptStale) {
      process.stderr.write(
        `[rescue] WARNING: manifest is ${ageDays.toFixed(1)} days old ` +
        `(started_at=${m.started_at}); proceeding because --accept-stale is set.\n`
      );
    }
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

  // No --apply → classify-only (the original read-only behavior). The
  // envelope's next_action is now a structured AskUserQuestion-style object
  // so the calling agent doesn't have to parse English.
  if (!options.apply) {
    const failedIds = (m.entries || []).filter((e) => e.status === "failed").map((e) => e.id);
    const neverStartedIds = (m.entries || []).filter((e) => e.status === "queued" && (e.attempts || 0) === 0).map((e) => e.id);
    const nonDoneIds = (m.entries || []).filter((e) => e.status !== "done").map((e) => e.id);
    const env = okEnvelope(command, {
      phase: "done",
      next_action: {
        kind: "ask_user_question",
        prompt: "Which subset to redo?",
        choices: [
          { id: "failed-only", label: `Redo failures only (${failedIds.length} entries)`, entry_ids: failedIds },
          { id: "never-started-only", label: `Redo never-started only (${neverStartedIds.length} entries)`, entry_ids: neverStartedIds },
          { id: "all-non-done", label: `Redo all non-done (${nonDoneIds.length} entries)`, entry_ids: nonDoneIds },
        ],
        rerun_with: `node use-codex.mjs rescue --manifest ${manifestPath} --apply <subset>`,
      },
      manifest_path: manifestPath,
      run_id: m.run_id,
      mode: m.mode,
      classification,
      workspace_root: wsRoot,
    });
    if (acceptStale) env.meta.accept_stale = true;
    return env;
  }

  // --apply <subset>: select, cleanup, flip-to-queued, re-spawn the original
  // mode's runner. Refuses rescue-of-rescue.
  if (m.mode === "rescue") {
    return errEnvelope(command, "bad_argument",
      "Refusing rescue-of-rescue: the manifest's mode is `rescue`. Resume the original mode.");
  }
  if (!RUNNERS[m.mode]) {
    return errEnvelope(command, "bad_argument",
      `Manifest's mode (${m.mode}) is not a re-spawnable mode. Supported: ${Object.keys(RUNNERS).join(", ")}.`);
  }

  const subset = selectRescueSubset(m, String(options.apply));
  if (subset.invalid !== undefined) {
    return errEnvelope(command, "bad_argument",
      `--apply must be one of: ${[...RESCUE_APPLY_SUBSETS].join(" | ")} | ids:s1,s2,...  Got: ${subset.invalid}`);
  }
  if ((subset.unknown || []).length > 0) {
    return errEnvelope(command, "bad_argument",
      `--apply ids: unknown slug(s): ${subset.unknown.join(", ")}.`);
  }
  if (subset.ids.length === 0) {
    const env = okEnvelope(command, {
      phase: "done",
      next_action: { kind: "noop", reason: "subset is empty; nothing to redispatch." },
      manifest_path: manifestPath,
      run_id: m.run_id,
      mode: m.mode,
      classification,
      workspace_root: wsRoot,
    });
    if (acceptStale) env.meta.accept_stale = true;
    return env;
  }

  const dryRun = !!options["dry-run"];

  // DRY-RUN PREVIEW: do NOT mutate the manifest, do NOT spawn the runner, do
  // NOT run pre-rescue cleanup. Build a preview envelope describing what the
  // real path WOULD do, so the operator can probe redispatch shape safely.
  // (Mode validity was already enforced above at the rescue-of-rescue / RUNNERS
  // gate; we don't re-check here.)
  if (dryRun) {
    const rerunCmd = `node use-codex.mjs rescue --manifest ${manifestPath} --apply ${String(options.apply)}`;
    const env = okEnvelope(command, {
      phase: "preview",
      next_action: {
        kind: "preview",
        reason: "dry-run; manifest not modified, runner not spawned",
        rerun_with: rerunCmd,
      },
      manifest_path: manifestPath,
      run_id: m.run_id,
      mode: m.mode,
      apply: String(options.apply),
      flipped_entries: [],
      redispatch: { selected_ids: subset.ids, subset: String(options.apply) },
      workspace_root: wsRoot,
      classification,
      dry_run: true,
    });
    env.meta.dry_run = true;
    if (acceptStale) env.meta.accept_stale = true;
    return env;
  }

  const codexErr = ensureCodexAvailable(command);
  if (codexErr) return codexErr;

  // Pre-rescue cleanup: kill stale pids, stash dirty worktrees, prune.
  const cleanup = preRescueCleanup(m, subset.ids, wsRoot);

  // Flip selected entries → queued.
  for (const id of subset.ids) {
    const r = flipEntryToQueued(manifestPath, id, wsRoot);
    if (r.status !== 0) {
      return errEnvelope(command, "python_helper_failed",
        `manifest-update.py failed flipping ${id}: ${(r.stderr || "").trim() || "no stderr"}`,
        { stdout: r.stdout, stderr: r.stderr });
    }
  }

  // Re-spawn the original mode's runner.
  const runnerPath = RUNNERS[m.mode];
  const runnerErr = ensureRunnerExists(runnerPath, command);
  if (runnerErr) return runnerErr;
  const monitorRoot = m.monitor_root || defaultMonitorRoot(manifestPath);
  const runnerLogPath = ensureLogPath(monitorRoot, m.run_id || generateRunId());
  const cap = m.concurrency_cap || DEFAULT_CONCURRENCY[m.mode] || 1;

  let runnerArgs;
  let runnerEnv = {};
  if (m.mode === "exec") {
    runnerArgs = [manifestPath];
    runnerEnv = { JOBS: String(cap), PROJECT_DIR: wsRoot };
  } else if (m.mode === "batch") {
    runnerArgs = [];
    const promptsDir = m.paths?.prompts_dir
      ? path.resolve(wsRoot, m.paths.prompts_dir)
      : path.join(monitorRoot, "prompts", m.run_id || "");
    const logsDir = m.paths?.logs_dir
      ? path.resolve(wsRoot, m.paths.logs_dir)
      : path.join(monitorRoot, "logs", m.run_id || "");
    // Honor original --answers-dir from manifest (persisted at mjs:877 + mjs:856).
    // Stale-workspace edge: if the user moved cwd, run-batch.sh surfaces a clean
    // error when the dir is missing — no dispatcher-side existence check needed.
    const answersFromManifest = m.answers_dir || m.paths?.answers_dir;
    const answersDir = answersFromManifest
      ? path.resolve(wsRoot, answersFromManifest)
      : path.join(wsRoot, "answers");
    runnerEnv = {
      JOBS: String(cap),
      PROMPTS: promptsDir,
      ANSWERS: answersDir,
      LOGS: logsDir,
      USE_CODEX_MANIFEST: manifestPath,
    };
  } else if (m.mode === "single") {
    const entry = (m.entries || []).find((e) => e.id === subset.ids[0]) || (m.entries || [])[0];
    runnerArgs = [
      "--prompt-file", entry.prompt_path || (entry.mode_state?.single?.prompt_file || ""),
      "--cwd", wsRoot,
      "--out", entry.answer_path || "",
      "--manifest", manifestPath,
      "--entry-id", entry.id,
    ];
    if (entry.mode_state?.single?.output_schema) {
      runnerArgs.push("--output-schema", entry.mode_state.single.output_schema);
    }
    if (entry.mode_state?.single?.reuse_worktree) runnerArgs.push("--reuse-worktree");
    if (entry.mode_state?.single?.resume_thread) {
      runnerArgs.push("--resume-thread", entry.mode_state.single.resume_thread);
    } else if (entry.codex_thread_id) {
      // Default rescue-of-single: resume the recorded thread.
      runnerArgs.push("--resume-thread", entry.codex_thread_id);
    } else {
      runnerArgs.push("--resume-last");
    }
  } else if (m.mode === "review") {
    runnerArgs = [manifestPath, "1"];
    runnerEnv = { JOBS: String(cap), PROJECT_DIR: wsRoot };
  } else {
    return errEnvelope(command, "bad_argument", `unsupported mode for rescue: ${m.mode}`);
  }

  const pid = spawnRunnerDetached({
    runnerPath,
    args: runnerArgs,
    cwd: wsRoot,
    env: runnerEnv,
    runnerLogPath,
  });
  const foregroundErr = foregroundRejectedEnvelope(command, pid);
  if (foregroundErr) return foregroundErr;

  const env = okEnvelope(command, {
    phase: "queued",
    next_action: "arm Monitor and wait",
    foreground_completed: pid?.foreground === true && pid?.status === 0,
    manifest_path: manifestPath,
    run_id: m.run_id,
    mode: m.mode,
    apply: String(options.apply),
    flipped_entries: subset.ids,
    redispatch: { selected_ids: subset.ids, subset: String(options.apply) },
    cleanup,
    runner_pid: pid,
    runner_status: pid.foreground ? pid.status : null,
    runner_log_path: runnerLogPath,
    workspace_root: wsRoot,
    classification,
    dry_run: false,
  }, buildMonitorForMode(m.mode, { manifestPath, runId: m.run_id, monitorRoot, jsonlPath: ((m.entries || [])[0] || {}).jsonl_path }));
  env.meta.dry_run = false;
  if (acceptStale) env.meta.accept_stale = true;
  return env;
}

async function handleAudit(argv) {
  const command = "audit";
  const parsed = parseArgsStrict(argv, command, {
    valueOptions: ["manifest", "cwd"],
    booleanOptions: ["json"],
  });
  if (parsed.err) return parsed.err;
  const { options } = parsed.value;
  const cwd = path.resolve(options.cwd || process.cwd());
  const wsRoot = workspaceFor(cwd);
  const manifestPath = options.manifest ? path.resolve(options.manifest) : manifestPathFor(cwd);

  // D-NEW-2 (round-8 follow-up): when the manifest exists on disk but won't
  // parse as JSON (truncated mid-write, half-written, deliberately damaged),
  // the Python helper silently treats it as "manifest absent" and the
  // dispatcher emits ok:true / "no drift detected". That's a false-negative
  // on a real recovery scenario (W3-S2 trial). Mirror handleRescue's
  // pre-helper corruption check: if the file exists AND won't parse, return
  // a typed `manifest_corrupt` envelope before delegating to the helper.
  if (fs.existsSync(manifestPath)) {
    const m = readManifestIfPresent(manifestPath);
    if (m && m.__corrupt) {
      return errEnvelope(command, "manifest_corrupt",
        `Manifest at ${manifestPath} is not valid JSON. Repair or delete before retrying. Run rescue mode for partial-run recovery.`,
        { manifest_path: manifestPath });
    }
  }

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
  // audit-fleet-state.py exit-code contract:
  //   0 = clean (no drift)
  //   1 = actionable (drift detected and/or manifest absent) — STILL a successful audit
  //   2 = manifest unreadable (env-level failure)
  //   3 = environmental error (e.g. permission denied)
  // Only exits >= 2 (or non-zero/non-one) indicate a real helper failure. Exits
  // 0 and 1 both produce a valid JSON report on stdout that the agent should
  // see as ok:true; the report itself carries `drift_total` / `actionable` so
  // the caller can distinguish clean from drift without re-reading the exit code.
  if (r.status !== 0 && r.status !== 1) {
    return errEnvelope(command, "python_helper_failed",
      `audit-fleet-state.py exited ${r.status}: ${(r.stderr || "").trim() || "no stderr"}`,
      { stdout: r.stdout, stderr: r.stderr });
  }
  let audit;
  try { audit = JSON.parse(r.stdout); } catch (e) {
    return errEnvelope(command, "python_helper_failed",
      `audit-fleet-state.py produced non-JSON stdout: ${e.message}`, { stdout: r.stdout });
  }
  const helperDriftTotal = (audit && typeof audit.drift_total === "number") ? audit.drift_total : 0;
  const orphans = (audit && Array.isArray(audit.orphan_worktrees)) ? audit.orphan_worktrees.length : 0;
  // Fold orphan worktrees into drift_total + drift_kinds so the top-level
  // scalar matches `actionable`. audit-fleet-state.py reports orphans as a
  // separate top-level array but excludes them from drift_total/drift_kinds;
  // an operator scanning `result.drift_total` alone would otherwise miss
  // orphan-only drift even though `actionable: true` and `next_action`
  // already point at rescue.
  const driftTotal = helperDriftTotal + orphans;
  if (audit && orphans > 0) {
    audit.drift_kinds = { ...(audit.drift_kinds || {}), orphan_worktrees: orphans };
  }
  // P2-15: mirror the orphan-corrected drift_total inside `result.audit` so
  // operators reading `result.audit.drift_total` see the same number as
  // `result.drift_total`. audit-fleet-state.py's own drift_total excludes
  // orphans; the dispatcher is the layer that combines them.
  if (audit && typeof audit === "object") {
    audit.drift_total = driftTotal;
  }
  return okEnvelope(command, {
    phase: "done",
    next_action: (driftTotal > 0)
      ? "review the drift summary; consider rescue mode"
      : "review the manifest",
    manifest_path: manifestPath,
    drift_total: driftTotal,
    audit,
    workspace_root: wsRoot,
  });
}

async function handleTidy(argv) {
  const command = "tidy";
  const parsed = parseArgsStrict(argv, command, {
    valueOptions: ["manifest", "cwd", "base", "force-abandon"],
    // P2-14: accept --json for parity with `audit`; cleanup-worktrees.py
    // already takes --json (the dispatcher always passes it). The flag is a
    // no-op at the dispatcher boundary because tidy's envelope is always
    // JSON; accepting --json prevents `unknown_option` rejection when the
    // operator mirrors the audit invocation shape.
    booleanOptions: ["execute", "json"],
  });
  if (parsed.err) return parsed.err;
  const { options } = parsed.value;
  const cwd = path.resolve(options.cwd || process.cwd());
  const wsRoot = workspaceFor(cwd);
  const manifestPath = options.manifest ? path.resolve(options.manifest) : manifestPathFor(cwd);

  // D-NEW-2 (round-8 follow-up): see handleAudit for rationale. Tidy's
  // helper also silently absorbs corrupt manifests and reports "nothing to
  // clean", which would let the operator believe a damaged-on-disk manifest
  // is healthy (W3-S2 trial). Mirror handleRescue's corruption check.
  if (fs.existsSync(manifestPath)) {
    const m = readManifestIfPresent(manifestPath);
    if (m && m.__corrupt) {
      return errEnvelope(command, "manifest_corrupt",
        `Manifest at ${manifestPath} is not valid JSON. Repair or delete before retrying. Run rescue mode for partial-run recovery.`,
        { manifest_path: manifestPath });
    }
  }

  if (!fs.existsSync(PY_HELPERS.tidy)) {
    return errEnvelope(command, "python_helper_failed",
      `cleanup-worktrees.py not found at ${PY_HELPERS.tidy}. The parallel subagent hasn't authored it yet.`,
      { helper_path: PY_HELPERS.tidy });
  }
  const args = ["--manifest", manifestPath, "--json"];
  if (options.execute) args.push("--execute");
  // D-NEW (round-8 follow-up, A4 audit): the dispatcher's tidy handler
  // declares --base and --force-abandon in valueOptions, so they parse
  // without `unknown_option`, but pre-patch the args list above did not
  // forward either to cleanup-worktrees.py. The helper accepts both
  // (cleanup-worktrees.py:160 / :164). The silent-drop was strictly worse
  // than D11's loud `unknown arg` because the helper still emits its
  // refusal message instructing the operator to "Pass --force-abandon
  // <id>" — which they already did. Forward both flags here so the
  // operator's destructive authorization actually reaches the helper.
  if (options.base) args.push("--base", String(options.base));
  if (options["force-abandon"]) args.push("--force-abandon", String(options["force-abandon"]));
  const r = runPythonHelper(PY_HELPERS.tidy, args, wsRoot);
  // P1-5 / D17: align tidy's success contract with audit's. cleanup-worktrees.py
  //   0 = clean / nothing to do
  //   1 = actionable preview (planned removals OR dry-run-refused entries)
  //   2 = refused during --execute (operator must pass --force-abandon)
  //   3 = removal failed mid-execute
  //   4 = manifest write failed
  // Exits 0 and 1 are both successful audits/previews — the report itself
  // carries `summary.refused` / `summary.planned` so the agent classifies
  // outcomes from the JSON, not from the exit code alone.
  if (r.status !== 0 && r.status !== 1) {
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
// P1-10 (symlink fix): equality on raw `import.meta.url` vs `process.argv[1]`
// fails when the dispatcher is invoked through a symlink — Node resolves
// `import.meta.url` to the real path while `process.argv[1]` keeps the
// symlink path, so `main()` silently never fires and stdout is empty.
// `fs.realpathSync` resolves both sides through symlinks; the try/catch
// keeps non-existent / permission-denied argv[1] from throwing.
function isMainModule() {
  try {
    return fs.realpathSync(fileURLToPath(import.meta.url))
      === fs.realpathSync(process.argv[1]);
  } catch {
    return false;
  }
}
if (isMainModule()) {
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
  carryForwardDoneEntries,
  parseArgsStrict,
  resolveConcurrency,
  selectRescueSubset,
  POLICY,
  MONITOR_HARD_MAX_MS,
  CONCURRENCY_HARD_CAP,
  CONCURRENCY_ABSOLUTE_CEILING,
  DEFAULT_CONCURRENCY,
};

#!/usr/bin/env bash
# bootstrap.sh — one-shot universal pre-flight for orchestrate-codex.
#
# What it does:
#   1. Verifies git repo (when applicable; batch/single can skip with SKIP_GIT=1).
#   2. Verifies `codex` CLI is on PATH and authenticated (codex login status).
#   3. Verifies jq + flock (mandatory for manifest-update.sh) + node (≥18 for codex-cc).
#   4. Resolves the same state dir as codex-cc/lib/state.mjs and creates the
#      orchestrate-codex subdir. Manifest path is printed on stdout for the
#      dispatcher to capture.
#   5. Pins the baseline SHA when inside a git repo (HEAD at start of run).
#   6. Advises on .gitignore coverage for the per-mode worktree pattern
#      (../<repo>-wt-<mode>-*).
#
# Inputs (env):
#   PROJECT_DIR    repo root (default: cwd)
#   ORCHESTRATE_MODE  exec|batch|single|review|rescue (default: unknown)
#   ORCHESTRATE_RUN_ID  run id; if empty, generated and emitted on stdout
#   ORCHESTRATE_SLUG    workspace slug override (defaults to derived from cwd)
#   SKIP_GIT       1 to skip git checks (batch mode without a repo)
#   MONITOR_ROOT   monitor logs dir (default: <state-dir>/logs)
#
# Outputs (stdout): one KEY=VALUE per resolved path. Format:
#   STATE_DIR=<abs path>
#   MANIFEST_PATH=<abs path to manifest.json (may not yet exist)>
#   MONITOR_ROOT=<abs path>
#   BASELINE_SHA=<sha or empty if not a git repo>
#   RUN_ID=<id>
#   PLUGIN_DATA_ROOT=<abs path>
#
# Exit codes: 0 OK, 1 not-a-git-repo (when SKIP_GIT=0), 2 codex CLI missing,
#             3 codex unauthenticated, 4 missing jq/flock/node, 5 plugin-data
#             dir unwritable.

set -uo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
ORCHESTRATE_MODE="${ORCHESTRATE_MODE:-unknown}"
SKIP_GIT="${SKIP_GIT:-0}"
ORCHESTRATE_RUN_ID="${ORCHESTRATE_RUN_ID:-}"
ORCHESTRATE_SLUG="${ORCHESTRATE_SLUG:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

# stderr banner for human readers; the final KEY=VALUE block goes to stdout.
say() { echo "[bootstrap] $*" >&2; }
fail() { echo "[bootstrap] ERROR: $*" >&2; exit "${2:-1}"; }

cd "$PROJECT_DIR" || fail "cannot cd to PROJECT_DIR=$PROJECT_DIR" 1

say "mode=$ORCHESTRATE_MODE project=$PROJECT_DIR"

# ── 1. Mandatory binaries ──────────────────────────────────────
for bin in jq flock; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    # macOS doesn't ship flock by default — the user must `brew install flock`.
    fail "$bin not found on PATH (required for manifest atomicity)" 4
  fi
done
if ! command -v node >/dev/null 2>&1; then
  fail "node not found on PATH (required for the codex-cc dispatcher)" 4
fi

# ── 2. codex CLI present + authenticated ──────────────────────
if ! command -v codex >/dev/null 2>&1; then
  fail "codex CLI not found on PATH. Install: npm i -g @openai/codex" 2
fi
CODEX_VERSION="$(codex --version 2>/dev/null || echo unknown)"
say "codex version: $CODEX_VERSION"
say "model: $CODEX_MODEL  effort: $CODEX_EFFORT"

if codex login status >/dev/null 2>&1; then
  say "codex auth: OK"
else
  if [[ "${ORCHESTRATE_SKIP_CODEX_AUTH:-0}" == "1" ]]; then
    say "WARN: codex login status returned non-zero; ORCHESTRATE_SKIP_CODEX_AUTH=1 bypassed the hard gate."
  else
    fail "codex login status returned non-zero. Run \`codex login\` before dispatching." 3
  fi
fi

# ── 3. Git repo verification (skippable for batch w/o repo) ───
BASELINE_SHA=""
if [[ "$SKIP_GIT" != "1" ]]; then
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    fail "$PROJECT_DIR is not a git repo. Run \`git init\` first, or set SKIP_GIT=1 (batch mode)." 1
  fi
  BASELINE_SHA="$(git rev-parse HEAD 2>/dev/null || echo "")"
  say "baseline: ${BASELINE_SHA:0:8}"
else
  say "git checks skipped (SKIP_GIT=1)"
fi

# ── 4. codex-cc state dir resolution ──────────────────────────
# Mirrors scripts/codex-cc/lib/state.mjs exactly:
#   $CLAUDE_PLUGIN_DATA/state/<slug>-<sha256(realpath)[:16]>
#   or ${TMPDIR:-/tmp}/codex-companion/<slug>-<sha256(realpath)[:16]>
if [[ -z "$ORCHESTRATE_SLUG" ]]; then
  workspace_root="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PROJECT_DIR")"
  canonical_root="$(cd "$workspace_root" 2>/dev/null && pwd -P || printf '%s' "$workspace_root")"
  base="$(basename "$workspace_root")"
  slug="$(printf '%s' "$base" | sed -E 's/[^a-zA-Z0-9._-]+/-/g; s/^-+|-+$//g')"
  [[ -n "$slug" ]] || slug="workspace"
  if command -v shasum >/dev/null 2>&1; then
    hash="$(printf '%s' "$canonical_root" | shasum -a 256 | awk '{print substr($1,1,16)}')"
  else
    hash="$(printf '%s' "$canonical_root" | sha256sum | awk '{print substr($1,1,16)}')"
  fi
  ORCHESTRATE_SLUG="${slug}-${hash}"
fi

if [[ -n "${CLAUDE_PLUGIN_DATA:-}" ]]; then
  PLUGIN_DATA_ROOT="$CLAUDE_PLUGIN_DATA"
  STATE_ROOT="$CLAUDE_PLUGIN_DATA/state"
else
  PLUGIN_DATA_ROOT=""
  STATE_ROOT="${TMPDIR:-/tmp}/codex-companion"
fi

STATE_DIR="$STATE_ROOT/$ORCHESTRATE_SLUG/orchestrate-codex"
MANIFEST_PATH="$STATE_DIR/manifest.json"
MONITOR_ROOT="${MONITOR_ROOT:-$STATE_DIR/logs}"

if ! mkdir -p "$STATE_DIR" "$MONITOR_ROOT" 2>/dev/null; then
  fail "cannot create state dir $STATE_DIR (plugin-data dir not writable)" 5
fi
say "state-dir: $STATE_DIR"
say "manifest:  $MANIFEST_PATH (created by dispatcher)"
say "monitor:   $MONITOR_ROOT"

# ── 5. Run id ─────────────────────────────────────────────────
if [[ -z "$ORCHESTRATE_RUN_ID" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    suffix="$(openssl rand -hex 2)"
  else
    suffix="$(printf '%04x' $(( RANDOM & 0xffff )))"
  fi
  ORCHESTRATE_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$suffix"
fi
say "run-id: $ORCHESTRATE_RUN_ID"

# ── 6. .gitignore advisory for the worktree pattern ───────────
# orchestrate-codex's worktree convention is `../<repo>-wt-<mode>-<slug>`,
# which lives OUTSIDE the repo, so .gitignore doesn't strictly need to cover
# it. Users running with WORKTREE_DIR_NAME=.worktrees inside the repo will
# want .gitignore to cover that path; probe and advise.
if [[ "$SKIP_GIT" != "1" ]]; then
  WT_DIR_NAME="${WORKTREE_DIR_NAME:-.worktrees}"
  if ! git check-ignore -q "$WT_DIR_NAME/.test" 2>/dev/null; then
    say "advisory: probed $WT_DIR_NAME/ against .gitignore and it is NOT covered."
    say "  Ignore this if you use the default out-of-repo worktree convention"
    say "  (../<repo>-wt-<mode>-<slug>); only relevant if you have set"
    say "  WORKTREE_DIR_NAME to an in-repo path, in which case add: $WT_DIR_NAME/"
  fi
fi

# ── 7. Emit machine-readable resolved paths on stdout ─────────
# The dispatcher (orchestrate-codex.mjs) reads this block to populate the
# manifest. Format: KEY=VALUE, one per line, no trailing whitespace.
cat <<EOF
STATE_DIR=$STATE_DIR
MANIFEST_PATH=$MANIFEST_PATH
MONITOR_ROOT=$MONITOR_ROOT
BASELINE_SHA=$BASELINE_SHA
RUN_ID=$ORCHESTRATE_RUN_ID
PLUGIN_DATA_ROOT=$PLUGIN_DATA_ROOT
WORKSPACE_SLUG=$ORCHESTRATE_SLUG
CODEX_MODEL=$CODEX_MODEL
CODEX_EFFORT=$CODEX_EFFORT
EOF

say "ready"

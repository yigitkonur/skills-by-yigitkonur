#!/usr/bin/env bash
# run-review.sh — review mode driver. One invocation = one round, fanned out
# over branches.
#
# For every branch in the manifest, in parallel:
#   1. Setup-worktree per branch (if not already present from a prior round).
#   2. Spawn `codex exec review --base <base> --json -o <findings.md>` inside
#      the worktree. `codex exec review` is the non-interactive review surface;
#      its JSONL output flows through codex-json-filter.sh so Monitor sees
#      compact lines.
#   3. Write the round's findings under <state-dir>/rounds/<slug>.<round>.md
#      and the JSONL log under <state-dir>/rounds/<slug>.<round>.jsonl.
#
# CLI flag drift note: the plan's appendix says `codex review` accepts a
# narrower flag set (no --json, no -o, no bypass). The live `codex exec
# review` accepts ALL of: --json, -o, --dangerously-bypass-approvals-and-sandbox,
# --skip-git-repo-check, -m, --ephemeral. We use `codex exec review` (not bare
# `codex review`) for that reason. CODEX_REVIEW_FLAGS in codex-flags.sh is
# kept narrow as a safety rail for direct `codex review` invocations.
#
# Monitor contract: emits one stdout line per state transition:
#   START <slug>     review starting
#   DONE  <slug>     findings written, classifier-eligible
#   FAIL  <slug>     codex review failed
#   SKIP  <slug>     pre-existing findings file (idempotent)
# Final line: `--- all jobs finished ---`.
#
# Usage:
#   run-review.sh [--dry-run] <manifest.json> <round-number>
#
# The manifest's review entries[] shape:
#   { id, slug, branch, base_branch, worktree_path?, status, ... }
#
# Inputs (env):
#   JOBS              parallel concurrency (default 4)
#   PROJECT_DIR       repo root (default: cwd)
#   ORCHESTRATE_MODE  exported to setup-worktree as `review`
#   FILTER_LEVEL      passed to codex-json-filter.sh (default normal)
#   STATE_DIR         where rounds/<slug>.<round>.{md,jsonl} live. Defaults
#                     to dirname(<manifest>).
#
# Exit codes: 0 fleet ran, 1 manifest issue, 2 codex/jq missing,
#             3 invalid args/round.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

DRY_RUN=0
JOBS="${JOBS:-4}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
FILTER_LEVEL="${FILTER_LEVEL:-normal}"
export ORCHESTRATE_MODE="${ORCHESTRATE_MODE:-review}"

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -lt 2 ]]; then
  echo "usage: $0 [--dry-run] <manifest.json> <round-number>" >&2
  exit 3
fi

MANIFEST="$1"
ROUND="$2"

if [[ ! -f "$MANIFEST" ]]; then
  echo "FATAL manifest not found: $MANIFEST" >&2
  exit 1
fi
if ! jq -e . "$MANIFEST" >/dev/null 2>&1; then
  echo "FATAL manifest is not valid JSON: $MANIFEST" >&2
  exit 1
fi
if ! [[ "$ROUND" =~ ^[0-9]+$ ]]; then
  echo "FATAL round must be a non-negative integer, got: $ROUND" >&2
  exit 3
fi
if [[ "$ROUND" -gt 10 ]]; then
  echo "WARN round=$ROUND exceeds the soft cap of 10. The plan's review" >&2
  echo "     mode tightened the cap from 20 → 10 because each review is" >&2
  echo "     a single codex review call (not a multi-turn applier loop)." >&2
fi

if ! command -v codex >/dev/null 2>&1 && [[ "$DRY_RUN" != "1" ]]; then
  echo "FATAL codex CLI not found on PATH" >&2
  exit 2
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "FATAL jq not found on PATH" >&2
  exit 2
fi

if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "FATAL JOBS must be a positive integer, got: $JOBS" >&2
  exit 3
fi

STATE_DIR="${STATE_DIR:-$(dirname "$MANIFEST")}"
ROUNDS_DIR="$STATE_DIR/rounds"
mkdir -p "$ROUNDS_DIR"

JSON_FILTER="$SCRIPT_DIR/codex-json-filter.sh"

# ── Build worklist: entries with status NOT IN {converged, blocked} ────
WORKLIST="$(mktemp)"
trap 'rm -f "$WORKLIST"' EXIT

jq -r '
  .entries[]
  | select((.status // "queued") != "converged"
           and (.status // "queued") != "blocked"
           and (.status // "queued") != "cap-reached")
  | [
      .id,
      (.slug // .id),
      (.branch // ""),
      (.base_branch // "main"),
      (.worktree_path // ""),
      (.status // "queued")
    ]
  | @tsv
' "$MANIFEST" > "$WORKLIST"

if [[ ! -s "$WORKLIST" ]]; then
  echo "[run-review] no entries to review (all branches terminal)"
  echo "--- all jobs finished ---"
  exit 0
fi

echo "[run-review] manifest: $MANIFEST"
echo "[run-review] round:    $ROUND"
echo "[run-review] entries:  $(wc -l < "$WORKLIST" | tr -d ' ') to review"
echo "[run-review] rounds:   $ROUNDS_DIR"

# ── Per-branch runner ──────────────────────────────────────────
run_one() {
  local row="$1"
  IFS=$'\t' read -r id slug branch base wt_path _status <<<"$row"

  local findings="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.md"
  local jsonl="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.jsonl"
  local errlog="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.err.log"

  if [[ -s "$findings" ]]; then
    echo "SKIP  $id (round $ROUND_NUM findings already exist: $findings)"
    return 0
  fi

  if [[ -z "$branch" ]]; then
    echo "FAIL  $id (no branch in manifest entry)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now last_error="missing branch" 2>/dev/null || true
    return 1
  fi

  echo "START $id (round $ROUND_NUM, branch=$branch base=$base)"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    status=running attempts=+1 round="$ROUND_NUM" \
    started_at=now 2>/dev/null || true

  # ── Setup worktree if needed ─────────────────────────────────
  local wt_resolved=""
  if [[ -n "$wt_path" && -d "$wt_path" ]]; then
    wt_resolved="$wt_path"
  else
    if [[ "$DRY_RUN_LOCAL" == "1" ]]; then
      wt_resolved="<dry-run-wt>/$slug"
    else
      local setup_out
      if ! setup_out="$(ALLOW_REUSE=1 "$SCRIPT_DIR_ABS/setup-worktree.sh" "$slug" "$branch" "$base" 2>&1)"; then
        echo "FAIL  $id (setup-worktree failed)"
        printf '%s\n' "$setup_out" | sed 's/^/  [setup] /'
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
          status=failed finished_at=now last_error="setup-worktree failed" 2>/dev/null || true
        return 1
      fi
      wt_resolved="$(printf '%s\n' "$setup_out" | awk -F= '/^WORKTREE_PATH=/ { sub(/^WORKTREE_PATH=/, ""); print; exit }')"
      if [[ -z "$wt_resolved" ]]; then
        echo "FAIL  $id (could not parse WORKTREE_PATH from setup-worktree)"
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
          status=failed finished_at=now last_error="setup-worktree parse failed" 2>/dev/null || true
        return 1
      fi
    fi
  fi
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    worktree_path="$wt_resolved" 2>/dev/null || true

  # ── Reconstruct CODEX_FLAGS in subshell ─────────────────────
  # Newline-delimited string (NULs get stripped by `$(...)`); no flag value
  # in our policy contains a newline.
  local -a flags=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && flags+=("$f")
  done <<<"$CODEX_FLAGS_STR"

  # ── Spawn codex exec review ─────────────────────────────────
  # Note: `codex exec review` accepts the full bypass+skip-git+model flag set
  # (verified live, contradicting the plan's narrower CODEX_REVIEW_FLAGS).
  # We pass --base <base> + --json + -o <findings>, plus CODEX_FLAGS.
  if [[ "$DRY_RUN_LOCAL" == "1" ]]; then
    echo "[dry-run] (cd $wt_resolved && codex exec review ${flags[*]} --base $base --json -o $findings)"
    echo "DONE  $id (dry-run)"
    return 0
  fi

  local start_ts end_ts elapsed exit_code thread_id=""
  start_ts="$(date +%s)"

  set +e
  # The codex review JSONL stream → tee → filter chain mirrors run-single.
  if [[ -x "$JSON_FILTER" ]]; then
    (cd "$wt_resolved" && \
      codex exec review "${flags[@]}" --base "$base" --json -o "$findings" 2>"$errlog") \
      | tee "$jsonl" \
      | CODEX_FILTER_LEVEL="$FILTER_LEVEL" "$JSON_FILTER" \
      | sed "s/^/[review:$slug] /"
    exit_code="${PIPESTATUS[0]}"
  else
    (cd "$wt_resolved" && \
      codex exec review "${flags[@]}" --base "$base" --json -o "$findings" 2>"$errlog") \
      | tee "$jsonl" \
      | sed "s/^/[review:$slug] /"
    exit_code="${PIPESTATUS[0]}"
  fi
  set -e

  end_ts="$(date +%s)"
  elapsed=$(( end_ts - start_ts ))

  if [[ -f "$jsonl" ]]; then
    thread_id="$(grep -m1 '"type":"thread.started"' "$jsonl" 2>/dev/null \
                  | jq -r '.thread_id // ""' 2>/dev/null || echo "")"
  fi

  if [[ "$exit_code" -ne 0 ]]; then
    echo "FAIL  $id (codex review exit=$exit_code; runtime=${elapsed}s; see $errlog)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now exit_code="$exit_code" \
      last_error="codex review exit $exit_code" \
      codex_thread_id="$thread_id" \
      last_findings_path="$findings" 2>/dev/null || true
    return 1
  fi

  if [[ ! -s "$findings" ]]; then
    echo "FAIL  $id (codex review exit=0 but findings empty)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
      status=failed finished_at=now exit_code=0 last_error="empty findings" \
      codex_thread_id="$thread_id" \
      last_findings_path="$findings" 2>/dev/null || true
    return 1
  fi

  # Status stays as `running` here — the orchestrator (Claude main agent)
  # decides converged/cap-reached after reading the findings + classifier.
  # We mark `reviewed` to indicate the round produced findings cleanly.
  echo "DONE  $id (runtime=${elapsed}s findings=$(wc -c < "$findings" | tr -d ' ')B)"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$id" \
    status=reviewed finished_at=now exit_code=0 \
    codex_thread_id="$thread_id" \
    last_findings_path="$findings" 2>/dev/null || true
}

CODEX_FLAGS_STR="$(printf '%s\n' "${CODEX_FLAGS[@]}")"
export CODEX_FLAGS_STR
export SCRIPT_DIR_ABS="$SCRIPT_DIR"
export ORCHESTRATE_MANIFEST="$MANIFEST"
export ROUND_NUM="$ROUND"
export ROUNDS_DIR JSON_FILTER FILTER_LEVEL DRY_RUN_LOCAL="$DRY_RUN" PROJECT_DIR
export -f run_one

awk -F'\t' '$6 != "converged" && $6 != "blocked" && $6 != "cap-reached"' "$WORKLIST" \
  | tr '\n' '\0' \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"'

echo "--- all jobs finished ---"

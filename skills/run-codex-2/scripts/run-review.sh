#!/usr/bin/env bash
# run-review.sh — review mode driver. ONE invocation = ONE round, fanned out
# over branches. Multi-round loops are driven by the orchestrator (Claude main
# agent) re-invoking this script with an incremented <round-number>; the
# round counter is NOT advanced from inside the script.
#
# For every branch in the manifest, in parallel:
#   1. Setup-worktree per branch (if not already present from a prior round).
#   2. Spawn `codex exec review --base <base> --json -o <findings.md>` inside
#      the worktree. `codex exec review` is the non-interactive review surface;
#      its JSONL output flows through codex-json-filter.sh so Monitor sees
#      compact lines.
#   3. Write the round's findings under <state-dir>/rounds/<slug>.r<round>.md
#      and the JSONL log under <state-dir>/rounds/<slug>.r<round>.jsonl.
#   4. Convert the JSONL event stream into a structured findings JSON file
#      (<slug>.r<round>.json) so classify-review-feedback.py can consume it.
#      `codex exec review -o <file>` writes markdown despite `--json`; the
#      classifier requires JSON, so we synthesise it from the JSONL events.
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
# Manifest writes per entry (manifest-contract.md):
#   - log_path / jsonl_path / answer_path  (per-round paths)
#   - mode_state.rounds[]: one record appended per completed round
#     ({round, findings_md, findings_json, jsonl, ts})
#   - last_findings_path / codex_thread_id / round
#   - status `done` on round success (the orchestrator advances to
#     `converged` / `cap_reached` / `blocked` based on the classifier).
#
# Signal handling: a `trap 'kill 0' TERM INT EXIT` near top propagates
# SIGTERM to xargs and codex children — no orphan codex review processes
# survive the runner.
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
#   USE_CODEX_MODE  exported to setup-worktree as `review`
#   FILTER_LEVEL      passed to codex-json-filter.sh (default normal)
#   STATE_DIR         where rounds/<slug>.r<round>.{md,json,jsonl} live.
#                     Defaults to dirname(<manifest>).
#
# Exit codes: 0 fleet ran, 1 manifest issue, 2 codex/jq missing,
#             3 invalid args/round.

set -u

# ── Signal trap: on SIGTERM/SIGINT propagate to xargs children (and the
# codex review CLIs they spawn) so a runner kill leaves no orphan codex
# processes. Bash defers traps while waiting on a foreground process — to
# avoid that we run xargs in the background and use `wait`.
_run_review_signal() {
  trap - TERM INT
  if [[ -n "${_run_review_xargs_pid:-}" ]]; then
    kill -TERM "$_run_review_xargs_pid" 2>/dev/null || true
  fi
  # Process-group sweep: BSD xargs on macOS doesn't propagate SIGTERM to
  # its children, so we hit every descendant via the pgid.
  pkill -TERM -g $$ 2>/dev/null || true
  sleep 0.5
  pkill -KILL -g $$ 2>/dev/null || true
  exit 143
}
trap _run_review_signal TERM INT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

DRY_RUN=0
JOBS="${JOBS:-4}"
PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
FILTER_LEVEL="${FILTER_LEVEL:-normal}"
export USE_CODEX_MODE="${USE_CODEX_MODE:-review}"

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
# Absolute-ize the manifest path for the worker subshells (which `cd` into
# the per-branch worktrees and would otherwise resolve a relative path
# under the worktree, not the original cwd).
case "$MANIFEST" in
  /*) ;;
  *)  MANIFEST="$(cd "$(dirname "$MANIFEST")" && pwd -P)/$(basename "$MANIFEST")" ;;
esac
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
# Resolve to an absolute path so worker subshells that `cd` into per-branch
# worktrees still write to the same rounds dir. (Without this, a relative
# `./rounds/foo.err.log` would resolve under each worktree.)
case "$STATE_DIR" in
  /*) ;;
  *)  STATE_DIR="$(cd "$STATE_DIR" 2>/dev/null && pwd -P)" ;;
esac
ROUNDS_DIR="$STATE_DIR/rounds"
mkdir -p "$ROUNDS_DIR"

JSON_FILTER="$SCRIPT_DIR/codex-json-filter.sh"

# ── Build worklist: entries with status NOT IN {converged, blocked} ────
WORKLIST="$(mktemp)"
# Resource cleanup on EXIT (separate from signal propagation above).
trap 'rm -f "$WORKLIST"' EXIT

jq -r '
  .entries[]
  | select((.status // "queued") != "converged"
           and (.status // "queued") != "blocked"
           and (.status // "queued") != "cap_reached")
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
  local findings_json="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.json"
  local jsonl="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.jsonl"
  local errlog="$ROUNDS_DIR/${slug}.r${ROUND_NUM}.err.log"

  if [[ -s "$findings" ]]; then
    echo "SKIP  $id (round $ROUND_NUM findings already exist: $findings)"
    return 0
  fi

  if [[ -z "$branch" ]]; then
    echo "FAIL  $id (no branch in manifest entry)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
      status=failed finished_at=now last_error="missing branch" 2>/dev/null || true
    return 1
  fi

  echo "START $id (round $ROUND_NUM, branch=$branch base=$base)"
  # Populate paths up front per the manifest contract. For review mode the
  # `answer_path` slot points at the markdown findings (review's primary
  # output); the JSON synthesised later goes on mode_state.rounds[].
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
    status=running attempts=+1 round="$ROUND_NUM" \
    started_at=now \
    log_path="$errlog" \
    jsonl_path="$jsonl" \
    answer_path="$findings" 2>/dev/null || true

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
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
          status=failed finished_at=now last_error="setup-worktree failed" 2>/dev/null || true
        return 1
      fi
      wt_resolved="$(printf '%s\n' "$setup_out" | awk -F= '/^WORKTREE_PATH=/ { sub(/^WORKTREE_PATH=/, ""); print; exit }')"
      if [[ -z "$wt_resolved" ]]; then
        echo "FAIL  $id (could not parse WORKTREE_PATH from setup-worktree)"
        "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
          status=failed finished_at=now last_error="setup-worktree parse failed" 2>/dev/null || true
        return 1
      fi
    fi
  fi
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
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
    # Materialize a stub findings file so downstream classifier + tests see the
    # expected artifact, and mark the entry converged so the orchestrator's
    # round loop terminates cleanly in dry-run.
    mkdir -p "$(dirname "$findings")"
    printf '{"summary":"dry-run","comments":[]}\n' > "$findings"
    # P0-1: dry-run discriminator — see run-fleet.sh for rationale. Review
    # uses status=converged on dry-run to terminate the orchestrator's round
    # loop cleanly; the dry_run=true flag prevents carryForwardDoneEntries
    # from preserving this fake-converged entry across re-dispatch.
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
      status=converged finished_at=now exit_code=0 \
      last_findings_path="$findings" dry_run=true 2>/dev/null || true
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
    thread_id="$(jq -r '
      select(.type == "thread.started")
      | select((.parent_thread_id // .parent_id // null) == null)
      | select((.subagent // false) == false)
      | .thread_id // empty
    ' "$jsonl" 2>/dev/null | head -n 1 || echo "")"
  fi

  if [[ "$exit_code" -ne 0 ]]; then
    echo "FAIL  $id (codex review exit=$exit_code; runtime=${elapsed}s; see $errlog)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
      status=failed finished_at=now exit_code="$exit_code" \
      last_error="codex review exit $exit_code" \
      codex_thread_id="$thread_id" \
      last_findings_path="$findings" 2>/dev/null || true
    return 1
  fi

  if [[ ! -s "$findings" ]]; then
    echo "FAIL  $id (codex review exit=0 but findings empty)"
    "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
      status=failed finished_at=now exit_code=0 last_error="empty findings" \
      codex_thread_id="$thread_id" \
      last_findings_path="$findings" 2>/dev/null || true
    return 1
  fi

  # ── Synthesise JSON findings from the JSONL event stream ────
  # `codex exec review -o <file>` writes markdown despite `--json`; the
  # classifier (classify-review-feedback.py) requires JSON. We walk the
  # JSONL events for `item.type=agent_message` (the textual review output)
  # and emit a normalised structure: { thread_id, agent_messages[],
  # findings_md_path }. The classifier currently re-parses the markdown,
  # but committing a JSON sidecar preserves the documented contract that
  # `<findings>.json` is the classifier's input.
  if [[ -s "$jsonl" ]]; then
    # Read the markdown findings (if non-empty) so we can pass it to the
    # classifier as `raw_text` — the classifier falls back to `raw_text`
    # when no structured `items`/`findings` array is present.
    local md_text=""
    if [[ -s "$findings" ]]; then
      md_text="$(cat "$findings")"
    fi
    if ! jq -s \
            --arg md "$findings" \
            --arg slug "$slug" \
            --arg base "$base" \
            --arg raw_text "$md_text" \
            --argjson round "$ROUND_NUM" '
      # Pull the first thread.started thread_id and every agent_message text.
      ((. // []) | map(select(type == "object"))) as $events
      | {
          # Classifier-compatible top-level keys (it prefers items/findings
          # or falls back to raw_text/text).
          review_id:      ($slug + ".r" + ($round | tostring)),
          findings:       [],
          raw_text:       $raw_text,
          # Forensic context for the orchestrator.
          slug:           $slug,
          base:           $base,
          round:          $round,
          findings_md:    $md,
          thread_id:      ([$events[]
                            | select(.type == "thread.started")
                            | select((.parent_thread_id // .parent_id // null) == null)
                            | select((.subagent // false) == false)
                            | .thread_id] | first // null),
          agent_messages: [$events[] | select(.type == "agent_message" or .item.type == "agent_message")
                           | (.message // .item.message // .text // "")
                           | select(. != "")],
          raw_event_count: ($events | length)
        }
    ' < <(while IFS= read -r line; do
            # Each JSONL line is one event. Tolerate non-JSON lines (codex
            # sometimes emits banner text on stdout) by filtering them out.
            jq -e . <<<"$line" >/dev/null 2>&1 && printf '%s\n' "$line"
          done < "$jsonl") > "$findings_json" 2>/dev/null; then
      # If the synthesis fails, leave a minimal stub the classifier can
      # still consume (raw_text path) so it can surface a parse error.
      jq -n --arg slug "$slug" --argjson round "$ROUND_NUM" \
            --arg md "$findings" --arg raw_text "$md_text" '
        { review_id: ($slug + ".r" + ($round | tostring)),
          findings: [], raw_text: $raw_text,
          slug: $slug, round: $round, findings_md: $md,
          error: "jsonl_parse_failed" }
      ' > "$findings_json" 2>/dev/null || \
        printf '{"review_id":"%s.r%s","findings":[],"raw_text":"","error":"jsonl_parse_failed"}\n' \
          "$slug" "$ROUND_NUM" > "$findings_json"
    fi
  else
    jq -n --arg slug "$slug" --argjson round "$ROUND_NUM" \
          --arg md "$findings" '
      { review_id: ($slug + ".r" + ($round | tostring)),
        findings: [], raw_text: "",
        slug: $slug, round: $round, findings_md: $md,
        error: "jsonl_missing" }
    ' > "$findings_json" 2>/dev/null || \
      printf '{"review_id":"%s.r%s","findings":[],"raw_text":"","error":"jsonl_missing"}\n' \
        "$slug" "$ROUND_NUM" > "$findings_json"
  fi

  # ── Append a per-round record to mode_state.rounds[] ────────
  # `manifest-update.sh` only assigns scalars, so we do a flock'd jq
  # in-place edit here. The lock file matches manifest-update.sh's so the
  # two writers serialise.
  local lockfile="${USE_CODEX_MANIFEST}.lock"
  local round_record
  round_record="$(jq -n \
    --argjson round "$ROUND_NUM" \
    --arg findings_md "$findings" \
    --arg findings_json "$findings_json" \
    --arg jsonl "$jsonl" \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
    { round: $round,
      findings_md: $findings_md,
      findings_json: $findings_json,
      jsonl: $jsonl,
      ts: $ts }
  ')"
  if command -v flock >/dev/null 2>&1; then
    (
      exec 9>"$lockfile"
      if flock -w 30 9; then
        local tmpf
        tmpf="$(mktemp "${USE_CODEX_MANIFEST}.tmp.XXXXXX")"
        if jq --arg id "$id" --argjson rec "$round_record" '
          .entries |= map(
            if .id == $id then
              .mode_state = (.mode_state // {})
              | .mode_state.rounds = ((.mode_state.rounds // []) + [$rec])
            else . end
          )
        ' "$USE_CODEX_MANIFEST" > "$tmpf" 2>/dev/null \
           && jq -e . "$tmpf" >/dev/null 2>&1; then
          mv -f "$tmpf" "$USE_CODEX_MANIFEST"
        else
          rm -f "$tmpf"
        fi
      fi
    )
  fi

  # Status `done` per the documented manifest enum (not `reviewed`, which
  # isn't in the taxonomy). The orchestrator advances to converged /
  # cap_reached / blocked after reading the classifier's verdict.
  echo "DONE  $id (runtime=${elapsed}s findings=$(wc -c < "$findings" | tr -d ' ')B json=$findings_json)"
  "$SCRIPT_DIR_ABS/manifest-update.sh" entry "$USE_CODEX_MANIFEST" "$id" \
    status=done finished_at=now exit_code=0 \
    codex_thread_id="$thread_id" \
    last_findings_path="$findings" \
    last_findings_json="$findings_json" 2>/dev/null || true
}

CODEX_FLAGS_STR="$(printf '%s\n' "${CODEX_FLAGS[@]}")"
export CODEX_FLAGS_STR
export SCRIPT_DIR_ABS="$SCRIPT_DIR"
export USE_CODEX_MANIFEST="$MANIFEST"
export ROUND_NUM="$ROUND"
export ROUNDS_DIR JSON_FILTER FILTER_LEVEL DRY_RUN_LOCAL="$DRY_RUN" PROJECT_DIR
export -f run_one

# Running xargs in the background + `wait` lets bash dispatch TERM/INT
# traps immediately (otherwise they queue until xargs returns).
awk -F'\t' '$6 != "converged" && $6 != "blocked" && $6 != "cap_reached"' "$WORKLIST" \
  | tr '\n' '\0' \
  | xargs -0 -n 1 -P "$JOBS" bash -c 'run_one "$0"' &
_run_review_xargs_pid=$!
wait "$_run_review_xargs_pid"

echo "--- all jobs finished ---"

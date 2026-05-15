#!/usr/bin/env bash
# run-single.sh — single mission wrapper.
#
# Spawns ONE `codex exec` against a prompt file, pipes its --json stream
# through codex-json-filter.sh so the Monitor tool sees compact human-readable
# event lines, and writes the final agent message to an answer file.
#
# Pairing `--json` + `-o`: the JSONL stream is the live monitor surface; the
# `-o` file is the source of truth for "did codex produce output". When MCP
# servers are active, `--json` can drop events silently (upstream issue 15451)
# but `-o` still writes.
#
# Monitor contract: the JSONL filter emits one stdout line per codex event
# (line-buffered via grep --line-buffered), so the Monitor tool delivers each
# event as a notification. After the codex process exits, run-single emits a
# DONE/FAIL line and `--- all jobs finished ---`.
#
# Usage:
#   run-single.sh --prompt-file <file> [--cwd <dir>] [--out <file>] [--manifest <m.json> --entry-id <id>]
#   run-single.sh --dry-run --prompt-file <file>
#
# Inputs (env, alternative to flags):
#   PROMPT_FILE   prompt path
#   CWD           working dir for codex (default: cwd)
#   OUT           answer file path (default: <state>/single.last.md)
#   ORCHESTRATE_MANIFEST + ORCHESTRATE_ENTRY_ID for status writes
#   FILTER_LEVEL  passed to codex-json-filter.sh (minimal|normal|verbose)
#
# Exit codes: 0 codex exited 0 + answer non-empty,
#             1 codex exited non-zero,
#             2 answer file empty (after exit 0),
#             3 missing prompt file or invalid args.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=codex-flags.sh
. "$SCRIPT_DIR/codex-flags.sh"

PROMPT_FILE="${PROMPT_FILE:-}"
PROMPT_TEXT="${PROMPT_TEXT:-}"
CWD="${CWD:-$(pwd)}"
OUT="${OUT:-}"
JSONL="${JSONL:-}"
DRY_RUN=0
FILTER_LEVEL="${FILTER_LEVEL:-normal}"
ORCHESTRATE_MANIFEST="${ORCHESTRATE_MANIFEST:-}"
ORCHESTRATE_ENTRY_ID="${ORCHESTRATE_ENTRY_ID:-single}"
REUSE_WORKTREE=0
ORCHESTRATE_OUTPUT_SCHEMA="${ORCHESTRATE_OUTPUT_SCHEMA:-}"
# Rescue redispatch flags — set by --resume-thread / --resume-last from
# orchestrate-codex.mjs:2210-2219. Default unset = fresh `codex exec`.
RESUME_THREAD="${RESUME_THREAD:-}"
RESUME_LAST=0

usage() {
  cat >&2 <<'EOF'
run-single.sh — spawn one codex exec, stream JSONL through the filter.

Usage:
  run-single.sh --prompt-file <file> [--cwd <dir>] [--out <file>]
  run-single.sh --prompt <text> [--cwd <dir>] [--out <file>]
                [--manifest <m.json> --entry-id <id>]
                [--jsonl <path>]
                [--filter-level minimal|normal|verbose]
                [--dry-run]
EOF
  exit 3
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
    --prompt)      PROMPT_TEXT="$2"; shift 2 ;;
    --cwd)         CWD="$2"; shift 2 ;;
    --out)         OUT="$2"; shift 2 ;;
    --jsonl)       JSONL="$2"; shift 2 ;;
    --manifest)    ORCHESTRATE_MANIFEST="$2"; shift 2 ;;
    --entry-id)    ORCHESTRATE_ENTRY_ID="$2"; shift 2 ;;
    --filter-level) FILTER_LEVEL="$2"; shift 2 ;;
    --reuse-worktree) REUSE_WORKTREE=1; shift ;;
    # P1-11: dispatcher forwards `--output-schema <path>` (handleSingle in
    # orchestrate-codex.mjs records the schema path in the manifest entry
    # then re-forwards). The runner has no schema-validation responsibility
    # today; codex honours per-prompt schema instructions, and the manifest
    # carries the path for downstream audit/rescue. Accept-and-record so
    # the forward does not crash with `unknown arg`.
    --output-schema) ORCHESTRATE_OUTPUT_SCHEMA="$2"; shift 2 ;;
    # Rescue context-preserving resume. orchestrate-codex.mjs:2210-2218 picks one
    # of these per the manifest entry's recorded codex_thread_id (or falls back
    # to --resume-last when no thread_id was captured). Both forms turn the
    # `codex exec` invocation into `codex exec resume <id>` / `codex exec resume --last`.
    --resume-thread) RESUME_THREAD="$2"; shift 2 ;;
    --resume-last)   RESUME_LAST=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     usage ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      ;;
  esac
done

if [[ ! -d "$CWD" ]]; then
  echo "FATAL --cwd not a directory: $CWD" >&2
  exit 3
fi
if [[ -z "$PROMPT_FILE" && -n "$PROMPT_TEXT" ]]; then
  mkdir -p "$CWD/.orchestrate-codex"
  PROMPT_FILE="$CWD/.orchestrate-codex/${ORCHESTRATE_ENTRY_ID}.prompt.md"
  printf '%s\n' "$PROMPT_TEXT" > "$PROMPT_FILE"
fi
if [[ -z "$PROMPT_FILE" || ! -f "$PROMPT_FILE" ]]; then
  echo "FATAL --prompt-file or --prompt required; prompt file must exist: '$PROMPT_FILE'" >&2
  exit 3
fi
if [[ -z "$OUT" ]]; then
  OUT="$CWD/.orchestrate-codex/single.last.md"
fi
if [[ -z "$JSONL" ]]; then
  JSONL="$(dirname "$OUT")/${ORCHESTRATE_ENTRY_ID}.jsonl"
fi
mkdir -p "$(dirname "$OUT")" "$(dirname "$JSONL")"

if ! command -v codex >/dev/null 2>&1 && [[ "$DRY_RUN" != "1" ]]; then
  echo "FATAL codex CLI not found on PATH" >&2
  exit 3
fi

JSON_FILTER="$SCRIPT_DIR/codex-json-filter.sh"
if [[ ! -x "$JSON_FILTER" ]]; then
  echo "WARN $JSON_FILTER not executable; events will not be filtered." >&2
fi

# Build resume head + schema tail. With set -u, empty arrays must be expanded
# via ${arr[@]+"${arr[@]}"} to avoid "unbound variable" on macOS bash 3.2.
INVOKE_HEAD=()
if [[ -n "${RESUME_THREAD:-}" ]]; then
  INVOKE_HEAD=(resume "$RESUME_THREAD")
elif [[ "${RESUME_LAST:-0}" == "1" ]]; then
  INVOKE_HEAD=(resume --last)
fi
SCHEMA_TAIL=()
if [[ -n "${ORCHESTRATE_OUTPUT_SCHEMA:-}" ]]; then
  SCHEMA_TAIL=(--output-schema "$ORCHESTRATE_OUTPUT_SCHEMA")
fi

# ── Path resolution + manifest start row ─────────────────────
# Per the manifest contract every entry carries log_path / jsonl_path /
# answer_path. Single mode runs one entry: we resolve them up front and
# populate them on the same write that flips status to `running`.
LOG_PATH="$(dirname "$OUT")/${ORCHESTRATE_ENTRY_ID}.jsonl"
ERR_LOG="$(dirname "$OUT")/${ORCHESTRATE_ENTRY_ID}.err.log"
mkdir -p "$(dirname "$LOG_PATH")" "$(dirname "$ERR_LOG")"

if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
  "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
    status=running started_at=now attempts=+1 \
    log_path="$ERR_LOG" \
    jsonl_path="$LOG_PATH" \
    answer_path="$OUT" 2>/dev/null || true
fi

echo "START $ORCHESTRATE_ENTRY_ID"

# ── Spawn codex ────────────────────────────────────────────────

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] codex exec ${INVOKE_HEAD[*]:-} ${CODEX_FLAGS[*]} ${SCHEMA_TAIL[*]:-} --json -C $CWD -o $OUT < $PROMPT_FILE"
  printf 'dry-run answer for %s\n' "$ORCHESTRATE_ENTRY_ID" > "$OUT"
  printf '{"type":"turn.completed","dry_run":true}\n' > "$LOG_PATH"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
    # P0-1: dry-run discriminator — see run-fleet.sh for rationale.
    "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
      status=done finished_at=now exit_code=0 codex_thread_id=dry-run dry_run=true 2>/dev/null || true
  fi
  # Sentinel: codex-json-filter.sh translates this to `--- single done ---`
  # so live-watch operators (tail -F | filter) see a clear stop signal and
  # know to TaskStop the Monitor. Existing JSONL consumers ignore unknown
  # event types by default.
  printf '{"type":"orchestrate.done","entry_id":"%s","status":"done"}\n' "$ORCHESTRATE_ENTRY_ID" >> "$LOG_PATH"
  echo "DONE  $ORCHESTRATE_ENTRY_ID (dry-run)"
  echo "--- all jobs finished ---"
  exit 0
fi

# Stream codex's JSONL stdout through:
#   1. tee → jsonl file (LOG_PATH; raw event log on disk for rescue/audit)
#   2. codex-json-filter.sh (so Monitor sees compact lines)
# stderr (ERR_LOG, set above) holds auth errors, deprecation warnings,
# panics — kept separate so the JSONL pipeline stays parseable.
START_TS="$(date +%s)"
EXIT_CODE=0

set +e
if [[ -x "$JSON_FILTER" ]]; then
  # shellcheck disable=SC2002
  cat "$PROMPT_FILE" | codex exec ${INVOKE_HEAD[@]+"${INVOKE_HEAD[@]}"} "${CODEX_FLAGS[@]}" ${SCHEMA_TAIL[@]+"${SCHEMA_TAIL[@]}"} --json -C "$CWD" -o "$OUT" 2>"$ERR_LOG" \
    | tee "$LOG_PATH" \
    | CODEX_FILTER_LEVEL="$FILTER_LEVEL" "$JSON_FILTER"
  # Pipeline: cat | codex | tee | filter — codex is at index 1.
  EXIT_CODE="${PIPESTATUS[1]}"
else
  cat "$PROMPT_FILE" | codex exec ${INVOKE_HEAD[@]+"${INVOKE_HEAD[@]}"} "${CODEX_FLAGS[@]}" ${SCHEMA_TAIL[@]+"${SCHEMA_TAIL[@]}"} --json -C "$CWD" -o "$OUT" 2>"$ERR_LOG" \
    | tee "$LOG_PATH"
  EXIT_CODE="${PIPESTATUS[1]}"
fi
set -e

END_TS="$(date +%s)"
ELAPSED=$(( END_TS - START_TS ))

# ── Final state ────────────────────────────────────────────────
THREAD_ID=""
if [[ -f "$LOG_PATH" ]]; then
  THREAD_ID="$(jq -r '
    select(.type == "thread.started")
    | select((.parent_thread_id // .parent_id // null) == null)
    | select((.subagent // false) == false)
    | .thread_id // empty
  ' "$LOG_PATH" 2>/dev/null | head -n 1 || echo "")"
fi

# Sentinel writer: appends one orchestrate.done JSONL event to the live log
# AFTER the terminal manifest write. codex-json-filter.sh translates this to
# `--- single done (<id>: <status>) ---` so live-watch operators see a clear
# stop signal and know to TaskStop the Monitor. New event type — existing
# JSONL consumers ignore unknown `type` values by default.
emit_orchestrate_done() {
  local status="$1"
  if [[ -n "$LOG_PATH" ]]; then
    printf '{"type":"orchestrate.done","entry_id":"%s","status":"%s"}\n' \
      "$ORCHESTRATE_ENTRY_ID" "$status" >> "$LOG_PATH" 2>/dev/null || true
  fi
}

if [[ "$EXIT_CODE" -ne 0 ]]; then
  echo "FAIL  $ORCHESTRATE_ENTRY_ID (codex exit=$EXIT_CODE; runtime=${ELAPSED}s; see $ERR_LOG)"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
    "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
      status=failed finished_at=now exit_code="$EXIT_CODE" \
      last_error="codex exit $EXIT_CODE" \
      codex_thread_id="$THREAD_ID" 2>/dev/null || true
  fi
  emit_orchestrate_done "failed"
  echo "--- all jobs finished ---"
  exit 1
fi

if [[ ! -s "$OUT" ]]; then
  echo "FAIL  $ORCHESTRATE_ENTRY_ID (codex exit=0 but answer empty: $OUT)"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
    "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
      status=failed finished_at=now exit_code=0 last_error="empty answer" \
      codex_thread_id="$THREAD_ID" 2>/dev/null || true
  fi
  emit_orchestrate_done "failed"
  echo "--- all jobs finished ---"
  exit 2
fi

echo "DONE  $ORCHESTRATE_ENTRY_ID (runtime=${ELAPSED}s; answer=$(wc -c < "$OUT" | tr -d ' ')B)"
if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
  "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
    status=done finished_at=now exit_code=0 \
    codex_thread_id="$THREAD_ID" 2>/dev/null || true
fi
emit_orchestrate_done "done"

echo "--- all jobs finished ---"
exit 0

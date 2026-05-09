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

# ── Manifest start row ────────────────────────────────────────
if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
  "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
    status=running started_at=now attempts=+1 2>/dev/null || true
fi

echo "START $ORCHESTRATE_ENTRY_ID"

# ── Spawn codex ────────────────────────────────────────────────
LOG_PATH="$JSONL"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] codex exec ${CODEX_FLAGS[*]} --json -C $CWD -o $OUT < $PROMPT_FILE"
  printf 'dry-run answer for %s\n' "$ORCHESTRATE_ENTRY_ID" > "$OUT"
  printf '{"type":"turn.completed","dry_run":true}\n' > "$LOG_PATH"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
    "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
      status=done finished_at=now exit_code=0 codex_thread_id=dry-run 2>/dev/null || true
  fi
  echo "DONE  $ORCHESTRATE_ENTRY_ID (dry-run)"
  echo "--- all jobs finished ---"
  exit 0
fi

# Stream codex's JSONL stdout through:
#   1. tee → log file (so we have the raw event log on disk for rescue/audit)
#   2. codex-json-filter.sh (so Monitor sees compact lines)
# stderr goes to a separate log file (auth errors, rate limits, etc).
ERR_LOG="$(dirname "$OUT")/${ORCHESTRATE_ENTRY_ID}.err.log"
START_TS="$(date +%s)"
EXIT_CODE=0

set +e
if [[ -x "$JSON_FILTER" ]]; then
  # shellcheck disable=SC2002
  cat "$PROMPT_FILE" | codex exec "${CODEX_FLAGS[@]}" --json -C "$CWD" -o "$OUT" 2>"$ERR_LOG" \
    | tee "$LOG_PATH" \
    | CODEX_FILTER_LEVEL="$FILTER_LEVEL" "$JSON_FILTER"
  # PIPESTATUS[0] is codex's exit code.
  EXIT_CODE="${PIPESTATUS[1]}"
else
  cat "$PROMPT_FILE" | codex exec "${CODEX_FLAGS[@]}" --json -C "$CWD" -o "$OUT" 2>"$ERR_LOG" \
    | tee "$LOG_PATH"
  EXIT_CODE="${PIPESTATUS[1]}"
fi
set -e

END_TS="$(date +%s)"
ELAPSED=$(( END_TS - START_TS ))

# ── Final state ────────────────────────────────────────────────
THREAD_ID=""
if [[ -f "$LOG_PATH" ]]; then
  THREAD_ID="$(grep -m1 '"type":"thread.started"' "$LOG_PATH" 2>/dev/null \
                | jq -r '.thread_id // ""' 2>/dev/null || echo "")"
fi

if [[ "$EXIT_CODE" -ne 0 ]]; then
  echo "FAIL  $ORCHESTRATE_ENTRY_ID (codex exit=$EXIT_CODE; runtime=${ELAPSED}s; see $ERR_LOG)"
  if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
    "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
      status=failed finished_at=now exit_code="$EXIT_CODE" \
      last_error="codex exit $EXIT_CODE" \
      codex_thread_id="$THREAD_ID" 2>/dev/null || true
  fi
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
  echo "--- all jobs finished ---"
  exit 2
fi

echo "DONE  $ORCHESTRATE_ENTRY_ID (runtime=${ELAPSED}s; answer=$(wc -c < "$OUT" | tr -d ' ')B)"
if [[ -n "$ORCHESTRATE_MANIFEST" && -f "$ORCHESTRATE_MANIFEST" ]]; then
  "$SCRIPT_DIR/manifest-update.sh" entry "$ORCHESTRATE_MANIFEST" "$ORCHESTRATE_ENTRY_ID" \
    status=done finished_at=now exit_code=0 \
    codex_thread_id="$THREAD_ID" 2>/dev/null || true
fi

echo "--- all jobs finished ---"
exit 0

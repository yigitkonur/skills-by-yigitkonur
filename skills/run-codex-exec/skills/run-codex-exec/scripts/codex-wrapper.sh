#!/usr/bin/env bash
# codex-wrapper.sh — run `codex exec` inside a git worktree, auto-commit on
# success, and write a post-verify status line the monitor can spot.
#
# Usage: codex-wrapper.sh <worktree-name> <plan-slug> "<task prompt>"
#
# Environment variables:
#   PROJECT_DIR       — repo root (default: cwd)
#   MONITOR_ROOT      — log directory (default: /tmp/codex-monitor)
#   WORKTREE_DIR_NAME — worktree subdir name under PROJECT_DIR (default: .worktrees)
#   COMMIT_LEVEL      — commit message verbosity: 1=minimal 2=standard 3=verbose (default: 3)
#   CODEX_MODEL       — codex model (default: gpt-5.4)
#   CODEX_REASONING   — model_reasoning_effort: low|medium|high|xhigh (default: high)
#   POST_VERIFY_CMD   — shell command for post-commit verification (default: npx tsc --noEmit)
#   POST_VERIFY_TESTS — shell command for running tests (default: npx vitest run)
set -uo pipefail

WORKTREE_NAME="${1:?worktree name required (arg 1)}"
PLAN_SLUG="${2:?plan slug required (arg 2)}"
TASK="${3:?task prompt required (arg 3)}"

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
MONITOR_ROOT="${MONITOR_ROOT:-/tmp/codex-monitor}"
WT_DIR_NAME="${WORKTREE_DIR_NAME:-.worktrees}"
WORKTREE_DIR="$PROJECT_DIR/$WT_DIR_NAME/$WORKTREE_NAME"
LOG_DIR="$MONITOR_ROOT/logs"
COMMIT_LEVEL="${COMMIT_LEVEL:-3}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_REASONING="${CODEX_REASONING:-high}"

# ── Smart post-verify defaults ─────────────────────────────────
# If POST_VERIFY_CMD / POST_VERIFY_TESTS aren't explicitly set, auto-detect
# based on what the worktree actually contains. Running `npx tsc --noEmit`
# in a non-TS project silently reports "0 errors" — a false-positive green
# signal. Similarly vitest + no config ⇒ no tests found but exit 0.
if [[ -z "${POST_VERIFY_CMD:-}" ]]; then
  if [[ -f "$WORKTREE_DIR/tsconfig.json" ]]; then
    POST_VERIFY_CMD="npx tsc --noEmit"
  elif [[ -f "$WORKTREE_DIR/pyproject.toml" || -f "$WORKTREE_DIR/mypy.ini" ]]; then
    POST_VERIFY_CMD="python3 -m mypy --strict . --no-error-summary"
  elif [[ -f "$WORKTREE_DIR/Cargo.toml" ]]; then
    POST_VERIFY_CMD="cargo check --quiet"
  elif [[ -f "$WORKTREE_DIR/go.mod" ]]; then
    POST_VERIFY_CMD="go vet ./..."
  else
    POST_VERIFY_CMD="echo 'post-verify: no known type-check config detected (override via POST_VERIFY_CMD)'"
  fi
fi
if [[ -z "${POST_VERIFY_TESTS:-}" ]]; then
  if [[ -f "$WORKTREE_DIR/vitest.config.ts" || -f "$WORKTREE_DIR/vitest.config.js" ]]; then
    POST_VERIFY_TESTS="npx vitest run"
  elif [[ -f "$WORKTREE_DIR/jest.config.js" || -f "$WORKTREE_DIR/jest.config.ts" ]]; then
    POST_VERIFY_TESTS="npx jest --silent"
  elif [[ -f "$WORKTREE_DIR/pytest.ini" || -f "$WORKTREE_DIR/pyproject.toml" ]] && \
       grep -q "pytest\|tool.pytest" "$WORKTREE_DIR/pyproject.toml" 2>/dev/null; then
    POST_VERIFY_TESTS="python3 -m pytest -q"
  elif [[ -f "$WORKTREE_DIR/Cargo.toml" ]]; then
    POST_VERIFY_TESTS="cargo test --quiet"
  elif [[ -f "$WORKTREE_DIR/go.mod" ]]; then
    POST_VERIFY_TESTS="go test ./..."
  else
    POST_VERIFY_TESTS="echo 'post-verify: no known test runner detected (override via POST_VERIFY_TESTS)'"
  fi
fi

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${WORKTREE_NAME}.log"

if [[ ! -d "$WORKTREE_DIR" ]]; then
  echo "[wrapper $PLAN_SLUG] ERROR: worktree $WORKTREE_DIR does not exist. Run setup-worktree.sh first." >&2
  exit 2
fi

cd "$WORKTREE_DIR"
BRANCH=$(git branch --show-current)
PID=$$
START=$(date +%s)
echo "[wrapper $PLAN_SLUG] $(date -u +%H:%M:%SZ) pid=$PID branch=$BRANCH starting" | tee -a "$LOG_FILE"

# ── Run codex exec ─────────────────────────────────────────────
OUTPUT_FILE=$(mktemp)
codex exec \
  --full-auto \
  --model "$CODEX_MODEL" \
  --config "model_reasoning_effort=$CODEX_REASONING" \
  "$TASK" 2>&1 | tee "$OUTPUT_FILE" >> "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}
END=$(date +%s)
ELAPSED=$(( END - START ))
echo "[wrapper $PLAN_SLUG] exit=$EXIT_CODE runtime=${ELAPSED}s" | tee -a "$LOG_FILE"

# ── Skip commit if codex made no changes ──────────────────────
if git diff --quiet && git diff --cached --quiet; then
  echo "[wrapper $PLAN_SLUG] no changes detected, skipping commit" | tee -a "$LOG_FILE"
  rm -f "$OUTPUT_FILE"
  # Post-verify still runs so the monitor has a signal (no-commit ≠ broken repo)
  V_OUT=$($POST_VERIFY_CMD 2>&1)
  V_EXIT=$?
  ERR_COUNT=$(printf '%s' "$V_OUT" | grep -cE "error TS|: error:|^error\[|^ERROR" || echo "0")
  [[ "$V_EXIT" -ne 0 && "$ERR_COUNT" == "0" ]] && ERR_COUNT="?"
  echo "[wrapper $PLAN_SLUG] post-verify verify_errors=$ERR_COUNT tests='skipped (no changes)'" | tee -a "$LOG_FILE"
  exit "$EXIT_CODE"
fi

git add -A
SUMMARY=$(echo "$TASK" | head -1 | cut -c1-60)

# ── Commit message by COMMIT_LEVEL ────────────────────────────
case "$COMMIT_LEVEL" in
  1)
      git commit -m "agent($PLAN_SLUG): $SUMMARY [auto]"
      ;;
  2)
      STATS=$(git diff --cached --stat | tail -1)
      git commit -m "agent($PLAN_SLUG): $SUMMARY

Stats   : $STATS
Runtime : ${ELAPSED}s
Exit    : $EXIT_CODE
Branch  : $BRANCH
PID     : $PID"
      ;;
  3|*)
      STATS=$(git diff --cached --stat)
      FILES=$(git diff --cached --name-only | head -10 | tr '\n' ',' | sed 's/,$//')
      TAIL=$(tail -20 "$OUTPUT_FILE" 2>/dev/null | sed 's/^/  /')
      git commit -m "agent($PLAN_SLUG): $SUMMARY

Branch    : $BRANCH
Runtime   : ${ELAPSED}s
Exit      : $EXIT_CODE
PID       : $PID
Timestamp : $(date -u +%Y-%m-%dT%H:%M:%SZ)
Files     : $FILES

--- diff stats ---
$STATS

--- agent output (last 20 lines) ---
$TAIL

Source    : codex exec ($CODEX_MODEL $CODEX_REASONING reasoning)"
      ;;
esac

rm -f "$OUTPUT_FILE"
echo "[wrapper $PLAN_SLUG] committed" | tee -a "$LOG_FILE"

# ── Post-verify — report-only; does not block commit ──────────
# Run the auto-detected or user-supplied type-check + test commands.
# The count of "error" lines in the type-check output is our green/red signal.
# Non-zero exit from the type-check itself also counts as failure.
VERIFY_OUTPUT=$($POST_VERIFY_CMD 2>&1)
VERIFY_EXIT=$?
# Match both TypeScript-style "error TS" and mypy-style " error:" + cargo "error" + generic ERROR
ERR_COUNT=$(printf '%s' "$VERIFY_OUTPUT" | grep -cE "error TS|: error:|^error\[|^ERROR" || echo "0")
if [[ "$VERIFY_EXIT" -ne 0 && "$ERR_COUNT" == "0" ]]; then
  # Type-checker exited non-zero without matched error lines — still a failure
  ERR_COUNT="?"
fi
TEST_TAIL="skipped"
if [[ "$ERR_COUNT" == "0" ]]; then
  TEST_TAIL=$($POST_VERIFY_TESTS 2>&1 | grep -E "Test Files|Tests |passed|failed|ok |FAIL" | tail -1 | tr -d '\n')
  [[ -z "$TEST_TAIL" ]] && TEST_TAIL="no-summary-line"
fi
# Use label `verify_errors` (not `tsc_errors`) so the field reflects whichever
# type-check actually ran. Monitor grep pattern should match either for backward compat.
echo "[wrapper $PLAN_SLUG] post-verify verify_errors=$ERR_COUNT (cmd='$POST_VERIFY_CMD') tests='$TEST_TAIL' (cmd='$POST_VERIFY_TESTS')" | tee -a "$LOG_FILE"

exit "$EXIT_CODE"

#!/usr/bin/env bash
# codex-monitor.sh — unified observability loop for parallel `codex exec` agents
# in git worktrees. Emits one stdout line per tick (so the Claude Monitor tool
# delivers each as a notification) AND fires a native macOS notification via
# osascript. No external dependencies beyond bash + git + optional osascript.
#
# Environment variables:
#   PROJECT_DIR                  — repo root (default: cwd)
#   MONITOR_ROOT                 — where logs + baseline.sha live (default: /tmp/codex-monitor)
#   CODEX_MONITOR_INTERVAL       — seconds between ticks (default: 60)
#   CONSEC_WARN_AT               — ticks with identical note before flagging `streak` (default: 3)
#   NOTIFY_TITLE                 — osascript title (default: "Codex Monitor")
#   CODEX_MONITOR_NO_OSASCRIPT   — set to 1 to disable native notifications (default: off)
#   WORKTREE_DIR_NAME            — worktree subdir name relative to PROJECT_DIR (default: .worktrees)
set -uo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
MONITOR_ROOT="${MONITOR_ROOT:-/tmp/codex-monitor}"
BASELINE_FILE="${MONITOR_ROOT}/baseline.sha"
LOG_FILE="${MONITOR_ROOT}/logs/monitor.log"
INTERVAL="${CODEX_MONITOR_INTERVAL:-60}"
CONSEC_WARN_AT="${CONSEC_WARN_AT:-3}"
NOTIFY_TITLE="${NOTIFY_TITLE:-Codex Monitor}"
NO_OSASCRIPT="${CODEX_MONITOR_NO_OSASCRIPT:-}"
WT_DIR_NAME="${WORKTREE_DIR_NAME:-.worktrees}"

mkdir -p "$(dirname "$LOG_FILE")"

# ── Baseline: pin current HEAD on first run. Delete baseline.sha to reset. ──
if [[ ! -f "$BASELINE_FILE" ]]; then
  (cd "$PROJECT_DIR" && git rev-parse HEAD) > "$BASELINE_FILE"
fi
BASELINE="$(cat "$BASELINE_FILE")"

trap 'echo "[shutdown $(date -u +%H:%M:%SZ)] monitor stopping"; exit 0' TERM INT

# ── Helpers ───────────────────────────────────────────────────
notify() {
  [[ -n "$NO_OSASCRIPT" ]] && return 0
  command -v osascript >/dev/null 2>&1 || return 0
  local body="$1" subtitle="${2:-}"
  body="${body//\"/\\\"}"
  subtitle="${subtitle//\"/\\\"}"
  osascript -e \
    "display notification \"$body\" with title \"$NOTIFY_TITLE\" subtitle \"$subtitle\"" \
    2>/dev/null || true
}

project_file_count() {
  find "$PROJECT_DIR" \
    -not -path '*/.git/*' \
    -not -path "*/$WT_DIR_NAME/*" \
    -not -path '*/node_modules/*' \
    -not -path '*/.next/*' \
    -not -path '*/dist/*' \
    -not -path '*/build/*' \
    -type f 2>/dev/null \
    | wc -l | tr -d ' '
}

worktree_signature() {
  local sig=""
  for wt in "$PROJECT_DIR/$WT_DIR_NAME"/*/; do
    [[ -d "$wt" ]] || continue
    local branch ahead dirty
    branch=$(cd "$wt" && git branch --show-current 2>/dev/null)
    ahead=$(cd "$wt" && git rev-list --count "$BASELINE..HEAD" 2>/dev/null || echo "0")
    dirty=$(cd "$wt" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    sig="${sig}${branch}:${ahead}:${dirty};"
  done
  printf '%s' "$sig" | md5 -q 2>/dev/null || printf 'empty'
}

worktree_summary() {
  local out=()
  for wt in "$PROJECT_DIR/$WT_DIR_NAME"/*/; do
    [[ -d "$wt" ]] || continue
    local name ahead dirty
    name=$(basename "$wt")
    ahead=$(cd "$wt" && git rev-list --count "$BASELINE..HEAD" 2>/dev/null || echo "?")
    dirty=$(cd "$wt" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    out+=("${name}=${ahead}c/${dirty}d")
  done
  echo "${out[*]}"
}

# ── State ─────────────────────────────────────────────────────
prev_commits=0
prev_size=0
prev_note=""
prev_worktree_sig=""
consecutive=0

cd "$PROJECT_DIR"
echo "[startup $(date -u +%H:%M:%SZ)] baseline=$BASELINE interval=${INTERVAL}s osascript=${NO_OSASCRIPT:-on}"

# ── Loop ──────────────────────────────────────────────────────
while true; do
  ts=$(date -u +%H:%M:%SZ)

  # Process counts — these are the two signals that matter.
  codex_procs=$(pgrep -f "codex exec" 2>/dev/null | wc -l | tr -d ' ')
  wrapper_procs=$(pgrep -f "codex-wrapper" 2>/dev/null | wc -l | tr -d ' ')

  # Git state on main
  main_commits=$(git log --oneline "$BASELINE..HEAD" 2>/dev/null | wc -l | tr -d ' ')
  main_dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

  # Total commits across all branches reachable from baseline (catches in-flight
  # agent commits that haven't been merged yet)
  all_commits=$(git log --all --oneline "$BASELINE.." 2>/dev/null | wc -l | tr -d ' ')

  wt_sig=$(worktree_signature)
  size=$(project_file_count)

  # ── Rule engine ────────────────────────────────────────────
  flags=()
  note=""

  # Rule 1: derive the top-level narrative
  if [[ "$codex_procs" -eq 0 && "$all_commits" -eq "$prev_commits" ]]; then
    note="idle"
  elif [[ "$codex_procs" -gt 0 && "$all_commits" -eq "$prev_commits" ]]; then
    note="working/no-commit-yet"
  elif [[ "$all_commits" -gt "$prev_commits" ]]; then
    diff=$(( all_commits - prev_commits ))
    note="+${diff}commit"
  fi

  # Rule 2: identical state for N consecutive ticks ⇒ system may be stuck
  if [[ "$note" == "$prev_note" && -n "$note" ]]; then
    consecutive=$(( consecutive + 1 ))
  else
    consecutive=1
    prev_note="$note"
  fi
  [[ "$consecutive" -ge "$CONSEC_WARN_AT" ]] && flags+=("streak:${consecutive}x")

  # Rule 3: worktree contents changed but no new commit landed
  if [[ "$wt_sig" != "$prev_worktree_sig" && "$all_commits" -eq "$prev_commits" ]]; then
    flags+=("silent-edit")
  fi

  # Rule 4: main branch is dirty — parallel work shouldn't touch main
  [[ "$main_dirty" -gt 0 ]] && flags+=("main-dirty:${main_dirty}")

  # Rule 5: commits advanced with no codex procs alive ⇒ something finished
  if [[ "$codex_procs" -eq 0 && "$all_commits" -gt "$prev_commits" ]]; then
    flags+=("agent-done-committed")
  fi

  # Rule 6: file count changed without a commit ⇒ generated/cache files bypassing git
  if [[ "$size" -ne "$prev_size" && "$all_commits" -eq "$prev_commits" ]]; then
    delta=$(( size - prev_size ))
    if [[ "$delta" -gt 0 ]]; then
      flags+=("size-drift:+${delta}files")
    else
      flags+=("size-drift:${delta}files")
    fi
  fi

  note_str=""
  [[ -n "$note" ]] && note_str=" ($note)"
  flag_str=""
  if [[ ${#flags[@]} -gt 0 ]]; then
    flag_str=" [$(IFS=', '; echo "${flags[*]}")]"
  fi

  summary=$(worktree_summary)
  procs_str="codex:$codex_procs/wrap:$wrapper_procs"
  commits_str="main:$main_commits/all:$all_commits"
  line="$ts procs=$procs_str commits=$commits_str${note_str}${flag_str} :: $summary"
  echo "$line"
  echo "$line" >> "$LOG_FILE"
  notify "procs=$procs_str  commits=$commits_str${note_str}${flag_str}" "$ts"

  prev_commits=$all_commits
  prev_size=$size
  prev_worktree_sig=$wt_sig

  sleep "$INTERVAL"
done

#!/usr/bin/env bash
# codex-monitor.sh — fleet-level rule-engine ticker. Emits one stdout line
# per tick (so Claude Code's Monitor tool delivers each as a notification).
# Manifest-aware: counts queued/running/done/failed across entries[] and
# folds them into the tick line.
#
# This is a long-running process. Arm it BEFORE the fleet runner so the first
# wave of events is captured. Unlike codex-json-filter.sh (which transforms
# a single codex stream), codex-monitor watches the FLEET state.
#
# Inputs (env):
#   PROJECT_DIR                  repo root (default: cwd)
#   ORCHESTRATE_MANIFEST         manifest.json path (recommended; without it
#                                the monitor only reports git/process counts)
#   MONITOR_ROOT                 logs dir (default: <state-dir>/logs)
#   CODEX_MONITOR_INTERVAL       seconds between ticks (default: 30)
#   CONSEC_WARN_AT               ticks with identical note before flagging
#                                `streak` (default: 3)
#   NOTIFY_TITLE                 osascript title (default: "Orchestrate Codex")
#   CODEX_MONITOR_NO_OSASCRIPT   1 to disable native macOS notifications
#   WORKTREE_DIR_NAME            in-repo worktree subdir (legacy; default
#                                .worktrees). Sibling worktrees are detected
#                                via `git worktree list --porcelain`.
#   ORCHESTRATE_QUIET_AFTER      ticks of `procs=0 && all-terminal` before
#                                emitting `--- fleet quiet ---` and exiting
#                                (default: 0 = governed by AUTOSTOP_GRACE_SEC
#                                only; the QUIET_AFTER knob remains as an
#                                explicit ticker override).
#   AUTOSTOP_GRACE_SEC           seconds the manifest must stay terminal AND
#                                no codex procs must be alive before the
#                                monitor emits `--- all jobs finished ---`
#                                and exits 0 (default: 60). Set to 0 to
#                                disable auto-stop entirely.
#
# Tick-line shape (stable; do not change without updating codex-monitor.md
# AND references/universal/monitor-contract.md):
#
#   <UTC-iso-z> procs=codex:N commits=main:M/all:A manifest=[<summary>]\
#       (<note>) [<flag>,<flag>...] :: <wt-summary>
#
# Where <summary> is `queued=N running=N done=N failed=N skipped=N reviewed=N total=N`
# (or the literal `manifest=none` when no manifest is configured), <note> is
# one of `idle | working/no-commit-yet | +Ncommit`, and the optional flag
# bracket lists any of `streak:Nx | agent-done-committed | manifest-changed
# | fleet-quiet`.
#
# Coverage rule (Monitor contract): every tick emits exactly one line, line-
# buffered so the Monitor doesn't sit silent. Terminal events ALWAYS
# include a transition flag (e.g. `agent-done-committed` / `fleet-quiet`)
# so the watcher can distinguish "still working" from "all done". When the
# manifest reaches a fully terminal state and stays there for
# AUTOSTOP_GRACE_SEC seconds, the monitor self-terminates with the sentinel
# line `--- all jobs finished ---` and exits 0.

set -uo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"
ORCHESTRATE_MANIFEST="${ORCHESTRATE_MANIFEST:-}"
MONITOR_ROOT="${MONITOR_ROOT:-/tmp/run-codex-1-monitor}"
INTERVAL="${CODEX_MONITOR_INTERVAL:-30}"
CONSEC_WARN_AT="${CONSEC_WARN_AT:-3}"
NOTIFY_TITLE="${NOTIFY_TITLE:-Orchestrate Codex}"
NO_OSASCRIPT="${CODEX_MONITOR_NO_OSASCRIPT:-}"
WT_DIR_NAME="${WORKTREE_DIR_NAME:-.worktrees}"
QUIET_AFTER="${ORCHESTRATE_QUIET_AFTER:-0}"
AUTOSTOP_GRACE_SEC="${AUTOSTOP_GRACE_SEC:-60}"

mkdir -p "$MONITOR_ROOT"
LOG_FILE="$MONITOR_ROOT/monitor.log"

# ── Baseline pinning ─────────────────────────────────────────
BASELINE_FILE="$MONITOR_ROOT/baseline.sha"
if [[ -d "$PROJECT_DIR/.git" ]]; then
  if [[ ! -f "$BASELINE_FILE" ]]; then
    (cd "$PROJECT_DIR" && git rev-parse HEAD 2>/dev/null) > "$BASELINE_FILE" || true
  fi
fi
BASELINE=""
[[ -f "$BASELINE_FILE" ]] && BASELINE="$(cat "$BASELINE_FILE")"

trap 'echo "[shutdown $(date -u +%H:%M:%SZ)] monitor stopping"; exit 0' TERM INT

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

# ── Manifest summary helper ──────────────────────────────────
# Returns "queued=N running=N done=N failed=N skipped=N reviewed=N total=N"
manifest_summary() {
  if [[ -z "$ORCHESTRATE_MANIFEST" || ! -f "$ORCHESTRATE_MANIFEST" ]]; then
    printf 'manifest=none'
    return 0
  fi
  jq -r '
    .entries // []
    | reduce .[] as $e (
        { queued:0, running:0, done:0, failed:0, skipped:0, reviewed:0, rescued:0, total:0 };
        .[$e.status // "queued"] = ((.[$e.status // "queued"] // 0) + 1)
        | .total += 1
      )
    | "queued=\(.queued // 0) running=\(.running // 0) done=\(.done // 0) failed=\(.failed // 0) skipped=\(.skipped // 0) reviewed=\(.reviewed // 0) total=\(.total)"
  ' "$ORCHESTRATE_MANIFEST" 2>/dev/null || printf 'manifest=parse-error'
}

# Returns "all-terminal" if every entry is in a terminal status, else "in-flight".
manifest_terminal_state() {
  if [[ -z "$ORCHESTRATE_MANIFEST" || ! -f "$ORCHESTRATE_MANIFEST" ]]; then
    printf 'no-manifest'
    return 0
  fi
  local non_terminal
  non_terminal="$(jq -r '
    [.entries // []
     | .[]
     | select((.status // "queued") == "queued" or (.status // "queued") == "running")]
    | length
  ' "$ORCHESTRATE_MANIFEST" 2>/dev/null || echo "?")"
  # Treat an empty entries[] (total=0) as in-flight: an empty manifest is a
  # not-yet-seeded run, not a finished run. The dispatcher always seeds at
  # least one entry before spawning the runner.
  local total
  total="$(jq -r '(.entries // []) | length' "$ORCHESTRATE_MANIFEST" 2>/dev/null || echo "0")"
  if [[ "$total" == "0" ]]; then
    printf 'in-flight'
  elif [[ "$non_terminal" == "0" ]]; then
    printf 'all-terminal'
  else
    printf 'in-flight'
  fi
}

# ── Worktree summary helper ──────────────────────────────────
# Authoritative source: `git worktree list --porcelain`. We parse it for the
# main worktree's siblings so the count is right regardless of whether the
# worktrees live under <project>/.worktrees/ or ../<project>-wt-* (the two
# layouts the skill ships). Falls back to the legacy in-repo glob only when
# git refuses (non-repo / detached / other).
worktree_summary() {
  local out=()
  local wt_root_in="$PROJECT_DIR/$WT_DIR_NAME"

  # Primary: ask git. Each worktree's "worktree <path>" line gives an absolute
  # path; the first is always the main repo, which we drop.
  local porcelain=""
  if command -v git >/dev/null 2>&1 && [[ -d "$PROJECT_DIR/.git" ]]; then
    porcelain="$(git -C "$PROJECT_DIR" worktree list --porcelain 2>/dev/null || true)"
  fi
  if [[ -n "$porcelain" ]]; then
    local main_wt="$PROJECT_DIR"
    main_wt="$(cd "$PROJECT_DIR" 2>/dev/null && pwd -P || echo "$PROJECT_DIR")"
    while IFS= read -r path; do
      [[ -z "$path" ]] && continue
      [[ -d "$path" ]] || continue
      # Skip the main worktree (the project root itself).
      local resolved
      resolved="$(cd "$path" 2>/dev/null && pwd -P || echo "$path")"
      [[ "$resolved" == "$main_wt" ]] && continue
      local name ahead dirty
      name="$(basename "$path")"
      if [[ -n "$BASELINE" ]]; then
        ahead="$(git -C "$path" rev-list --count "$BASELINE..HEAD" 2>/dev/null || echo "?")"
      else
        ahead="?"
      fi
      dirty="$(git -C "$path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
      out+=("$name=${ahead}c/${dirty}d")
    done < <(printf '%s\n' "$porcelain" | awk '/^worktree /{print substr($0,10)}')
  fi

  # Fallback: legacy in-repo glob. Only used when git couldn't help (no .git,
  # no `git` binary, etc.).
  if [[ ${#out[@]} -eq 0 && -d "$wt_root_in" ]]; then
    for wt in "$wt_root_in"/*/; do
      [[ -d "$wt" ]] || continue
      local name ahead dirty
      name="$(basename "$wt")"
      if [[ -n "$BASELINE" ]]; then
        ahead="$(cd "$wt" && git rev-list --count "$BASELINE..HEAD" 2>/dev/null || echo "?")"
      else
        ahead="?"
      fi
      dirty="$(cd "$wt" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
      out+=("$name=${ahead}c/${dirty}d")
    done
  fi

  if [[ ${#out[@]} -eq 0 ]]; then
    printf 'wts=0'
  else
    printf '%s' "${out[*]}"
  fi
}

# ── State for the rule engine ────────────────────────────────
prev_commits=0
prev_summary=""
prev_note=""
consecutive=0
quiet_streak=0
terminal_since_epoch=0   # epoch seconds when the manifest first went terminal

cd "$PROJECT_DIR" || { echo "[fatal] cannot cd to $PROJECT_DIR" >&2; exit 1; }
echo "[startup $(date -u +%H:%M:%SZ)] manifest=${ORCHESTRATE_MANIFEST:-none} interval=${INTERVAL}s baseline=${BASELINE:0:8} autostop_grace=${AUTOSTOP_GRACE_SEC}s"

while true; do
  ts="$(date -u +%H:%M:%SZ)"
  now_epoch="$(date +%s)"

  codex_procs="$(pgrep -f 'codex exec' 2>/dev/null | wc -l | tr -d ' ')"

  # Git counts are valid only if the project is a git repo with a baseline.
  main_commits=0
  all_commits=0
  if [[ -n "$BASELINE" ]]; then
    main_commits="$(git log --oneline "$BASELINE..HEAD" 2>/dev/null | wc -l | tr -d ' ')"
    all_commits="$(git log --all --oneline "$BASELINE.." 2>/dev/null | wc -l | tr -d ' ')"
  fi

  m_summary="$(manifest_summary)"
  m_state="$(manifest_terminal_state)"

  # ── Rule engine ─────────────────────────────────────────────
  flags=()
  note=""

  if [[ "$codex_procs" -eq 0 && "$all_commits" -eq "$prev_commits" ]]; then
    note="idle"
  elif [[ "$codex_procs" -gt 0 && "$all_commits" -eq "$prev_commits" ]]; then
    note="working/no-commit-yet"
  elif [[ "$all_commits" -gt "$prev_commits" ]]; then
    diff=$(( all_commits - prev_commits ))
    note="+${diff}commit"
  fi

  if [[ "$note" == "$prev_note" && -n "$note" ]]; then
    consecutive=$(( consecutive + 1 ))
  else
    consecutive=1
    prev_note="$note"
  fi
  [[ "$consecutive" -ge "$CONSEC_WARN_AT" ]] && flags+=("streak:${consecutive}x")

  if [[ "$codex_procs" -eq 0 && "$all_commits" -gt "$prev_commits" ]]; then
    flags+=("agent-done-committed")
  fi

  if [[ "$m_summary" != "$prev_summary" && "$prev_summary" != "" ]]; then
    flags+=("manifest-changed")
  fi

  # Terminal-fleet flag — only if we have a manifest
  if [[ "$m_state" == "all-terminal" && "$codex_procs" -eq 0 ]]; then
    flags+=("fleet-quiet")
    quiet_streak=$(( quiet_streak + 1 ))
    [[ "$terminal_since_epoch" -eq 0 ]] && terminal_since_epoch="$now_epoch"
  else
    quiet_streak=0
    terminal_since_epoch=0
  fi

  note_str=""
  [[ -n "$note" ]] && note_str=" ($note)"
  flag_str=""
  if [[ ${#flags[@]} -gt 0 ]]; then
    flag_str=" [$(IFS=, ; echo "${flags[*]}")]"
  fi

  wt_str="$(worktree_summary)"
  line="$ts procs=codex:$codex_procs commits=main:$main_commits/all:$all_commits manifest=[$m_summary]${note_str}${flag_str} :: $wt_str"
  echo "$line"
  echo "$line" >> "$LOG_FILE"
  notify "procs=$codex_procs $m_summary${note_str}${flag_str}" "$ts"

  prev_commits="$all_commits"
  prev_summary="$m_summary"

  # ── Auto-stop ───────────────────────────────────────────────
  # 1. Default sentinel: manifest fully terminal AND no codex procs AND the
  #    state has held for AUTOSTOP_GRACE_SEC seconds. Emits the doc'd
  #    `--- all jobs finished ---` line and exits 0. This is the universal
  #    self-termination — the operator never has to remember TaskStop on a
  #    fully-finished fleet.
  # 2. Legacy sentinel: ORCHESTRATE_QUIET_AFTER>0 fires `--- fleet quiet ---`
  #    after that many consecutive quiet ticks regardless of grace seconds.
  #    Kept for backward compatibility with callers that already key off it.
  if [[ "$AUTOSTOP_GRACE_SEC" -gt 0 \
        && "$m_state" == "all-terminal" \
        && "$codex_procs" -eq 0 \
        && "$terminal_since_epoch" -gt 0 \
        && $(( now_epoch - terminal_since_epoch )) -ge "$AUTOSTOP_GRACE_SEC" ]]; then
    echo "--- all jobs finished ---"
    echo "--- all jobs finished ---" >> "$LOG_FILE"
    exit 0
  fi
  if [[ "$QUIET_AFTER" -gt 0 && "$quiet_streak" -ge "$QUIET_AFTER" ]]; then
    echo "--- fleet quiet ---"
    echo "--- fleet quiet ---" >> "$LOG_FILE"
    exit 0
  fi

  sleep "$INTERVAL"
done

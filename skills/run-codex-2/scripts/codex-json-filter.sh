#!/usr/bin/env bash
# codex-json-filter.sh — read JSONL from `codex exec --json` on stdin, emit
# ONE compact human-readable line per interesting event.
#
# Designed for Claude Code's Monitor tool: each stdout line becomes one
# notification. Line-buffered: `read -r` reads one line at a time, jq parses
# one event at a time, and stdout is flushed line-by-line (printf is line-
# buffered when stdout is a pipe to another program that reads line-by-line,
# which is the Monitor case).
#
# Implementation: pure bash `while read` loop with `jq` invoked per line.
# (Earlier doc revisions referred to an awk + fflush impl; that was never
# accurate.) The bash impl flushes naturally because `printf` writes one line
# at a time and there is no intermediate stdio buffer between us and the pipe.
#
# Usage:
#   codex exec --dangerously-bypass-approvals-and-sandbox --json <args> "<prompt>" 2>&1 \
#     | codex-json-filter.sh [--level <minimal|normal|verbose>]
#
# Inputs:
#   --level <name>       same as CODEX_FILTER_LEVEL; CLI flag wins over env.
#   CODEX_FILTER_LEVEL   minimal | normal (default) | verbose
#                        Tags emitted at each level (strict subset relation
#                        minimal ⊂ normal ⊂ verbose):
#                          minimal: [START] [CMD>] [CMD✓] [CMD✗] [SAID]
#                                   [TURN<] [ERR]
#                          normal : minimal + [TURN>] [THINK] [FILE] [ITEM>]
#                                   [ITEM<]
#                          verbose: normal  + [?] (unknown event types) and
#                                   command-output tail on [CMD✓]
#                        ([ITEM>] is item.started, [ITEM<] is item.completed
#                        for item types we don't have a dedicated tag for.)
#   CODEX_FILTER_MAXLEN  max chars per emitted line (default: 200)
#
# Exit codes:
#   0  EOF on stdin (codex finished) OR downstream closed pipe (SIGPIPE).
#   1  Internal error (rare).
#   2  Bad CLI flag.
#
# SIGPIPE: when a downstream consumer (e.g. `head`, the Monitor) closes the
# pipe, the filter exits 0. The PIPE trap converts the signal into a clean
# `exit 0`; every emit is wrapped so the loop also exits cleanly if `printf`
# returns EPIPE before the signal is delivered.
#
# Event schema (codex-cli 0.130.x; verified live):
#   thread.started    { type, thread_id }
#   turn.started      { type }
#   item.started      { type, item: { id, type, command?, status, aggregated_output, exit_code } }
#   item.completed    { type, item: { id, type, text|command|aggregated_output|message, exit_code, status, phase? } }
#   turn.completed    { type, usage: { input_tokens, cached_input_tokens, output_tokens } }
#   error             { type, message } or { error: { message } }
#
# Known item.type values: command_execution, reasoning, agent_message,
#   todo_list, file_change, mcp_tool_call, dynamic_tool_call, web_search,
#   plan_update, error.
#
# Skill-specific extension (NOT emitted by codex itself):
#   run-codex-2.done  { type, entry_id, status }
#     Appended to the JSONL log by `run-single.sh` AFTER the terminal manifest
#     write. The filter translates this into `--- single done (<id>: <status>) ---`
#     so live-watch operators (`tail -F <jsonl> | codex-json-filter.sh`) see a
#     clear stop signal and know to TaskStop the Monitor. Existing JSONL
#     consumers ignore unknown event types by default — additive.

set -uo pipefail

# SIGPIPE handling: when a downstream reader (`head`, the Monitor, etc.)
# closes the pipe we want to exit 0 cleanly — not 141, which would propagate
# under callers using `set -o pipefail`. The trap converts the signal into
# a clean exit; the `emit` wrapper handles the EPIPE-before-signal race.
trap 'exit 0' PIPE

LEVEL="${CODEX_FILTER_LEVEL:-normal}"
MAXLEN="${CODEX_FILTER_MAXLEN:-200}"

# Parse CLI flags. Only --level is honored; everything else errors out.
# In the documented pipeline `codex exec --json | codex-json-filter.sh`
# argv is empty, so this loop is a no-op for the common case.
while [[ $# -gt 0 ]]; do
  case "$1" in
    --level)
      LEVEL="${2:-normal}"
      shift 2
      ;;
    --level=*)
      LEVEL="${1#--level=}"
      shift
      ;;
    -h|--help)
      sed -n '2,55p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      printf 'codex-json-filter: unknown flag %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

case "$LEVEL" in
  minimal|normal|verbose) ;;
  *)
    printf 'codex-json-filter: invalid --level %s (expected minimal|normal|verbose)\n' "$LEVEL" >&2
    exit 2
    ;;
esac

# Single emission point. Suppresses EPIPE stderr noise and exits 0 if the
# downstream pipe is gone — both belt and suspenders next to `trap PIPE`.
emit() {
  printf '%s\n' "$1" 2>/dev/null || exit 0
}

trunc() {
  local s="$1"
  if [[ ${#s} -gt $MAXLEN ]]; then
    printf '%s…' "${s:0:$MAXLEN}"
  else
    printf '%s' "$s"
  fi
}

oneline() {
  printf '%s' "$1" | tr '\n' ' ' | tr -s ' '
}

ts() { date -u +%H:%M:%SZ; }

# Read one JSONL line at a time. `read -r` does NOT buffer beyond one line,
# so events surface as they arrive. jq is invoked per-line; the per-line
# overhead is negligible compared to codex's wall time.
while IFS= read -r raw; do
  # Non-JSON lines (stderr we merged via 2>&1, rate-limit messages, etc.)
  # Surface error-shaped lines so the Monitor sees rate limits / 503s.
  if [[ "$raw" != \{* ]]; then
    if printf '%s' "$raw" | grep -qiE 'error|503|rate limit|failed|timeout'; then
      emit "$(ts) [ERR] $(trunc "$(oneline "$raw")")"
    fi
    continue
  fi

  # Single jq invocation pulls every field we might care about.
  parsed="$(printf '%s' "$raw" | jq -r '
    {
      type: .type,
      item_type: (.item.type // ""),
      item_id: (.item.id // ""),
      cmd: (.item.command // ""),
      exit: (.item.exit_code // ""),
      output: (.item.aggregated_output // ""),
      text: (.item.text // ""),
      item_msg: (.item.message // ""),
      phase: (.item.phase // ""),
      thread: (.thread_id // ""),
      err_msg: (.error.message // .message // ""),
      usage_in: (.usage.input_tokens // ""),
      usage_out: (.usage.output_tokens // ""),
      usage_cached: (.usage.cached_input_tokens // ""),
      orch_entry_id: (.entry_id // ""),
      orch_status: (.status // "")
    } | @json' 2>/dev/null)" || continue

  [[ -z "$parsed" ]] && continue
  type="$(printf '%s' "$parsed" | jq -r .type)"

  case "$type" in
    thread.started)
      thread="$(printf '%s' "$parsed" | jq -r .thread)"
      emit "$(ts) [START] thread=${thread:0:8}"
      ;;

    turn.started)
      [[ "$LEVEL" != "minimal" ]] && emit "$(ts) [TURN>] model-turn begin"
      ;;

    item.started)
      item_type="$(printf '%s' "$parsed" | jq -r .item_type)"
      if [[ "$item_type" == "command_execution" ]]; then
        cmd="$(printf '%s' "$parsed" | jq -r .cmd)"
        emit "$(ts) [CMD>] $(trunc "$(oneline "$cmd")")"
      elif [[ "$LEVEL" != "minimal" ]]; then
        emit "$(ts) [ITEM>] $item_type starting"
      fi
      ;;

    item.completed)
      item_type="$(printf '%s' "$parsed" | jq -r .item_type)"
      case "$item_type" in
        command_execution)
          exit_code="$(printf '%s' "$parsed" | jq -r .exit)"
          cmd="$(printf '%s' "$parsed" | jq -r .cmd)"
          if [[ -n "$exit_code" && "$exit_code" != "0" ]]; then
            out="$(printf '%s' "$parsed" | jq -r .output)"
            emit "$(ts) [CMD✗] exit=$exit_code $(trunc "$(oneline "$cmd")") :: $(trunc "$(oneline "$out")")"
          elif [[ "$LEVEL" == "verbose" ]]; then
            out="$(printf '%s' "$parsed" | jq -r .output)"
            emit "$(ts) [CMD✓] $(trunc "$(oneline "$cmd")") :: $(trunc "$(oneline "$out")")"
          else
            emit "$(ts) [CMD✓] exit=0 $(trunc "$(oneline "$cmd")")"
          fi
          ;;
        reasoning)
          if [[ "$LEVEL" != "minimal" ]]; then
            text="$(printf '%s' "$parsed" | jq -r .text)"
            first_line="$(printf '%s' "$text" | awk 'NF { print; exit }')"
            emit "$(ts) [THINK] $(trunc "$first_line")"
          fi
          ;;
        agent_message)
          text="$(printf '%s' "$parsed" | jq -r .text)"
          first_line="$(printf '%s' "$text" | awk 'NF { print; exit }')"
          emit "$(ts) [SAID] $(trunc "$first_line")"
          ;;
        error)
          # codex emits item.completed{type:error} for things like config
          # deprecation warnings. They're real errors per the Monitor
          # contract — surface them at every level.
          msg="$(printf '%s' "$parsed" | jq -r .item_msg)"
          [[ -z "$msg" ]] && msg="(no message)"
          emit "$(ts) [ERR] $(trunc "$(oneline "$msg")")"
          ;;
        file_change)
          [[ "$LEVEL" != "minimal" ]] && emit "$(ts) [FILE] $item_type"
          ;;
        mcp_tool_call|dynamic_tool_call|web_search|plan_update|todo_list)
          [[ "$LEVEL" != "minimal" ]] && emit "$(ts) [ITEM<] $item_type"
          ;;
        *)
          [[ "$LEVEL" == "verbose" ]] && emit "$(ts) [ITEM<] $item_type"
          ;;
      esac
      ;;

    turn.completed)
      tin="$(printf '%s' "$parsed" | jq -r .usage_in)"
      tout="$(printf '%s' "$parsed" | jq -r .usage_out)"
      tcached="$(printf '%s' "$parsed" | jq -r .usage_cached)"
      emit "$(ts) [TURN<] tokens: in=$tin out=$tout cached=$tcached"
      ;;

    run-codex-2.done)
      # Skill-specific terminal sentinel — appended by run-single.sh after the
      # terminal manifest write. Live-watch operators see this and TaskStop the
      # Monitor. Emitted at every verbosity level (it's the stop signal).
      oid="$(printf '%s' "$parsed" | jq -r .orch_entry_id)"
      ostat="$(printf '%s' "$parsed" | jq -r .orch_status)"
      [[ -z "$oid" || "$oid" == "null" ]] && oid="single"
      [[ -z "$ostat" || "$ostat" == "null" ]] && ostat="unknown"
      emit "--- single done ($oid: $ostat) ---"
      ;;

    error|*.error)
      msg="$(printf '%s' "$parsed" | jq -r .err_msg)"
      emit "$(ts) [ERR] $(trunc "$(oneline "$msg")")"
      ;;

    *)
      [[ "$LEVEL" == "verbose" ]] && emit "$(ts) [?] $type"
      ;;
  esac
done

exit 0

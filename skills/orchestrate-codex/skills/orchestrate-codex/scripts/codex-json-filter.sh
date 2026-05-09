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
# Usage:
#   codex exec --dangerously-bypass-approvals-and-sandbox --json <args> "<prompt>" 2>&1 \
#     | codex-json-filter.sh
#
# Inputs (env):
#   CODEX_FILTER_LEVEL   minimal | normal (default) | verbose
#                        minimal: [START] [CMD>] [CMD✓/✗] [SAID] [TURN<] [ERR]
#                        normal : + [TURN>] [THINK] [ITEM>]
#                        verbose: + command output tail on success, [?] for
#                                 unknown event types.
#   CODEX_FILTER_MAXLEN  max chars per emitted line (default: 200)
#
# Event schema (codex-cli 0.129.x; verified live):
#   thread.started    { type, thread_id }
#   turn.started      { type }
#   item.started      { type, item: { id, type, command?, status, aggregated_output, exit_code } }
#   item.completed    { type, item: { id, type, text|command|aggregated_output, exit_code, status, phase? } }
#   turn.completed    { type, usage: { input_tokens, cached_input_tokens, output_tokens } }
#   error             { type, message } or { error: { message } }
#
# Known item.type values: command_execution, reasoning, agent_message,
#   todo_list, file_change, mcp_tool_call, dynamic_tool_call, web_search,
#   plan_update.

set -uo pipefail

LEVEL="${CODEX_FILTER_LEVEL:-normal}"
MAXLEN="${CODEX_FILTER_MAXLEN:-200}"

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
      printf '%s [ERR] %s\n' "$(ts)" "$(trunc "$(oneline "$raw")")"
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
      phase: (.item.phase // ""),
      thread: (.thread_id // ""),
      err_msg: (.error.message // .message // ""),
      usage_in: (.usage.input_tokens // ""),
      usage_out: (.usage.output_tokens // ""),
      usage_cached: (.usage.cached_input_tokens // "")
    } | @json' 2>/dev/null)" || continue

  [[ -z "$parsed" ]] && continue
  type="$(printf '%s' "$parsed" | jq -r .type)"

  case "$type" in
    thread.started)
      thread="$(printf '%s' "$parsed" | jq -r .thread)"
      printf '%s [START] thread=%s\n' "$(ts)" "${thread:0:8}"
      ;;

    turn.started)
      [[ "$LEVEL" != "minimal" ]] && printf '%s [TURN>] model-turn begin\n' "$(ts)"
      ;;

    item.started)
      item_type="$(printf '%s' "$parsed" | jq -r .item_type)"
      if [[ "$item_type" == "command_execution" ]]; then
        cmd="$(printf '%s' "$parsed" | jq -r .cmd)"
        printf '%s [CMD>] %s\n' "$(ts)" "$(trunc "$(oneline "$cmd")")"
      elif [[ "$LEVEL" != "minimal" ]]; then
        printf '%s [ITEM>] %s starting\n' "$(ts)" "$item_type"
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
            printf '%s [CMD✗] exit=%s %s :: %s\n' "$(ts)" "$exit_code" \
              "$(trunc "$(oneline "$cmd")")" "$(trunc "$(oneline "$out")")"
          elif [[ "$LEVEL" == "verbose" ]]; then
            out="$(printf '%s' "$parsed" | jq -r .output)"
            printf '%s [CMD✓] %s :: %s\n' "$(ts)" \
              "$(trunc "$(oneline "$cmd")")" "$(trunc "$(oneline "$out")")"
          else
            printf '%s [CMD✓] exit=0 %s\n' "$(ts)" "$(trunc "$(oneline "$cmd")")"
          fi
          ;;
        reasoning)
          if [[ "$LEVEL" != "minimal" ]]; then
            text="$(printf '%s' "$parsed" | jq -r .text)"
            first_line="$(printf '%s' "$text" | awk 'NF { print; exit }')"
            printf '%s [THINK] %s\n' "$(ts)" "$(trunc "$first_line")"
          fi
          ;;
        agent_message)
          text="$(printf '%s' "$parsed" | jq -r .text)"
          first_line="$(printf '%s' "$text" | awk 'NF { print; exit }')"
          printf '%s [SAID] %s\n' "$(ts)" "$(trunc "$first_line")"
          ;;
        file_change)
          [[ "$LEVEL" != "minimal" ]] && printf '%s [FILE] %s\n' "$(ts)" "$item_type"
          ;;
        mcp_tool_call|dynamic_tool_call|web_search|plan_update|todo_list)
          [[ "$LEVEL" != "minimal" ]] && printf '%s [ITEM<] %s\n' "$(ts)" "$item_type"
          ;;
        *)
          [[ "$LEVEL" == "verbose" ]] && printf '%s [ITEM<] %s\n' "$(ts)" "$item_type"
          ;;
      esac
      ;;

    turn.completed)
      tin="$(printf '%s' "$parsed" | jq -r .usage_in)"
      tout="$(printf '%s' "$parsed" | jq -r .usage_out)"
      tcached="$(printf '%s' "$parsed" | jq -r .usage_cached)"
      printf '%s [TURN<] tokens: in=%s out=%s cached=%s\n' "$(ts)" "$tin" "$tout" "$tcached"
      ;;

    error|*.error)
      msg="$(printf '%s' "$parsed" | jq -r .err_msg)"
      printf '%s [ERR] %s\n' "$(ts)" "$(trunc "$(oneline "$msg")")"
      ;;

    *)
      [[ "$LEVEL" == "verbose" ]] && printf '%s [?] %s\n' "$(ts)" "$type"
      ;;
  esac
done

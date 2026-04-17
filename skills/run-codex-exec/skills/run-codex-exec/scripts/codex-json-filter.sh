#!/usr/bin/env bash
# codex-json-filter.sh — read JSONL from `codex exec --json` on stdin,
# emit ONE compact human-readable line per interesting event.
#
# Designed for Claude Code's Monitor tool: each stdout line becomes one
# notification. Uses jq with line-buffered parsing so events surface in
# real time rather than at end of stream.
#
# Usage:
#   codex exec --json --full-auto <args> <prompt> 2>&1 | codex-json-filter.sh
#   (Wire the above as a Monitor `command` to stream live events into chat.)
#
# Environment variables:
#   CODEX_FILTER_LEVEL   minimal | normal (default) | verbose
#                        minimal: [START] [CMD>] [CMD✓/✗] [SAID] [TURN<] [ERR]
#                        normal : + [TURN>] [THINK] [ITEM>]
#                        verbose: + command output tail on success
#   CODEX_FILTER_MAXLEN  max chars per emitted line (default: 200)
#
# Event schema observed from codex-cli 0.121.0:
#   thread.started    — {type, thread_id}
#   turn.started      — {type}
#   item.started      — {type, item: {id, type, command?, status, aggregated_output, exit_code}}
#   item.completed    — {type, item: {id, type, text|command|aggregated_output, exit_code, status}}
#   turn.completed    — {type, usage: {input_tokens, cached_input_tokens, output_tokens}}
#
# Known item.type values:
#   command_execution, reasoning, agent_message, todo_list
#   (unknown types caught by default case and shown in verbose mode)
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

while IFS= read -r raw; do
  # Non-JSON lines (stderr we merged via 2>&1, rate-limit errors, etc.)
  if [[ "$raw" != \{* ]]; then
    if printf '%s' "$raw" | grep -qiE "error|503|rate limit|failed"; then
      echo "$(ts) [ERR] $(trunc "$(oneline "$raw")")"
    fi
    continue
  fi

  # Parse the JSON line once into the fields we care about
  parsed=$(printf '%s' "$raw" | jq -r --unbuffered '
    {
      type: .type,
      item_type: (.item.type // ""),
      item_id: (.item.id // ""),
      cmd: (.item.command // ""),
      exit: (.item.exit_code // ""),
      output: (.item.aggregated_output // ""),
      text: (.item.text // ""),
      thread: (.thread_id // ""),
      usage_in: (.usage.input_tokens // ""),
      usage_out: (.usage.output_tokens // ""),
      usage_cached: (.usage.cached_input_tokens // "")
    } | @json' 2>/dev/null) || continue

  [[ -z "$parsed" ]] && continue
  type=$(printf '%s' "$parsed" | jq -r .type)

  case "$type" in
    thread.started)
      thread=$(printf '%s' "$parsed" | jq -r .thread)
      echo "$(ts) [START] thread=${thread:0:8}"
      ;;

    turn.started)
      [[ "$LEVEL" != "minimal" ]] && echo "$(ts) [TURN>] model-turn begin"
      ;;

    item.started)
      item_type=$(printf '%s' "$parsed" | jq -r .item_type)
      if [[ "$item_type" == "command_execution" ]]; then
        cmd=$(printf '%s' "$parsed" | jq -r .cmd)
        echo "$(ts) [CMD>] $(trunc "$(oneline "$cmd")")"
      elif [[ "$LEVEL" != "minimal" ]]; then
        echo "$(ts) [ITEM>] $item_type starting"
      fi
      ;;

    item.completed)
      item_type=$(printf '%s' "$parsed" | jq -r .item_type)
      case "$item_type" in
        command_execution)
          exit_code=$(printf '%s' "$parsed" | jq -r .exit)
          cmd=$(printf '%s' "$parsed" | jq -r .cmd)
          if [[ "$exit_code" != "0" && -n "$exit_code" ]]; then
            out=$(printf '%s' "$parsed" | jq -r .output)
            echo "$(ts) [CMD✗] exit=$exit_code $(trunc "$(oneline "$cmd")") :: $(trunc "$(oneline "$out")")"
          elif [[ "$LEVEL" == "verbose" ]]; then
            out=$(printf '%s' "$parsed" | jq -r .output)
            echo "$(ts) [CMD✓] $(trunc "$(oneline "$cmd")") :: $(trunc "$(oneline "$out")")"
          else
            echo "$(ts) [CMD✓] exit=0 $(trunc "$(oneline "$cmd")")"
          fi
          ;;
        reasoning)
          if [[ "$LEVEL" != "minimal" ]]; then
            text=$(printf '%s' "$parsed" | jq -r .text)
            first_line=$(printf '%s' "$text" | awk 'NF' | head -1)
            echo "$(ts) [THINK] $(trunc "$first_line")"
          fi
          ;;
        agent_message)
          text=$(printf '%s' "$parsed" | jq -r .text)
          first_line=$(printf '%s' "$text" | awk 'NF' | head -1)
          echo "$(ts) [SAID] $(trunc "$first_line")"
          ;;
        *)
          [[ "$LEVEL" == "verbose" ]] && echo "$(ts) [ITEM<] $item_type"
          ;;
      esac
      ;;

    turn.completed)
      in=$(printf '%s' "$parsed" | jq -r .usage_in)
      out=$(printf '%s' "$parsed" | jq -r .usage_out)
      cached=$(printf '%s' "$parsed" | jq -r .usage_cached)
      echo "$(ts) [TURN<] tokens: in=$in out=$out cached=$cached"
      ;;

    error|*.error)
      text=$(printf '%s' "$parsed" | jq -r '.error // .message // empty')
      echo "$(ts) [ERR] $(trunc "$(oneline "$text")")"
      ;;

    *)
      [[ "$LEVEL" == "verbose" ]] && echo "$(ts) [?] $type"
      ;;
  esac
done

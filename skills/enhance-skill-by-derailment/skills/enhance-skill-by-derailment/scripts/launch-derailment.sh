#!/usr/bin/env bash
set -o pipefail

usage() {
  cat <<'USAGE'
Usage:
  launch-derailment.sh --skill-path PATH --task TEXT [options]

Required:
  --skill-path PATH   Directory containing SKILL.md
  --task TEXT         Real user-style task for the subagent

Options:
  --round N           Derailment round label, default: 1
  --trace-out PATH    File to tee agent output into when running a command
  --agent-cmd CMD     Command that reads the prompt from stdin
  -h, --help          Show this help

DERAILMENT_AGENT_CMD can be used instead of --agent-cmd.
USAGE
}

die() {
  local code="$1"
  shift
  printf 'ERROR: %s\n' "$*" >&2
  exit "$code"
}

skill_path=""
task=""
round="1"
trace_out=""
agent_cmd="${DERAILMENT_AGENT_CMD:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill-path)
      [[ $# -ge 2 ]] || die 2 "--skill-path requires a value"
      skill_path="$2"
      shift 2
      ;;
    --task)
      [[ $# -ge 2 ]] || die 2 "--task requires a value"
      task="$2"
      shift 2
      ;;
    --round)
      [[ $# -ge 2 ]] || die 2 "--round requires a value"
      round="$2"
      shift 2
      ;;
    --trace-out)
      [[ $# -ge 2 ]] || die 2 "--trace-out requires a value"
      trace_out="$2"
      shift 2
      ;;
    --agent-cmd)
      [[ $# -ge 2 ]] || die 2 "--agent-cmd requires a value"
      agent_cmd="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die 2 "unknown argument: $1"
      ;;
  esac
done

[[ -n "$skill_path" ]] || die 2 "missing --skill-path"
[[ -n "${task//[[:space:]]/}" ]] || die 2 "missing or empty --task"
[[ "$round" =~ ^[0-9]+$ ]] || die 2 "--round must be a positive integer"
[[ "$round" -gt 0 ]] || die 2 "--round must be greater than 0"
[[ -f "$skill_path/SKILL.md" ]] || die 2 "SKILL.md not found at: $skill_path/SKILL.md"

if [[ -n "$trace_out" ]]; then
  trace_dir="$(dirname "$trace_out")"
  [[ -d "$trace_dir" ]] || die 3 "trace directory does not exist: $trace_dir"
  [[ -w "$trace_dir" ]] || die 3 "trace directory is not writable: $trace_dir"
  if [[ -e "$trace_out" && ! -w "$trace_out" ]]; then
    die 3 "trace path is not writable: $trace_out"
  fi
  : >> "$trace_out" || die 3 "trace path is not writable: $trace_out"
fi

render_prompt() {
  cat <<PROMPT
I need help with: ${task}

There's a skill for this at ${skill_path}. Read the SKILL.md and the
reference files it points to, then follow the workflow to do what I asked.

As you work, only flag moments where the skill text changes your path:
- [STUCK] if the skill leaves you unable to continue; name the missing or conflicting instruction
- [GUESSED] if you had to invent a decision the skill should have made explicit; point to the section that should have answered it
- [BROKE] if following the skill led you to a command or pattern that failed; include the command and the instruction that led you there
- [NICE] if a specific sentence, example, or routing cue saved you from a mistake

Valid marker shapes:
| Marker | Example shape |
|---|---|
| [STUCK] | [STUCK] references/fix-patterns.md says to run X, but no install step or fallback exists. |
| [GUESSED] | [GUESSED] Step 2 says "large skill" but gives no threshold; I chose 10 files. |
| [BROKE] | [BROKE] Command from Step 4 failed: ...; the documented output path did not exist. |
| [NICE] | [NICE] The routing table sent me to friction-classification.md before editing. |
PROMPT
}

prompt="$(render_prompt)"

if [[ -z "$agent_cmd" ]]; then
  printf '%s\n\n' "$prompt"
  printf 'Next step: send this round %s prompt to a fresh capable subagent and save the trace' "$round"
  if [[ -n "$trace_out" ]]; then
    printf ' at %s' "$trace_out"
  fi
  printf '.\n'
  exit 0
fi

if [[ -n "$trace_out" ]]; then
  printf '%s\n' "$prompt" | bash -lc "$agent_cmd" | tee "$trace_out"
  status=$?
else
  printf '%s\n' "$prompt" | bash -lc "$agent_cmd"
  status=$?
fi

if [[ "$status" -ne 0 ]]; then
  printf 'ERROR: agent command failed with status %s\n' "$status" >&2
  exit 4
fi

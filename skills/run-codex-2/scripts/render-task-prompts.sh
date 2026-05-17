#!/usr/bin/env bash
# render-task-prompts.sh — wrap raw description files (Linear tickets, GitHub
# issue bodies, design docs) into prompt files shaped for run-codex-2
# exec / single mode.
#
# The runner pipes prompt files VERBATIM to `codex exec`. Without the
# SUBAGENT-STOP prefix and the 6-section skeleton (Intent / Discovery /
# Constraints / Success criteria / Out-of-scope / Failure protocol), codex
# burns 20–80k tokens on meta-skill rumination before any work. This helper
# wraps each input file once so operators stop hand-rewriting tickets.
#
# Usage:
#   render-task-prompts.sh INPUT_DIR OUTPUT_DIR [--mode exec|single]
#                                              [--prefix on|off]
#                                              [--force]
#
#   INPUT_DIR    directory containing one *.md file per task (raw content).
#   OUTPUT_DIR   directory to write rendered prompt files into. Created if
#                missing. One output file per input, same basename.
#   --mode       exec (default) or single. Drives the prefix default and
#                the success-criteria default for audit-style tasks.
#   --prefix     on | off. Force-toggle the SUBAGENT-STOP prefix. Defaults:
#                  exec   → on
#                  single → on, unless input mentions
#                           "research" / "analysis" / "audit" → off
#   --force      overwrite existing OUTPUT_DIR/<basename>.md instead of
#                emitting a "[skip]" line.
#
# Output:
#   "[render] <input> → <output>"   per file written
#   "[skip]   <output> (exists)"     per file already present (no --force)
#
# Exit codes:
#   0  every file rendered or skipped
#   1  INPUT_DIR is empty / unreadable / contains no *.md files
#   2  usage error (bad flag, missing arg)
#
# Cross-link: references/templates/exec.tmpl.md (canonical prefix) and
#             references/templates/single.tmpl.md (single-mode skeleton).

set -u

usage() {
  cat >&2 <<'EOF'
usage: render-task-prompts.sh INPUT_DIR OUTPUT_DIR [--mode exec|single] [--prefix on|off] [--force]

Wraps each *.md file in INPUT_DIR with the SUBAGENT-STOP prefix and the
6-section run-codex-2 prompt skeleton. Output goes to OUTPUT_DIR
with the same basename. Idempotent: existing output files are skipped
unless --force is passed.
EOF
}

# ---------------------------------------------------------------- arg parse
INPUT_DIR=""
OUTPUT_DIR=""
MODE="exec"
PREFIX_OVERRIDE=""   # "" | "on" | "off"
FORCE=0

positional=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || { echo "error: --mode requires a value (exec|single)" >&2; usage; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --mode=*)
      MODE="${1#--mode=}"
      shift
      ;;
    --prefix)
      [[ $# -ge 2 ]] || { echo "error: --prefix requires a value (on|off)" >&2; usage; exit 2; }
      PREFIX_OVERRIDE="$2"
      shift 2
      ;;
    --prefix=*)
      PREFIX_OVERRIDE="${1#--prefix=}"
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "error: unknown flag: $1" >&2
      usage
      exit 2
      ;;
    *)
      if [[ $positional -eq 0 ]]; then
        INPUT_DIR="$1"
      elif [[ $positional -eq 1 ]]; then
        OUTPUT_DIR="$1"
      else
        echo "error: unexpected positional arg: $1" >&2
        usage
        exit 2
      fi
      positional=$((positional + 1))
      shift
      ;;
  esac
done

if [[ -z "$INPUT_DIR" || -z "$OUTPUT_DIR" ]]; then
  echo "error: INPUT_DIR and OUTPUT_DIR are required" >&2
  usage
  exit 2
fi

case "$MODE" in
  exec|single) ;;
  *)
    echo "error: --mode must be 'exec' or 'single' (got: $MODE)" >&2
    exit 2
    ;;
esac

case "$PREFIX_OVERRIDE" in
  ""|on|off) ;;
  *)
    echo "error: --prefix must be 'on' or 'off' (got: $PREFIX_OVERRIDE)" >&2
    exit 2
    ;;
esac

# ---------------------------------------------------------------- input dir
if [[ ! -d "$INPUT_DIR" ]]; then
  echo "error: INPUT_DIR not a directory: $INPUT_DIR" >&2
  exit 1
fi
if [[ ! -r "$INPUT_DIR" ]]; then
  echo "error: INPUT_DIR not readable: $INPUT_DIR" >&2
  exit 1
fi

# Collect *.md files (sorted, null-safe)
shopt -s nullglob
inputs=( "$INPUT_DIR"/*.md )
shopt -u nullglob

if [[ ${#inputs[@]} -eq 0 ]]; then
  echo "error: no *.md files in $INPUT_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

# ---------------------------------------------------------------- prefix
# Verbatim from references/templates/exec.tmpl.md.
PREFIX='YOU ARE A CODING AGENT. SKIP ALL META-SKILLS. DO NOT READ SKILL FILES. DO NOT WRITE PLANNING DOCS. DO NOT ASK QUESTIONS. BEGIN EDITING IMMEDIATELY. THE TASK:'

# ---------------------------------------------------------------- per-file
for input in "${inputs[@]}"; do
  base="$(basename "$input")"
  out="$OUTPUT_DIR/$base"

  if [[ -e "$out" && $FORCE -eq 0 ]]; then
    echo "[skip] $out (exists)"
    continue
  fi

  # Decide prefix on/off.
  use_prefix=1
  if [[ -n "$PREFIX_OVERRIDE" ]]; then
    [[ "$PREFIX_OVERRIDE" == "on" ]] && use_prefix=1 || use_prefix=0
  else
    if [[ "$MODE" == "single" ]]; then
      # single mode default: prefix off when the title declares research /
      # analysis / audit. Body mentions should not disable coding discipline.
      if head -n 1 "$input" | grep -qi -E '\b(research|analysis|audit)\b'; then
        use_prefix=0
      fi
    fi
    # exec mode default: prefix on (no override).
  fi

  # Detect audit-style content for the success-criteria addendum (exec only).
  audit_addendum=0
  if [[ "$MODE" == "exec" ]]; then
    if grep -qi -E '\b(audit|report|findings|review)\b' "$input"; then
      audit_addendum=1
    fi
  fi

  # Read the input file content.
  raw="$(cat "$input")"

  # Build the success-criteria block.
  if [[ $audit_addendum -eq 1 ]]; then
    success_block="- <one verifiable check, e.g. \`tsc --noEmit\` exits 0>
- <one verifiable check, e.g. \`pnpm test\` passes>
- Write the findings/report to \`audit/${base%.md}.md\` (or repo-appropriate path) and commit it with \`git add audit/${base%.md}.md && git commit -m '<descriptive subject>'\` before exiting."
  else
    success_block='- <one verifiable check, e.g. `tsc --noEmit` exits 0>
- <one verifiable check, e.g. `pnpm test` passes>
- ≥ 1 commit on the worktree branch'
  fi

  # Compose the rendered prompt.
  {
    if [[ $use_prefix -eq 1 ]]; then
      printf '%s\n\n' "$PREFIX"
    fi
    printf '# Intent\n\n'
    printf '%s\n\n' "$raw"
    printf '# Discovery — read first\n\n'
    printf -- '- <path 1> — <one-line reason>\n'
    printf -- '- <path 2> — <one-line reason>\n'
    printf -- '- AGENTS.md / CLAUDE.md / CONTRIBUTING.md (if present at the repo root)\n\n'
    printf '# Constraints\n\n'
    printf -- '- <hard fact the agent must respect>\n\n'
    printf '# Success criteria\n\n'
    printf '%s\n\n' "$success_block"
    printf '# Out-of-scope\n\n'
    printf -- '- Do NOT touch unrelated files\n'
    printf -- '- Do NOT add new dependencies unless explicitly requested\n\n'
    printf '# Failure protocol\n\n'
    if [[ "$MODE" == "exec" ]]; then
      printf 'If you cannot satisfy success criteria: stop, write a `.fleet-failure-%s.md` in the worktree root with the reason, exit non-zero. Do not improvise. Do not partial-commit.\n' "${base%.md}"
    else
      printf 'If blocked: stop, summarize what was tried and what was discovered, exit non-zero with the summary in the last-message file.\n'
    fi
  } > "$out"

  echo "[render] $input → $out"
done

exit 0

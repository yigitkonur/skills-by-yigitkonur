#!/usr/bin/env bash
# render.sh — prompt rendering for run-codex-1.
#
# Two modes:
#   template  Substitute placeholder in TEMPLATE across rows of INPUT_LIST,
#             writing PROMPTS_DIR/<slug>.md per row. (Was: render-prompts.sh)
#   wrap      Wrap each *.md in INPUT_DIR with a SUBAGENT-STOP prefix
#             ("YOU ARE A CODING AGENT.") and 6-section skeleton, writing to
#             OUTPUT_DIR/<basename>. (Was: render-task-prompts.sh)
#
# Usage:
#   render.sh --mode template INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]
#   render.sh --mode wrap     INPUT_DIR OUTPUT_DIR [--prefix on|off]
#                             [--mode-target exec|single] [--force]
#
# Shared:
#   --help, --version
#   Slug rule (both modes): [a-z0-9._-]  (lowercase; non-allowed → '-')
#   Collision rule (both modes): refuse on existing output unless --force; exit 2
#   Atomic write: mktemp + mv (no direct redirection)
#   Default --execute (writes); pass --dry-run for preview only
#
# Exit codes:
#   0  success
#   1  I/O error (input missing, output unwritable)
#   2  bad CLI flag, invalid mode, slug collision without --force

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
render.sh — prompt rendering for run-codex-1 (template + wrap modes).

Usage:
  render.sh --mode template INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER] [--force] [--dry-run]
  render.sh --mode wrap     INPUT_DIR OUTPUT_DIR [--prefix on|off] [--mode-target exec|single] [--force] [--dry-run]

Shared flags:
  --help, -h         this message
  --version          version string
  --force            overwrite existing output (default: refuse on collision; exit 2)
  --dry-run          print planned writes; do not modify filesystem

template mode:
  INPUT_LIST    file with one row per prompt; tab-delimited "name<TAB>content" or plain "name"
  TEMPLATE      template file containing PLACEHOLDER (default XXXXXXXXXXXXX)
  PROMPTS_DIR   output directory; per-row outputs at PROMPTS_DIR/<slug>.md
  PLACEHOLDER   string substituted (default XXXXXXXXXXXXX)

wrap mode:
  INPUT_DIR     directory of *.md files (non-recursive)
  OUTPUT_DIR    directory for wrapped outputs (one file per input, basename preserved)
  --prefix on|off    force SUBAGENT-STOP prefix on/off (auto-detected by default;
                     prefix-off triggers: research/analysis/audit content in single mode)
  --mode-target X    exec (default) or single — controls failure-protocol paragraph variant

Examples:
  render.sh --mode template inputs.txt template.md prompts/
  render.sh --mode wrap tickets/ prompts/ --mode-target single
EOF
}

# Parse top-level flags
MODE=""
FORCE=0
DRY_RUN=0
PREFIX_OVERRIDE=""
MODE_TARGET="exec"
declare -a POS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"; shift 2;;
    --mode=*)
      MODE="${1#*=}"; shift;;
    --prefix)
      PREFIX_OVERRIDE="$2"; shift 2;;
    --prefix=*)
      PREFIX_OVERRIDE="${1#*=}"; shift;;
    --mode-target)
      MODE_TARGET="$2"; shift 2;;
    --mode-target=*)
      MODE_TARGET="${1#*=}"; shift;;
    --force)
      FORCE=1; shift;;
    --dry-run)
      DRY_RUN=1; shift;;
    --help|-h)
      usage; exit 0;;
    --version)
      echo "render.sh v1.0 (run-codex-1 unified renderer)"; exit 0;;
    *)
      POS+=("$1"); shift;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "render.sh: --mode is required (template or wrap)" >&2
  usage >&2
  exit 2
fi

# Slug sanitization (shared between modes)
# Lowercase; non-allowed chars → '-'; collapse runs of '-'; strip ends.
_sanitize_slug() {
  local raw="$1"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  raw="$(printf '%s' "$raw" | tr -c 'a-z0-9._-' '-')"
  raw="$(printf '%s' "$raw" | sed 's/--*/-/g')"
  raw="$(printf '%s' "$raw" | sed 's/^-*//;s/-*$//')"
  printf '%s' "$raw"
}

# Atomic write helper: mktemp in parent, write content via cat, mv into place.
# Refuses collision unless FORCE=1.
_atomic_write() {
  local target="$1"
  local content="$2"
  if [[ -e "$target" ]] && [[ "$FORCE" -ne 1 ]]; then
    echo "render.sh: collision: $target (use --force to overwrite)" >&2
    exit 2
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[render] $target ($(printf '%s' "$content" | wc -c) bytes)"
    return 0
  fi
  local parent
  parent="$(dirname -- "$target")"
  mkdir -p "$parent"
  local tmp
  tmp="$(mktemp "${target}.tmp.XXXXXX")"
  printf '%s' "$content" > "$tmp"
  mv "$tmp" "$target"
  echo "[render] $target"
}

# ---------------------------------------------------------------------------
# Mode: template
# ---------------------------------------------------------------------------
do_template() {
  if [[ ${#POS[@]} -lt 3 ]]; then
    echo "render.sh template: usage: render.sh --mode template INPUT_LIST TEMPLATE PROMPTS_DIR [PLACEHOLDER]" >&2
    exit 2
  fi
  local INPUT_LIST="${POS[0]}"
  local TEMPLATE="${POS[1]}"
  local PROMPTS_DIR="${POS[2]}"
  local PLACEHOLDER="${POS[3]:-XXXXXXXXXXXXX}"

  [[ -f "$INPUT_LIST" ]] || { echo "render.sh template: input list not found: $INPUT_LIST" >&2; exit 1; }
  [[ -f "$TEMPLATE"   ]] || { echo "render.sh template: template not found: $TEMPLATE" >&2; exit 1; }

  local template_text
  template_text="$(cat "$TEMPLATE")"

  local linenum=0
  local written=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    linenum=$((linenum + 1))
    [[ -z "$line" ]] && continue
    local name content
    if [[ "$line" == *$'\t'* ]]; then
      name="${line%%$'\t'*}"
      content="${line#*$'\t'}"
    else
      name="$line"
      content="$line"
    fi
    local slug
    slug="$(_sanitize_slug "$name")"
    if [[ -z "$slug" ]]; then
      echo "render.sh template: empty slug from line $linenum: $line" >&2
      exit 1
    fi
    local out="$PROMPTS_DIR/$slug.md"
    # Substitute via awk with ENVIRON[] to avoid backslash interpretation.
    local rendered
    rendered="$(PROMPT_VAL="$content" awk -v ph="$PLACEHOLDER" '
      BEGIN { val = ENVIRON["PROMPT_VAL"] }
      { line = $0
        while ((i = index(line, ph)) > 0) {
          line = substr(line, 1, i-1) val substr(line, i + length(ph))
        }
        print line
      }
    ' <<<"$template_text")"
    _atomic_write "$out" "$rendered"
    written=$((written + 1))
  done < "$INPUT_LIST"

  echo "rendered: $written file(s) into $PROMPTS_DIR"
}

# ---------------------------------------------------------------------------
# Mode: wrap
# ---------------------------------------------------------------------------
# SUBAGENT-STOP prefix (literal first line in the rendered output)
_PREFIX_BLOCK=$(cat <<'EOF'
YOU ARE A CODING AGENT.

You are operating inside an isolated git worktree. The task below is your sole
focus. Do not pause for confirmation. Do not narrate plans. When you are done,
make a commit and stop.
EOF
)

do_wrap() {
  if [[ ${#POS[@]} -lt 2 ]]; then
    echo "render.sh wrap: usage: render.sh --mode wrap INPUT_DIR OUTPUT_DIR [--prefix on|off] [--mode-target exec|single]" >&2
    exit 2
  fi
  local INPUT_DIR="${POS[0]}"
  local OUTPUT_DIR="${POS[1]}"

  [[ -d "$INPUT_DIR" ]] || { echo "render.sh wrap: input dir not found or not a directory: $INPUT_DIR" >&2; exit 1; }
  [[ -r "$INPUT_DIR" ]] || { echo "render.sh wrap: input dir not readable: $INPUT_DIR" >&2; exit 1; }

  shopt -s nullglob
  local files=("$INPUT_DIR"/*.md)
  shopt -u nullglob
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "render.sh wrap: no *.md files found in $INPUT_DIR" >&2
    exit 1
  fi

  local rendered=0 skipped=0
  for input in "${files[@]}"; do
    local base
    base="$(basename "$input")"
    local out="$OUTPUT_DIR/$base"

    # Auto-detect prefix toggle
    local prefix_on=1
    if [[ -n "$PREFIX_OVERRIDE" ]]; then
      [[ "$PREFIX_OVERRIDE" == "off" ]] && prefix_on=0
    else
      # In single mode, research/analysis/audit content gets prefix off.
      if [[ "$MODE_TARGET" == "single" ]]; then
        local sniff
        sniff="$(head -c 4096 "$input" | tr '[:upper:]' '[:lower:]')"
        if [[ "$sniff" == *research* ]] || [[ "$sniff" == *analysis* ]] || [[ "$sniff" == *audit* ]]; then
          prefix_on=0
        fi
      fi
    fi

    # Failure-protocol paragraph varies by mode-target
    local failure_paragraph
    if [[ "$MODE_TARGET" == "single" ]]; then
      failure_paragraph="If blocked: stop, summarize what was tried and what was discovered, exit non-zero with the summary in the last-message file."
    else
      failure_paragraph="If blocked: write a brief summary of what was tried to .fleet-failure-$(basename "$input" .md).md and exit non-zero."
    fi

    local raw
    raw="$(cat "$input")"

    local content=""
    if [[ "$prefix_on" -eq 1 ]]; then
      content+="$_PREFIX_BLOCK"$'\n\n'
    fi
    content+="# Intent"$'\n\n'"$raw"$'\n\n'
    content+="# Discovery"$'\n\n'"<path 1>"$'\n'"<path 2>"$'\n'"AGENTS.md / CLAUDE.md / CONTRIBUTING.md"$'\n\n'
    content+="# Constraints"$'\n\n'"<constraint placeholder>"$'\n\n'
    content+="# Success criteria"$'\n\n'"<criterion 1>"$'\n'"<criterion 2>"$'\n'"<criterion 3>"$'\n\n'
    content+="# Out of scope"$'\n\n'"- Do NOT touch unrelated files."$'\n'"- Do NOT add new dependencies unless explicitly requested."$'\n\n'
    content+="# Failure protocol"$'\n\n'"$failure_paragraph"$'\n'

    if [[ -e "$out" ]] && [[ "$FORCE" -ne 1 ]]; then
      echo "[skip] $out (exists)"
      skipped=$((skipped + 1))
      continue
    fi
    _atomic_write "$out" "$content"
    rendered=$((rendered + 1))
  done

  echo "wrap: rendered=$rendered skipped=$skipped into $OUTPUT_DIR"
}

case "$MODE" in
  template) do_template;;
  wrap)     do_wrap;;
  *)
    echo "render.sh: unknown --mode '$MODE' (want 'template' or 'wrap')" >&2
    exit 2
    ;;
esac

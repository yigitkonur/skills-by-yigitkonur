#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage: audit-cli-help.sh [--subcommands FILE] CLI

Read-only CLI discoverability audit. Runs only help/version-style commands:
  CLI --help
  CLI --version
  CLI <subcommand...> --help for each non-comment line in FILE
EOF
}

SUBCOMMANDS_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --subcommands)
      SUBCOMMANDS_FILE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

CLI="${1:-}"

if [[ -z "$CLI" ]]; then
  usage >&2
  exit 2
fi

if [[ "$CLI" != */* ]] && ! command -v "$CLI" >/dev/null 2>&1; then
  echo "CLI not found on PATH: $CLI" >&2
  exit 2
fi

if [[ -n "$SUBCOMMANDS_FILE" && ! -f "$SUBCOMMANDS_FILE" ]]; then
  echo "Subcommands file not found: $SUBCOMMANDS_FILE" >&2
  exit 2
fi

run_capture() {
  "$@" 2>&1
}

has_text() {
  local haystack="$1"
  local needle="$2"
  printf '%s\n' "$haystack" | grep -F -- "$needle" >/dev/null 2>&1
}

has_regex() {
  local haystack="$1"
  local pattern="$2"
  printf '%s\n' "$haystack" | grep -Eiq -- "$pattern"
}

status_label() {
  local status="$1"
  if [[ "$status" -eq 0 ]]; then
    printf 'pass'
  else
    printf 'fail'
  fi
}

TOP_HELP="$(run_capture "$CLI" --help)"
TOP_HELP_STATUS=$?
VERSION_OUTPUT="$(run_capture "$CLI" --version)"
VERSION_STATUS=$?

ALL_HELP="$TOP_HELP"$'\n'"$VERSION_OUTPUT"
SUBCOMMAND_ROWS=""

if [[ -n "$SUBCOMMANDS_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" ]] && continue

    read -r -a parts <<< "$line"
    sub_help="$(run_capture "$CLI" "${parts[@]}" --help)"
    sub_status=$?
    ALL_HELP="$ALL_HELP"$'\n'"$sub_help"
    examples="no"
    exit_codes="no"
    has_regex "$sub_help" '(^|[[:space:]])examples?:' && examples="yes"
    has_regex "$sub_help" 'exit (code|status)|returns?[[:space:]]+[0-9]' && exit_codes="yes"
    SUBCOMMAND_ROWS+=$'\n'"| \`$line\` | $(status_label "$sub_status") | $examples | $exit_codes |"
  done < "$SUBCOMMANDS_FILE"
fi

STANDARD_FLAGS=(--json --output --quiet --yes --dry-run --force --no-input --timeout)

echo "# CLI Help Audit"
echo
echo "| Field | Value |"
echo "|---|---|"
echo "| CLI | \`$CLI\` |"
echo "| Top-level help | $(status_label "$TOP_HELP_STATUS") |"
echo "| Version command | $(status_label "$VERSION_STATUS") |"
if [[ -n "$SUBCOMMANDS_FILE" ]]; then
  echo "| Subcommand file | \`$SUBCOMMANDS_FILE\` |"
else
  echo "| Subcommand file | none |"
fi

echo
echo "## Standard Flag Coverage"
echo
echo "| Flag | Found in help |"
echo "|---|---|"
for flag in "${STANDARD_FLAGS[@]}"; do
  found="no"
  has_text "$ALL_HELP" "$flag" && found="yes"
  echo "| \`$flag\` | $found |"
done

echo
echo "## Documentation Signals"
echo
examples="no"
exit_codes="no"
has_regex "$ALL_HELP" '(^|[[:space:]])examples?:' && examples="yes"
has_regex "$ALL_HELP" 'exit (code|status)|returns?[[:space:]]+[0-9]' && exit_codes="yes"
echo "| Signal | Found |"
echo "|---|---|"
echo "| Examples documented | $examples |"
echo "| Exit codes documented | $exit_codes |"

if [[ -n "$SUBCOMMANDS_FILE" ]]; then
  echo
  echo "## Subcommand Help"
  echo
  echo "| Subcommand | Help | Examples | Exit codes |"
  echo "|---|---|---|---|"
  printf '%s\n' "$SUBCOMMAND_ROWS" | sed '/^$/d'
fi

echo
echo "## Missing Or Suspicious Affordances"
echo
missing=0
for flag in "${STANDARD_FLAGS[@]}"; do
  if ! has_text "$ALL_HELP" "$flag"; then
    echo "- Missing or undocumented standard flag: \`$flag\`"
    missing=$((missing + 1))
  fi
done
if [[ "$examples" != "yes" ]]; then
  echo "- Help does not appear to document examples."
  missing=$((missing + 1))
fi
if [[ "$exit_codes" != "yes" ]]; then
  echo "- Help does not appear to document exit codes."
  missing=$((missing + 1))
fi
if [[ "$TOP_HELP_STATUS" -ne 0 ]]; then
  echo "- Top-level \`--help\` returned exit code $TOP_HELP_STATUS."
  missing=$((missing + 1))
fi
if [[ "$missing" -eq 0 ]]; then
  echo "- None detected by this conservative help scan."
fi

#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: launch-debug-session.sh <url> [session-name] [--headed]

Opens a playwright-cli browser/session for live debugging and prints the next
inspection commands. It does not close or delete sessions.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit $([[ $# -lt 1 ]] && echo 1 || echo 0)
fi

URL="$1"
shift

SESSION=""
HEADED=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --headed)
      HEADED="--headed"
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$SESSION" ]]; then
        echo "Only one session name is supported." >&2
        exit 2
      fi
      SESSION="$1"
      ;;
  esac
  shift
done

if command -v playwright-cli >/dev/null 2>&1; then
  CLI=(playwright-cli)
elif npx --no-install playwright-cli --version >/dev/null 2>&1; then
  CLI=(npx --no-install playwright-cli)
else
  echo "playwright-cli was not found globally or locally." >&2
  echo "Run scripts/check-playwright-cli.sh or install with: npm install -g @playwright/cli@latest" >&2
  exit 1
fi

HELP="$("${CLI[@]}" --help)"
for required in open requests show tracing-start; do
  if ! printf '%s\n' "$HELP" | grep -Eq "^[[:space:]]+$required([[:space:]]|$)"; then
    echo "The detected CLI lacks current command '$required'. Run scripts/check-playwright-cli.sh." >&2
    exit 1
  fi
done

COMMAND=("${CLI[@]}")
if [[ -n "$SESSION" ]]; then
  COMMAND+=("-s=$SESSION")
fi
COMMAND+=(open "$URL")
if [[ -n "$HEADED" ]]; then
  COMMAND+=("$HEADED")
fi

echo "== opening session =="
printf 'Command:'
printf ' %q' "${COMMAND[@]}"
printf '\n'
"${COMMAND[@]}"

PREFIX=("${CLI[@]}")
if [[ -n "$SESSION" ]]; then
  PREFIX+=("-s=$SESSION")
fi

echo
echo "== next commands =="
printf '%q ' "${PREFIX[@]}"; echo "snapshot"
printf '%q ' "${PREFIX[@]}"; echo "show"
printf '%q ' "${PREFIX[@]}"; echo "console error"
printf '%q ' "${PREFIX[@]}"; echo "requests"
printf '%q ' "${PREFIX[@]}"; echo "tracing-start"
printf '%q ' "${PREFIX[@]}"; echo "tracing-stop"

echo
echo "Cleanup is intentional: close this session only when done."
if [[ -n "$SESSION" ]]; then
  printf 'Close command: '; printf '%q ' "${PREFIX[@]}"; echo "close"
else
  printf 'Close command: '; printf '%q ' "${PREFIX[@]}"; echo "close"
fi

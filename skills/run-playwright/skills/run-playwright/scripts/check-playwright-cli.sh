#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

required_commands=(install-browser state-save list show)

has_command_in_help() {
  local help="$1"
  local name="$2"
  printf '%s\n' "$help" | grep -Eq "^[[:space:]]+$name([[:space:]]|$)"
}

candidate_has_current_surface() {
  local help="$1"
  local cmd
  for cmd in "${required_commands[@]}"; do
    has_command_in_help "$help" "$cmd" || return 1
  done
}

try_candidate() {
  local label="$1"
  shift
  local -a candidate=("$@")
  local version help

  if ! version="$("${candidate[@]}" --version 2>/dev/null)"; then
    echo "$label: unavailable"
    return 1
  fi

  if ! help="$("${candidate[@]}" --help 2>/dev/null)"; then
    echo "$label: version $version, but help failed"
    return 1
  fi

  echo "$label: version $version"
  if candidate_has_current_surface "$help"; then
    CLI=("${candidate[@]}")
    HELP="$help"
    SELECTED_LABEL="$label"
    return 0
  fi

  echo "warn: $label lacks current @playwright/cli commands; continuing to next candidate"
  return 1
}

echo "== playwright-cli availability =="

CLI=()
HELP=""
SELECTED_LABEL=""

if command -v playwright-cli >/dev/null 2>&1; then
  echo "global path: $(command -v playwright-cli)"
  try_candidate "global playwright-cli" playwright-cli || true
else
  echo "global: unavailable"
fi

if [[ -z "$SELECTED_LABEL" ]]; then
  try_candidate "local npx --no-install playwright-cli" npx --no-install playwright-cli || true
fi

if [[ -z "$SELECTED_LABEL" ]]; then
  try_candidate "fallback npx -y @playwright/cli@latest" npx -y @playwright/cli@latest || true
fi

if [[ -z "$SELECTED_LABEL" ]]; then
  echo "No current playwright-cli candidate found."
  exit 1
fi

echo
echo "== npm package =="
npm view @playwright/cli version dist-tags description bin --json

echo
echo "== binary version =="
"${CLI[@]}" --version
echo "selected: $SELECTED_LABEL"

echo
echo "== help =="
printf '%s\n' "$HELP"

echo
echo "== required command check =="
missing=0
for cmd in "${required_commands[@]}"; do
  if has_command_in_help "$HELP" "$cmd"; then
    echo "ok: $cmd"
  else
    echo "missing: $cmd"
    missing=1
  fi
done

echo
echo "== old command drift scan =="
old_commands=(
  "network"
  "session-list"
  "session-stop"
  "session-stop-all"
  "session-delete"
  "session-restart"
)

for cmd in "${old_commands[@]}"; do
  if grep -REn "playwright-cli[[:space:]][^[:cntrl:]]*${cmd}([^[:alnum:]_-]|$)" \
    "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references" "$SKILL_DIR/scripts" \
    --exclude='check-playwright-cli.sh' --exclude='check-playwright-cli.md' >/tmp/playwright-cli-drift.$$ 2>/dev/null; then
    if has_command_in_help "$HELP" "$cmd"; then
      echo "ok: docs mention supported command $cmd"
    else
      echo "warn: docs mention unsupported old command $cmd"
      cat /tmp/playwright-cli-drift.$$
    fi
  fi
  rm -f /tmp/playwright-cli-drift.$$
done

if [[ "$missing" -ne 0 ]]; then
  echo
  echo "Required command check failed."
  exit 1
fi

echo
echo "check complete"

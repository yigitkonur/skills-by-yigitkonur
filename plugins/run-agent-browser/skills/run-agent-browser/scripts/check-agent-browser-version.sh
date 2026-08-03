#!/usr/bin/env bash
set -euo pipefail

DEFAULT_MIN_VERSION="0.33.2"

usage() {
  cat <<'EOF'
Usage: check-agent-browser-version.sh [minimum-version]

Checks the installed CLI, version-matched core skill, Steel Browser endpoint
configuration, provider/CDP conflict handling, and Patchright scrape-pool health.
Defaults to the version used to verify this skill: 0.33.2.

Read-only: never installs packages, launches Chrome, reveals credentials, or
changes provider/runtime state.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 0; fi

MIN_VERSION="${1:-$DEFAULT_MIN_VERSION}"
MIN_VERSION="${MIN_VERSION#v}"
MIN_VERSION="${MIN_VERSION#V}"
if [[ ! "$MIN_VERSION" =~ ^[0-9]+(\.[0-9]+){0,2}$ ]]; then
  echo "minimum version must look like 0.33.2, 0.33, or v0.33.2" >&2
  exit 2
fi

normalize_version() {
  local raw="$1" major minor patch
  IFS=. read -r major minor patch <<<"$raw"
  printf '%s.%s.%s' "$major" "${minor:-0}" "${patch:-0}"
}

version_lt() {
  local left="$1" right="$2" l1 l2 l3 r1 r2 r3
  IFS=. read -r l1 l2 l3 <<<"$left"
  IFS=. read -r r1 r2 r3 <<<"$right"
  if ((10#$l1 != 10#$r1)); then ((10#$l1 < 10#$r1)); return; fi
  if ((10#$l2 != 10#$r2)); then ((10#$l2 < 10#$r2)); return; fi
  ((10#$l3 < 10#$r3))
}

MIN_VERSION="$(normalize_version "$MIN_VERSION")"
if command -v agent-browser >/dev/null 2>&1; then
  AB_CMD=(agent-browser)
else
  AB_CMD=(npx --no-install agent-browser)
fi

echo "resolved command:  ${AB_CMD[*]}"
echo "minimum version:   $MIN_VERSION"

VERSION_OUTPUT="$("${AB_CMD[@]}" --version 2>&1)" || {
  status=$?
  echo "can run:           no"
  printf '%s\n' "$VERSION_OUTPUT"
  exit "$status"
}
echo "can run:           yes"
echo "version output:    $VERSION_OUTPUT"

if [[ "$VERSION_OUTPUT" =~ ([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
  VERSION="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
else
  echo "version parsed:    no" >&2
  exit 3
fi

echo "version parsed:    $VERSION"
if version_lt "$VERSION" "$MIN_VERSION"; then
  echo "version check:     fail (upgrade required)" >&2
  exit 4
fi
echo "version check:     pass"

if "${AB_CMD[@]}" skills get core >/dev/null 2>&1; then
  echo "core skill:        available"
else
  echo "core skill:        unavailable" >&2
  exit 5
fi

if [[ -r "$HOME/.config/steel-browser-cdp.env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.config/steel-browser-cdp.env"
  echo "steel env:         available"
else
  echo "steel env:         unavailable" >&2
  exit 6
fi

for name in STEEL_AGENT_BROWSER_CDP STEEL_HEALTH_URL STEEL_CDP_VERSION_URL STEEL_UI_URL; do
  if [[ -z "${!name:-}" ]]; then
    echo "steel var $name: missing" >&2
    exit 7
  fi
done
echo "steel vars:        complete"

if curl -fsS --max-time 5 "$STEEL_HEALTH_URL" >/dev/null; then
  echo "steel health:      pass"
else
  echo "steel health:      fail" >&2
  exit 8
fi

if curl -fsS --max-time 5 "$STEEL_CDP_VERSION_URL" >/dev/null; then
  echo "steel CDP:         pass"
else
  echo "steel CDP:         fail" >&2
  exit 9
fi

if [[ -n "${AGENT_BROWSER_PROVIDER:-}" ]]; then
  echo "global provider:   set (${AGENT_BROWSER_PROVIDER}; CDP commands need env -u AGENT_BROWSER_PROVIDER)"
else
  echo "global provider:   unset"
fi

POOL_HEALTH_URL="https://browserpool.65.108.140.207.sslip.io/health"
if curl -fsS --max-time 10 "$POOL_HEALTH_URL" >/dev/null; then
  echo "Patchright pool:   healthy"
else
  echo "Patchright pool:   unavailable" >&2
  exit 10
fi

echo "runtime check:     pass"

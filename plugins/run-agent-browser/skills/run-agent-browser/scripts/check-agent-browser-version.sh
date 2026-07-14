#!/usr/bin/env bash
set -euo pipefail

DEFAULT_MIN_VERSION="0.31.1"

usage() {
  cat <<'EOF'
Usage: check-agent-browser-version.sh [minimum-version]

Checks the installed CLI, version-matched core skill, and optional local CDP
pool. Defaults to the version used to verify this skill: 0.31.1.

Uses an installed `agent-browser`, otherwise `npx --no-install`. It never
installs packages or Chrome.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 0; fi

MIN_VERSION="${1:-$DEFAULT_MIN_VERSION}"
MIN_VERSION="${MIN_VERSION#v}"
MIN_VERSION="${MIN_VERSION#V}"
if [[ ! "$MIN_VERSION" =~ ^[0-9]+(\.[0-9]+){0,2}$ ]]; then
  echo "minimum version must look like 0.31.1, 0.31, or v0.31.1" >&2
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
  exit 1
fi
echo "version parsed:    yes ($VERSION)"

if version_lt "$VERSION" "$MIN_VERSION"; then
  echo "minimum satisfied: no"
  exit 1
fi
echo "minimum satisfied: yes"

if "${AB_CMD[@]}" skills get core >/dev/null 2>&1; then
  echo "core skill:        available"
else
  echo "core skill:        unavailable" >&2
  exit 1
fi

if "${AB_CMD[@]}" pool status >/dev/null 2>&1; then
  echo "managed CDP pool:  available"
else
  echo "managed CDP pool:  unavailable (standard CLI mode)"
fi

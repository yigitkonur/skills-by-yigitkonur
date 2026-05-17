#!/usr/bin/env bash
set -euo pipefail

DEFAULT_MIN_VERSION="0.17.1"

usage() {
  cat <<'EOF'
Usage: check-agent-browser-version.sh [minimum-version]

Checks whether agent-browser can run and whether its parsed version is at least
the requested minimum. Defaults to 0.17.1.

The script uses an installed `agent-browser` binary when available, otherwise
it tries `npx --no-install agent-browser`. It does not install packages or
Chromium.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

MIN_VERSION="${1:-$DEFAULT_MIN_VERSION}"
MIN_VERSION="${MIN_VERSION#v}"
MIN_VERSION="${MIN_VERSION#V}"

if [[ ! "$MIN_VERSION" =~ ^[0-9]+(\.[0-9]+){0,2}$ ]]; then
  echo "minimum parsed:   no ($MIN_VERSION)"
  echo "minimum version must look like 0.17.1, 0.17, or v0.17.1" >&2
  exit 0
fi

normalize_version() {
  local raw="$1"
  local major minor patch
  IFS=. read -r major minor patch <<<"$raw"
  printf '%s.%s.%s' "$major" "${minor:-0}" "${patch:-0}"
}

MIN_VERSION="$(normalize_version "$MIN_VERSION")"

if command -v agent-browser >/dev/null 2>&1; then
  AB_CMD=(agent-browser)
else
  AB_CMD=(npx --no-install agent-browser)
fi

echo "resolved command: ${AB_CMD[*]}"
echo "minimum version:  ${MIN_VERSION}"

set +e
VERSION_OUTPUT="$("${AB_CMD[@]}" --version 2>&1)"
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "can run:          no"
  echo "version output:"
  echo "$VERSION_OUTPUT"
  exit $STATUS
fi

echo "can run:          yes"
echo "version output:   $VERSION_OUTPUT"

VERSION=""
if [[ "$VERSION_OUTPUT" =~ ([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
  VERSION="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
fi

if [[ -z "$VERSION" ]]; then
  echo "version parsed:   no"
  exit 0
fi

echo "version parsed:   yes ($VERSION)"

version_lt() {
  local left="$1"
  local right="$2"
  local left_major left_minor left_patch right_major right_minor right_patch

  IFS=. read -r left_major left_minor left_patch <<<"$left"
  IFS=. read -r right_major right_minor right_patch <<<"$right"

  left_minor="${left_minor:-0}"
  left_patch="${left_patch:-0}"
  right_minor="${right_minor:-0}"
  right_patch="${right_patch:-0}"

  if ((10#$left_major < 10#$right_major)); then return 0; fi
  if ((10#$left_major > 10#$right_major)); then return 1; fi
  if ((10#$left_minor < 10#$right_minor)); then return 0; fi
  if ((10#$left_minor > 10#$right_minor)); then return 1; fi
  if ((10#$left_patch < 10#$right_patch)); then return 0; fi
  return 1
}

if version_lt "$VERSION" "$MIN_VERSION"; then
  echo "minimum satisfied: no"
  exit 1
fi

echo "minimum satisfied: yes"

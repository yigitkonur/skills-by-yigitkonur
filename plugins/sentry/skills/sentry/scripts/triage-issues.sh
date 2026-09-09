#!/usr/bin/env bash
set -euo pipefail

# Quick, token-efficient Sentry triage script
# Automatically detects modern 'sentry' or legacy 'sentry-cli'

echo "=== Sentry Quick Triage ==="

if command -v sentry >/dev/null 2>&1; then
  TARGET="${1:-}"
  if [[ -z "${TARGET}" ]]; then
    ORG=$(sentry org list 2>/dev/null | head -1 | awk '{print $1}' || true)
    if [[ -z "${ORG}" ]]; then
      echo "❌ Unable to determine organization. Specify <org>/<project> as argument."
      exit 1
    fi
    TARGET="${ORG}/"
  fi

  echo "Querying unresolved issues via 'sentry' CLI for ${TARGET}..."
  sentry issue list "${TARGET}" -q 'is:unresolved' -s freq -t 24h -n 15 --json \
    --fields shortId,title,level,priority,seerFixabilityScore \
    | jq -r '.data[] | "\(.shortId)\t[\(.priority)]\tseer=\(.seerFixabilityScore // 0)\t\(.title)"' \
    | column -t -s $'\t' || true

elif command -v sentry-cli >/dev/null 2>&1; then
  echo "Querying unresolved issues via 'sentry-cli'..."
  sentry-cli issues list --status unresolved

else
  echo "❌ Neither 'sentry' nor 'sentry-cli' binary found in PATH."
  echo "Install modern CLI: brew install getsentry/tools/sentry"
  echo "Install legacy CLI: brew install getsentry/tools/sentry-cli"
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail

# Quick, token-efficient Sentry triage script
# Automatically detects modern 'sentry' or legacy 'sentry-cli'

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    echo "Usage: $0 [<org>/<project> | <project>]"
    echo ""
    echo "Quick, token-efficient Sentry triage script."
    echo "Automatically detects modern 'sentry' or legacy 'sentry-cli'."
    echo ""
    echo "Arguments:"
    echo "  <org>/<project>  Sentry organization and project slug (or project slug for sentry-cli)"
    echo "  -h, --help       Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $0 my-org/my-backend"
    echo "  $0 frontend"
    exit 0
  fi
done

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
  TARGET="${1:-}"
  if [[ -n "${TARGET}" ]]; then
    # Strip org prefix if provided as <org>/<project>
    PROJECT="${TARGET#*/}"
    echo "Querying unresolved issues via 'sentry-cli' for project '${PROJECT}'..."
    sentry-cli issues list -p "${PROJECT}" --status unresolved
  else
    echo "No project specified. Discovering projects..."
    PROJECTS=$(sentry-cli projects list 2>/dev/null | awk -F'|' 'NR>3 && NF>=3 {gsub(/^[ \t]+|[ \t]+$/, "", $3); if ($3 != "" && $3 != "Slug") print $3}' || true)
    if [[ -z "${PROJECTS}" ]]; then
      echo "❌ No projects found or failed to authenticate. Provide project slug: $0 <project>"
      exit 1
    fi
    for p in ${PROJECTS}; do
      echo "=== Project: ${p} ==="
      sentry-cli issues list -p "${p}" --status unresolved || true
    done
  fi

else
  echo "❌ Neither 'sentry' nor 'sentry-cli' binary found in PATH."
  echo "Install modern CLI: brew install getsentry/tools/sentry"
  echo "Install legacy CLI: brew install getsentry/tools/sentry-cli"
  exit 1
fi

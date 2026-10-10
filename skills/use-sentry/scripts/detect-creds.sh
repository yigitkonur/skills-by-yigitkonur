#!/usr/bin/env bash
set -euo pipefail

# Safe credential detector for Sentry
# Inspects ~/.sentryclirc and environment variables without printing secret tokens.

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    echo "Usage: $0"
    echo ""
    echo "Safe credential detector for Sentry."
    echo "Inspects ~/.sentryclirc and environment variables without printing secret tokens."
    echo ""
    echo "Options:"
    echo "  -h, --help  Show this help message and exit"
    exit 0
  fi
done

echo "=== Sentry Credential Pre-flight Check ==="

TOKEN=""
SOURCE=""
BASE_URL=""

# 1. Detect Base URL (Regional cluster awareness)
if [[ -n "${SENTRY_URL:-}" ]]; then
  BASE_URL="${SENTRY_URL%/}"
elif [[ -f "${HOME}/.sentryclirc" ]]; then
  EXTRACTED_URL=$(awk -F '=' '/^url/ {gsub(/[ "]/, "", $2); print $2}' "${HOME}/.sentryclirc" | head -n 1 || true)
  if [[ -n "${EXTRACTED_URL}" ]]; then
    BASE_URL="${EXTRACTED_URL%/}"
  fi
fi

if [[ -z "${BASE_URL}" ]]; then
  BASE_URL="https://sentry.io"
fi

# 2. Detect Auth Token
if [[ -n "${SENTRY_AUTH_TOKEN:-}" ]]; then
  TOKEN="${SENTRY_AUTH_TOKEN}"
  SOURCE="environment variable (SENTRY_AUTH_TOKEN)"
elif [[ -f "${HOME}/.sentryclirc" ]]; then
  EXTRACTED=$(awk -F '=' '/^\[auth\]/ {in_auth=1; next} /^\[/ {in_auth=0} in_auth && /^token/ {gsub(/ /, "", $2); print $2}' "${HOME}/.sentryclirc" || true)
  if [[ -n "${EXTRACTED}" ]]; then
    TOKEN="${EXTRACTED}"
    SOURCE="user config (~/.sentryclirc)"
  fi
fi

if [[ -z "${TOKEN}" ]]; then
  echo "❌ No Sentry authentication token detected."
  echo "Please set SENTRY_AUTH_TOKEN or add [auth] token=sntryu_... to ~/.sentryclirc"
  exit 1
fi

TOKEN_PREFIX="${TOKEN:0:6}"
TOKEN_LEN="${#TOKEN}"

echo "✅ Sentry auth token detected from ${SOURCE}."
echo "   Token type: ${TOKEN_PREFIX}... (${TOKEN_LEN} characters)"
echo "   Target Sentry URL: ${BASE_URL}"

echo "Checking organization access..."
HTTP_STATUS=$(curl -s -o /tmp/sentry_orgs_check.json -w "%{http_code}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "${BASE_URL}/api/0/organizations/" || echo "000")

if [[ "${HTTP_STATUS}" == "200" ]]; then
  ORG_COUNT=$(jq 'length' /tmp/sentry_orgs_check.json 2>/dev/null || echo "0")
  echo "✅ Authenticated successfully. Found ${ORG_COUNT} accessible organization(s):"
  jq -r '.[] | "   - \(.name) (slug: \(.slug))"' /tmp/sentry_orgs_check.json 2>/dev/null || true
  rm -f /tmp/sentry_orgs_check.json
else
  echo "❌ Authentication failed with HTTP status ${HTTP_STATUS} against ${BASE_URL}."
  rm -f /tmp/sentry_orgs_check.json
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail

# Diagnose Sentry network connectivity & test envelope tunnel endpoint
# Usage: ./verify-tunnel.sh <DSN_OR_PROJECT_ID>

INPUT="${1:-}"

if [[ -z "${INPUT}" ]]; then
  echo "Usage: $0 <DSN_OR_PROJECT_ID>"
  echo "Example: $0 4512053148975104"
  echo "Example: $0 https://public@o0.ingest.sentry.io/4512053148975104"
  exit 1
fi

PROJECT_ID=$(echo "${INPUT}" | sed -E 's/.*\/([0-9]+)$/\1/')
TUNNEL_URL="https://sentry.io/api/${PROJECT_ID}/envelope/"

echo "=== Sentry Network & Tunnel Diagnostic ==="
echo "Target Project ID: ${PROJECT_ID}"
echo "Tunnel Endpoint:   ${TUNNEL_URL}"
echo ""

SAMPLE_INGEST="o279668.ingest.us.sentry.io"
echo "Checking DNS resolution for ${SAMPLE_INGEST}..."
RESOLVED_IPS=$(dig +short "${SAMPLE_INGEST}" 2>/dev/null || true)

if echo "${RESOLVED_IPS}" | grep -q "195.175.254.2"; then
  echo "⚠️ WARNING: DNS is sinkholed to 195.175.254.2 (TTNet/ISP interception)."
  echo "   Direct ingest will FAIL with self-signed certificate error."
  echo "   Envelope tunnel is MANDATORY on this network."
else
  echo "✅ Ingest DNS resolved: ${RESOLVED_IPS:-none}"
fi
echo ""

echo "Testing HTTP POST to Sentry tunnel..."
HTTP_CODE=$(curl -s -o /tmp/tunnel_res.txt -w "%{http_code}" \
  -X POST \
  -H "Content-Type: application/x-sentry-envelope" \
  "${TUNNEL_URL}" || echo "000")

echo "Tunnel HTTP response code: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "400" || "${HTTP_CODE}" == "401" ]]; then
  echo "✅ Sentry tunnel endpoint is REACHABLE and responsive (Status: ${HTTP_CODE})."
  echo "   Response: $(cat /tmp/tunnel_res.txt)"
  rm -f /tmp/tunnel_res.txt
else
  echo "❌ Tunnel endpoint failed with HTTP ${HTTP_CODE}."
  cat /tmp/tunnel_res.txt || true
  rm -f /tmp/tunnel_res.txt
  exit 1
fi

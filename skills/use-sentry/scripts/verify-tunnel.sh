#!/usr/bin/env bash
set -euo pipefail

# Diagnose Sentry network connectivity & test application reverse proxy tunnel route
# Usage: ./verify-tunnel.sh [ENDPOINT_URL_OR_PROJECT_ID]

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    echo "Usage: $0 [ENDPOINT_URL_OR_PROJECT_ID]"
    echo ""
    echo "Diagnose Sentry network connectivity & test application reverse proxy tunnel endpoint."
    echo ""
    echo "Arguments:"
    echo "  [ENDPOINT_URL_OR_PROJECT_ID]  Application reverse proxy URL (default: http://localhost:3000/api/monitoring/tunnel) or Project ID"
    echo "  -h, --help                    Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $0 http://localhost:3000/api/monitoring/tunnel"
    echo "  $0 4512053148975104"
    exit 0
  fi
done

INPUT="${1:-http://localhost:3000/api/monitoring/tunnel}"
APP_BASE="${APP_BASE_URL:-http://localhost:3000}"

if [[ "${INPUT}" =~ ^[0-9]+$ || "${INPUT}" =~ ^https://[^@]+@ ]]; then
  PROJECT_ID=$(echo "${INPUT}" | sed -E 's/.*\/([0-9]+)$/\1/')
  TUNNEL_URL="${APP_BASE}/api/monitoring/tunnel"
else
  TUNNEL_URL="${INPUT}"
  PROJECT_ID="${PROJECT_ID:-4512053148975104}"
fi

echo "=== Sentry Network & Application Reverse Proxy Diagnostic ==="
echo "Target Project ID: ${PROJECT_ID}"
echo "Tunnel Endpoint:   ${TUNNEL_URL}"
echo ""

SAMPLE_INGEST="o279668.ingest.us.sentry.io"
echo "Checking DNS resolution for ${SAMPLE_INGEST}..."
RESOLVED_IPS=$(dig +short "${SAMPLE_INGEST}" 2>/dev/null || true)

if echo "${RESOLVED_IPS}" | grep -q "195.175.254.2"; then
  echo "⚠️ WARNING: DNS is sinkholed to 195.175.254.2 (TTNet/ISP interception)."
  echo "   Direct ingest will FAIL with self-signed certificate error."
  echo "   Application reverse proxy tunnel is MANDATORY on this network."
else
  echo "✅ Ingest DNS resolved: ${RESOLVED_IPS:-none}"
fi
echo ""

echo "Testing HTTP POST to application reverse proxy tunnel..."
SAMPLE_HEADER="{\"dsn\":\"https://public@o0.ingest.sentry.io/${PROJECT_ID}\"}"
SAMPLE_PAYLOAD="${SAMPLE_HEADER}\n{\"type\":\"event\"}\n{}"

HTTP_CODE=$(curl -s -o /tmp/tunnel_res.txt -w "%{http_code}" \
  -X POST \
  -H "Content-Type: application/x-sentry-envelope" \
  -d "${SAMPLE_PAYLOAD}" \
  "${TUNNEL_URL}" || echo "000")

echo "Tunnel HTTP response code: ${HTTP_CODE}"

if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "202" || "${HTTP_CODE}" == "400" || "${HTTP_CODE}" == "403" ]]; then
  echo "✅ Application reverse proxy tunnel route is REACHABLE and responsive (Status: ${HTTP_CODE})."
  cat /tmp/tunnel_res.txt 2>/dev/null || true
  rm -f /tmp/tunnel_res.txt
else
  echo "❌ Tunnel endpoint failed with HTTP ${HTTP_CODE}."
  cat /tmp/tunnel_res.txt 2>/dev/null || true
  rm -f /tmp/tunnel_res.txt
  exit 1
fi

#!/usr/bin/env bash
# verify-deploy.sh — prove a Coolify deploy actually ran (not just got queued).
#
# Polls the resource until Coolify reports running:healthy (or times out), then
# optionally probes an endpoint for a 2xx. A create/deploy API 201 does NOT mean
# the container is up — this closes that gap.
#
# Usage: verify-deploy.sh --uuid RESOURCE_UUID [--url URL] [--header 'K: V']...
#                         [--timeout SECONDS] [--token TOKEN] [--base-url URL]
#
# Auth: $COOLIFY_CLOUD_API_TOKEN (or --token)   Base: $COOLIFY_BASE_URL (default app.coolify.io)
set -euo pipefail

BASE_URL="${COOLIFY_BASE_URL:-https://app.coolify.io}"
TOKEN="${COOLIFY_CLOUD_API_TOKEN:-}"
UUID="" URL="" TIMEOUT=180
HEADERS=()

usage() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --uuid)     UUID="$2"; shift 2;;
    --url)      URL="$2"; shift 2;;
    --header)   HEADERS+=("$2"); shift 2;;
    --timeout)  TIMEOUT="$2"; shift 2;;
    --token)    TOKEN="$2"; shift 2;;
    --base-url) BASE_URL="$2"; shift 2;;
    -h|--help)  usage 0;;
    *) echo "unknown arg: $1" >&2; usage 1;;
  esac
done

[ -n "$TOKEN" ] || { echo "error: no token (set COOLIFY_CLOUD_API_TOKEN or --token)" >&2; exit 1; }
[ -n "$UUID" ]  || { echo "error: --uuid is required" >&2; usage 1; }
command -v curl >/dev/null    || { echo "error: curl not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "error: python3 not found" >&2; exit 1; }

status_of() {
  curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/resources" \
    | python3 -c "import json,sys
u=sys.argv[1]
try: rows=json.load(sys.stdin)
except Exception: print('?'); sys.exit()
for r in rows:
    if r.get('uuid')==u: print(r.get('status','?')); break
else: print('not-found')" "$UUID"
}

echo "→ polling resource $UUID for running:healthy (timeout ${TIMEOUT}s)"
DEADLINE=$(( $(date +%s) + TIMEOUT ))
LAST=""
while :; do
  ST="$(status_of || echo '?')"
  [ "$ST" != "$LAST" ] && { echo "  status: $ST"; LAST="$ST"; }
  case "$ST" in
    running:healthy) echo "✔ Coolify reports running:healthy"; break;;
    exited|*:unhealthy) echo "✗ deploy is $ST — check: docker ps -a && docker logs <container>" >&2; exit 1;;
  esac
  [ "$(date +%s)" -lt "$DEADLINE" ] || { echo "✗ timed out after ${TIMEOUT}s (last status: $ST)" >&2; exit 1; }
  sleep 4
done

if [ -n "$URL" ]; then
  echo "→ probing $URL"
  args=(-s -o /dev/null -w '%{http_code}')
  for h in "${HEADERS[@]:-}"; do [ -n "$h" ] && args+=(-H "$h"); done
  CODE="$(curl "${args[@]}" "$URL" || echo 000)"
  echo "  HTTP $CODE"
  case "$CODE" in
    2*) echo "✔ endpoint returned $CODE — deploy verified end-to-end";;
    *)  echo "✗ endpoint returned $CODE (container may be up but the app isn't serving)" >&2; exit 1;;
  esac
fi

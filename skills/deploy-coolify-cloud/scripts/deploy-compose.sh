#!/usr/bin/env bash
# deploy-compose.sh — create or update a Coolify docker-compose service via the API.
#
# The `coolify` CLI cannot create/edit services; this wraps the raw REST calls,
# base64-encodes the compose (required), and triggers instant_deploy.
#
# CREATE:  --compose FILE --name NAME --server UUID --project UUID --env UUID
# UPDATE:  --compose FILE --service UUID
#
# Auth:    $COOLIFY_CLOUD_API_TOKEN  (or --token)
# Base:    $COOLIFY_BASE_URL         (or --base-url; default https://app.coolify.io)
#
# NOTE: a 201/200 means the deploy job was QUEUED, not that the container is up.
#       Verify with verify-deploy.sh afterwards.
set -euo pipefail

# Auto-load the durable token file if present (see references/token-setup.md).
[ -f "$HOME/.config/coolify-cloud.env" ] && source "$HOME/.config/coolify-cloud.env"

BASE_URL="${COOLIFY_BASE_URL:-https://app.coolify.io}"
TOKEN="${COOLIFY_CLOUD_API_TOKEN:-}"
COMPOSE="" NAME="" SERVER="" PROJECT="" ENV_UUID="" SERVICE="" DESCRIPTION="" DEPLOY=true

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --compose)   COMPOSE="$2"; shift 2;;
    --name)      NAME="$2"; shift 2;;
    --server)    SERVER="$2"; shift 2;;
    --project)   PROJECT="$2"; shift 2;;
    --env)       ENV_UUID="$2"; shift 2;;
    --service)   SERVICE="$2"; shift 2;;
    --description) DESCRIPTION="$2"; shift 2;;
    --token)     TOKEN="$2"; shift 2;;
    --base-url)  BASE_URL="$2"; shift 2;;
    --no-deploy) DEPLOY=false; shift;;
    -h|--help)   usage 0;;
    *) echo "unknown arg: $1" >&2; usage 1;;
  esac
done

[ -n "$TOKEN" ]   || { echo "error: no token (set COOLIFY_CLOUD_API_TOKEN or --token)" >&2; exit 1; }
[ -n "$COMPOSE" ] || { echo "error: --compose FILE is required" >&2; usage 1; }
[ -f "$COMPOSE" ] || { echo "error: compose file not found: $COMPOSE" >&2; exit 1; }
command -v curl >/dev/null    || { echo "error: curl not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "error: python3 not found" >&2; exit 1; }

# Portable base64 (GNU wraps at 76 cols, macOS doesn't; strip newlines either way).
B64="$(base64 < "$COMPOSE" | tr -d '\n')"

if [ -n "$SERVICE" ]; then
  METHOD="PATCH"; URL="$BASE_URL/api/v1/services/$SERVICE"
  BODY="$(python3 -c "import json,sys; print(json.dumps({'docker_compose_raw':sys.argv[1],'instant_deploy':$( $DEPLOY && echo True || echo False )}))" "$B64")"
  echo "→ updating service $SERVICE"
else
  for req in NAME SERVER PROJECT ENV_UUID; do
    [ -n "${!req}" ] || { echo "error: create mode needs --name --server --project --env (missing $req)" >&2; exit 1; }
  done
  METHOD="POST"; URL="$BASE_URL/api/v1/services"
  BODY="$(python3 -c "
import json,sys
b64,name,server,project,env,desc,deploy = sys.argv[1:8]
p={'project_uuid':project,'environment_uuid':env,'server_uuid':server,'name':name,
   'docker_compose_raw':b64,'instant_deploy':deploy=='true'}
if desc: p['description']=desc
print(json.dumps(p))" "$B64" "$NAME" "$SERVER" "$PROJECT" "$ENV_UUID" "$DESCRIPTION" "$($DEPLOY && echo true || echo false)")"
  echo "→ creating service '$NAME' on server $SERVER"
fi

HTTP_CODE="$(curl -s -o /tmp/coolify-deploy-resp.$$ -w '%{http_code}' \
  -X "$METHOD" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data "$BODY" "$URL")"
RESP="$(cat /tmp/coolify-deploy-resp.$$)"; rm -f /tmp/coolify-deploy-resp.$$

echo "HTTP $HTTP_CODE"
echo "$RESP" | python3 -m json.tool 2>/dev/null || echo "$RESP"

case "$HTTP_CODE" in
  200|201)
    UUID="$(echo "$RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null || true)"
    echo ""
    echo "✔ request accepted — but this only means the deploy job was QUEUED."
    echo "  Verify the container actually came up:"
    echo "    scripts/verify-deploy.sh --uuid ${UUID:-<service-uuid>} --url http://127.0.0.1:<port>/<route>"
    ;;
  *) echo "" >&2; echo "✗ request failed (HTTP $HTTP_CODE) — see body above." >&2; exit 1;;
esac

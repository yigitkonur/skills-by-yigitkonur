#!/usr/bin/env bash
# set-domain.sh — pin a custom domain (+ Let's Encrypt TLS) on a Coolify compose service.
#
# Coolify auto-assigns a *.sslip.io domain on create. This sets YOUR domain by writing
# the sub-service's fqdn via the `urls` field — the only field that works (`domains`/`fqdn`
# are rejected). Triggers a redeploy so Traefik labels + the cert request regenerate.
#
#   --service UUID   the service uuid
#   --name NAME      the compose service key (e.g. litellm, langfuse-web)
#   --url URL        full URL with scheme (https://llm.example.com)
#   --no-override    omit force_domain_override (default: send it, to reclaim the sslip domain)
#   --no-deploy      set the domain but don't redeploy (nothing routes until you do)
#
# Auth: $COOLIFY_CLOUD_API_TOKEN (or --token). Base: $COOLIFY_BASE_URL (or --base-url).
#
# DNS for URL must already resolve to the server IP, or the Let's Encrypt HTTP-01 challenge
# (port 80) fails silently and Traefik serves a default cert. See domains-and-networking.md.
set -euo pipefail

BASE_URL="${COOLIFY_BASE_URL:-https://app.coolify.io}"
TOKEN="${COOLIFY_CLOUD_API_TOKEN:-}"
SERVICE="" NAME="" URL="" OVERRIDE=true DEPLOY=true

usage() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --service)   SERVICE="$2"; shift 2;;
    --name)      NAME="$2"; shift 2;;
    --url)       URL="$2"; shift 2;;
    --no-override) OVERRIDE=false; shift;;
    --no-deploy) DEPLOY=false; shift;;
    --token)     TOKEN="$2"; shift 2;;
    --base-url)  BASE_URL="$2"; shift 2;;
    -h|--help)   usage 0;;
    *) echo "unknown arg: $1" >&2; usage 1;;
  esac
done

[ -n "$TOKEN" ]   || { echo "error: no token (set COOLIFY_CLOUD_API_TOKEN or --token)" >&2; exit 1; }
for req in SERVICE NAME URL; do
  [ -n "${!req}" ] || { echo "error: --service --name --url are required (missing $req)" >&2; usage 1; }
done
command -v curl >/dev/null    || { echo "error: curl not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "error: python3 not found" >&2; exit 1; }

# Warn (don't block) if DNS doesn't resolve yet — the cert needs it before deploy.
HOST="${URL#*://}"; HOST="${HOST%%/*}"
if command -v getent >/dev/null && ! getent hosts "$HOST" >/dev/null 2>&1; then
  echo "warning: $HOST does not resolve yet — Let's Encrypt HTTP-01 will fail until DNS points at the server." >&2
fi

BODY="$(python3 -c "
import json,sys
name,url,override,deploy = sys.argv[1:5]
p={'urls':[{'name':name,'url':url}],'instant_deploy':deploy=='true'}
if override=='true': p['force_domain_override']=True
print(json.dumps(p))" "$NAME" "$URL" "$($OVERRIDE && echo true || echo false)" "$($DEPLOY && echo true || echo false)")"

echo "→ setting $NAME -> $URL on service $SERVICE"
HTTP_CODE="$(curl -s -o /tmp/coolify-domain-resp.$$ -w '%{http_code}' \
  -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  --data "$BODY" "$BASE_URL/api/v1/services/$SERVICE")"
RESP="$(cat /tmp/coolify-domain-resp.$$)"; rm -f /tmp/coolify-domain-resp.$$

echo "HTTP $HTTP_CODE"
echo "$RESP" | python3 -m json.tool 2>/dev/null || echo "$RESP"

case "$HTTP_CODE" in
  200|201)
    echo ""
    if $DEPLOY; then
      echo "✔ domain stored + redeploy queued. TLS takes ~30–60s (HTTP-01 on :80). Verify the cert issued:"
      echo "    echo | openssl s_client -connect ${HOST}:443 -servername ${HOST} 2>/dev/null | openssl x509 -noout -issuer -dates"
    else
      echo "✔ domain stored (no redeploy). Nothing routes until you redeploy — re-run without --no-deploy, or PATCH the service with instant_deploy:true."
    fi
    ;;
  *) echo "" >&2; echo "✗ request failed (HTTP $HTTP_CODE) — see body above." >&2; exit 1;;
esac

#!/usr/bin/env bash
# auto-update-service.sh — update a registry-backed Coolify service to its latest image.
#
# Pulls IMAGE; if the running container's image differs, triggers a Coolify redeploy
# (Coolify recreates the container with correct labels/networks) and waits for healthy.
# Compares image IDs, so an unchanged image causes NO redeploy (no needless restart).
#
#   --image REF        registry image, e.g. vendor/app:latest        (required)
#   --container NAME    running container name to compare against     (required)
#   --uuid UUID         Coolify service/resource uuid to redeploy     (required)
#   --timeout SECONDS   wait for healthy after redeploy (default 180)
#   --base-url URL      Coolify base (default $COOLIFY_BASE_URL or app.coolify.io)
#
# Auth: $COOLIFY_CLOUD_API_TOKEN. Source ~/.config/coolify-cloud.env before running,
# or run under a systemd unit / launchd agent that sources it (see auto-update.md).
set -euo pipefail

[ -f "$HOME/.config/coolify-cloud.env" ] && source "$HOME/.config/coolify-cloud.env"
BASE_URL="${COOLIFY_BASE_URL:-https://app.coolify.io}"
TOKEN="${COOLIFY_CLOUD_API_TOKEN:-}"
IMAGE="" CONTAINER="" UUID="" TIMEOUT=180

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --image)     IMAGE="$2"; shift 2;;
    --container) CONTAINER="$2"; shift 2;;
    --uuid)      UUID="$2"; shift 2;;
    --timeout)   TIMEOUT="$2"; shift 2;;
    --base-url)  BASE_URL="$2"; shift 2;;
    -h|--help)   usage 0;;
    *) echo "unknown arg: $1" >&2; usage 1;;
  esac
done

for req in IMAGE CONTAINER UUID; do
  [ -n "${!req}" ] || { echo "error: --image --container --uuid are required (missing $req)" >&2; usage 1; }
done
[ -n "$TOKEN" ] || { echo "error: no token (source ~/.config/coolify-cloud.env)" >&2; exit 1; }
command -v docker >/dev/null || { echo "error: docker not found" >&2; exit 1; }
command -v curl >/dev/null   || { echo "error: curl not found" >&2; exit 1; }

log() { echo "[auto-update] $*"; }

running_id="$(docker inspect "$CONTAINER" --format '{{.Image}}' 2>/dev/null || echo none)"
log "pulling $IMAGE ..."
docker pull -q "$IMAGE" >/dev/null
latest_id="$(docker inspect "$IMAGE" --format '{{.Id}}')"

if [ "$running_id" = "$latest_id" ]; then
  log "already up to date ($running_id); nothing to do."
  exit 0
fi

log "new image: running=$running_id latest=$latest_id -> redeploy via Coolify"
curl -sf -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/deploy?uuid=$UUID&force=false" >/dev/null \
  || { echo "error: deploy trigger failed" >&2; exit 1; }
log "deploy queued; waiting up to ${TIMEOUT}s for running:healthy on the new image"

DEADLINE=$(( $(date +%s) + TIMEOUT ))
while :; do
  st="$(docker inspect "$CONTAINER" --format '{{.State.Status}}:{{.State.Health.Status}}' 2>/dev/null || echo 'gone:none')"
  now_id="$(docker inspect "$CONTAINER" --format '{{.Image}}' 2>/dev/null || echo none)"
  if [ "$st" = "running:healthy" ] && [ "$now_id" = "$latest_id" ]; then
    log "update complete: healthy on $latest_id"
    exit 0
  fi
  [ "$(date +%s)" -lt "$DEADLINE" ] || { echo "warning: not running:healthy on new image within ${TIMEOUT}s (last: $st) — check Coolify" >&2; exit 1; }
  sleep 5
done

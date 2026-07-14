#!/usr/bin/env bash
# setup-token.sh — store a Coolify Cloud API token securely and verify it.
#
# Prompts without echo (so it doesn't enter shell history), writes
# ~/.config/coolify-cloud.env with chmod 600, adds a source line to the user's
# shell rc, and verifies the token against the Coolify API.
set -euo pipefail

BASE_URL="${COOLIFY_BASE_URL:-https://app.coolify.io}"
ENV_FILE="$HOME/.config/coolify-cloud.env"

usage() {
  cat <<'USAGE'
setup-token.sh [--base-url URL]

Stores COOLIFY_CLOUD_API_TOKEN in ~/.config/coolify-cloud.env (chmod 600),
adds a guarded source line to your shell rc, and verifies API access.
USAGE
  exit "${1:-0}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2;;
    -h|--help) usage 0;;
    *) echo "unknown arg: $1" >&2; usage 1;;
  esac
done

command -v curl >/dev/null || { echo "error: curl not found" >&2; exit 1; }
mkdir -p "$HOME/.config"
umask 077

printf "Paste Coolify API token (input hidden): " >&2
IFS= read -rs TOKEN
printf "\n" >&2
[ -n "$TOKEN" ] || { echo "error: empty token" >&2; exit 1; }

TMP="$(mktemp)"
{
  printf 'export COOLIFY_CLOUD_API_TOKEN=%s\n' "$TOKEN"
  printf 'export COOLIFY_BASE_URL=%s\n' "$BASE_URL"
} > "$TMP"
chmod 600 "$TMP"
mv "$TMP" "$ENV_FILE"
chmod 600 "$ENV_FILE"

# Persist for new shells (bash/zsh/profile). fish users can source manually or translate.
case "$(basename "${SHELL:-}")" in
  zsh)  RC="$HOME/.zshrc" ;;
  bash) RC="$HOME/.bashrc" ;;
  *)    RC="$HOME/.profile" ;;
esac
LINE='[ -f "$HOME/.config/coolify-cloud.env" ] && source "$HOME/.config/coolify-cloud.env"  # Coolify Cloud API token'
touch "$RC"
if ! grep -qF "coolify-cloud.env" "$RC" 2>/dev/null; then
  printf '\n%s\n' "$LINE" >> "$RC"
  echo "added source line to $RC"
else
  echo "source line already present in $RC"
fi

HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/servers" || echo 000)"
if [ "$HTTP_CODE" = "200" ]; then
  echo "verified: API returned 200"
  echo "saved: $ENV_FILE"
  echo "next shell will load it automatically; for this shell: source $ENV_FILE"
else
  echo "warning: API verification returned HTTP $HTTP_CODE" >&2
  echo "saved the token anyway; if this is 401, re-mint with read/write/deploy scope." >&2
  exit 1
fi

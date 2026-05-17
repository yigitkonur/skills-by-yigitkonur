#!/usr/bin/env sh
set -eu

ROOT=${1:-.}

if [ ! -d "$ROOT" ]; then
  echo "error: project root not found: $ROOT" >&2
  exit 1
fi

cd "$ROOT"

env_files=""
for file in .env .env.local .env.development .env.production; do
  if [ -f "$file" ]; then
    env_files="$env_files $file"
  fi
done

has_file_var() {
  var=$1
  for file in $env_files; do
    if grep -q "^${var}=" "$file"; then
      return 0
    fi
  done
  return 1
}

has_process_var() {
  var=$1
  eval "test -n \"\${$var:-}\""
}

present_label() {
  var=$1
  if has_process_var "$var"; then
    echo "process env"
  elif has_file_var "$var"; then
    echo "env file"
  else
    echo "missing"
  fi
}

exists_any() {
  for candidate in "$@"; do
    if [ -e "$candidate" ]; then
      return 0
    fi
  done
  return 1
}

config_files=$(find tina -maxdepth 1 -type f \( -name 'config.ts' -o -name 'config.tsx' -o -name 'config.js' -o -name 'config.jsx' \) 2>/dev/null || true)

cloud_score=0
self_score=0

if has_process_var NEXT_PUBLIC_TINA_CLIENT_ID || has_file_var NEXT_PUBLIC_TINA_CLIENT_ID; then cloud_score=$((cloud_score + 1)); fi
if has_process_var TINA_TOKEN || has_file_var TINA_TOKEN; then cloud_score=$((cloud_score + 1)); fi
if [ -n "$config_files" ] && grep -q 'clientId\|token' $config_files 2>/dev/null; then cloud_score=$((cloud_score + 1)); fi

if has_process_var TINA_PUBLIC_IS_LOCAL || has_file_var TINA_PUBLIC_IS_LOCAL; then self_score=$((self_score + 1)); fi
if has_process_var NEXTAUTH_SECRET || has_file_var NEXTAUTH_SECRET; then self_score=$((self_score + 1)); fi
if has_process_var GITHUB_PERSONAL_ACCESS_TOKEN || has_file_var GITHUB_PERSONAL_ACCESS_TOKEN; then self_score=$((self_score + 1)); fi
if has_process_var MONGODB_URI || has_file_var MONGODB_URI; then self_score=$((self_score + 1)); fi
if exists_any app/api/tina src/app/api/tina pages/api/tina src/pages/api/tina tina/database.ts tina/database.js; then self_score=$((self_score + 1)); fi
if [ -n "$config_files" ] && grep -q 'contentApiUrlOverride\|authProvider' $config_files 2>/dev/null; then self_score=$((self_score + 1)); fi

echo "TinaCMS env and lane check"
echo "root: $(pwd)"
echo ""

echo "Env files:${env_files:- (none found)}"
echo ""

echo "Common TinaCloud vars"
for var in NEXT_PUBLIC_TINA_CLIENT_ID TINA_TOKEN NEXT_PUBLIC_TINA_BRANCH; do
  echo "- $var: $(present_label "$var")"
done
echo ""

echo "Common self-hosted vars"
for var in TINA_PUBLIC_IS_LOCAL NEXTAUTH_SECRET GITHUB_OWNER GITHUB_REPO GITHUB_BRANCH GITHUB_PERSONAL_ACCESS_TOKEN KV_REST_API_URL KV_REST_API_TOKEN MONGODB_URI CLERK_SECRET TINA_PUBLIC_CLERK_PUBLIC_KEY TINA_PUBLIC_ALLOWED_EMAIL; do
  echo "- $var: $(present_label "$var")"
done
echo ""

echo "Local files"
echo "- tina/config.*: $([ -n "$config_files" ] && echo yes || echo no)"
echo "- tina/database.*: $(exists_any tina/database.ts tina/database.js && echo yes || echo no)"
echo "- generated client: $(exists_any tina/__generated__/client.ts tina/__generated__/client.js .tina/__generated__/client.ts .tina/__generated__/client.js && echo yes || echo no)"
echo "- admin route: $(exists_any app/admin src/app/admin pages/admin src/pages/admin && echo yes || echo no)"
echo "- preview route: $(exists_any app/api/preview/route.ts src/app/api/preview/route.ts pages/api/preview.ts src/pages/api/preview.ts && echo yes || echo no)"
echo "- proxy.ts: $(exists_any proxy.ts src/proxy.ts && echo yes || echo no)"
echo "- middleware.ts: $(exists_any middleware.ts src/middleware.ts && echo yes || echo no)"
echo "- self-hosted tina API route: $(exists_any app/api/tina src/app/api/tina pages/api/tina src/pages/api/tina && echo yes || echo no)"
echo ""

if [ "$self_score" -gt "$cloud_score" ]; then
  echo "Likely lane: self-hosted"
  echo "Read: references/self-hosted/00-overview.md and references/deployment/02-vercel-self-hosted.md"
elif [ "$cloud_score" -gt 0 ]; then
  echo "Likely lane: TinaCloud"
  echo "Read: references/tinacloud/01-overview.md and references/deployment/01-vercel-tinacloud.md"
else
  echo "Likely lane: unknown"
  echo "Default greenfield route: TinaCloud unless auth/storage/network constraints require self-hosting"
fi

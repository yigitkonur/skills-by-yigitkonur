#!/usr/bin/env bash
set -euo pipefail

mode="explain"
run_whoami="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token)
      mode="token"
      shift
      ;;
    --whoami)
      run_whoami="1"
      shift
      ;;
    -h|--help)
      sed -n '1,160p' "$(dirname "$0")/check-npm-auth.md"
      exit 0
      ;;
    *)
      echo "ERROR unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$mode" != "token" ]]; then
  echo "This script validates token-auth wiring only."
  echo "It does not validate trusted publishing; OIDC auth applies only during npm publish."
  echo "Pass --token when token auth is intended."
  exit 0
fi

token_var=""
if [[ -n "${NODE_AUTH_TOKEN:-}" ]]; then
  token_var="NODE_AUTH_TOKEN"
elif [[ -n "${NPM_TOKEN:-}" ]]; then
  token_var="NPM_TOKEN"
  export NODE_AUTH_TOKEN="$NPM_TOKEN"
fi

if [[ -z "$token_var" ]]; then
  echo "ERROR neither NODE_AUTH_TOKEN nor NPM_TOKEN is set" >&2
  exit 1
fi

echo "Token variable present: $token_var"
echo "Token value: hidden"

if [[ "$run_whoami" == "1" ]]; then
  userconfig="$(mktemp)"
  trap 'rm -f "$userconfig"' EXIT
  printf '%s\n' '//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}' > "$userconfig"
  NPM_CONFIG_USERCONFIG="$userconfig" npm whoami --registry https://registry.npmjs.org
else
  echo "Skipped npm whoami. Pass --whoami to verify the token against npmjs.org."
fi

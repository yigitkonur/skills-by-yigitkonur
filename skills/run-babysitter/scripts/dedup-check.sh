#!/usr/bin/env bash
# dedup-check.sh — the "never open the same issue twice" gate (phase ⑤ ACT).
# Usage: dedup-check.sh "<issue title>" [agent_docs_dir]
# Prints exactly one verdict line to stdout:
#   CLEAR                  → safe to create the issue
#   DUPLICATE <ref>        → already exists (local ledger OR an open/closed remote issue)
#   BAIL <reason>          → the search could not run; the caller MUST NOT create
# Exit codes: CLEAR=0  DUPLICATE=10  BAIL=20
#
# Hard rule: a FAILED search returns BAIL, never CLEAR. Falling through to "create"
# on a failed lookup is the classic duplicate-cascade bug — do not do it.
set -uo pipefail

title="${1:-}"
agent_docs="${2:-.agent-docs}"

[ -z "$title" ] && { echo "BAIL no-title-given"; exit 20; }

# --- deterministic slug (the idempotency key) --------------------------------
slug="$(printf '%s' "$title" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' \
  | cut -c1-60)"
[ -z "$slug" ] && slug="untitled"

# --- 1) local ledger check ---------------------------------------------------
ledger="$agent_docs/issues/filed/$slug.md"
if [ -f "$ledger" ]; then
  echo "DUPLICATE local-ledger:$ledger"
  exit 10
fi

# --- 2) remote search (open AND closed) --------------------------------------
if ! command -v gh >/dev/null 2>&1; then echo "BAIL gh-not-installed"; exit 20; fi
if ! gh auth status >/dev/null 2>&1; then echo "BAIL gh-not-authenticated"; exit 20; fi

# keywords: significant words from the title (drop a leading "type:" prefix and
# short/stop words), OR-joined, capped at 6.
kw="$(printf '%s' "$title" \
  | sed -E 's/^[a-zA-Z]+:[[:space:]]*//' \
  | tr '[:upper:]' '[:lower:]' \
  | tr -cs 'a-z0-9' ' ')"
search="$(printf '%s\n' $kw \
  | awk 'length($0)>3 && $0 !~ /^(the|and|for|with|that|this|from|into|when|will|should|have|been)$/' \
  | head -6 | paste -sd'|' - | sed 's/|/ OR /g')"
[ -z "$search" ] && search="$title"

errf="$(mktemp)"
out="$(gh issue list --state all --search "$search" --json number,title,url,state --limit 10 2>"$errf")"
rc=$?
err="$(cat "$errf" 2>/dev/null)"; rm -f "$errf"
if [ $rc -ne 0 ]; then
  if printf '%s' "$err" | grep -qi 'disabled'; then
    echo "BAIL issues-disabled"
  else
    echo "BAIL search-failed:$(printf '%s' "$err" | head -1)"
  fi
  exit 20
fi

count="$(printf '%s' "$out" | jq 'length' 2>/dev/null)"
[[ "$count" =~ ^[0-9]+$ ]] || count=0
if [ "$count" -gt 0 ]; then
  url="$(printf '%s' "$out" | jq -r '.[0].url' 2>/dev/null)"
  echo "DUPLICATE remote:$url ($count match(es) for: $search)"
  exit 10
fi

echo "CLEAR"
exit 0

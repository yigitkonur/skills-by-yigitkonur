#!/usr/bin/env bash
# Generic GitHub Actions CI watcher for agent event streams (e.g. the Monitor tool).
# Emits ONE line per state change and ALWAYS terminates with CI-DONE <verdict>.
#
# Usage:  scripts/ci-watch.sh <sha> [max-minutes]
#
# Contract (every path terminates):
#   CI-RUN   <n> registered: <workflow>:<state> ...
#   CI-CHG   <workflow>: <old> -> <new>
#   CI-HB    <elapsed>/<max>m  (liveness; ~2.5min so the prompt cache stays warm)
#   CI-DONE  success | failure <workflow> | no-run | timeout | probe-dead
#
# Why each mechanism exists (each reproduced against real runs, 2026-07-28):
#   diff-gating      a 15-min run would otherwise emit ~40 identical tables and the
#                    Monitor auto-stops for volume, losing the feedback entirely
#   registration     a paths-filtered / deleted / branch-protected workflow registers
#   deadline         ZERO runs, so a watcher without this waits forever on nothing
#   SHA pinning      `--commit <sha>` catches ALL workflows for that commit and can
#                    never report a false green from a stale branch tip
#   error streak     transient API blips retry; a wedged endpoint exits loudly
set -uo pipefail

# Requires: gh (authenticated), jq. Override repo with CI_WATCH_REPO=org/name.

if (( $# == 0 )); then
  echo "CI-DONE probe-dead — usage: scripts/ci-watch.sh <sha> [max-minutes]"
  exit 0
fi
SHA_IN="$1"
# `gh run list --commit` silently returns ZERO results for a short SHA — which the
# registration deadline would then report as "no-run". Always normalize to 40 chars.
SHA="$(git rev-parse "$SHA_IN" 2>/dev/null || true)"
if [[ ! "$SHA" =~ ^[0-9a-fA-F]{40}$ ]]; then
  echo "CI-DONE probe-dead — could not resolve '${SHA_IN}' to a full 40-char SHA"
  exit 0
fi
MAX_MIN="${2:-30}"
POLL="${CI_WATCH_POLL:-20}"
REGISTER_DEADLINE="${CI_WATCH_REGISTER_DEADLINE:-240}"   # seconds to allow all runs to register
HB_EVERY="${CI_WATCH_HB:-150}"                            # heartbeat seconds (< 5min cache TTL)

for setting in MAX_MIN POLL REGISTER_DEADLINE HB_EVERY; do
  value="${!setting}"
  if [[ ! "$value" =~ ^[1-9][0-9]*$ ]]; then
    echo "CI-DONE probe-dead — ${setting} must be a positive integer (got '${value}')"
    exit 0
  fi
done

if [[ -n "${CI_WATCH_REPO:-}" ]]; then
  REPO="$CI_WATCH_REPO"
elif ! REPO="$(timeout 15 gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)" || [[ -z "$REPO" ]]; then
  echo "CI-DONE probe-dead — could not discover repository within 15s; set CI_WATCH_REPO=org/name"
  exit 0
fi

# Uses whatever identity `gh` is already authenticated as. Set GH_TOKEN yourself
# if the repo needs a specific account.

start=$(date +%s)
deadline=$(( start + MAX_MIN * 60 ))
registration_end=$(( start + REGISTER_DEADLINE ))
last_hb=$start
declare -A seen
registered=0
errors=0

probe() {
  # Per-probe timeout: a wedged request can never freeze the loop. The explicit limit
  # avoids silently ignoring runs beyond gh's default page of 20.
  timeout 25 gh run list -R "$REPO" --commit "$SHA" --limit 1000 \
    --json databaseId,workflowName,status,conclusion 2>/dev/null
}

while :; do
  now=$(date +%s)

  if (( now > deadline )); then
    echo "CI-DONE timeout — ${MAX_MIN}m elapsed; gh run list -R ${REPO} --commit ${SHA}"
    exit 0
  fi

  if ! json="$(probe)"; then
    errors=$(( errors + 1 ))
    if (( errors == 3 )); then echo "CI-WARN api errors x3 (still retrying)"; fi
    if (( errors >= 10 )); then
      echo "CI-DONE probe-dead — 10 consecutive API failures"
      exit 0
    fi
    sleep "$POLL"; continue
  fi
  errors=0

  count="$(jq 'length' <<<"$json")"

  # --- registration deadline -------------------------------------------------
  # Do not issue a terminal verdict until the registration window closes. A fast first
  # workflow can finish before a later workflow appears for the same commit.
  if (( count == 0 )); then
    if (( now >= registration_end )); then
      echo "CI-DONE no-run — no workflow registered for ${SHA:0:8} in $(( REGISTER_DEADLINE / 60 ))m"
      echo "        (expected when the push only touched paths-ignore'd files)"
      exit 0
    fi
    if (( now - last_hb >= HB_EVERY )); then
      echo "CI-HB   $(( (now-start)/60 ))/${MAX_MIN}m awaiting registration"
      last_hb=$now
    fi
    sleep "$POLL"; continue
  fi

  if (( registered == 0 )); then
    registered=1
    echo "CI-RUN  ${count} registered: $(jq -r '[.[]|"\(.workflowName):\(.status)"]|join(" · ")' <<<"$json")"
  fi

  # --- diff-gated state changes ---------------------------------------------
  while IFS=$'\t' read -r id name state concl; do
    [[ -z "$id" ]] && continue
    cur="${state}${concl:+/$concl}"
    if [[ "${seen[$id]:-}" != "$cur" ]]; then
      [[ -n "${seen[$id]:-}" ]] && echo "CI-CHG  ${name} (#${id}): ${seen[$id]} -> ${cur}"
      seen[$id]="$cur"
    fi
  done < <(jq -r '.[]|[.databaseId,.workflowName,.status,(.conclusion//"")]|@tsv' <<<"$json")

  # --- terminal verdict ------------------------------------------------------
  pending="$(jq '[.[]|select(.status!="completed")]|length' <<<"$json")"
  if (( now >= registration_end && pending == 0 )); then
    bad="$(jq -r '[.[]|select(.conclusion!="success" and .conclusion!="skipped")|.workflowName]|join(",")' <<<"$json")"
    if [[ -n "$bad" ]]; then
      rid="$(jq -r '[.[]|select(.conclusion!="success" and .conclusion!="skipped")][0].databaseId' <<<"$json")"
      echo "CI-DONE failure ${bad} — gh run view ${rid} -R ${REPO} --log-failed"
    else
      echo "CI-DONE success — all ${count} workflow(s) green on ${SHA:0:8}"
    fi
    exit 0
  fi

  if (( now - last_hb >= HB_EVERY )); then
    echo "CI-HB   $(( (now-start)/60 ))/${MAX_MIN}m $(jq -r '[.[]|"\(.workflowName):\(.status)"]|join(" · ")' <<<"$json")"
    last_hb=$now
  fi

  sleep "$POLL"
done

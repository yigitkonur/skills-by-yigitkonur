#!/usr/bin/env bash
# ci-watch.sh — non-blocking GitHub Actions watcher for autonomous agents.
#
#   bash ci-watch.sh <pinned-sha> [branch] [deadline-min]
#
# Emits ONE line per state change plus periodic liveness, and guarantees a
# terminal `CI-DONE <verdict>` on every exit path. Silence past the deadline
# is structurally impossible. Arm it with a streaming-notification facility
# (in Claude Code, the Monitor tool) and keep working.
#
# WHY NOT `gh run watch`: it redraws a TTY block on an interval, so piped into
# a line consumer every redraw is a duplicate notification; it also follows a
# single run, missing a second failing workflow for the same commit; and it
# has no registration deadline (cli/cli #6448/#6560/#8194).
# WHY NOT a success-only poll loop: a failed run and a running run both fail
# the grep, so it never exits and never reports the failure.
#
# Provider-neutral in shape: to target another CI, keep the event contract and
# replace only the `gh run list --commit` probe with one that prints
# "<name>: <state>" lines for the pinned identifier.
#
# Requires: gh (authenticated) + jq. Override repo with CI_WATCH_REPO=org/name.
set -uo pipefail

SHA="${1:?usage: ci-watch.sh <pinned-sha> [branch] [deadline-min]}"
BRANCH="${2:-}"
DEADLINE_MIN="${3:-20}"
REPO="${CI_WATCH_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null)}"
INTERVAL="${CI_WATCH_INTERVAL:-20}"
HB_SEC="${CI_WATCH_HB:-150}"          # < a typical 300s prompt-cache TTL
REG_MIN="${CI_WATCH_REG_MIN:-4}"      # give up if nothing registers
PROBE_CAP="${CI_WATCH_PROBE_CAP:-45}" # per-probe timeout

[ -n "$REPO" ] || { echo "CI-DONE probe-dead — set CI_WATCH_REPO=org/name"; exit 1; }

start=$SECONDS
deadline_sec=$(( ${DEADLINE_MIN%.*} * 60 ))
prev=""
registered=0
last_emit=$SECONDS
errs=0
emit() { printf '%s\n' "$*"; last_emit=$SECONDS; }
timeout_if_elapsed() {
  elapsed=$(( SECONDS - start ))
  if [ "$elapsed" -ge "$deadline_sec" ]; then
    emit "CI-DONE timeout at ${DEADLINE_MIN}m — last: ${prev:-nothing registered}"
    exit 124
  fi
}
bounded_sleep() {
  timeout_if_elapsed
  remaining=$(( deadline_sec - elapsed ))
  sleep_for=$INTERVAL
  [ "$sleep_for" -gt "$remaining" ] && sleep_for=$remaining
  sleep "$sleep_for"
}

while :; do
  timeout_if_elapsed
  remaining=$(( deadline_sec - elapsed ))
  probe_cap=$PROBE_CAP
  [ "$probe_cap" -gt "$remaining" ] && probe_cap=$remaining

  if ! snap=$(timeout "$probe_cap" gh run list --repo "$REPO" --commit "$SHA" --limit 1000 \
        --json databaseId,workflowName,status,conclusion 2>/dev/null); then
    timeout_if_elapsed
    errs=$(( errs + 1 ))
    [ "$errs" -eq 3 ] && emit "CI-ERR probe failing (3x consecutive)"
    [ "$errs" -ge 10 ] && { emit "CI-DONE probe-dead after 10 consecutive errors"; exit 1; }
    bounded_sleep; continue
  fi
  errs=0

  count=$(jq 'length' <<<"$snap")
  state=$(jq -r '.[] | "\(.workflowName): \(.status)\(if .conclusion != "" and .conclusion != null then " -> "+.conclusion else "" end)"' <<<"$snap" | sort)

  if [ "$count" -eq 0 ]; then
    if [ "$registered" -eq 0 ] && [ "$elapsed" -gt $(( ${REG_MIN%.*} * 60 )) ]; then
      emit "CI-DONE no-run — nothing registered for ${SHA:0:9} in ${REG_MIN}m (path filter? wrong sha? docs-only push?)"
      exit 1
    fi
    bounded_sleep; continue
  fi

  if [ "$registered" -eq 0 ]; then
    registered=1
    emit "CI-RUN registered ${count}: $(tr '\n' '|' <<<"$state" | sed 's/|$//; s/|/ · /g')"
    prev="$state"
  elif [ "$state" != "$prev" ]; then
    while IFS= read -r line; do
      [ -n "$line" ] && emit "CI-CHG $line"
    done < <(comm -13 <(printf '%s\n' "$prev") <(printf '%s\n' "$state"))
    prev="$state"
  fi

  # Terminal: every workflow for the SHA completed.
  if jq -e 'length > 0 and all(.status == "completed")' <<<"$snap" >/dev/null; then
    bad=$(jq -r '[.[] | select((.conclusion // "") | IN("success","skipped","neutral") | not) | .workflowName] | join(", ")' <<<"$snap")
    if [ -z "$bad" ]; then
      emit "CI-DONE success (${count} workflows) · $(( SECONDS - start ))s"
      exit 0
    fi
    # A superseding push makes the concurrency group auto-cancel the older run.
    # `cancelled` is NOT a failure; reporting it as red sends the agent chasing
    # a phantom break. When every non-green conclusion is `cancelled`, report
    # cancelled/superseded regardless of whether a branch was supplied — only
    # a genuine failure/timeout/etc. is red.
    genuine=$(jq -r '[.[] | select((.conclusion // "") | IN("success","skipped","neutral","cancelled") | not) | .workflowName] | join(", ")' <<<"$snap")
    if [ -z "$genuine" ]; then
      newest=""
      if [ -n "$BRANCH" ]; then
        newest=$(timeout 20 gh run list --repo "$REPO" --branch "$BRANCH" --limit 1 \
                  --json headSha --jq '.[0].headSha // empty' 2>/dev/null || true)
        [ "$newest" = "$SHA" ] && newest=""
      fi
      if [ -n "$newest" ]; then
        emit "CI-DONE superseded by ${newest:0:9} (auto-cancelled: ${bad}) — arm a fresh watch"
      else
        emit "CI-DONE cancelled — ${bad} (superseded or manually cancelled; not a build failure) — re-check or re-push"
      fi
      exit 0
    fi
    id=$(jq -r '[.[] | select((.conclusion // "") | IN("success","skipped","neutral","cancelled") | not)][0].databaseId // empty' <<<"$snap")
    emit "CI-DONE failure — ${genuine}${id:+ — gh run view $id --repo $REPO --log-failed}"
    exit 1
  fi

  if [ "$HB_SEC" -gt 0 ] && [ $(( SECONDS - last_emit )) -ge "$HB_SEC" ]; then
    emit "CI-HB $(( elapsed / 60 ))/${DEADLINE_MIN}m · $(tr '\n' '|' <<<"$prev" | sed 's/|$//; s/|/ · /g')"
  fi
  bounded_sleep
done

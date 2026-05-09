#!/usr/bin/env bash
# Reports computed status for a GitHub Issue tree.
# Usage: issue-tree-status.sh OWNER/REPO ROOT_ISSUE
set -euo pipefail

usage() {
  echo "Usage: issue-tree-status.sh OWNER/REPO ROOT_ISSUE" >&2
  echo "       issue-tree-status.sh --repo OWNER/REPO --root ROOT_ISSUE" >&2
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

REPO=""
ROOT=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --root)
      ROOT="${2:-}"
      shift 2
      ;;
    -*)
      usage
      exit 1
      ;;
    *)
      if [ -z "$REPO" ]; then
        REPO="$1"
      elif [ -z "$ROOT" ]; then
        ROOT="$1"
      else
        usage
        exit 1
      fi
      shift
      ;;
  esac
done

if [ -z "$REPO" ] || [ -z "$ROOT" ]; then
  usage
  exit 1
fi

command -v gh >/dev/null || { echo "ERROR: gh CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ISSUES="$TMP_DIR/issues.jsonl"
EDGES="$TMP_DIR/edges.tsv"
SEEN="$TMP_DIR/seen.txt"
STALE="$TMP_DIR/stale.txt"
: > "$ISSUES"
: > "$EDGES"
: > "$SEEN"
: > "$STALE"

api() {
  gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2026-03-10" \
    "$@"
}

collect_issue() {
  local issue="$1"
  local parent="${2:-}"
  local issue_json children child reported_parent

  if grep -qx "$issue" "$SEEN"; then
    return
  fi

  issue_json=$(api "repos/$REPO/issues/$issue") || {
    echo "ERROR: could not fetch #$issue" >&2
    exit 1
  }

  echo "$issue" >> "$SEEN"
  printf '%s\n' "$issue_json" >> "$ISSUES"

  if [ -n "$parent" ]; then
    reported_parent=$(api "repos/$REPO/issues/$issue/parent" --jq '.number') || {
      echo "ERROR: could not fetch parent for #$issue" >&2
      exit 1
    }
    if [ "$reported_parent" != "$parent" ]; then
      printf '#%s reports parent #%s, expected #%s\n' "$issue" "$reported_parent" "$parent" >> "$STALE"
    fi
  fi

  children=$(api --paginate "repos/$REPO/issues/$issue/sub_issues" --jq '.[].number') || {
    echo "ERROR: could not list sub-issues for #$issue" >&2
    exit 1
  }

  for child in $children; do
    printf '%s\t%s\n' "$issue" "$child" >> "$EDGES"
    collect_issue "$child" "$issue"
  done
}

issue_value() {
  local issue="$1"
  local filter="$2"
  jq -r --argjson issue "$issue" "select(.number == \$issue) | $filter" "$ISSUES"
}

has_label() {
  local issue="$1"
  local label="$2"
  jq -e --argjson issue "$issue" --arg label "$label" \
    'select(.number == $issue) | any(.labels[].name; . == $label)' "$ISSUES" >/dev/null
}

wave_label() {
  local issue="$1"
  issue_value "$issue" '([.labels[].name | select(startswith("wave:"))][0] // "wave:unlabeled")'
}

wave_rank() {
  case "$1" in
    wave:0-foundation) echo 0 ;;
    wave:[0-9]*)
      echo "${1#wave:}"
      ;;
    *) echo 999 ;;
  esac
}

type_label() {
  local issue="$1"
  issue_value "$issue" '([.labels[].name | select(startswith("type:"))][0] // "type:unknown")'
}

blockers_for() {
  local issue="$1"
  local body line
  body=$(issue_value "$issue" '.body // ""')
  line=$(printf '%s\n' "$body" | grep -Ei '^[[:space:]]*-?[[:space:]]*\*\*Blocked by:\*\*' | head -1 || true)
  [ -z "$line" ] && return 0
  printf '%s\n' "$line" | grep -Eo '#[0-9]+' | tr -d '#' || true
}

state_for_issue() {
  local issue="$1"
  local state
  state=$(issue_value "$issue" '.state // empty')
  if [ -n "$state" ]; then
    echo "$state"
    return
  fi
  api "repos/$REPO/issues/$issue" --jq '.state' 2>/dev/null || echo "missing"
}

open_blockers_for() {
  local issue="$1"
  local blocker state
  for blocker in $(blockers_for "$issue"); do
    state=$(state_for_issue "$blocker")
    [ "$state" != "closed" ] && printf '#%s(%s) ' "$blocker" "$state"
  done
}

open_child_count() {
  local issue="$1"
  local child state count=0
  while IFS=$'\t' read -r parent child; do
    [ "$parent" = "$issue" ] || continue
    state=$(state_for_issue "$child")
    [ "$state" != "closed" ] && count=$((count + 1))
  done < "$EDGES"
  echo "$count"
}

child_count() {
  local issue="$1"
  awk -v issue="$issue" '$1 == issue { count++ } END { print count + 0 }' "$EDGES"
}

has_active_status() {
  local issue="$1"
  has_label "$issue" "status:in-progress" && return 0
  has_label "$issue" "status:blocked" && return 0
  has_label "$issue" "status:failed" && return 0
  has_label "$issue" "status:needs-review" && return 0
  return 1
}

is_ready_leaf() {
  local issue="$1"
  local state type blockers open_children
  state=$(state_for_issue "$issue")
  type=$(type_label "$issue")
  blockers=$(open_blockers_for "$issue")
  open_children=$(open_child_count "$issue")

  [ "$state" = "open" ] || return 1
  [ "$type" = "type:task" ] || [ "$type" = "type:subtask" ] || return 1
  [ "$open_children" = "0" ] || return 1
  [ -z "$blockers" ] || return 1
  ! has_active_status "$issue"
}

is_blocked_issue() {
  local issue="$1"
  local blockers
  blockers=$(open_blockers_for "$issue")
  [ -n "$blockers" ] && return 0
  has_label "$issue" "status:blocked"
}

is_parent_ready_to_close() {
  local issue="$1"
  local state children open_children
  state=$(state_for_issue "$issue")
  children=$(child_count "$issue")
  open_children=$(open_child_count "$issue")
  [ "$state" = "open" ] && [ "$children" -gt 0 ] && [ "$open_children" = "0" ]
}

print_issue_line() {
  local issue="$1"
  local title wave labels
  title=$(issue_value "$issue" '.title')
  wave=$(wave_label "$issue")
  labels=$(issue_value "$issue" '[.labels[].name] | join(", ")')
  printf -- '- #%s: %s (%s; %s)\n' "$issue" "$title" "$wave" "$labels"
}

collect_issue "$ROOT"

ROOT_TITLE=$(issue_value "$ROOT" '.title')
ROOT_STATE=$(issue_value "$ROOT" '.state')

WAVES_RAW="$TMP_DIR/waves.raw"
WAVES="$TMP_DIR/waves.txt"
jq -r '[.labels[].name | select(startswith("wave:"))][0] // "wave:unlabeled"' "$ISSUES" | sort -u > "$WAVES_RAW"
: > "$WAVES"
while IFS= read -r wave; do
  printf '%s\t%s\n' "$(wave_rank "$wave")" "$wave"
done < "$WAVES_RAW" | sort -n | cut -f2- > "$WAVES"

CURRENT_WAVE="none"
while IFS= read -r wave; do
  open_count=0
  for issue in $(jq -r '.number' "$ISSUES"); do
    [ "$(wave_label "$issue")" = "$wave" ] || continue
    [ "$(state_for_issue "$issue")" = "open" ] && open_count=$((open_count + 1))
  done
  if [ "$open_count" -gt 0 ]; then
    CURRENT_WAVE="$wave"
    break
  fi
done < "$WAVES"

echo "# Issue Tree Status"
echo ""
echo "- Root issue: #$ROOT - $ROOT_TITLE [$ROOT_STATE]"
echo "- Current wave: $CURRENT_WAVE"
echo "- Discovered waves: $(paste -sd ', ' "$WAVES")"
echo ""
echo "## Per-Wave Totals"
echo ""
echo "| Wave | Total | Closed | Open | Ready | Blocked | In Progress | Failed | Needs Review |"
echo "|---|---:|---:|---:|---:|---:|---:|---:|---:|"

while IFS= read -r wave; do
  total=0
  closed=0
  open=0
  ready=0
  blocked=0
  in_progress=0
  failed=0
  needs_review=0

  for issue in $(jq -r '.number' "$ISSUES"); do
    [ "$(wave_label "$issue")" = "$wave" ] || continue
    total=$((total + 1))
    [ "$(state_for_issue "$issue")" = "closed" ] && closed=$((closed + 1)) || open=$((open + 1))
    is_ready_leaf "$issue" && ready=$((ready + 1))
    is_blocked_issue "$issue" && blocked=$((blocked + 1))
    has_label "$issue" "status:in-progress" && in_progress=$((in_progress + 1))
    has_label "$issue" "status:failed" && failed=$((failed + 1))
    has_label "$issue" "status:needs-review" && needs_review=$((needs_review + 1))
  done

  printf '| %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' \
    "$wave" "$total" "$closed" "$open" "$ready" "$blocked" "$in_progress" "$failed" "$needs_review"
done < "$WAVES"

echo ""
echo "## Ready Leaf Issues"
echo ""
found=0
for issue in $(jq -r '.number' "$ISSUES"); do
  if is_ready_leaf "$issue"; then
    print_issue_line "$issue"
    found=1
  fi
done
[ "$found" = "0" ] && echo "none"

echo ""
echo "## Parent Closure Verification Queue"
echo ""
found=0
for issue in $(jq -r '.number' "$ISSUES"); do
  if is_parent_ready_to_close "$issue"; then
    print_issue_line "$issue"
    found=1
  fi
done
[ "$found" = "0" ] && echo "none"

echo ""
echo "## Blocked Issues"
echo ""
found=0
for issue in $(jq -r '.number' "$ISSUES"); do
  if is_blocked_issue "$issue" && [ "$(state_for_issue "$issue")" = "open" ]; then
    title=$(issue_value "$issue" '.title')
    blockers=$(open_blockers_for "$issue")
    [ -z "$blockers" ] && blockers="status:blocked label"
    printf -- '- #%s: %s - blocked by %s\n' "$issue" "$title" "$blockers"
    found=1
  fi
done
[ "$found" = "0" ] && echo "none"

echo ""
echo "## Failed Issues Awaiting Recovery"
echo ""
found=0
for issue in $(jq -r '.number' "$ISSUES"); do
  if has_label "$issue" "status:failed" && [ "$(state_for_issue "$issue")" = "open" ]; then
    print_issue_line "$issue"
    found=1
  fi
done
[ "$found" = "0" ] && echo "none"

echo ""
echo "## Stale Label Warnings"
echo ""
for issue in $(jq -r '.number' "$ISSUES"); do
  if has_label "$issue" "status:ready"; then
    blockers=$(open_blockers_for "$issue")
    open_children=$(open_child_count "$issue")
    if [ -n "$blockers" ]; then
      printf 'status:ready is stale on #%s; blocker reopened or remains open: %s\n' "$issue" "$blockers" >> "$STALE"
    fi
    if [ "$open_children" != "0" ]; then
      printf 'status:ready is stale on #%s; it still has %s open child issue(s)\n' "$issue" "$open_children" >> "$STALE"
    fi
  fi
  if has_label "$issue" "status:blocked" && [ -z "$(open_blockers_for "$issue")" ]; then
    printf 'status:blocked may be stale on #%s; no open blockers found in body\n' "$issue" >> "$STALE"
  fi
done

if [ -s "$STALE" ]; then
  sort -u "$STALE" | sed 's/^/- /'
else
  echo "none"
fi

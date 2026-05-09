#!/usr/bin/env bash
# Prepares prompt files and a manifest for ready issue-tree leaf issues.
# Usage: dispatch-wave.sh OWNER/REPO ROOT_ISSUE [--limit N] [--output-dir DIR] [--mark-in-progress]
set -euo pipefail

usage() {
  echo "Usage: dispatch-wave.sh OWNER/REPO ROOT_ISSUE [--limit N] [--output-dir DIR] [--mark-in-progress]" >&2
  echo "       dispatch-wave.sh --repo OWNER/REPO --root ROOT_ISSUE [--concurrency N]" >&2
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=""
ROOT=""
LIMIT="0"
OUTPUT_DIR=""
MARK_IN_PROGRESS=0

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
    --limit|--concurrency)
      LIMIT="${2:-}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --mark-in-progress)
      MARK_IN_PROGRESS=1
      shift
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

case "$LIMIT" in
  ''|*[!0-9]*)
    echo "ERROR: --limit/--concurrency must be a non-negative integer" >&2
    exit 1
    ;;
esac

command -v gh >/dev/null || { echo "ERROR: gh CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "ERROR: jq is required" >&2; exit 1; }

if [ -z "$OUTPUT_DIR" ]; then
  OUTPUT_DIR="./issue-tree-dispatch-$ROOT-$(date +%Y%m%d%H%M%S)"
fi

mkdir -p "$OUTPUT_DIR/prompts"
OUTPUT_DIR=$(cd "$OUTPUT_DIR" && pwd)

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ISSUES="$TMP_DIR/issues.jsonl"
EDGES="$TMP_DIR/edges.tsv"
SEEN="$TMP_DIR/seen.txt"
: > "$ISSUES"
: > "$EDGES"
: > "$SEEN"

api() {
  gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2026-03-10" \
    "$@"
}

collect_issue() {
  local issue="$1"
  local issue_json children child

  if grep -qx "$issue" "$SEEN"; then
    return
  fi

  issue_json=$(api "repos/$REPO/issues/$issue") || {
    echo "ERROR: could not fetch #$issue" >&2
    exit 1
  }

  echo "$issue" >> "$SEEN"
  printf '%s\n' "$issue_json" >> "$ISSUES"

  children=$(api --paginate "repos/$REPO/issues/$issue/sub_issues" --jq '.[].number') || {
    echo "ERROR: could not list sub-issues for #$issue" >&2
    exit 1
  }

  for child in $children; do
    printf '%s\t%s\n' "$issue" "$child" >> "$EDGES"
    collect_issue "$child"
  done
}

issue_value() {
  local issue="$1"
  local filter="$2"
  jq -r --argjson issue "$issue" "select(.number == \$issue) | $filter" "$ISSUES"
}

issue_json_value() {
  local issue="$1"
  local filter="$2"
  jq -c --argjson issue "$issue" "select(.number == \$issue) | $filter" "$ISSUES"
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
    [ "$state" != "closed" ] && printf '%s\n' "$blocker"
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
  local state type open_children
  state=$(state_for_issue "$issue")
  type=$(type_label "$issue")
  open_children=$(open_child_count "$issue")

  [ "$state" = "open" ] || return 1
  [ "$type" = "type:task" ] || [ "$type" = "type:subtask" ] || return 1
  [ "$open_children" = "0" ] || return 1
  [ -z "$(open_blockers_for "$issue")" ] || return 1
  ! has_active_status "$issue"
}

parent_for_issue() {
  local issue="$1"
  awk -v issue="$issue" '$2 == issue { print $1; found=1; exit } END { if (!found) print "root" }' "$EDGES"
}

json_array_from_lines() {
  if [ -t 0 ]; then
    jq -n '[]'
  else
    jq -R 'select(length > 0)' | jq -s .
  fi
}

collect_issue "$ROOT"

"$SCRIPT_DIR/issue-tree-status.sh" "$REPO" "$ROOT" > "$OUTPUT_DIR/status.md"

MANIFEST_JSONL="$TMP_DIR/manifest.jsonl"
: > "$MANIFEST_JSONL"

selected=0
for issue in $(jq -r '.number' "$ISSUES"); do
  if ! is_ready_leaf "$issue"; then
    continue
  fi
  if [ "$LIMIT" -gt 0 ] && [ "$selected" -ge "$LIMIT" ]; then
    continue
  fi

  selected=$((selected + 1))
  title=$(issue_value "$issue" '.title')
  body=$(issue_value "$issue" '.body // ""')
  wave=$(wave_label "$issue")
  labels_json=$(issue_json_value "$issue" '[.labels[].name]')
  parent=$(parent_for_issue "$issue")
  prompt_file="$OUTPUT_DIR/prompts/issue-$issue.md"
  blockers_json=$(blockers_for "$issue" | json_array_from_lines)

  {
    echo "# Execute #$issue: $title"
    echo ""
    echo "Repository: $REPO"
    echo "Issue: #$issue"
    echo "Wave: $wave"
    echo "Parent: $parent"
    echo ""
    echo "Use the current runtime's native subagent/task tool to execute this prompt. Do not treat gh CLI as the worker dispatch mechanism."
    echo ""
    echo "## Issue Body"
    echo ""
    printf '%s\n' "$body"
    echo ""
    echo "## Expected Completion Report Fields"
    echo ""
    echo "- issue_number"
    echo "- files_changed"
    echo "- commands_run"
    echo "- dod_evidence"
    echo "- deviations"
    echo "- remaining_risk"
  } > "$prompt_file"

  jq -n \
    --argjson issue_number "$issue" \
    --arg title "$title" \
    --arg wave "$wave" \
    --argjson labels "$labels_json" \
    --arg prompt_file "$prompt_file" \
    --argjson blockers "$blockers_json" \
    --arg parent "$parent" \
    '{
      issue_number: $issue_number,
      title: $title,
      wave: $wave,
      labels: $labels,
      prompt_file: $prompt_file,
      blockers: $blockers,
      parent: $parent,
      expected_completion_report_fields: [
        "issue_number",
        "files_changed",
        "commands_run",
        "dod_evidence",
        "deviations",
        "remaining_risk"
      ]
    }' >> "$MANIFEST_JSONL"

  if [ "$MARK_IN_PROGRESS" = "1" ]; then
    if has_label "$issue" "status:ready"; then
      gh issue edit "$issue" --repo "$REPO" --add-label "status:in-progress" --remove-label "status:ready" >/dev/null
    else
      gh issue edit "$issue" --repo "$REPO" --add-label "status:in-progress" >/dev/null
    fi
  fi
done

jq -s . "$MANIFEST_JSONL" > "$OUTPUT_DIR/manifest.json"

echo "Dispatch prep complete"
echo "- Status: $OUTPUT_DIR/status.md"
echo "- Manifest: $OUTPUT_DIR/manifest.json"
echo "- Prompt directory: $OUTPUT_DIR/prompts"
echo "- Ready issues selected: $selected"
if [ "$MARK_IN_PROGRESS" = "1" ]; then
  echo "- Label mutation: selected issues marked status:in-progress"
else
  echo "- Label mutation: none"
fi

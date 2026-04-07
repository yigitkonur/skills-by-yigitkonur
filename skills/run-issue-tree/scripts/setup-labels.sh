#!/usr/bin/env bash
# Creates the standard label set for wave-based issue planning.
# Usage: setup-labels.sh OWNER/REPO
# Set MAX_WAVE=N to create wave:1..wave:N labels (default 5).
set -euo pipefail

REPO="${1:?Usage: setup-labels.sh OWNER/REPO}"
MAX_WAVE="${MAX_WAVE:-5}"

command -v gh >/dev/null || { echo "ERROR: gh CLI is required" >&2; exit 1; }

case "$MAX_WAVE" in
  ''|*[!0-9]*)
    echo "ERROR: MAX_WAVE must be an integer >= 1" >&2
    exit 1
    ;;
esac

if [ "$MAX_WAVE" -lt 1 ]; then
  echo "ERROR: MAX_WAVE must be at least 1" >&2
  exit 1
fi

create_or_update_label() {
  local name="$1"
  local color="$2"
  local description="$3"

  gh label create "$name" --repo "$REPO" --color "$color" --description "$description" --force 2>/dev/null && echo "✓ $name" || echo "exists: $name"
}

wave_color() {
  case "$1" in
    1) echo "1D76DB" ;;
    2) echo "5319E7" ;;
    3) echo "B60205" ;;
    4) echo "D93F0B" ;;
    5) echo "E4E669" ;;
    6) echo "0E8A16" ;;
    7) echo "FBCA04" ;;
    8) echo "7057FF" ;;
    9) echo "006B75" ;;
    *) echo "5319E7" ;;
  esac
}

# Wave labels
create_or_update_label "wave:0-foundation" "0052CC" "Foundation — must complete before all other waves"
for wave in $(seq 1 "$MAX_WAVE"); do
  create_or_update_label "wave:$wave" "$(wave_color "$wave")" "Wave $wave"
done

# Type labels
create_or_update_label "type:epic" "3E4B9E" "Top-level grouping"
create_or_update_label "type:feature" "0E8A16" "User-facing capability"
create_or_update_label "type:task" "C2E0C6" "Implementation unit"
create_or_update_label "type:subtask" "BFD4F2" "Atomic work item"
create_or_update_label "type:tracking" "7057FF" "Traceability or dependency-matrix issue"

# Priority labels
create_or_update_label "priority:critical" "B60205" "Blocks everything"
create_or_update_label "priority:high" "D93F0B" "Must complete this wave"
create_or_update_label "priority:medium" "FBCA04" "Important, not blocking"
create_or_update_label "priority:low" "0E8A16" "Can defer"

# Status labels
create_or_update_label "status:blocked" "B60205" "Waiting on dependency"
create_or_update_label "status:ready" "0E8A16" "Ready for execution"
create_or_update_label "status:in-progress" "FBCA04" "Currently being worked"
create_or_update_label "status:needs-review" "D876E3" "Needs human review"
create_or_update_label "status:failed" "D73A4A" "Attempt failed; waiting on recovery decision"

echo ""
echo "Done - labels created for $REPO (foundation + wave:1..wave:$MAX_WAVE)"

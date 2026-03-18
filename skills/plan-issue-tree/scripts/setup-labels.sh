#!/usr/bin/env bash
# Creates the standard label set for wave-based issue planning.
# Usage: setup-labels.sh OWNER/REPO
set -euo pipefail

REPO="${1:?Usage: setup-labels.sh OWNER/REPO}"

# Wave labels
gh label create "wave:0-foundation" --repo "$REPO" --color "0052CC" --description "Foundation — must complete before all other waves" --force 2>/dev/null && echo "✓ wave:0-foundation" || echo "exists: wave:0-foundation"
gh label create "wave:1" --repo "$REPO" --color "1D76DB" --description "Wave 1" --force 2>/dev/null && echo "✓ wave:1" || echo "exists: wave:1"
gh label create "wave:2" --repo "$REPO" --color "5319E7" --description "Wave 2" --force 2>/dev/null && echo "✓ wave:2" || echo "exists: wave:2"
gh label create "wave:3" --repo "$REPO" --color "B60205" --description "Wave 3" --force 2>/dev/null && echo "✓ wave:3" || echo "exists: wave:3"
gh label create "wave:4" --repo "$REPO" --color "D93F0B" --description "Wave 4" --force 2>/dev/null && echo "✓ wave:4" || echo "exists: wave:4"
gh label create "wave:5" --repo "$REPO" --color "E4E669" --description "Wave 5" --force 2>/dev/null && echo "✓ wave:5" || echo "exists: wave:5"

# Type labels
gh label create "type:epic" --repo "$REPO" --color "3E4B9E" --description "Top-level grouping" --force 2>/dev/null && echo "✓ type:epic" || echo "exists: type:epic"
gh label create "type:feature" --repo "$REPO" --color "0E8A16" --description "User-facing capability" --force 2>/dev/null && echo "✓ type:feature" || echo "exists: type:feature"
gh label create "type:task" --repo "$REPO" --color "C2E0C6" --description "Implementation unit" --force 2>/dev/null && echo "✓ type:task" || echo "exists: type:task"
gh label create "type:subtask" --repo "$REPO" --color "BFD4F2" --description "Atomic work item" --force 2>/dev/null && echo "✓ type:subtask" || echo "exists: type:subtask"

# Priority labels
gh label create "priority:critical" --repo "$REPO" --color "B60205" --description "Blocks everything" --force 2>/dev/null && echo "✓ priority:critical" || echo "exists: priority:critical"
gh label create "priority:high" --repo "$REPO" --color "D93F0B" --description "Must complete this wave" --force 2>/dev/null && echo "✓ priority:high" || echo "exists: priority:high"
gh label create "priority:medium" --repo "$REPO" --color "FBCA04" --description "Important, not blocking" --force 2>/dev/null && echo "✓ priority:medium" || echo "exists: priority:medium"
gh label create "priority:low" --repo "$REPO" --color "0E8A16" --description "Can defer" --force 2>/dev/null && echo "✓ priority:low" || echo "exists: priority:low"

# Status labels
gh label create "status:blocked" --repo "$REPO" --color "B60205" --description "Waiting on dependency" --force 2>/dev/null && echo "✓ status:blocked" || echo "exists: status:blocked"
gh label create "status:ready" --repo "$REPO" --color "0E8A16" --description "Ready for execution" --force 2>/dev/null && echo "✓ status:ready" || echo "exists: status:ready"
gh label create "status:in-progress" --repo "$REPO" --color "FBCA04" --description "Currently being worked" --force 2>/dev/null && echo "✓ status:in-progress" || echo "exists: status:in-progress"
gh label create "status:needs-review" --repo "$REPO" --color "D876E3" --description "Needs human review" --force 2>/dev/null && echo "✓ status:needs-review" || echo "exists: status:needs-review"

echo ""
echo "Done — labels created for $REPO"

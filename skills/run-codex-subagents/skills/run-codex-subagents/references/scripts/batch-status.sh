#!/usr/bin/env bash
# batch-status.sh — Print status table for all tasks (or filtered by label/status)
#
# Usage:
#   bash batch-status.sh                    # All tasks
#   bash batch-status.sh --status completed # Only completed tasks
#   bash batch-status.sh --label wave-1     # Only tasks with label "wave-1"
#   bash batch-status.sh --recent 10        # Last 10 tasks by creation time
#
# Reads meta.json files from ~/.cli-codex-subagent/tasks/ and prints a table.

set -euo pipefail

TASK_DIR="${CLI_CODEX_SUBAGENT_STATE_DIR:-$HOME/.cli-codex-subagent}/tasks"
FILTER_STATUS=""
FILTER_LABEL=""
RECENT_COUNT=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --status) FILTER_STATUS="$2"; shift 2 ;;
        --label)  FILTER_LABEL="$2"; shift 2 ;;
        --recent) RECENT_COUNT="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 [--status STATUS] [--label LABEL] [--recent N]"
            echo ""
            echo "Options:"
            echo "  --status STATUS   Filter by status (completed, failed, working, cancelled)"
            echo "  --label LABEL     Filter by label"
            echo "  --recent N        Show only the N most recent tasks"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [ ! -d "$TASK_DIR" ]; then
    echo "No tasks directory found at $TASK_DIR"
    exit 1
fi

# Header
printf "%-30s %-12s %-8s %-12s %s\n" "TASK_ID" "STATUS" "ELAPSED" "TOKENS" "LAST_TIMELINE"
printf "%-30s %-12s %-8s %-12s %s\n" "-------" "------" "-------" "------" "-------------"

# Process each task directory
process_task() {
    local task_dir="$1"
    local task_id
    task_id=$(basename "$task_dir")
    local meta="$task_dir/meta.json"
    local timeline="$task_dir/timeline.log"

    if [ ! -f "$meta" ]; then
        return
    fi

    # Extract fields from meta.json
    local status created_at completed_at tokens labels
    status=$(python3 -c "import json; d=json.load(open('$meta')); print(d.get('status','?'))" 2>/dev/null || echo "?")
    created_at=$(python3 -c "import json; d=json.load(open('$meta')); print(d.get('createdAt',''))" 2>/dev/null || echo "")
    completed_at=$(python3 -c "import json; d=json.load(open('$meta')); print(d.get('completedAt','') or d.get('updatedAt',''))" 2>/dev/null || echo "")
    tokens=$(python3 -c "import json; d=json.load(open('$meta')); tu=d.get('tokenUsage',{}); print(tu.get('totalTokens',0))" 2>/dev/null || echo "0")
    labels=$(python3 -c "import json; d=json.load(open('$meta')); print(','.join(d.get('labels',[])))" 2>/dev/null || echo "")

    # Apply filters
    if [ -n "$FILTER_STATUS" ] && [ "$status" != "$FILTER_STATUS" ]; then
        return
    fi
    if [ -n "$FILTER_LABEL" ] && [[ ! ",$labels," == *",$FILTER_LABEL,"* ]]; then
        return
    fi

    # Calculate elapsed time
    local elapsed="—"
    if [ -n "$created_at" ] && [ -n "$completed_at" ]; then
        elapsed=$(python3 -c "
from datetime import datetime
try:
    c = datetime.fromisoformat('$created_at'.replace('Z','+00:00'))
    e = datetime.fromisoformat('$completed_at'.replace('Z','+00:00'))
    d = int((e - c).total_seconds())
    if d < 60: print(f'{d}s')
    elif d < 3600: print(f'{d//60}m{d%60}s')
    else: print(f'{d//3600}h{(d%3600)//60}m')
except: print('—')
" 2>/dev/null || echo "—")
    fi

    # Format tokens
    local tokens_fmt="—"
    if [ "$tokens" != "0" ] && [ "$tokens" != "" ]; then
        tokens_fmt=$(python3 -c "
t = $tokens
if t >= 1000: print(f'{t/1000:.0f}K')
else: print(t)
" 2>/dev/null || echo "$tokens")
    fi

    # Status badge
    local badge
    case "$status" in
        completed) badge="[done]" ;;
        failed)    badge="[FAIL]" ;;
        working)   badge="[busy]" ;;
        cancelled) badge="[stop]" ;;
        *)         badge="[$status]" ;;
    esac

    # Last timeline line (non-empty)
    local last_line="—"
    if [ -f "$timeline" ]; then
        last_line=$(tail -1 "$timeline" 2>/dev/null | head -c 60 || echo "—")
    fi

    # Output with created_at for sorting
    printf "%s\t%-30s %-12s %-8s %-12s %s\n" "$created_at" "$task_id" "$badge" "$elapsed" "$tokens_fmt" "$last_line"
}

# Collect output for sorting
output=""
for task_dir in "$TASK_DIR"/*/; do
    [ -d "$task_dir" ] || continue
    line=$(process_task "$task_dir")
    if [ -n "$line" ]; then
        output+="$line"$'\n'
    fi
done

# Sort by creation time (descending), then strip the sort key
if [ -n "$output" ]; then
    sorted=$(echo "$output" | sort -t$'\t' -k1 -r | cut -f2-)

    if [ "$RECENT_COUNT" -gt 0 ]; then
        echo "$sorted" | head -n "$RECENT_COUNT"
    else
        echo "$sorted"
    fi
fi

# Summary
echo ""
total=$(echo "$output" | grep -c "." || echo 0)
done_count=$(echo "$output" | grep -c "\[done\]" || echo 0)
fail_count=$(echo "$output" | grep -c "\[FAIL\]" || echo 0)
busy_count=$(echo "$output" | grep -c "\[busy\]" || echo 0)
echo "Total: $total tasks ($done_count done, $fail_count failed, $busy_count busy)"

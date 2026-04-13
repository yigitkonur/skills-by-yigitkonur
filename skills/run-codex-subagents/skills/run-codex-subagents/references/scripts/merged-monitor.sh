#!/usr/bin/env bash
# merged-monitor.sh — Monitor multiple task timelines simultaneously
#
# Usage:
#   bash merged-monitor.sh task-id-1 task-id-2 task-id-3
#
# Each line is prefixed with [task-id] for identification.
# Press Ctrl+C to stop all monitors.

set -euo pipefail

TASK_DIR="${CLI_CODEX_SUBAGENT_STATE_DIR:-$HOME/.cli-codex-subagent}/tasks"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <task-id-1> [task-id-2] [task-id-3] ..."
    echo ""
    echo "Monitors timeline.log files from multiple tasks simultaneously."
    echo "Each line is prefixed with the task ID for identification."
    echo ""
    echo "Available tasks:"
    if [ -d "$TASK_DIR" ]; then
        for d in "$TASK_DIR"/*/; do
            id=$(basename "$d")
            if [ -f "$d/timeline.log" ]; then
                status="(has timeline)"
            else
                status="(no timeline yet)"
            fi
            echo "  $id $status"
        done
    else
        echo "  (no tasks directory found at $TASK_DIR)"
    fi
    exit 1
fi

# Collect PIDs for cleanup
TAIL_PIDS=()

cleanup() {
    echo ""
    echo "[monitor] Stopping all watchers..."
    for pid in "${TAIL_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo "[monitor] Done."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Validate task IDs and start tailing
for task_id in "$@"; do
    timeline="$TASK_DIR/$task_id/timeline.log"

    if [ ! -d "$TASK_DIR/$task_id" ]; then
        echo "[monitor] WARNING: Task directory not found: $task_id"
        continue
    fi

    # Create timeline.log if it doesn't exist yet (task may not have started)
    if [ ! -f "$timeline" ]; then
        echo "[monitor] Waiting for timeline: $task_id"
        touch "$timeline"
    fi

    # Use short ID for prefix (first 2 words of the adjective-animal-number format)
    short_id=$(echo "$task_id" | cut -d'-' -f1-2)

    # Start tail in background with sed prefix
    # --unbuffered ensures lines appear immediately
    if command -v gsed &>/dev/null; then
        # macOS with GNU sed installed via homebrew
        tail -f "$timeline" | gsed --unbuffered "s/^/[$short_id] /" &
    elif sed --unbuffered '' </dev/null 2>/dev/null; then
        # GNU sed available
        tail -f "$timeline" | sed --unbuffered "s/^/[$short_id] /" &
    else
        # macOS default sed (no --unbuffered, use -l for line buffering)
        tail -f "$timeline" | sed -l "s/^/[$short_id] /" &
    fi
    TAIL_PIDS+=($!)
done

if [ ${#TAIL_PIDS[@]} -eq 0 ]; then
    echo "[monitor] No valid tasks to monitor."
    exit 1
fi

echo "[monitor] Watching ${#TAIL_PIDS[@]} task(s). Press Ctrl+C to stop."
echo "---"

# Wait for all background processes
wait

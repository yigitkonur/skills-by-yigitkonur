# Parallel Dispatch

How to spawn multiple tasks simultaneously and coordinate their completion.

## Core pattern

```bash
#!/usr/bin/env bash
# Spawn phase
TASK_A=$(cli-codex-subagent run auth.md    --effort low --label wave-1 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
TASK_B=$(cli-codex-subagent run billing.md --effort low --label wave-1 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
TASK_C=$(cli-codex-subagent run notify.md  --effort low --label wave-1 --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")

echo "Spawned: $TASK_A $TASK_B $TASK_C"

# Wait phase (blocks until each finishes)
cli-codex-subagent task wait "$TASK_A"; echo "A done"
cli-codex-subagent task wait "$TASK_B"; echo "B done"
cli-codex-subagent task wait "$TASK_C"; echo "C done"

# Audit
cli-codex-subagent task list --label wave-1
```

**Key rule:** spawn ALL before waiting. Tasks run concurrently with the CLI. Waiting before you've spawned everything serializes unnecessarily.

## From a prompt file list

```bash
#!/usr/bin/env bash
TASKS=()
for PROMPT in prompts/wave-1/*.md; do
    TASK_ID=$(cli-codex-subagent run "$PROMPT" --effort low --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
    TASKS+=("$TASK_ID")
    echo "Spawned $TASK_ID <- $PROMPT"
done

# Wait for all
for TASK_ID in "${TASKS[@]}"; do
    cli-codex-subagent task wait "$TASK_ID"
    STATUS=$(cli-codex-subagent task read "$TASK_ID" --field status)
    echo "$TASK_ID: $STATUS"
done
```

## Multi-wave execution

Sequential waves where each wave depends on the previous one's output.

```bash
#!/usr/bin/env bash
set -euo pipefail

run_wave() {
    local LABEL="$1"
    shift
    local TASKS=()
    for PROMPT in "$@"; do
        TASK_ID=$(cli-codex-subagent run "$PROMPT" --effort low --auto-approve --label "$LABEL" --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
        TASKS+=("$TASK_ID")
        echo "  spawned $TASK_ID <- $PROMPT"
    done
    for TASK_ID in "${TASKS[@]}"; do
        cli-codex-subagent task wait "$TASK_ID"
    done
    echo "Wave $LABEL complete"
    cli-codex-subagent task list --label "$LABEL"
}

echo "=== Wave 1: Schema ==="
run_wave wave-1 tasks/schema.md tasks/migrations.md

echo "=== Wave 2: Business logic ==="
run_wave wave-2 tasks/auth.md tasks/billing.md tasks/notify.md

echo "=== Wave 3: Integration ==="
run_wave wave-3 tasks/api-routes.md tasks/e2e-tests.md

echo "All waves complete."
```

## Cap per wave

The Codex runtime runs tasks sequentially in one process. More than 6-8 concurrent tasks risks resource exhaustion. To batch larger lists:

```bash
#!/usr/bin/env bash
BATCH_SIZE=5
TASKS=()
COUNT=0
WAVE=1

for PROMPT in prompts/*.md; do
    TASK_ID=$(cli-codex-subagent run "$PROMPT" --effort low --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
    TASKS+=("$TASK_ID")
    COUNT=$((COUNT + 1))
    if [ "$COUNT" -ge "$BATCH_SIZE" ]; then
        echo "Waiting for batch of $COUNT..."
        for TID in "${TASKS[@]}"; do
            cli-codex-subagent task wait "$TID"
        done
        TASKS=()
        COUNT=0
        WAVE=$((WAVE + 1))
        echo "--- batch $WAVE starting ---"
    fi
done

# Wait for trailing tasks
for TID in "${TASKS[@]}"; do
    cli-codex-subagent task wait "$TID"
done
```

## Handling failures in a wave

After a wave finishes, check for failures before proceeding:

```bash
# After waiting for all wave-1 tasks:
FAILED=$(cli-codex-subagent task list --label wave-1 --status failed --json | python3 -c "import sys,json; tasks=json.load(sys.stdin)['data']; print(len(tasks))")
echo "Failed: $FAILED"

if [ "$FAILED" -gt 0 ]; then
    echo "Wave 1 had failures. Checking partial work..."
    git status
    # Decision: retry, fix, or abort wave 2
fi
```

## Watching multiple tasks live

Use tmux panes or background follow processes:

```bash
# Background follow to log files
cli-codex-subagent task follow "$TASK_A" > /tmp/auth.log &
cli-codex-subagent task follow "$TASK_B" > /tmp/billing.log &
cli-codex-subagent task follow "$TASK_C" > /tmp/notify.log &

# Tail all three
tail -f /tmp/auth.log /tmp/billing.log /tmp/notify.log
```

Or use tmux:
```bash
tmux new-session -d -s monitor
tmux send-keys -t monitor "cli-codex-subagent task follow $TASK_A" Enter
tmux split-window -h
tmux send-keys -t monitor "cli-codex-subagent task follow $TASK_B" Enter
tmux split-window -v
tmux send-keys -t monitor "cli-codex-subagent task follow $TASK_C" Enter
tmux attach -t monitor
```

## Common mistakes

| Mistake | Problem |
|---------|---------|
| `wait` after each `run` | Tasks run one at a time — all parallelism lost |
| Spawning 20+ at once | Resource exhaustion; daemon OOM; zombie tasks |
| Ignoring failures | Wave 2 builds on broken wave 1 output |
| No labels | Can't distinguish waves with `task list` |
| Not using `--auto-approve` | Manual approvals block unattended batch runs |

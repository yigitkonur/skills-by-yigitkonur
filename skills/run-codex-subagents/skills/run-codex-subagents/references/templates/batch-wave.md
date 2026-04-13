# Batch Wave Template

Template for dispatching parallel waves of tasks with monitoring, inter-wave checks, and scoreboard tracking.

## Template: Single Wave

### Spawn phase — all tasks before waiting

```bash
#!/usr/bin/env bash

TASK_1=$(cli-codex-subagent run task1.md --effort low --label wave-1 --label domain-1 --auto-approve --json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")

TASK_2=$(cli-codex-subagent run task2.md --effort low --label wave-1 --label domain-2 --auto-approve --json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")

TASK_3=$(cli-codex-subagent run task3.md --effort low --label wave-1 --label domain-3 --auto-approve --json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")

echo "Spawned: $TASK_1 $TASK_2 $TASK_3"
```

### Monitor phase — follow all in background

```bash
cli-codex-subagent task follow "$TASK_1" > /tmp/task1.log &
cli-codex-subagent task follow "$TASK_2" > /tmp/task2.log &
cli-codex-subagent task follow "$TASK_3" > /tmp/task3.log &

# Or tail merged (prepend task ID to each line)
tail -f /tmp/task1.log /tmp/task2.log /tmp/task3.log
```

### Collect phase — wait for each

```bash
cli-codex-subagent task wait "$TASK_1"
cli-codex-subagent task wait "$TASK_2"
cli-codex-subagent task wait "$TASK_3"
```

### Verify phase — scoreboard check

```bash
cli-codex-subagent task list --label wave-1

# Expected:
# tsk_abc123  [done]    completed   23s    109K tokens   wave-1,domain-1
# tsk_def456  [done]    completed   45s    85K tokens    wave-1,domain-2
# tsk_ghi789  [done]    completed   31s    72K tokens    wave-1,domain-3
```

## Template: Multi-Wave Execution

### Wave 1: Foundation (no dependencies)

```bash
#!/usr/bin/env bash
set -euo pipefail

# Spawn all Wave 1 tasks
W1_TYPES=$(cli-codex-subagent run tasks/types.md  --effort low --label wave-1 --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
W1_CONFIG=$(cli-codex-subagent run tasks/config.md --effort low --label wave-1 --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
W1_UTILS=$(cli-codex-subagent run tasks/utils.md  --effort low --label wave-1 --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")

# Wait for all
cli-codex-subagent task wait "$W1_TYPES"
cli-codex-subagent task wait "$W1_CONFIG"
cli-codex-subagent task wait "$W1_UTILS"

# Scoreboard check — all wave-1 done?
cli-codex-subagent task list --label wave-1
```

### Wave 2: Depends on Wave 1

```bash
# Spawn Wave 2 (only after wave-1 complete)
W2_AUTH=$(cli-codex-subagent run tasks/auth.md     --effort low --label wave-2 --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")
W2_API=$(cli-codex-subagent run tasks/api.md      --effort low --label wave-2 --auto-approve --json | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['id'])")

cli-codex-subagent task wait "$W2_AUTH"
cli-codex-subagent task wait "$W2_API"

# Scoreboard
cli-codex-subagent task list --label wave-2
```

### Wave 3: Integration

```bash
cli-codex-subagent run tasks/integration.md --effort low --label wave-3 --auto-approve --follow
```

## Handling Failures Mid-Wave

```bash
# After waiting for wave-1:
cli-codex-subagent task list --label wave-1 --status failed --json

# If failures exist:
# 1. Check partial work on disk
git status

# 2. If partial work is usable, fix it
cli-codex-subagent run tasks/fix-w1-failure.md --effort low --label wave-1 --label retry --follow

# 3. Verify all Wave 1 work is complete before proceeding
cli-codex-subagent task list --label wave-1
```

## Rules

1. **Spawn all tasks in a wave before waiting.** Don't `task wait` between spawns.
2. **Label every task by wave.** `--label wave-N` on every spawn.
3. **Follow tasks in background.** Use `> /tmp/task.log &` to capture events.
4. **Check scoreboard between waves.** `task list --label wave-N` before proceeding to N+1.
5. **Cap at 5-8 tasks per wave.** More risks resource exhaustion.
6. **Handle failures before proceeding.** Carry-forward failures corrupt later waves.
7. **Use `--auto-approve` for unattended batch runs.** Manual approvals break the pipeline.

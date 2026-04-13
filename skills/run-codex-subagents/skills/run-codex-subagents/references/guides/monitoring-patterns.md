# Monitoring Patterns

How to observe tasks as they run using `cli-codex-subagent`.

## Primary pattern: --follow flag

The simplest monitoring path. Attaches a live event stream to any running task.

```bash
# Start a task and follow immediately
cli-codex-subagent run task.md --effort medium --follow

# Or attach to an existing task
cli-codex-subagent task follow tsk_abc123
```

Output:
```
TURN    019d786c-c74a-7001-bbbe-c6f3b4e1e1b4
THINK   Let me start by exploring the project structure
CMD     find src -name "*.ts" | head -20 → exit=0 (0.3s)
FILE    src/index.ts (read)
CMD     cat src/index.ts → exit=0 (0.2s)
TOKENS  18629 / 996147 (1.9%)
THINK   Now I understand the structure. Let me create the new controller.
FILE    src/controllers/auth.ts (created)
CMD     npx tsc --noEmit → exit=0 (4.1s)
MSG     Done! Created auth.ts with JWT validation middleware.
DONE    completed
```

## Monitoring multiple tasks in parallel

Use background processes:

```bash
# Spawn 3 tasks
TASK_A=$(cli-codex-subagent run auth.md    --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
TASK_B=$(cli-codex-subagent run billing.md --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")
TASK_C=$(cli-codex-subagent run notify.md  --json | python3 -c "import sys,json; print(json.load(sys.stdin)['taskId'])")

# Follow all three simultaneously (in tmux panes, or to log files)
cli-codex-subagent task follow "$TASK_A" > /tmp/auth.log    &
cli-codex-subagent task follow "$TASK_B" > /tmp/billing.log &
cli-codex-subagent task follow "$TASK_C" > /tmp/notify.log  &

# Block until all finish
cli-codex-subagent task wait "$TASK_A"
cli-codex-subagent task wait "$TASK_B"
cli-codex-subagent task wait "$TASK_C"

# Check results
cli-codex-subagent task list --label wave-1
```

## Machine-readable event stream

For automation: parse events as JSON lines.

```bash
cli-codex-subagent task follow tsk_abc123 --stream-json | while IFS= read -r line; do
    TYPE=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('type',''))")
    if [ "$TYPE" = "task_complete" ]; then
        echo "DONE"
        break
    elif [ "$TYPE" = "task_error" ]; then
        echo "FAILED"
        break
    fi
done
```

## Scoreboard check (between waves)

After spawning and waiting, audit all tasks at once:

```bash
cli-codex-subagent task list --label wave-1
```

Output:
```
tsk_abc123  [done]    completed   23s    109K tokens   wave-1
tsk_def456  [done]    completed   45s    85K tokens    wave-1
tsk_ghi789  [fail]    failed      8s     —             wave-1
```

Count by status:
```bash
cli-codex-subagent task list --label wave-1 --json | python3 -c "
import sys, json
tasks = json.load(sys.stdin)
from collections import Counter
print(Counter(t['status'] for t in tasks))
"
```

## Tail existing task output after it completes

If you weren't following live, read what happened:

```bash
# Tail the summary (human-readable)
cli-codex-subagent task read tsk_abc123

# Full event trace
cli-codex-subagent task events tsk_abc123

# Last N events only
cli-codex-subagent task events tsk_abc123 --tail 30

# Raw events (JSONL)
cli-codex-subagent task events tsk_abc123 --raw
```

## Direct disk access (no daemon required)

Artifacts are plain files — accessible even if the daemon isn't running:

```bash
STATE="${CLI_CODEX_SUBAGENT_STATE_DIR:-$HOME/.cli-codex-subagent}"
TASK_DIR="$STATE/tasks/tsk_abc123"

# Tail live (while running)
tail -f "$TASK_DIR/timeline.log"

# Event JSONL
cat "$TASK_DIR/events.jsonl" | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    if e.get('type') == 'tool_result':
        print(e.get('output', '')[:200])
"

# Summary
cat "$TASK_DIR/summary.log"

# Prompt that was used
cat "$TASK_DIR/prompt.md"
```

## Cross-task patterns to watch

```bash
# Find all tasks that are currently running
cli-codex-subagent task list --status working

# Find all tasks that failed today
cli-codex-subagent task list --status failed --json | python3 -c "
import sys, json
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
tasks = json.load(sys.stdin)
today = [t for t in tasks if t.get('createdAt','')[:10] == now.strftime('%Y-%m-%d')]
for t in today:
    print(t['taskId'], t.get('errorMessage','')[:80])
"
```

## High-token tasks (token burn rate)

In `task follow` output, watch the TOKENS lines:

```
TOKENS  18629 / 996147 (1.9%)
```

If you see >50% with no end in sight, the task is burning context. Intervene:
1. Cancel the task: `cli-codex-subagent task cancel tsk_abc123`
2. Check `git status` for partial work
3. Rewrite the prompt with smaller scope
4. Restart at lower effort: `--effort low`

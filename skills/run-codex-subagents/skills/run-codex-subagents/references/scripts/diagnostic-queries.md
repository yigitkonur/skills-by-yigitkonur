# Diagnostic Queries

Ready-to-use jq one-liners for `events.jsonl` analysis. All paths assume `~/.mcp-codex-worker/tasks/{id}/events.jsonl`.

## Quick health check

Was the task healthy? Shows turn completions and process exits.

```bash
jq -r 'select(.method | test("turn/completed|_process_exit")) |
  "\(.t | split("T")[1] | split(".")[0]) \(.method) \(
    if .method == "turn/completed" then .params.turn.status
    elif .method == "_process_exit" then "code=\(.code) signal=\(.signal)"
    else "" end
  )"' events.jsonl
```

Output:
```
17:24:27 turn/completed completed
17:24:28 _process_exit code=0 signal=null
```

## Commands only

List all shell commands with exit codes and durations.

```bash
jq -r 'select(.params.item.type == "commandExecution" and .method == "item/completed") |
  "\(.t | split("T")[1] | split(".")[0]) exit=\(.params.item.exitCode) \(.params.item.durationMs)ms \(.params.item.command | split("\"") | .[1] // .)"' events.jsonl
```

## Token usage progression

Track how fast tokens are consumed. Shows total tokens at each update.

```bash
jq 'select(.method == "thread/tokenUsage/updated") |
  { t: (.t | split("T")[1] | split(".")[0]),
    total: .params.tokenUsage.total.totalTokens,
    input: .params.tokenUsage.total.inputTokens,
    output: .params.tokenUsage.total.outputTokens,
    reasoning: .params.tokenUsage.total.reasoningOutputTokens,
    pct: ((.params.tokenUsage.total.totalTokens / .params.tokenUsage.modelContextWindow * 100 * 10 | floor) / 10)
  }' events.jsonl
```

## Final token count only

```bash
jq -s 'map(select(.method == "thread/tokenUsage/updated")) | last |
  .params.tokenUsage.total' events.jsonl
```

## Timeline without noise

Filter out all delta/streaming events for a clean trace.

```bash
jq -r 'select(.method | test("Delta$|delta$|summaryPartAdded|hook/") | not) |
  "\(.t | split("T")[1] | split(".")[0]) \(.method)"' events.jsonl
```

## Time gaps (find >1s gaps between events)

Identify where the agent spent time thinking or waiting.

```python
#!/usr/bin/env python3
"""Find gaps > 1 second between consecutive events."""
import json, sys
from datetime import datetime

prev_t = None
prev_method = None

for line in open(sys.argv[1] if len(sys.argv) > 1 else "events.jsonl"):
    line = line.strip()
    if not line:
        continue
    e = json.loads(line)
    t = datetime.fromisoformat(e["t"].replace("Z", "+00:00"))
    if prev_t:
        gap = (t - prev_t).total_seconds()
        if gap > 1.0:
            ts = t.strftime("%H:%M:%S")
            print(f"{ts} +{gap:.1f}s gap after {prev_method} → {e['method']}")
    prev_t = t
    prev_method = e["method"]
```

Usage: `python3 time_gaps.py ~/.mcp-codex-worker/tasks/{id}/events.jsonl`

## Exit analysis

Check for process exits and STDERR across all tasks.

```bash
# All exits
for f in ~/.mcp-codex-worker/tasks/*/events.jsonl; do
  id=$(basename $(dirname "$f"))
  jq -r "select(.method == \"_process_exit\") |
    \"$id  code=\(.code) signal=\(.signal)\"" "$f" 2>/dev/null
done

# All STDERR (first line only per task)
for f in ~/.mcp-codex-worker/tasks/*/events.jsonl; do
  id=$(basename $(dirname "$f"))
  jq -r "select(.method == \"_stderr\") | .data" "$f" 2>/dev/null | head -1 | \
    sed "s/^/$id  /"
done
```

## Same-timestamp death detection

When parallel tasks share a Codex process and one crashes, all siblings die at the same millisecond. Detect this:

```bash
# Group _process_exit events by timestamp (within 100ms)
for f in ~/.mcp-codex-worker/tasks/*/events.jsonl; do
  id=$(basename $(dirname "$f"))
  jq -r "select(.method == \"_process_exit\") | \"$id \(.t)\"" "$f" 2>/dev/null
done | sort -k2 | awk '
  {
    split($2, a, ".")
    ts = a[1]
    if (ts == prev_ts) {
      if (!printed_prev) { print prev_line; printed_prev = 1 }
      print $0
    } else {
      printed_prev = 0
    }
    prev_ts = ts
    prev_line = $0
  }
'
```

If you see 2+ task IDs with the same timestamp, they were killed by the same process exit.

## Auto-answer audit

List all auto-answered questions to verify correctness.

```bash
for f in ~/.mcp-codex-worker/tasks/*/events.jsonl; do
  id=$(basename $(dirname "$f"))
  jq -r "select(.method == \"_auto_answer\") |
    \"$id  \(.summary)\"" "$f" 2>/dev/null
done
```

## Error events

```bash
jq -r 'select(.method == "error") |
  "\(.t | split("T")[1] | split(".")[0]) \(.params.error.codexErrorInfo): \(.params.error.message) (retry=\(.params.willRetry))"' events.jsonl
```

## Item type distribution

Count how many of each item type completed.

```bash
jq -r 'select(.method == "item/completed") | .params.item.type' events.jsonl | sort | uniq -c | sort -rn
```

## Reasoning vs execution ratio

Compare time spent thinking vs executing commands.

```bash
jq -r 'select(.method == "item/completed" and (.params.item.type == "reasoning" or .params.item.type == "commandExecution")) |
  "\(.params.item.type) \(.params.item.durationMs // 0)"' events.jsonl | \
  awk '{sum[$1]+=$2; count[$1]++} END {for(k in sum) printf "%s: %d events, %dms total\n", k, count[k], sum[k]}'
```

## Plan progression

Watch how the agent's plan evolved.

```bash
jq -r 'select(.method == "turn/plan/updated") |
  "\(.t | split("T")[1] | split(".")[0]) PLAN: \([.params.plan[] | "\(if .status == "completed" then "[v]" elif .status == "inProgress" then "[>]" else "[ ]" end) \(.step[:60])"] | join(" | "))"' events.jsonl
```

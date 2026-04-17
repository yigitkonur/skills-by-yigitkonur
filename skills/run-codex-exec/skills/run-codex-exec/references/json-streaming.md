# JSON Streaming with `codex exec --json`

`codex exec --json` emits one JSON event per line (JSONL) — a real-time stream of everything the agent does: commands, reasoning, final message, token usage. Pair it with `scripts/codex-json-filter.sh` + Claude Code's Monitor tool to get live notifications instead of watching a black box until it finishes.

## Event schema (codex-cli 0.121.0)

Each line is one of these `type` values. The filter knows all of them.

| Event | Shape | Meaning |
|---|---|---|
| `thread.started` | `{type, thread_id}` | New session. Thread ID is useful for `codex resume`. |
| `turn.started` | `{type}` | Model's reasoning turn begins. |
| `item.started` | `{type, item: {id, type, ...}}` | Agent begins a tool call. |
| `item.completed` | `{type, item: {id, type, ..., status, exit_code?, text?}}` | Agent finishes a tool call or produces a message. |
| `turn.completed` | `{type, usage: {input_tokens, cached_input_tokens, output_tokens}}` | Turn done. Token accounting attached. |

### `item.type` subtypes observed

| Subtype | Payload | Filter emits |
|---|---|---|
| `command_execution` | `{command, aggregated_output, exit_code, status}` | `[CMD>]` on start, `[CMD✓]` / `[CMD✗]` on completion |
| `reasoning` | `{text}` — markdown chain-of-thought | `[THINK]` with first line (hidden in `minimal`) |
| `agent_message` | `{text}` — final answer | `[SAID]` with first line |
| `todo_list` | internal todo tracking | `[ITEM>] todo_list starting` (generic) |
| *(unknown)* | anything else codex adds in the future | `[ITEM>] <type> starting` (generic default) |

## The filter script

`scripts/codex-json-filter.sh` reads JSONL on stdin and emits one compact line per interesting event. It also surfaces rate-limit errors and other stderr lines (when merged via `2>&1`) that don't arrive as JSON.

### Verbosity levels

| `CODEX_FILTER_LEVEL` | Shows | Typical use |
|---|---|---|
| `minimal` | START, CMD>, CMD✓/✗, SAID, TURN<, ERR | Production runs where you only care about commands + outcomes |
| `normal` *(default)* | minimal + TURN>, THINK, ITEM> | Development/debugging — see the agent's thinking |
| `verbose` | normal + command output tail on success, unknown item types | Deep debugging sessions |

### Truncation

Each emitted line is capped at `CODEX_FILTER_MAXLEN` characters (default 200). Long commands, long reasoning, long outputs get an `…` suffix. Set `CODEX_FILTER_MAXLEN=500` for less truncation on big terminals.

## Integration with Monitor tool

In Claude Code, point Monitor at the combined pipeline:

```
Monitor({
  description: "Codex <task-name> event stream",
  command: "codex exec --json --full-auto --skip-git-repo-check -C <cwd> '<prompt>' 2>&1 | /path/to/codex-json-filter.sh",
  timeout_ms: 1800000,  // 30 min
  persistent: false
})
```

Each filter output line becomes one chat notification. You see the agent's every step as it happens.

## Sample output (real run)

```
05:41:44Z [START] thread=019d99f5
05:41:44Z [TURN>] model-turn begin
05:42:12Z [THINK] **Sorting directory sizes**
05:42:12Z [ITEM>] todo_list starting
05:42:17Z [CMD>] /bin/zsh -lc "python3 - <<'PY' from pathlib import Path base = Path('/tmp/codex-stream-test')…
05:42:17Z [CMD✓] exit=0 /bin/zsh -lc "python3 - <<'PY' from pathlib import Path base = Path('/tmp/codex-stream-test')…
05:42:25Z [SAID] Done.
05:42:26Z [TURN<] tokens: in=63224 out=2073 cached=51840
```

## When to use streaming vs wrapper-with-auto-commit

Both are valid — they serve different needs.

| | Streaming (`--json` + filter) | Wrapper (`codex-wrapper.sh`) |
|---|---|---|
| Observability | Event-by-event live | One line per tick from `codex-monitor.sh` |
| Completion signal | Stream ends | Auto-commit + post-verify |
| Parallelism | One monitor per agent | One monitor for the whole fleet |
| Good for | Single interactive task where you want to see every step | Fan-out N parallel agents and walk away |

If you're dispatching 1 agent and want to watch it think → use streaming.
If you're dispatching 6 agents and want to come back in an hour → use the wrapper + fleet monitor.

They can be combined: the wrapper's `codex exec` invocation can gain `--json` and the internal log becomes machine-parseable, while the fleet-level `codex-monitor.sh` continues watching process counts + commits. That's the best of both.

## Practical pipeline recipes

### Just run codex and stream

```bash
codex exec --json --full-auto "your task" 2>&1 | codex-json-filter.sh
```

### Save JSONL for post-mortem AND stream

```bash
codex exec --json --full-auto "your task" 2>&1 \
  | tee /tmp/session.jsonl \
  | codex-json-filter.sh
```

Later, replay the raw JSONL through the filter at a different verbosity:

```bash
CODEX_FILTER_LEVEL=verbose cat /tmp/session.jsonl | codex-json-filter.sh
```

### Monitor an ongoing session's raw log

The wrapper writes codex's stdout to `<MONITOR_ROOT>/logs/<worktree>.log`. If that log was captured with `--json`, you can watch it live:

```bash
tail -f /tmp/codex-monitor/logs/wave1-reports.log | codex-json-filter.sh
```

### Filter by event type with `jq`

When you want a specific slice — e.g., just the commands:

```bash
cat /tmp/session.jsonl | jq -rc 'select(.item.type=="command_execution" and .type=="item.completed") | "\(.item.exit_code) \(.item.command[:80])"'
```

## Rate-limit behavior in `--json` mode

When the backend returns 503, codex prints the error to stderr. If you merged stderr (`2>&1 |`) before the filter, the filter's non-JSON branch catches it:

```
05:29:35Z [ERR] ERROR: unexpected status 503 Service Unavailable: Rate limit exceeded. Try again in 2731s…
```

Without `2>&1`, the error never reaches the filter and the stream just ends silently after a few seconds. **Always merge stderr for visibility.**

## Known gaps + future additions

- File patches via `apply_patch` appear as `command_execution` with the patch commands. No dedicated `file_change` event exists as of 0.121.0.
- Reasoning summaries can be switched on via `-c reasoning.summary=detailed`; filter just shows their first line.
- If codex adds new `item.type` values in the future (e.g., `image_generation`, `search`), the filter's default-case catches them at verbose level and the user can extend the case statement.

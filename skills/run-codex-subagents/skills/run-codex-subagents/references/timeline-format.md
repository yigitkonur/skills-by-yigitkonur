# Timeline Format

The timeline is the primary monitoring tool. Each line follows this format:

```
HH:MM:SS TAG     detail
```

Timestamp is local time (from the ISO timestamp in events). TAG is left-aligned, padded to 7 chars. Lines are capped at 500 characters.

## All 16 line types

### VERSION / STARTED / TURN

```
19:08:28 VERSION 1.0.29                                  ← _server_version
10:24:03 STARTED                                          ← thread/status/changed (first active)
10:24:03 TURN    019d786c-191e-7cb2-a0d9-70d6a03885e9    ← turn/started
```

### THINK (two variants)

**Variant 1: Reasoning without summary.** Agent is thinking but no summary text is available yet.

```
10:24:06 THINK   (reasoning...)
```

Source: `item/started` with `type: "reasoning"` and empty summary.

**Variant 2: Reasoning with summary.** Agent's thinking has been summarized.

```
10:24:16 THINK   Inspecting agents' paths
10:24:25 THINK   Reevaluating file creation constraints
09:35:35 THINK   Deciding on commit strategy
```

Source: `item/completed` with `type: "reasoning"` and non-empty summary, or accumulated from `item/reasoning/summaryTextDelta` events.

### PLAN

Agent's execution plan with status icons.

```
09:35:36 PLAN    [->] Inspect repo guidance, migration docs, Next docs, and action domains · [ ] Install TanStack Query packages · [ ] Implement query keys, invalidation map, and provider; update layout · [ ] Run typecheck and tests, fix issues if any · [ ] Commit changes with requested message
```

Icons:
- `[✓]` or `[v]` — step completed
- `[→]` or `[->]` — step in progress
- `[ ]` — step pending

Source event: `turn/plan/updated`. The plan object has `step` (string) and `status` (`"completed"`, `"inProgress"`, `"pending"`).

### CMD

Shell command executed. Shell wrapper (`/bin/zsh -lc "..."`) is stripped. `rtk` prefix is stripped. Duration shows `<1ms` for sub-millisecond commands.

```
10:24:10 CMD     find FastNotch -path '*/AGENTS.md' -print → exit=0 (<1ms)
10:24:10 CMD     pwd && find .. -name AGENTS.md -print → exit=0 (0.3s)
10:24:25 CMD     python3 - <<'PY'
files = sorted(base.glob('*.… → exit=0 (<1ms)
```

Format: `{stripped_command} → exit={code} ({duration})`

Long commands are truncated with `...` at the 500-char line cap.

Source event: `item/completed` with `type: "commandExecution"`. The raw command includes the shell wrapper; the timeline strips it.

### FILE

File changed by the agent.

```
14:22:15 FILE    src/utils/slugify.ts (created)
14:22:18 FILE    src/index.ts (modified)
```

Format: `{path} ({kind})` where kind is `created`, `modified`, or `deleted`.

Source event: `item/completed` with `type: "fileChange"`, or `turn/diff/updated`.

### MSG

Agent message to the user. Truncated at 200 characters with `[+N chars]` suffix.

```
10:24:27 MSG     I inspected the target directory and counted the Swift files:  - `NotchHoverStateMachine.swift` — 249 - `BluetoothPopupController.swift` — 212 - `TimerPopupController.swift` — 198 - `MusicHoverControl [+38 chars]
```

Source event: `item/completed` with `type: "agentMessage"`.

### MCP / TOKENS

```
14:22:20 MCP     database-mcp/query → completed           ← item/completed (mcpToolCall)
14:22:25 MCP     search-mcp/index → failed
10:24:09 TOKENS {"threadId":"...","tokenUsage":{"total":{"totalTokens":18629},"modelContextWindow":258400}}  ← tokenUsage/updated
10:24:16 TOKENS {"threadId":"...","tokenUsage":{"total":{"totalTokens":38407},"modelContextWindow":258400}}
```

MCP format: `{serverName}/{toolName} → {status}`. TOKENS format: JSON object with `tokenUsage.total.totalTokens` and `modelContextWindow` fields. Duplicates (same total) are filtered.

### AUTO

Auto-answered question. Shows the question and selected answer.

```
11:49:06 AUTO    What color should I use for /tmp/color-choice.txt? → "Red (Recommended)"
```

Format: `{question} → "{answer}"`

Source event: `_auto_answer`.

### APPROVE (two variants)

Auto-approved request.

**Command approval:**
```
14:22:03 APPROVE cmd: npm install express @types/express
```

**File approval:**
```
14:22:05 APPROVE files: src/config.ts, package.json
```

Source: synthetic events from auto-resolved `command_approval` and `file_approval`.

### ASK

Task is waiting for orchestrator input (only for `dynamic_tool` — the one pause type that isn't auto-resolved).

```
14:22:10 ASK     dynamic_tool: run_benchmark({"suite": "perf"})
```

Source: `_server_request` when the type is `dynamic_tool`.

### STDERR

Process error output. ANSI escape codes are stripped. Only the first STDERR line per burst is captured in the timeline (rest in events.jsonl).

```
11:49:06 STDERR  2026-04-10T18:49:06.689008Z ERROR codex_app_server::bespoke_event_handling: failed to deserialize ToolRequestUserInputResponse: invalid type: string "Red (Recommended)", expected struct ToolRequestUs...
10:04:59 STDERR  2026-04-10T17:04:59.747880Z ERROR codex_core::tools::router: error=request_user_input is unavailable in Default mode
```

Source event: `_stderr`. ANSI codes (`\u001b[...m`) are stripped before writing.

### EXIT / DONE

```
11:00:28 EXIT    code=0 signal=null       ← _process_exit
10:24:27 DONE    completed                ← turn/completed
14:22:30 DONE    failed
```

EXIT: `code=0` with no DONE usually means budget exhaustion. Non-zero = crash. Source: `_process_exit`.
DONE: `turn.status` from `turn/completed` event.

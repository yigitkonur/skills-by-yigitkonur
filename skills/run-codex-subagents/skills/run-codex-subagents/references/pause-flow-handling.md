# Pause Flow Handling

When wait-task returns `input_required`, the agent is paused. The `pending_question` field tells you what it needs. There are 5 pause types, but **only `dynamic_tool` actually pauses the task for the orchestrator**. The other 4 are auto-resolved by the MCP server.

## CRITICAL: Auto-resolution behavior

| Type | Auto-resolved? | How |
|---|---|---|
| `command_approval` | **YES** — auto-accepted | Server sends `accept` immediately |
| `file_approval` | **YES** — auto-accepted | Server sends `accept` immediately |
| `elicitation` | **YES** — auto-accepted | Server sends `accept` immediately |
| `user_input` | **YES** — auto-answered | Server selects first option (the one marked "(Recommended)") |
| `dynamic_tool` | **NO** — task pauses | Orchestrator must provide result or error |

The server's `developer_instructions` include a QUESTION POLICY that tells the agent: put the recommended option first and mark it with "(Recommended)". This ensures auto-answer picks the right choice.

You will see auto-resolutions in the timeline as `AUTO` and `APPROVE` lines. In `events.jsonl`, they appear as `_auto_answer` and synthetic approval events.

## Type 1: user_input

Agent asked a question. Server auto-selects the first option.

**Server request (in events.jsonl):**
```json
{
  "t": "2026-04-10T18:49:06.687Z",
  "method": "_server_request:item/tool/requestUserInput",
  "requestId": 0,
  "params": {
    "threadId": "019d78b9-e054-...",
    "turnId": "019d78b9-e05f-...",
    "itemId": "call_FhnUjvAGUjyvlC0geDhLxfmZ",
    "questions": [
      {
        "id": "color_choice",
        "header": "Color",
        "question": "What color should I use for /tmp/color-choice.txt?",
        "isOther": true,
        "isSecret": false,
        "options": [
          { "label": "Red (Recommended)", "description": "Use red." },
          { "label": "Blue", "description": "Use blue." },
          { "label": "Green", "description": "Use green." }
        ]
      }
    ]
  }
}
```

**Auto-answer (in events.jsonl):**
```json
{
  "t": "2026-04-10T18:49:06.688Z",
  "method": "_auto_answer",
  "answers": { "color_choice": "Red (Recommended)" },
  "summary": "What color should I use for /tmp/color-choice.txt? → \"Red (Recommended)\""
}
```

**Timeline line:**
```
11:49:06 AUTO    What color should I use for /tmp/color-choice.txt? → "Red (Recommended)"
```

**Manual respond-task (if you need to override):**
```json
{
  "task_id": "bold-falcon-42",
  "type": "user_input",
  "answers": { "color_choice": "Blue" }
}
```

## Type 2: command_approval (auto-accepted)

Agent wants to run a shell command. Pending question: `{type: "command_approval", requestId, command, sandboxPolicy}`.

```
14:22:03 APPROVE cmd: npm install express @types/express
```

Manual override: `{task_id, type: "command_approval", decision: "accept" | "reject"}`

## Type 3: file_approval (auto-accepted)

Agent wants to write/modify files. Pending question: `{type: "file_approval", requestId, fileChanges: [{path, patch}]}`.

```
14:22:05 APPROVE files: src/config.ts, package.json
```

Manual override: `{task_id, type: "file_approval", decision: "accept" | "reject"}`

## Type 4: elicitation (auto-accepted)

MCP server wants confirmation. Pending question: `{type: "elicitation", requestId, serverName, message, schema}`.

```
14:22:07 APPROVE elicitation: database-mcp — Allow read access to production database?
```

Manual override: `{task_id, type: "elicitation", action: "accept" | "decline"}`

## Type 5: dynamic_tool (THE ONLY REAL PAUSE)

Agent invoked a tool that requires external execution. The task genuinely pauses — you must provide the result.

**wait-task response:**
```json
{
  "status": "input_required",
  "pending_question": {
    "type": "dynamic_tool",
    "requestId": "req-5",
    "toolName": "run_benchmark",
    "arguments": "{\"suite\": \"perf\"}"
  }
}
```

**Timeline line:**
```
14:22:10 ASK     dynamic_tool: run_benchmark({"suite": "perf"})
```

**respond-task (success):**
```json
{
  "task_id": "bold-falcon-42",
  "type": "dynamic_tool",
  "result": "All 12 benchmarks passed. Mean latency: 45ms."
}
```

**respond-task (error):**
```json
{
  "task_id": "bold-falcon-42",
  "type": "dynamic_tool",
  "error": "Benchmark suite not found."
}
```

## Handling wrong auto-answers

If the auto-answer picked the wrong option:
1. The task continues with the wrong choice
2. You see `[auto-answer]` or `AUTO` in the output/timeline
3. Steer via `message-task`: "Undo: you used Red but I need Blue. Re-do the file with Blue."
4. Or: cancel and respawn with a clearer prompt that doesn't trigger a question

## Multiple pauses in sequence

A task can pause multiple times. After each respond-task, call wait-task again:

```
spawn → wait → input_required (dynamic_tool #1)
  → respond → wait → input_required (dynamic_tool #2)
  → respond → wait → completed
```

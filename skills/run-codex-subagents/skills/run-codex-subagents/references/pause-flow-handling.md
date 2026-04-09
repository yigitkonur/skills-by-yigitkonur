# Pause Flow Handling

When wait-task returns `input_required`, the agent is paused and needs a response before it can continue. The `pending_question` field in the wait-task response tells you what the agent needs.

## Pause types

### user_input — Agent has questions

The agent wants to ask the user something. Common scenarios: clarifying ambiguous requirements, choosing between options, confirming destructive operations.

**wait-task response:**
```json
{
  "status": "input_required",
  "pending_question": {
    "type": "user_input",
    "requestId": "req-1",
    "questions": [
      {
        "id": "db_choice",
        "text": "Which database should I use?",
        "options": ["PostgreSQL", "MySQL", "SQLite"],
        "allowFreeform": true
      }
    ]
  }
}
```

**respond-task call:**
```json
{
  "task_id": "bold-falcon-42",
  "type": "user_input",
  "answers": {
    "db_choice": "PostgreSQL"
  }
}
```

The `answers` object maps question `id` to answer string. If `allowFreeform` is true, any text is valid. If false, pick from `options`.

### command_approval — Agent wants to run a shell command

The agent wants to execute a command. The `command` field shows the exact command.

**wait-task response:**
```json
{
  "status": "input_required",
  "pending_question": {
    "type": "command_approval",
    "requestId": "req-2",
    "command": "npm install express @types/express",
    "sandboxPolicy": "workspaceWrite"
  }
}
```

**respond-task call:**
```json
{
  "task_id": "bold-falcon-42",
  "type": "command_approval",
  "decision": "accept"
}
```

**Decision guidance:**
- `accept` — let the agent run the command
- `reject` — block the command; agent may try an alternative or ask again

Review the `command` field before accepting. Be cautious with destructive commands (`rm -rf`, `git reset --hard`, etc.).

### file_approval — Agent wants to modify files

The agent wants to write or modify files. The `fileChanges` array shows paths and patches.

**wait-task response:**
```json
{
  "status": "input_required",
  "pending_question": {
    "type": "file_approval",
    "requestId": "req-3",
    "fileChanges": [
      { "path": "src/config.ts", "patch": "+export const API_URL = ..." },
      { "path": "package.json", "patch": "+\"express\": \"^4.18.0\"" }
    ]
  }
}
```

**respond-task call:**
```json
{
  "task_id": "bold-falcon-42",
  "type": "file_approval",
  "decision": "accept"
}
```

### elicitation — MCP server confirmation

An MCP server the agent is using wants confirmation for an operation.

**wait-task response:**
```json
{
  "status": "input_required",
  "pending_question": {
    "type": "elicitation",
    "requestId": "req-4",
    "serverName": "database-mcp",
    "message": "Allow read access to production database?",
    "schema": {}
  }
}
```

**respond-task call:**
```json
{
  "task_id": "bold-falcon-42",
  "type": "elicitation",
  "action": "accept"
}
```

Or to decline:
```json
{
  "task_id": "bold-falcon-42",
  "type": "elicitation",
  "action": "decline"
}
```

**Note:** Unanswered elicitations auto-decline after 30 seconds.

### dynamic_tool — Agent invoked a custom tool

The agent called a tool that requires external execution. You provide the result.

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

**respond-task call (success):**
```json
{
  "task_id": "bold-falcon-42",
  "type": "dynamic_tool",
  "result": "All 12 benchmarks passed. Mean latency: 45ms."
}
```

**respond-task call (error):**
```json
{
  "task_id": "bold-falcon-42",
  "type": "dynamic_tool",
  "error": "Benchmark suite not found."
}
```

## Multiple pauses in sequence

An agent may pause multiple times during a single task. After each respond-task, call wait-task again. The cycle continues until the task reaches a terminal state.

```
spawn → wait → input_required (question 1)
  → respond → wait → input_required (question 2)
  → respond → wait → input_required (command approval)
  → respond → wait → completed
```

## Auto-approve strategy

For trusted environments where you want maximum autonomy:

```
while wait-task returns input_required:
  if pending_question.type == "command_approval":
    respond with decision: "accept"
  elif pending_question.type == "file_approval":
    respond with decision: "accept"
  elif pending_question.type == "user_input":
    respond with best-guess answers
  elif pending_question.type == "elicitation":
    respond with action: "accept"
  wait-task again
```

For untrusted environments, always review before responding.

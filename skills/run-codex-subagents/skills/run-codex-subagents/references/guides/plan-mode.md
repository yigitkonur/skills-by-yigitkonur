# Plan Mode

Plan-first collaboration mode for Codex tasks.

## What it does

When `--plan` is passed, the Codex agent creates an execution plan **before** writing any code. The plan appears as `PLAN` events in the event stream and shows structured steps with status tracking.

## When to use

| Effort | Recommendation |
|--------|----------------|
| `none` / `minimal` / `low` | Skip — overhead not worth it |
| `medium` | **Use `--plan`** — helps structure multi-step work |
| `high` / `xhigh` | **Always use `--plan`** — essential for complex tasks |

## Usage

```bash
# Plan-first with follow (recommended)
cli-codex-subagent run task.md --follow --plan --auto-approve --compact

# Plan-first with steer (continue in session)
cli-codex-subagent task steer tsk_abc123 followup.md --follow --plan --compact

# Explicitly skip planning
cli-codex-subagent run task.md --follow --no-plan --auto-approve
```

`--no-plan` is the default behavior — the agent proceeds directly without creating a plan first.

## Event stream

With `--plan`, the event stream includes `PLAN` tags:

```
TURN    019d786c-...
PLAN    Step 1: Analyze existing code [done]
PLAN    Step 2: Implement auth middleware [inProgress]
CMD     cat src/middleware.ts ✓ exit 0
FILE    src/middleware/auth.ts (created)
PLAN    Step 2: Implement auth middleware [done]
PLAN    Step 3: Write and run tests [pending]
...
```

## Protocol details

The `--plan` flag sets `collaborationMode` in the turn/start request:

```json
{
  "collaborationMode": {
    "mode": "plan",
    "settings": {
      "model": "<selected-model>",
      "reasoning_effort": "<effort-level>",
      "developer_instructions": null
    }
  }
}
```

The Codex runtime responds with `turn/plan/updated` notifications containing:

```json
{
  "method": "turn/plan/updated",
  "params": {
    "turnId": "019d76fa-3314-...",
    "explanation": "Here's my plan...",
    "plan": [
      { "step": "Analyze existing code", "status": "done" },
      { "step": "Implement middleware", "status": "inProgress" },
      { "step": "Write tests", "status": "pending" }
    ]
  }
}
```

Plan text also streams incrementally via `item/plan/delta` events.

## Best practices

1. **Always pair with `--follow`** — otherwise you can't see the plan
2. **Use `--compact`** for clean plan output without verbose tool details
3. **Combine with `--effort medium` or higher** — low-effort tasks don't benefit from planning
4. **For parallel dispatch**, skip `--plan` — fire-and-forget tasks should execute directly

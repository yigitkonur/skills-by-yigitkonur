# Herdr primitives

Read only for command syntax, targeting or an explicitly requested remote target.
The installed CLI's relevant help is authoritative; these forms were inspected
on Herdr 0.9.1. This is not proof of live harness behavior on every installation.

## Discovery and target identity

```bash
herdr --help
herdr pane current --current
herdr agent start --help
herdr agent prompt --help
herdr agent wait --help
```

Require `HERDR_ENV=1` and successful current-pane lookup before session control.
Parse returned workspace/tab/pane/terminal IDs; target a verified pane or agent,
not a terminal ID. Opaque IDs are not inferred from labels or environment vars.
Agent names must be unique and match `[a-z][a-z0-9_-]{0,31}` on inspected builds.

## One-operation commands

```bash
herdr tab create --workspace "$WORKSPACE_ID" --cwd "$CHECKOUT" --label "$LABEL" --no-focus
herdr pane layout --pane "$PANE_ID"
herdr pane split --pane "$PANE_ID" --direction right --cwd "$CHECKOUT" --no-focus
herdr agent start "$NAME" --kind agy --pane "$PANE_ID" --timeout 30000 -- --model gemini-3.8-flash --effort high
herdr agent prompt "$TARGET" "$TEXT"
herdr agent wait "$TARGET" --timeout 30000
herdr agent get "$TARGET"
herdr agent read "$TARGET" --source visible --lines 30
herdr pane process-info --pane "$PANE_ID"
herdr pane send-text "$PANE_ID" "$TEXT"
herdr pane send-keys "$PANE_ID" enter
herdr pane close "$PANE_ID"
```

These are syntax examples, not a script to run sequentially. Text injection only
happens into a verified foreground composer. `send-text` does not submit Enter;
`agent prompt` does. No invented `pane close --pane`, `pane layout --workspace`,
`herdr wait`, or instruction-mode CLI flags.

Read create/start results before the next operation. A timeout/error may leave a
created tab, worktree or running process. Reconcile before repeating mutations.
Respect `--no-focus`; CLI operations should not steal the user's working pane.

## Remote machines

Use remote targeting only when the user explicitly scopes the task to that
machine. Read installed machine/SSH help and inventory before connecting.
Do not change the global active machine as a side effect of a local job, stop
servers, expose ports or create credentials merely to repair missing context.
Validate caller and project identity on the intended machine; a local live pane
ID is not evidence that the remote target belongs to this assignment.

# Async Tasks

`mcpc 0.2.x` has real public task support.
Use this guide instead of old `0.1.11` advice that told you to avoid task workflows.

## When to use task mode

Reach for it when either of these is true:

- the tool metadata shows `taskSupport: required`
- the tool can run long enough that you want streamed progress or a detached task ID

Inspect the tool first:

```bash
mcpc @session tools-list --full
mcpc --json @session tools-get simulate-research-query | jq '.execution'
```

## Modes

### Plain call

```bash
mcpc @session tools-call tool-name arg:=value
```

Use this for normal tools and for tools whose execution says `taskSupport: forbidden`.

### Wait for result with `--task`

```bash
mcpc @everything-http tools-call simulate-research-query topic:='"mcpc tasks"' --task
```

Use this when you want the final result body in the CLI.

### Detach with `--detach`

```bash
mcpc --json @everything-http tools-call simulate-research-query topic:='"mcpc detach"' --detach
mcpc --json @everything-http tasks-get <taskId>
mcpc --json @everything-http tasks-list
mcpc @everything-http tasks-cancel <taskId>
```

Use this when the task ID is enough for orchestration.
In `0.2.4`, `tasks-get` returns task status information, not the original result payload.
There is no standalone `tasks-result` command.

## Common outcomes

- `task:required`: plain `tools-call` fails until you add `--task` or `--detach`
- `task:forbidden`: `--task` or `--detach` will fail because the server does not want task execution for that tool
- completed detached tasks can still appear in `tasks-list`, but you do not recover the original result body there

## Good verification target

The Everything server's `simulate-research-query` tool is the fastest way to confirm current task behavior.

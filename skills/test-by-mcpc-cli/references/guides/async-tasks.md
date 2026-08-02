# Async Tasks

`mcpc 0.6.0` has full async task support: start a task, walk away, come back in a
later invocation and pull the real result. Verified against 0.6.0.

## When to use task mode

Reach for it when either of these is true:

- the tool's `execution.taskSupport` is `required` (shown as `[task:required]` in
  `tools-list --full`)
- the tool can run long enough that you want streamed progress or a detached task ID

Inspect the tool first:

```bash
mcpc @session tools-list --full
mcpc --json @session tools-get simulate-research-query | jq '.execution'
```

`tools-list --full` annotates each tool inline: `[task:optional|required|forbidden]`.

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

Blocks with a progress spinner and returns the final result body in the CLI. Under the
hood this is create-task → poll → fetch-result; the returned payload still carries
`_meta["io.modelcontextprotocol/related-task"].taskId` for later reference.
Ctrl+C (or ESC) detaches instead of killing the task: it keeps running server-side and
mcpc prints the task ID plus recovery commands.

### Detach with `--detach`

```bash
mcpc --json @everything-http tools-call simulate-research-query topic:='"mcpc detach"' --detach
mcpc --json @everything-http tasks-get <taskId>
mcpc --json @everything-http tasks-list
mcpc --json @everything-http tasks-result <taskId>
mcpc @everything-http tasks-cancel <taskId>
```

`--detach` returns `{ taskId, status }` instantly (implies `--task`). Use this when the
task ID is enough for orchestration, and fetch the real payload later — even from a
separate process — with `tasks-result`.

## `tasks-result` — the standalone result command

`tasks-result <taskId>` exists (since v0.2.6) and blocks until the task reaches a
terminal state, then returns the actual `CallToolResult` payload (`--json` gives the
raw MCP shape: `{ content, isError?, structuredContent? }`). This works across process
invocations: start a task in one shell, fetch its result from a completely different
one, once `tasks-get`/`tasks-list` shows it `completed`.

`tasks-get`/`tasks-list` report status only (`{ taskId, status, ttl, createdAt,
lastUpdatedAt, statusMessage?, pollInterval? }`) — they never carry the result body.
`tasks-result` is the only command that returns it. Shares the same `isError` → exit-2
rendering as `tools-call`.

A cancelled task's `tasks-result` fails cleanly: `Task <id> has no result stored` (exit
2), not a crash — cancellation pre-empts the result, it does not corrupt it.

## Common outcomes

- `task:required`: plain `tools-call` fails until you add `--task` or `--detach`
- `task:forbidden`: `--task` or `--detach` fail because the server does not want task
  execution for that tool
- `--task`/`--detach` against a tool/server with no task support **fail with an error**
  — since 0.6.0 they no longer silently fall back to a synchronous call
- completed detached tasks appear in `tasks-list`/`tasks-get` (status only); recover the
  original result body with `tasks-result`
- on servers using MCP protocol 2026-07-28, task commands (`tasks-list`, `tasks-get`,
  `tasks-result`, `tasks-cancel`, `tools-call --task/--detach`) report the tasks
  extension as not yet supported — tasks keep working unchanged on 2025-11-25 servers.
  See `references/guides/protocol-versions.md` for the full protocol-version story.

## Good verification target

The Everything server's `simulate-research-query` tool (`[task:required]`) is the
fastest way to confirm current task behavior end to end.

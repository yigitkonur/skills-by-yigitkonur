# Common Errors

## `Unknown command` after a URL target

You are probably using pre-0.2.0 syntax such as:

```bash
mcpc https://host/mcp tools-list
mcpc https://host/mcp connect @demo
```

Fix it by connecting first:

```bash
mcpc connect https://host/mcp @demo
mcpc @demo tools-list
```

## `Error: Unknown option: --clean=sessions`

`--clean=...` was replaced in `0.2.0`. `mcpc clean sessions` removes **all** sessions, including live ones; use bare `mcpc clean` for stale-only cleanup.

## `Server "<name>" not found in config file`

Check both of these:

- the config root key is `mcpServers`
- the connect target is `file:entry`, for example `mcpc connect .vscode/mcp.json:filesystem @fs`

The error lists available server names from the file, so a typo'd entry is easy to spot. Relative `file:entry` paths (e.g. `docs/mcp-config.json:fs`) are correctly parsed as config references, not URLs — fixed since 0.3.0, which previously misinterpreted them as HTTP targets.

## Session created but calls fail immediately

`mcpc connect` can exit `0` before transport establishment. An unreachable server creates a non-live `connecting` or `reconnecting` session, and subsequent commands exit `1` until it connects; close it if the target is wrong. A host root is not always the MCP endpoint: `https://research-mcp.yigitkonur.com/mcp` works, while `https://research-mcp.yigitkonur.com` does not.

## `tools-call --task`/`--detach` errors instead of running

Since 0.6.0, `--task`/`--detach` on a connection that can't back it **fails outright** — no more silent fallback to a synchronous call. Two distinct messages, both exit `2`:

- no tasks at all on this protocol (2026-07-28 moved tasks to an unsupported extension): `Tasks are not available on this connection: MCP 2026-07-28 moved tasks to the io.modelcontextprotocol/tasks extension, which is not supported yet. Task commands currently work only on servers using protocol 2025-11-25`
- server doesn't advertise the capability: `This server does not support task-augmented tool calls (no tasks.requests.tools.call capability), so --task/--detach cannot be used. Re-run the command without them to call the tool synchronously`

Fix: drop `--task`/`--detach` for a plain sync call, or check `tools-list` for the tool's `[task:optional|required|forbidden]` annotation first.

## Tool call exits non-zero

For `tools-call` and `tasks-result`, exit `2` is a reliable signal since v0.5.0 — any `isError: true` result exits `2`. Still inspect the JSON payload for the reason. Common causes:

- argument shape mismatch, such as `queries:=OpenAI` instead of a JSON array
- a `task:required` tool called without `--task` or `--detach`
- an unknown tool name, a schema-validation rejection, or a runtime failure inside the tool

Exit code alone is *not* sufficient for other command families (e.g. `resources-read` writing to a file, or any "found nothing" case not modeled as `isError`) — payload inspection is the richer signal there.

`tasks-result <taskId>` (available since 0.2.6; works cross-process) blocks until the task is terminal and returns the final `CallToolResult` — including when called from a different shell/process than the one that started the task with `--detach`. Fetching a cancelled task's result fails cleanly (exit `2`, "has no result stored"), not a crash.

## `mcpc restart @name` on a session that doesn't exist

```
$ mcpc restart @nonexistent
Error: Session not found: @nonexistent
```

Exits `1` (a CLI usage error, not an MCP round-trip) — the name was never created, so there is nothing to restart. Use `mcpc` (no args) to see the sessions that actually exist.

## Session stuck in `unauthorized`, `expired`, or `disconnected`

`mcpc` (bare) prints a recovery hint under each non-live session. `expired` needs `mcpc @session restart`. `unauthorized` needs `mcpc login <server>` then `mcpc @session restart` — a session using a static bearer/`-H` header stays `unauthorized` and does not auto-retry (fixed in 0.3.0, so it no longer flip-flops between `unauthorized` and `connecting` on every invocation); an OAuth-profile session does auto-retry in the background, since a sibling session sharing the profile may have refreshed the token. `disconnected` (bridge alive, server gone quiet >2min) usually self-recovers; `mcpc @session restart` forces a fresh connection if it stays stuck. Inspect `mcpc --json` for the exact status field, then clean stale records if needed:

```bash
mcpc clean
```

## HTTP server works in a browser, but `mcpc` fails

Check whether the server is actually Streamable HTTP.
If the bridge log shows `Cannot POST /sse` or `Cannot POST /`, you are probably pointing `mcpc` at an SSE endpoint. For a stdio server, `mcpc connect` failures now include a tail of the child process's captured stderr (since 0.3.0) — check `mcpc @session logs` for the full picture (missing TLS trust, proxy vars, or credentials are common causes).

If an established stdio session instead returns `Error: Failed to list tools: Not connected. For details, run: mcpc @session logs` (exit `2`) while its status stays `live`, the child died under a surviving bridge. Run `mcpc @session ping` for a one-shot recovery attempt; it triggers bridge restart/retry. If you need deterministic recovery before another command, use `mcpc restart @session` instead.

## `server-discover` fails on an older connection

```
$ mcpc @session server-discover
Error: server/discover is not available on this connection: it was introduced in
MCP 2026-07-28, and this connection negotiated 2025-11-25, where the initialize
handshake carries the same information. Run "mcpc @session" to see it, or
"mcpc @session ping" to check liveness
```

Exits `2`. Not a bug — `server/discover` only exists on 2026-07-28 connections; `mcpc @session` and `mcpc @session ping` are the working alternatives on older negotiated versions.

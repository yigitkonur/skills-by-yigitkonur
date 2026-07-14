# Common Errors

## `Unknown command` after a URL target

You are probably using `0.1.11` syntax such as:

```bash
mcpc https://host/mcp tools-list
mcpc https://host/mcp connect @demo
```

Fix it by connecting first:

```bash
mcpc connect https://host/mcp @demo
mcpc @demo tools-list
```

## `Unknown option '--clean=...'`

Use the command form instead:

```bash
mcpc clean sessions
```

## `Entry not found` or config target confusion

Check both of these:

- the config root key is `mcpServers`
- the connect target is `file:entry`, for example `mcpc connect .vscode/mcp.json:filesystem @fs`

## Session created but calls fail immediately

The MCP path is probably wrong.
A host root is not always the MCP endpoint.
For example, `https://research.yigitkonur.com/mcp` works, while `https://research.yigitkonur.com` does not.

## Tool call exits `0` but still failed

Inspect the JSON payload.
You likely have `isError: true`.
Common causes:

- argument shape mismatch, such as `queries:=OpenAI` instead of a JSON array
- sampling demo tools on Everything returning `Method not found`
- a `task:required` tool called without `--task` or `--detach`

## `tasks-get` does not show the final result body

That is current `0.2.4` behavior.
Use `--task` when you need the final result in the CLI.
Do not expect a standalone `tasks-result` command.

## Session stuck in `unauthorized` or `expired`

Inspect `mcpc --json` status, then either reconnect with the right auth mode or clean stale session records:

```bash
mcpc clean sessions
```

## HTTP server works in a browser, but `mcpc` fails

Check whether the server is actually Streamable HTTP.
If the bridge log shows `Cannot POST /sse` or `Cannot POST /`, you are probably pointing `mcpc` at an SSE endpoint.

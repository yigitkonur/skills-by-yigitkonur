# Data Model

Use live JSON output as the contract you script against, verified against 0.6.0.

## Top-level `mcpc --json`

Current output is shaped like:

```json
{
  "sessions": [
    {
      "name": "@research-test",
      "server": { "url": "https://research-mcp.yigitkonur.com/mcp" },
      "createdAt": "...",
      "lastConnectionAttemptAt": "...",
      "lastSeenAt": "...",
      "status": "live",
      "pid": 12345,
      "protocolVersion": "2025-11-25",
      "serverInfo": { "name": "...", "version": "..." },
      "capabilities": { "tools": { "listChanged": true }, "...": "..." },
      "mcpSessionId": "...",
      "stateless": false,
      "hasInstructions": false
    }
  ],
  "profiles": [
    {
      "name": "default",
      "serverUrl": "https://mcp.example.com/mcp",
      "authType": "oauth",
      "createdAt": "..."
    }
  ]
}
```

`stateless` is tri-state (`true | false | null`, always present, never omitted) — `true` for
2026-07-28 stateless servers, `false` for stateful (session-ID-bearing) connections, `null` while
undetermined. `hasInstructions` reports only whether the server sent instructions text; the text
itself is excluded here ("can be kilobytes per session") — fetch it with `mcpc --json @<session>`.
`activeTasks` and `resourceSubscriptions` are real fields on the session object but only appear
when non-empty.

## Session JSON from `mcpc --json @session` / `connect --json`

Both return an extended MCP `InitializeResult` (2025-11-25 connections) or `DiscoverResult`
(2026-07-28 connections), with an `_mcpc` metadata block layered in:

```json
{
  "_mcpc": {
    "sessionName": "@research-test",
    "profileName": "default",
    "server": { "url": "https://research-mcp.yigitkonur.com/mcp" },
    "transport": "streamable-http",
    "stateless": false,
    "logPath": "/root/.mcpc/logs/bridge-@research-test.log",
    "resourceSubscriptions": []
  },
  "protocolVersion": "2025-11-25",
  "supportedVersions": ["2026-07-28", "2025-11-25"],
  "capabilities": { "...": "..." },
  "serverInfo": { "name": "...", "version": "..." },
  "instructions": "...",
  "_meta": { "...": "..." },
  "toolNames": ["plan-research", "web-search", "extract-evidence", "review-research"]
}
```

- `_mcpc.transport` (0.6.0) — the wire transport name, e.g. `"streamable-http"`.
- `_mcpc.stateless` — same tri-state semantics as above.
- `_mcpc.logPath` — bridge log file for this session (0.3.1). Log file size is deliberately not
  included; `stat` the path or run `mcpc @<session> logs` for a fresh read.
- `supportedVersions` / `_meta` — only present on 2026-07-28 connections (from `server/discover`).
- Schemas: `https://modelcontextprotocol.io/specification/2025-11-25/schema#initializeresult` and
  `https://modelcontextprotocol.io/specification/2026-07-28/schema#discoverresult`.

## Status vocabulary

CLI-facing JSON (`status` field, derived by `getBridgeStatus()`) uses exactly these 7 states:

- `live`
- `connecting`
- `reconnecting`
- `disconnected`
- `crashed`
- `unauthorized`
- `expired`

Internal persisted `status` on disk (`SessionStatus`) is a related but not identical, smaller
vocabulary (`active | connecting | reconnecting | unauthorized | expired | crashed` — no
`disconnected`, and persisted `active` maps to displayed `live`/`disconnected` depending on
`lastSeenAt` recency). Do not assume the on-disk file shape is the stable public API — script
against `mcpc --json`, not against `~/.mcpc/sessions.json` directly.

## Task data

`SessionData` persists `activeTasks` (task ID → `{taskId, toolName, createdAt}`) for crash
recovery. Public task support is a first-class command surface: `tools-call --task`,
`tools-call --detach`, and `tasks-list`/`tasks-get`/`tasks-result`/`tasks-cancel` — including
`tasks-result`, which blocks until the final result is ready and works across process
invocations (a `--detach` in one shell, `tasks-result` from a fresh shell later, both against the
same task ID). `tasks-result` shares `renderCallToolResult()` with `tools-call`: `isError: true`
in the result sets exit code 2 in both human and `--json` modes.

## Error JSON shape

CLI errors in `--json` mode always include an exit `code` field alongside `error`/`message`:

```json
{ "error": "ClientError", "message": "...", "code": 1, "details": "..." }
```

`code` matches the exit-code contract: `1` client error, `2` server/tool error, `3` network
error, `4` auth error.

## Storage notes

- credentials prefer OS keychain and fall back to `~/.mcpc/credentials.json` (mode `0600`)
- x402 wallets prefer keychain and fall back to `~/.mcpc/wallets.json`
- session logs live in `~/.mcpc/logs/bridge-@session.log`, rotated to `.log.1`–`.log.5`; read
  via `mcpc @session logs` rather than the raw file
- `~/.mcpc/sessions.json` is file-locked for concurrent access; corrupted files are now backed
  up and reported instead of silently reset (0.5.0 fix)

## Config example

```bash
mcpc connect ~/.vscode/mcp.json:filesystem @fs
```

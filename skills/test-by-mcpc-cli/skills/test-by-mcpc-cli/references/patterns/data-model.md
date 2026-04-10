# Data Model

Use live JSON output as the contract you script against.

## Top-level `mcpc --json`

Current output is shaped like:

```json
{
  "sessions": [
    {
      "name": "@research-test",
      "server": { "url": "https://research.yigitkonur.com/mcp" },
      "createdAt": "...",
      "lastConnectionAttemptAt": "...",
      "lastSeenAt": "...",
      "status": "live",
      "protocolVersion": "2025-11-25",
      "serverInfo": { "name": "...", "version": "..." },
      "mcpSessionId": "...",
      "notifications": { "tools": {}, "prompts": {}, "resources": {} },
      "activeTasks": {}
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

## Session JSON from `mcpc --json @session`

Expect fields such as:

- `_mcpc.sessionName`
- `_mcpc.server`
- `protocolVersion`
- `capabilities`
- `serverInfo`
- `tools`

## Status vocabulary

CLI-facing JSON commonly uses:

- `live`
- `connecting`
- `reconnecting`
- `disconnected`
- `crashed`
- `unauthorized`
- `expired`

Internal persisted status uses a related but not identical vocabulary.
Do not assume the on-disk file shape is the stable public API.

## Task data

`SessionData` can include `activeTasks`.
Public task support now exists through `tools-call --task`, `tools-call --detach`, and `tasks-*`.
That means task metadata is no longer just an internal concern.

## Storage notes

- credentials prefer OS keychain and fall back to `~/.mcpc/credentials.json`
- x402 wallets prefer keychain and fall back to `~/.mcpc/wallets.json`
- session logs live in `~/.mcpc/logs/bridge-@session.log`
- shell history lives in `~/.mcpc/shell-history`

## Config example

```bash
mcpc connect ~/.vscode/mcp.json:filesystem @fs
```

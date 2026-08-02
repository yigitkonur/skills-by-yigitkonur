# Config Resolution

`mcpc connect` (`0.6.0`) accepts four server-argument shapes: a bare host, a single
`file:entry`, a bare config file (bulk — every entry), or no argument at all
(auto-discover every standard config and connect everything). Use `file:entry` to target
one stdio (or HTTP) entry inside a config file.

## Expected file shape

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

VS Code's `"servers"` key is also accepted — normalized to `mcpServers` internally, so a
file that uses `"servers"` instead of `"mcpServers"` still works without edits.

## Connect forms

```bash
mcpc connect ~/.vscode/mcp.json:filesystem @fs   # one entry (file:entry)
mcpc connect ~/.vscode/mcp.json                  # every entry in the file (bulk)
mcpc connect                                     # auto-discover configs, connect everything
```

## Bulk connect (bare config file, no `:entry`)

Passing a config file with no `:entry` suffix connects **every** server defined in it in
one call, auto-generating a session name per entry from the entry name. Bulk connects:

- **do not accept an explicit `@session` name** — only single-entry (`file:entry`)
  connects can be named.
- **skip stdio (command-based) entries by default** — stdio entries spawn a local process
  on connect, so mcpc only launches them for configs you've explicitly opted into
  trusting. Pass `--stdio` to include them: `mcpc connect ~/.vscode/mcp.json --stdio`.
  Single-entry (`file:entry`) connects are unaffected by this gating.
- wait for every connection to finish (each entry shown `created`/`active`/`failed`,
  bounded by `--timeout`) before returning, rather than reporting an optimistic
  "connecting" status.

## Auto-discovery (no server argument)

`mcpc connect` with no server argument scans the working directory and home directory for
standard MCP config files — `.mcp.json`, `mcp.json`, `mcp_config.json`, `.cursor/mcp.json`,
`.vscode/mcp.json`, `.kiro/settings/mcp.json`, `~/.claude.json`,
`~/.codeium/windsurf/mcp_config.json`, plus VS Code and Claude Desktop config locations —
and connects every server found across all of them, applying the same bulk-connect rules
above (no `@session`, stdio skipped unless `--stdio`). Duplicate session names are
deduplicated, with project-scoped configs winning over global ones.

## Session reuse across all connect forms

`@session` is optional on a single-entry connect; if omitted, mcpc auto-generates a name
from the server host or config entry name. A **matching session — same server URL, same
profile, same set of header keys — is reused** instead of duplicated; anything that
differs on any of those three creates a new session.

## URL normalization

- non-local bare hosts get `https://`
- localhost-style targets keep `http://`
- the path still matters, so `research-mcp.yigitkonur.com/mcp` is not the same as
  `research-mcp.yigitkonur.com`

## `--protocol-version` pinning

Pass `--protocol-version <version>` (e.g. `--protocol-version 2025-11-25`) on `connect` to
pin one exact MCP protocol version instead of letting mcpc auto-negotiate the newest
version both sides support (mcpc's negotiation range is `2026-07-28` down to `2024-10-07`).
The connection fails outright if the server doesn't offer the pinned version — no fallback.
Also settable as a `protocolVersion` field on an individual `mcp.json` config entry.

## Common mistakes

- assuming a bare config file only connects one entry — it connects **all** of them
- expecting `@session` to work on a bulk connect (file or auto-discovery) — it's rejected
- forgetting stdio entries are skipped by default on bulk connects — pass `--stdio` to
  include them
- omitting the `:entry` suffix when only one server should be connected
- assuming root host URLs are enough when the server is mounted under a subpath like `/mcp`

## Stdio security note

Config entries with a `command` field spawn a local process on connect — even if the MCP
handshake afterward fails. Only connect to (or bulk-connect/auto-discover with `--stdio`
against) config files whose stdio entries you trust.

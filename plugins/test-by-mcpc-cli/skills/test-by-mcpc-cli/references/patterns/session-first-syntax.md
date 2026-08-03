# Session-First Syntax Migration

Use this table when translating pre-`0.2.0` (`0.1.11`) examples to current `0.6.0` syntax.
Every "Current pattern" below is still correct at `0.6.0`.

| Old pattern | Current pattern |
|---|---|
| `mcpc mcp.example.com connect @demo` | `mcpc connect mcp.example.com @demo` |
| `mcpc --config .vscode/mcp.json filesystem connect @fs` | `mcpc connect .vscode/mcp.json:filesystem @fs` |
| `mcpc mcp.example.com tools-list` | `mcpc connect mcp.example.com @demo` then `mcpc @demo tools-list` |
| `mcpc --clean=sessions` | `mcpc clean sessions` |
| `mcpc x402 sign -r <base64>` | `mcpc x402 sign <payment-required>` |
| `mcpc tools` / `mcpc resources` / `mcpc prompts` (shorthand, removed `0.3.0`) | `mcpc @session tools-list` / `resources-list` / `prompts-list` |
| `mcpc @session tools/list` (raw MCP JSON-RPC method name) | Works since `0.6.0` — undocumented alias for `tools-list`; same session-first ordering, `mcpc help tools/list` does not resolve it |

## Migration rules

- command-first for `connect`, `login`, `logout`, `clean`, `x402`, unscoped `grep`, and canonical `close @session` / `restart @session` (`@session close` / `@session restart` also work)
- session-first for server operations and scoped `grep`: `mcpc @session <command>` — for these commands, putting `@session` after the command (`mcpc tools-list @session`) fails with "Missing session target for command", confirmed live against `mcpc 0.6.0`
- `file:entry` instead of the old `--config file entry` surface
- no direct one-shot server commands — `connect` first, always
- the interactive `shell` command was deprecated in `0.3.1` and removed in `0.4.0` — no replacement; run individual `mcpc @session <command>` calls instead

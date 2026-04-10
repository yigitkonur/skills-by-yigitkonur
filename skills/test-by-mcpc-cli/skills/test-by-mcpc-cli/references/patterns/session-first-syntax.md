# Session-First Syntax Migration

Use this table when translating `0.1.11` examples to `0.2.x`.

| Old pattern | Current pattern |
|---|---|
| `mcpc mcp.example.com connect @demo` | `mcpc connect mcp.example.com @demo` |
| `mcpc --config .vscode/mcp.json filesystem connect @fs` | `mcpc connect .vscode/mcp.json:filesystem @fs` |
| `mcpc mcp.example.com tools-list` | `mcpc connect mcp.example.com @demo` then `mcpc @demo tools-list` |
| `mcpc --clean=sessions` | `mcpc clean sessions` |
| `mcpc x402 sign -r <base64>` | `mcpc x402 sign <payment-required>` |

## Migration rules

- command-first for `connect`, `clean`, `login`, and `logout`
- session-first for server operations after connect
- `file:entry` instead of the old `--config file entry` surface
- no direct one-shot server commands in the released `0.2.x` CLI

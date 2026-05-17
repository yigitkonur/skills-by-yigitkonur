# `mcp-use introspect` Tombstone

`mcp-use introspect` is not a shipped command in the CLI dependency installed by `mcp-use@1.26.0` (`@mcp-use/cli@3.1.2`). Do not document workflows that depend on it.

## Use instead

| Need | Supported command |
|---|---|
| Connect to a server | `mcp-use client connect <url>` |
| List tools | `mcp-use client tools list` |
| Describe a tool | `mcp-use client tools describe <name>` |
| List resources | `mcp-use client resources list` |
| List prompts | `mcp-use client prompts list` |
| Interactive exploration | `mcp-use client interactive` |

For raw JSON or scripting:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

For richer agent-driven introspection (calling tools, validating schemas), use `test-by-mcpc-cli` (sibling skill in this pack).

## See also

- `../20-inspector/` — interactive web UI for the same data
- `11-mcp-use-generate-docs.md` — tombstone for another non-shipped command name

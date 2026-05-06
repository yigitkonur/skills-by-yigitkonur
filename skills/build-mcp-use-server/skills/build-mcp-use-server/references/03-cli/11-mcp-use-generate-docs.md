# `mcp-use generate-docs` Tombstone

`mcp-use generate-docs` is not a shipped command in the CLI dependency installed by `mcp-use@1.26.0` (`@mcp-use/cli@3.1.2`). Do not document CI or release workflows that depend on it.

## Use instead

| Need | Supported path |
|---|---|
| Human inspection | `mcp-use client ...` commands or the Inspector |
| Raw MCP surface | JSON-RPC requests to `/mcp` |
| Static type surface | `.mcp-use/tool-registry.d.ts` from `mcp-use generate-types` |
| Release docs | Hand-write from source or build a custom script using MCP JSON-RPC |

For raw tool-list output:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## See also

- `09-mcp-use-introspect.md` — tombstone for another non-shipped command name
- `07-mcp-use-generate-types.md` — the supported type-generation command
- `../04-tools/`, `../06-resources/`, `../07-prompts/` — hand-written source material for docs

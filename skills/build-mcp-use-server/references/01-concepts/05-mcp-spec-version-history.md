# MCP Spec Version History

*Read this when you need to understand which MCP protocol features are available in a given v2 release.*

## Separate axes: MCP protocol vs mcp-use framework

**MCP protocol spec** versions (governed by `@modelcontextprotocol/sdk`):
- **v2.0.0** (2025+) — current standard MCP protocol (what mcp-use v2 implements)

**mcp-use package** versions (independent):
- **v2.0.0-beta.66** (shipped; dist-tag `beta`) — the v2 framework shipping now
- **v1.34.5** (shipped; dist-tag `latest`) — v1 end-of-life

This skill teaches MCP **protocol** features as shipped in `@modelcontextprotocol/server@2.0.0`. MCP protocol versions are not the same as mcp-use package versions.

## MCP protocol 2.0.0 features

| Feature | Protocol support | mcp-use v2 support | Notes |
|---------|------------------|-------------------|-------|
| Tools + schemas | v2.0.0 | ✅ Native | Definition-first API; Standard Schema (Zod v4, etc.) |
| Resources | v2.0.0 | ✅ Native | Static + URI templates; completion callbacks |
| Prompts | v2.0.0 | ✅ Native | Completable arguments; message templates |
| Elicitation (input_required) | v2.0.0 | ✅ Native | Form mode; request-state codec for round-tripping |
| Sampling (LLM generation) | v2.0.0 | ❌ **Removed** | Host generates instead; server provides tools |
| Streamable HTTP | v2.0.0 | ✅ Primary | Fetch API handler; stateless per-request |
| Stdio | v2.0.0 | ❌ **Removed** | Use HTTP or raw SDK only |
| Resource subscriptions | v2.0.0 | ✅ Native | `server.notifyResourceUpdated(uri)` |
| Progress tokens | v2.0.0 | ✅ Native | `await ctx.reportProgress(current, total)` |
| MCP Apps views | v2.0.0 | ✅ Native | React components in `views/<name>/view.tsx`; `text/html;profile=mcp-app` MIME |
| Structured content | v2.0.0 | ✅ Native | `structuredContent` field for tool results |

## Capability detection

Query client capabilities at runtime:

```typescript
ctx.client.can("elicitation")       // Form-mode or URL-mode input
ctx.client.supportsViews()           // MCP Apps views supported
ctx.client.extension("io.example")   // Custom extension presence
```

## Version skew handling

Clients using older protocol versions may connect. Degrade gracefully:

```typescript
if (!ctx.client.can("elicitation")) {
  return { content: [{ type: "text", text: "Unsupported" }] };
}
// Proceed with elicitation-dependent flow
```

See `16-client-introspection/02-capabilities.md` for the full surface.

## Migration between mcp-use versions

See cluster `28-migration/` for v1→v2 paths and deprecated-feature removals.

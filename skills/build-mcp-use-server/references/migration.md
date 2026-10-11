# Migration Guide: v1 to v2

*Authoritative migration guide for upgrading older mcp-use servers to v2.*

Official documentation:
- [Server Migration Guide](https://docs.mcp-use.com/v2/typescript/server/migration)
- [Framework Changelog & Breaking Changes](https://docs.mcp-use.com/typescript/changelog/changelog)

---

## Replace Retired Patterns

| Older / Compatibility Pattern | v2 Replacement |
| --- | --- |
| `import { MCPServer } from "mcp-use/server"` | `import { MCPServer } from "mcp-use"` |
| Tool `schema` | Tool `inputSchema`; prompt arguments still use `schema` |
| Inline callback fields `{ callback: ... }` | Pass callback as 2nd argument: `server.tool(def, fn)` |
| Chained `server.tool(...).tool(...)` | Register separately; `server.tool()` returns a typed `ToolRef` |
| Nested resource template config | Top-level `uriTemplate` and `complete` fields |
| Response helpers `text()`, `object()`, `widget()` | Raw JSON-RPC envelopes: `{ content: [...], structuredContent: ... }` |
| `resources/<name>/widget.tsx` | `views/<name>/view.tsx` |
| Tool `widget: { name }` | Tool `view: { name }` |
| `widget({ props, output })` | `{ content, structuredContent, _meta? }` |
| `useWidget()` or `useWidgetProps()` | Destructured `useToolContext<"tool-name">()` |
| Aggregate `McpUseProvider` | Standalone runtime bootstrap; use `<AppsSDKUIProvider linkComponent="a">` |
| Aggregate widget state and host methods | `useViewState`, `useHostContext`, `useDisplayMode`, `useCallTool` |
| Server-side sampling (`ctx.sample()`) | Removed; guide host model with prompts or `<ModelContext>` |
| Imperative elicitation (`ctx.elicit()`) | Replaced with `inputRequired`, `inputResponse`, and `acceptedContent` |

---

## Rebuild Interactive UI

For each rendering tool:
1. Move the entry component to `views/<name>/view.tsx`.
2. Export the tool reference from the server entry (`export const myTool = server.tool(...)`).
3. Add `outputSchema` and `view: { name: "<name>" }`.
4. Return model-readable summary in `content`, typed JSON in `structuredContent`, and private data in `_meta`.
5. Destructure `useToolContext<"tool-name">()` and narrow `status === "pending" | "ready" | "error"`.
6. Style using `@openai/apps-sdk-ui` components, Tailwind 4, and official design tokens.
7. Wrap view trees with `<AppsSDKUIProvider linkComponent="a">`.
8. Move CSP rules to `view.csp`.

---

## Remove Transport & Session Assumptions

Treat callbacks as request-scoped and concurrent:
- Replace active-session registries, session affinity, in-memory user maps, and post-response client targeting with request context (`ctx.requestState`) or an external database.
- Use `ctx.client` strictly for self-reported capabilities (`ctx.client.views`).
- Use `ctx.auth` for verified OAuth user identity.
- Use `basePath` for the MCP endpoint path (default `/mcp`).

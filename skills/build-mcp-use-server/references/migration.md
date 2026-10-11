# Migration Guide: v1 to v2

*Authoritative migration guide for upgrading older mcp-use servers to v2.*

Official documentation:
- [Server Migration Guide](https://docs.mcp-use.com/v2/typescript/server/migration)
- [Framework Changelog & Breaking Changes](https://docs.mcp-use.com/typescript/changelog/changelog)

---

## Replace Retired Patterns

| Older / Compatibility Pattern | v2 Replacement |
| --- | --- |
| Node.js `<22.22.2` / CommonJS | Node.js `>=22.22.2` and ESM (`"type": "module"`). CommonJS is dropped. |
| `import { MCPServer } from "mcp-use/server"` | `import { MCPServer } from "mcp-use"` (subpath removed) |
| `server.getHandler()` | Deprecated. Use `server.fetch` directly for Edge/Fetch runtimes, or `toNodeHandler(server)` from `"mcp-use/node"` for Node.js `http`/Express. |
| Unexported / local tool declarations | Assign every static tool to an exported constant (`export const myTool = server.tool(...)`) for `mcp-env.d.ts` live type inference. |
| Tool `schema` | Tool `inputSchema`; prompt arguments still use `schema` |
| Inline callback fields `{ callback: ... }` | Pass callback as 2nd argument: `server.tool(def, fn)` |
| Chained `server.tool(...).tool(...)` | Register separately; `server.tool()` returns a typed `ToolRef` |
| Nested resource template config | Top-level `uriTemplate` and `complete` fields |
| Response helpers `text()`, `object()`, `widget()` | Raw `CallToolResult` envelopes: `{ content: [...], structuredContent: ... }` |
| Native `array()` helper | Native `array()` no longer wraps items in `{ data }`; return raw envelope with `structuredContent`. |
| Widget URI `ui://widget/<name>.html` | `ui://views/<name>.html` (`text/html;profile=mcp-app`) |
| `resources/<name>/widget.tsx` | `views/<name>/view.tsx` |
| Tool `widget: { name }` | Tool `view: { name }` |
| `widget({ props, output })` | `{ content, structuredContent, _meta? }` |
| `useWidget()` or `useWidgetProps()` | Destructured `useToolContext<"tool-name">()` |
| Aggregate `<McpUseProvider>` | Removed. Views run standalone in self-bootstrapping, auto-resizing iframes. (Optional: `<AppsSDKUIProvider linkComponent="a">` only when using `@openai/apps-sdk-ui`). |
| Aggregate widget state and host methods | `useViewState`, `useHostContext`, `useDisplayMode`, `useCallTool` |
| Server-side sampling (`ctx.sample()`) | Removed; guide host model with prompts or `<ModelContext>` |
| Imperative elicitation (`ctx.elicit()`) | Replaced with `inputRequired`, `inputResponse`, and `acceptedContent` |
| `ctx.req` | `ctx.request` (HonoRequest; access raw Web Request via `ctx.request.raw`) |
| `ctx.log(...)` | `ctx.sendLog(...)` (sends MCP log notification) |
| `ctx.client.supportsApps()` | `ctx.client.supportsViews()` (boolean method) |
| `ctx.user` | `ctx.auth.user` (verified identity under OAuth) |

---

## Rebuild Interactive UI

For each rendering tool:
1. Move the entry component to `views/<name>/view.tsx`.
2. Export the static tool reference from the server entry (`export const myTool = server.tool(...)`).
3. Add `outputSchema` and `view: { name: "<name>" }` to the tool definition.
4. Return concise model-readable text in `content`, typed JSON in `structuredContent`, and View-only data in `_meta`.
5. Destructure `useToolContext<"tool-name">()` and narrow `status === "pending" | "ready" | "error"`.
6. For ChatGPT Apps, style using `@openai/apps-sdk-ui` components, Tailwind 4, and official design tokens. Wrap view trees with `<AppsSDKUIProvider linkComponent="a">` only if using Apps SDK UI components.
7. Move CSP rules to `view.csp`.

---

## Remove Transport & Session Assumptions

Treat callbacks as request-scoped, stateless, and concurrent:
- Replace active-session registries, session affinity, in-memory user maps, and post-response client targeting with external database storage.
- Use `ctx.requestState` strictly as a `RequestStateAccessor` to read opaque state echoed by clients across `input_required` rounds (`ctx.requestState.get()`), not as generic request storage.
- Use `ctx.client.supportsViews()` to inspect whether the client supports interactive MCP App views.
- Use `ctx.auth` for verified OAuth user identity. Never use unverified client hints (`ctx.client.user()`) for authorization.
- Use `basePath` for the MCP endpoint path (default `/mcp`).

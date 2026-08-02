# MCP Apps and Views Terminology

*Read this when you need to understand the vocabulary: MCP Apps, views, resources, and how they bind to tools.*

## Core terms

| Term | v2 meaning | Example |
|------|-----------|---------|
| **MCP Apps** | Protocol standard for rendering React components in iframe sandboxes inside MCP-aware hosts (ChatGPT, Claude Desktop, etc.). MIME type `text/html;profile=mcp-app`. | Tool with view binding renders a React component in ChatGPT sidebar. |
| **View** | React component file at `views/<name>/view.tsx` that renders a tool's structured result. Accessed via `useToolContext<"tool-name">()`. | User searches for "coffee shops", view renders map + list. |
| **Tool view binding** | Config on tool definition that names a view: `view: { name: "search-results", description: "...", ...}`. Requires `outputSchema` on the tool. | `server.tool({ name: "search", outputSchema: z.object(...), view: { name: "results" } }, async ...)` |
| **Structured content** | Result field matching tool's `outputSchema`; passed to view as `useToolContext().output`. | Tool returns `{ structuredContent: { count: 42, items: [...] } }`. |
| **CSP** | Content Security Policy headers on view iframe; controls what domains the view can connect to (API calls, fonts, etc.). Defined on view binding. | `view: { csp: { connectDomains: ["api.example.com"] } }` |

## No "widgets" in v2

v1 used the term **widget** generically. v2 standardizes on **view** because:
- Clearly separates the tool feature (a view binding) from the render artifact (React component)
- Aligns with MCP Apps protocol naming
- Avoids confusion with other widget paradigms (Flutter widgets, etc.)

## Tool-to-view cardinality

**One view per tool.** Each tool can have at most one view binding. If you need multiple visualizations for one tool's output, create separate views and route via tool selection (server-side), not client-side view swapping.

## Default MCP Apps support

All modern mcp-use servers support MCP Apps out of the box. When a host declares `text/html;profile=mcp-app` MIME support, the view renders. If the host doesn't support views, the tool still works (returns text fallback).

See `18-mcp-apps/01-what-are-mcp-apps.md` for detailed MCP Apps protocol and `18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md` for ChatGPT Apps SDK migration context.

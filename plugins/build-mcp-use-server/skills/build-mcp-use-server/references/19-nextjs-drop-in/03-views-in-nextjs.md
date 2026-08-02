# MCP App views in Next.js

*Read this when building MCP App views inside a Next.js project.*

MCP App views in Next.js embedded mode run in browser iframes and receive tool output as props. Each view is a React component in `src/views/<name>/view.tsx` (or your configured views directory).

For full v2 MCP Apps patterns, see references/18-mcp-apps. This file covers only Next.js-specific concerns:

1. **Shared imports:** Views can import browser-safe components and utilities from the Next.js project. Do not import Server Components or modules that depend on `next/headers`, `next/cache`, databases, or the filesystem.

2. **Build output:** Next.js build compiles views to `.mcp-use/build/views/` during `next build`. Assets are served alongside the MCP endpoint.

3. **Asset discovery:** The Next.js `withMcpUse` integration auto-discovers views in the configured `viewsDir` (default `src/views`). No additional registration step needed for embedded mode — views are compiled and served automatically.

4. **CSP configuration:** View CSP metadata is specified inline; see references/18-mcp-apps/05-csp-metadata.md for domain/frame rules.

See references/18-mcp-apps for the complete MCP Apps developer guide: tool `view:` field registration, React hooks (`useToolContext`, `useViewState`, `useSendFollowUp`), component API, and anti-patterns.

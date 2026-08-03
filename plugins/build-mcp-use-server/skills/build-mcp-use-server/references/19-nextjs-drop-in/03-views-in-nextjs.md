# MCP App views in Next.js

*Read this when building MCP App views inside a Next.js project.*

MCP App views in Next.js embedded mode run in browser iframes and receive tool output as props. Each view is a React component in `views/<name>/view.tsx` at the project root by default, or under `<mcpDir>/views` / an explicit `viewsDir` set on `withMcpUse` (see references/19-nextjs-drop-in/02-route-and-file-placement.md). The repository example (`examples/nextjs`) places views under `views/<name>/view.tsx`.

For full v2 MCP Apps patterns, see references/18-mcp-apps. This file covers only Next.js-specific concerns:

1. **Shared imports:** Views can import browser-safe components and utilities from the Next.js project. Do not import Server Components or modules that depend on `next/headers`, `next/cache`, databases, or the filesystem.

2. **Build output:** `withMcpUse` compiles views with Vite into `.mcp-use/build/views/` every time Next evaluates `next.config` (dev and build). Assets are served under `{basePath}/_mcp-use/views/<name>/...` and `{basePath}/_mcp-use/public/...` by the same route handler that serves the MCP endpoint.

3. **Asset discovery:** `withMcpUse` discovers views in the configured `viewsDir` (or the `views/` directory at the project root / `<mcpDir>/views` if unset — there is no `src/views` auto-detection). No additional registration step needed for embedded mode — views are compiled and served automatically. `createNextHandler` reads the build manifest lazily on first request and primes the server's view registry before calling `server.fetch`.

4. **CSP configuration:** View CSP metadata is specified inline; see references/18-mcp-apps/server-surface/05-csp-metadata.md for domain/frame rules.

See references/18-mcp-apps for the complete MCP Apps developer guide: tool `view:` field registration, React hooks (`useToolContext`, `useViewState`, `useSendFollowUp`), component API, and anti-patterns.

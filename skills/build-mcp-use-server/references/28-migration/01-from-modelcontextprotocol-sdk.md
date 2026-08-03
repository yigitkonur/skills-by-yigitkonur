# Adopting mcp-use v2 from raw SDK

*Read this when migrating a raw `@modelcontextprotocol/server` project to mcp-use v2 directly.*

If you have a raw SDK server, adopting mcp-use v2 gives you declarative tools, built-in OAuth providers, HTTP routing, and Views. **For v1→v2 within mcp-use**, see `02-v1-to-v2-overview.md` instead.

## When adoption makes sense

- You are on raw SDK and want simpler tool registration with authentication.
- You want to add Views (MCP Apps) without raw resource/HTML wiring.
- You are starting a new server and want the mcp-use workflow (CLI, Inspector, HMR).

Raw SDK remains the better fit for cases such as:
- Non-HTTP transports (stdio, custom streams) with full control.
- Embedding in specialized runtimes without mcp-use adapters.
- Custom MCP protocol extensions beyond tools/resources/prompts.

## Key conceptual differences

| Aspect | Raw SDK | mcp-use v2 |
|---|---|---|
| Tool registration | `McpServer.registerTool(name, config, callback)` | `server.tool(definition, callback)`; returns an exportable `ToolRef` |
| OAuth | None; app-owned verification | Built-in DCR providers (Clerk, Auth0, Supabase, WorkOS, Keycloak, Better Auth) |
| Response helpers | None; return raw envelopes | Deprecated shims (`text()`, `object()`) + prefer raw `CallToolResult` |
| Views/MCP Apps | Manual HTML + resource registration | Tool `view: { name }` config + generated `views/<name>/view.tsx` |
| HTTP serving | Manual (Express, Hono, plain Node) | Integrated `server.listen(port)` or `server.fetch` |
| Asset serving | App-owned | Integrated CSP, Vite bundling, static `public/` dir |

## Installation

```bash
npm install mcp-use@2.0.0-beta.66 zod@4
```

**Node.js requirement**: >=22.22.2, ESM only.

## Minimal conversion: Raw SDK → mcp-use v2

Raw SDK example (v2 split package `@modelcontextprotocol/server`, `McpServer.registerTool`):
```typescript
import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

const server = new McpServer({ name: "demo", version: "1.0.0" });

server.registerTool(
  "greet",
  {
    description: "Greet someone",
    inputSchema: z.object({ name: z.string() }),
    outputSchema: z.object({ greeting: z.string() }),
  },
  async ({ name }) => {
    const greeting = `Hello ${name}`;
    return {
      content: [{ type: "text", text: greeting }],
      structuredContent: { greeting },
    };
  }
);
```

> The classic `@modelcontextprotocol/sdk` pattern (`new Server(...)` + `server.setRequestHandler(CallToolRequestSchema, ...)` with a schema object as the first argument) is v1-only. The v2 split package's low-level `Server` class takes a **string method name** (`server.setRequestHandler("tools/call", handler)`) for spec methods; `McpServer.registerTool()` (shown above) is the idiomatic v2 declarative equivalent and the closer comparison point for mcp-use's own `server.tool()`.

mcp-use v2 equivalent:
```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "demo", version: "1.0.0" });

export const greet = server.tool(
  {
    name: "greet",
    description: "Greet someone",
    inputSchema: z.object({ name: z.string() }),
    outputSchema: z.object({ greeting: z.string() }),
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello ${name}` }],
    structuredContent: { greeting: `Hello ${name}` },
  })
);

export default server;
```

**Export every static tool** so `mcp-env.d.ts` can register them for View type checking.

## Setup checklist

1. Install `mcp-use@2.0.0-beta.66` and `zod@4`.
2. Create `package.json` with `"type": "module"` and `"engines": { "node": ">=22.22.2" }`.
3. Use the current scaffold's TypeScript baseline (or keep equivalent stricter settings):
   ```json
   {
     "compilerOptions": {
       "target": "ES2024",
       "module": "NodeNext",
       "moduleResolution": "NodeNext",
       "lib": ["ES2024", "DOM", "DOM.Iterable"],
       "jsx": "react-jsx",
       "strict": true,
       "noEmit": true,
       "skipLibCheck": true
     },
     "include": ["index.ts", "server.ts", "mcp-env.d.ts", "src/**/*", "views/**/*", ".mcp-use/**/*.d.ts"]
   }
   ```
4. Scaffold with: `npx create-mcp-use-app@beta --template blank`.
5. Add `mcp-use dev`, `mcp-use build`, `mcp-use start`, `mcp-use typecheck` scripts to `package.json`.

## Authentication migration

**Raw SDK**: Application handles OAuth token verification.

**mcp-use v2**: Use a built-in provider:
```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";

const server = new MCPServer({
  name: "secure-server",
  version: "1.0.0",
  oauth: oauthClerkProvider({ frontendApiUrl: "https://your-clerk-domain.clerk.accounts.dev" }),
});

export const protected = server.tool(
  { name: "protected", inputSchema: z.object({}), outputSchema: z.object({}) },
  async (_, ctx) => {
    console.log(`User: ${ctx.auth.user.id}`); // Verified user
    return { content: [...], structuredContent: {} };
  }
);
```

For custom verification, use `oauthCustomProvider`. `createTokenVerifier(resource)` must return an `OAuthTokenVerifier` object (`{ verifyAccessToken }`), and `mapAuthInfo` reads verified data from `authInfo.extra` (a field your verifier populates) — `authInfo` has no `.claims` property:
```typescript
import { oauthCustomProvider } from "mcp-use/oauth";

const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => ({
    async verifyAccessToken(token) {
      // Your verification logic; must return AuthInfo (token, clientId, scopes, expiresAt, resource, extra)
      return {
        token,
        clientId: "client-123",
        scopes: [],
        expiresAt: Math.floor(Date.now() / 1000) + 3600,
        resource,
        extra: { payload: { sub: "user-123" } }, // your verified claims, any shape you choose
      };
    },
  }),
  oauthMetadata: { /* RFC 8414 metadata */ },
  mapAuthInfo: (authInfo) => ({
    user: { id: (authInfo.extra?.payload as { sub: string })?.sub ?? "unknown" },
    payload: (authInfo.extra?.payload as Record<string, unknown>) ?? {},
    permissions: [],
  }),
});
```

---

**Sister skill** `convert-mcp-sdk-v1-to-v2` covers raw SDK v1→v2 migration.
**Next**: See `02-v1-to-v2-overview.md` if you have an existing v1 mcp-use server.

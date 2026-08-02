# Adopting mcp-use v2 from raw SDK

*Read this when migrating a raw `@modelcontextprotocol/server` project to mcp-use v2 directly.*

If you have a raw SDK server, adopting mcp-use v2 gives you declarative tools, built-in OAuth providers, HTTP routing, and Views. **For v1→v2 within mcp-use**, see `02-v1-to-v2-overview.md` instead.

## When adoption makes sense

- You are on raw SDK and want simpler tool registration with authentication.
- You want to add Views (MCP Apps) without raw resource/HTML wiring.
- You are starting a new server and want the mcp-use workflow (CLI, Inspector, HMR).

Raw SDK stays relevant only for:
- Non-HTTP transports (stdio, custom streams) with full control.
- Embedding in specialized runtimes without mcp-use adapters.
- Custom MCP protocol extensions beyond tools/resources/prompts.

## Key conceptual differences

| Aspect | Raw SDK | mcp-use v2 |
|---|---|---|
| Tool registration | Imperative handlers + schema | Declarative definition-first + callback |
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

Raw SDK example:
```typescript
import { Server } from "@modelcontextprotocol/server";
const server = new Server({ name: "demo", version: "1.0.0" }, { capabilities: { tools: {} } });
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "greet") {
    return { content: [{ type: "text", text: `Hello ${req.params.arguments.name}` }] };
  }
});
```

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
3. Create `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "target": "ES2022",
       "module": "ESNext",
       "moduleResolution": "bundler",
       "lib": ["ES2022"],
       "jsx": "react-jsx"
     }
   }
   ```
4. Scaffold with: `npx create-mcp-use-app@beta --template blank`.
5. Add `mcp-use dev`, `mcp-use build`, `mcp-use start`, `mcp-use typecheck` scripts to `package.json`.

## Authentication migration

**Raw SDK**: Application handles OAuth token verification.

**mcp-use v2**: Use a built-in provider:
```typescript
import { MCPServer, oauthClerkProvider } from "mcp-use/oauth/clerk";

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

For custom verification, use `oauthCustomProvider`:
```typescript
import { oauthCustomProvider } from "mcp-use/oauth";
const oauth = oauthCustomProvider({
  createTokenVerifier: (resource) => async (token) => {
    // Your verification logic
    return { payload: { sub: "user-123", ... } };
  },
  oauthMetadata: { /* RFC 8414 metadata */ },
  mapAuthInfo: (authInfo) => ({
    user: { id: authInfo.claims?.sub ?? "unknown" },
    payload: authInfo.claims ?? {},
    permissions: [],
  }),
});
```

---

**Sister skill** `convert-mcp-sdk-v1-to-v2` covers raw SDK v1→v2 migration.
**Next**: See `02-v1-to-v2-overview.md` if you have an existing v1 mcp-use server.

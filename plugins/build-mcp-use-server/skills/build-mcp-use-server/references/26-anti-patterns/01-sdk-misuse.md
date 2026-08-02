# SDK Misuse

*Read this when a server import, module format, or transport choice may still follow a v1 or raw-SDK pattern.*

## Importing the server from `mcp-use/server`

Do not use the v1 server subpath:

```typescript
import { MCPServer } from "mcp-use/server";
```

v2 exports `MCPServer` from the package root:

```typescript
import { MCPServer } from "mcp-use";
```

A `Cannot find module 'mcp-use/server'` error is not a TypeScript module-resolution problem. Replace the import. See `references/28-migration/03-v1-to-v2-imports-server-and-tools.md`.

## Importing OAuth providers from the root

Do not assume provider factories share the server entry point:

```typescript
import { MCPServer, oauthAuth0Provider } from "mcp-use";
```

Keep the server at the root and import each provider from its provider subpath:

```typescript
import { MCPServer } from "mcp-use";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
```

Provider paths are listed in `references/11-auth/01-overview.md`.

## Using CommonJS

v2 is ESM-only. This fails in an ESM project:

```javascript
const { MCPServer } = require("mcp-use");
module.exports = server;
```

Use `import` and `export`, set `"type": "module"`, and run on Node 22 or newer:

```typescript
import { MCPServer } from "mcp-use";
export default server;
```

Do not solve `require is not defined` by removing ESM mode; migrate the source instead. See `references/02-setup/01-prerequisites.md`.

## Constructing a raw SDK transport

Do not combine mcp-use registration with `StdioServerTransport` or another raw SDK server transport:

```typescript
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
await server.connect(new StdioServerTransport());
```

v2 serves Streamable HTTP. Use `server.listen()` for a Node process, `server.fetch` for Fetch runtimes, or the documented runtime adapters. See `references/09-transports/01-overview.md`.

## Attempting stdio serving

These v1 shapes have no v2 equivalent:

```typescript
await server.listen({ stdio: true });
await server.listen("stdio");
```

Use an HTTP endpoint instead:

```typescript
await server.listen(3000);
```

If a client only accepts stdio, add an external bridge on the client side or choose a compatible client. Do not claim the v2 server can serve stdio. See `references/09-transports/05-no-stdio-and-sse-history.md`.

## Installing a separate React package

Do not install or import `@mcp-use/react`; that package does not exist. React hooks and components come from the `mcp-use/react` subpath:

```tsx
import { ThemeProvider, useToolContext } from "mcp-use/react";
```

See `references/18-mcp-apps/view-react/01-setup-and-providers.md`.

## Correct v2 pattern

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "example-server",
  version: "1.0.0",
});

export const greet = server.tool(
  {
    name: "greet",
    description: "Greet one person by name.",
    inputSchema: z.object({
      name: z.string().describe("Person to greet"),
    }),
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}.` }],
  }),
);

await server.listen(3000);
```
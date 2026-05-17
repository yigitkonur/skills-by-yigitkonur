# Serverless handlers

On platforms that own the HTTP server lifecycle, use `server.getHandler(opts?)` instead of `server.listen()`. The handler is fetch-compatible: `(req: Request) => Promise<Response>`.

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  stateless: true,
})

server.tool({ name: 'hello' }, async () => text('Hello!'))

const handler = await server.getHandler()
```

The package auto-defaults to stateless only when it detects Deno. For other serverless/edge handlers, set `stateless: true` explicitly unless you have designed durable sessions and stream fan-out. See `04-stateless-mode.md` for what becomes unavailable.

For full deploy guides per platform (build configs, env vars, runtime quirks), see `../25-deploy/platforms/`.

## Vercel

The package docs name Vercel Edge Functions as a `getHandler()` integration target, but mcp-use does not provide a Vercel-specific export helper. Keep the mcp-use side to `const handler = await server.getHandler()` and adapt that Request-to-Response function to the route format your Vercel runtime expects.

`baseUrl` should match the public Vercel URL (`https://my-app.vercel.app`) - set `baseUrl` or `MCP_URL`.

## Cloudflare Workers

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'worker-server',
  version: '1.0.0',
  stateless: true,
  allowedOrigins: ['https://app.example.com'],
})

server.tool({ name: 'hello' }, async () => text('Hello!'))

const handler = await server.getHandler()
```

Wire the returned Request-to-Response handler into the Worker entrypoint. Long-lived SSE has platform limits - validate before relying on it.

## Supabase Edge Functions

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'supabase-edge-server',
  version: '1.0.0',
})

server.tool({ name: 'runtime' }, async () => text('supabase-edge'))

const handler = await server.getHandler({ provider: 'supabase' })
```

Pass `{ provider: 'supabase' }` to enable automatic Supabase path rewriting. Supabase runs on Deno, so the constructor defaults to stateless mode.

Source disagreement: https://manufact.com/docs/typescript/server/deployment/supabase currently shows `await server.listen()`, but `mcp-use@1.26.0/package/dist/src/server/mcp-server.d.ts` exposes `getHandler({ provider: 'supabase' })`; package declarations win.

## Deno Deploy

Use the same `server.getHandler()` surface as other Fetch runtimes. Deno defaults to stateless mode; set `baseUrl` or `MCP_URL` explicitly so widget asset URLs use the public origin.

## Cross-platform anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| In-memory `Map` for "sessions" | Cold starts and fan-out destroy it | Stay stateless, or use `RedisSessionStore` |
| Assuming SSE works indefinitely | Platform timeouts cut connections | Treat serverless as request/response unless you've verified the platform |
| Hardcoding `baseUrl` to localhost | Widget assets unreachable | Set `MCP_URL` to the platform's public URL |
| Using `listen()` on a serverless platform | The platform owns the listen socket | Use `getHandler()` |

## Related

- Browser security on public HTTP: `../08-server-config/03-cors-and-allowed-origins.md`
- Public URL behind reverse proxies / platforms: `../08-server-config/02-network-config.md`
- Stateful on serverless (Redis stores): `../10-sessions/`
- Full per-platform deploy guides: `../25-deploy/platforms/`

# Session-Based Proxy

Use the explicit-session form when you already created and initialized an `MCPSession` with the `mcp-use` client SDK:

```typescript
await server.proxy(session, { namespace: "secure" });
```

This is a startup-time composition API. It introspects the session once, registers the upstream tools/resources/prompts on the gateway, and forwards later calls through that same session.

---

## 1. When to Use the Session Form

Use `server.proxy(session, { namespace })` when:

- The upstream connection is fixed for this gateway instance.
- You need headers or client callbacks that the config object can also express, but you want to create the client/session yourself.
- You need a custom connector or manual connection lifecycle before mounting the upstream.

Use the config form in `01-server-proxy-and-gateway.md` for static stdio/HTTP upstreams. Use manual per-call routing (section 3) when credentials differ by caller.

---

## 2. Fixed Authenticated Session

```typescript
import { MCPServer } from "mcp-use/server";
import { MCPClient } from "mcp-use/client";

const server = new MCPServer({ name: "gateway", version: "1.0.0" });

const client = new MCPClient({
  mcpServers: {
    secure: {
      url: "https://secure.example.com/mcp",
      headers: { Authorization: "Bearer service-token" },
    },
  },
});

const session = await client.createSession("secure");

await server.proxy(session, { namespace: "secure" });
await server.listen(3000);
```

Tools from the upstream are exposed as `secure_*`.

---

## 3. Per-Caller Auth: Do Not Proxy Per Request

`server.proxy(session)` binds one upstream session to one namespace. If each caller needs a different bearer token, register the gateway tool yourself and route inside the handler with `session.callTool()`.

```typescript
import { MCPClient, type MCPSession } from "mcp-use/client";
import { MCPServer, error } from "mcp-use/server";
import { z } from "zod";

const gateway = new MCPServer({ name: "gateway", version: "1.0.0" });

type UpstreamHandle = { client: MCPClient; session: MCPSession };
const upstreams = new Map<string, UpstreamHandle>();

async function getUpstreamFor(subject: string, accessToken: string) {
  const cached = upstreams.get(subject);
  if (cached) return cached.session;

  const client = new MCPClient({
    mcpServers: {
      upstream: {
        url: "https://api.example.com/mcp",
        headers: { Authorization: `Bearer ${accessToken}` },
      },
    },
  });

  const session = await client.createSession("upstream");
  upstreams.set(subject, { client, session });
  return session;
}

gateway.tool(
  {
    name: "upstream_search",
    description: "Search via the caller's upstream credentials",
    schema: z.object({ q: z.string() }),
  },
  async ({ q }, ctx) => {
    if (!ctx.auth) return error("Authentication required");

    const session = await getUpstreamFor(
      ctx.auth.user.userId,
      ctx.auth.accessToken
    );
    return session.callTool("search", { q });
  }
);
```

`ctx.client.user()` is client-reported and unverified. Use `ctx.auth.accessToken` and `ctx.auth.user.userId` when upstream authorization depends on verified OAuth identity.

---

## 4. Lifecycle

Close the cached clients on shutdown:

```typescript
process.on("SIGTERM", async () => {
  for (const { client } of upstreams.values()) {
    await client.close().catch(() => {});
  }
  upstreams.clear();
  process.exit(0);
});
```

If an upstream session drops, remove the cached handle and let the next call recreate it:

```typescript
async function safeCall(
  subject: string,
  accessToken: string,
  name: string,
  args: Record<string, unknown>
) {
  try {
    const session = await getUpstreamFor(subject, accessToken);
    return await session.callTool(name, args);
  } catch (e) {
    const cached = upstreams.get(subject);
    await cached?.client.close().catch(() => {});
    upstreams.delete(subject);
    throw e;
  }
}
```

---

## 5. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Calling `server.proxy(session)` inside a tool handler | Re-registers a gateway surface during user traffic | Run `proxy()` once at startup, or route with `session.callTool()` manually. |
| Forwarding `ctx.client.user()?.subject` as a bearer token | User context is client-reported and unverified | Use `ctx.auth.accessToken` from OAuth middleware. |
| Caching only `MCPSession` and never closing the owning `MCPClient` | Leaves connectors open | Keep `{ client, session }` and call `client.close()`. |
| Using one proxied namespace for users with different tool visibility | Proxy introspection runs once | Register explicit gateway tools that enforce per-call policy. |

---

## 6. See Also

- **Static-config proxy** → `01-server-proxy-and-gateway.md`
- **OAuth provider setup** → `../11-auth/01-overview-decision-matrix.md`
- **Verified `ctx.auth` object** → `../11-auth/03-ctx-auth-object.md`
- **Client-reported user context** → `../16-client-introspection/05-extension-and-user.md`
- **MCPClient sessions** → `mcp-use@1.26.0/dist/src/client.d.ts` and `dist/src/session.d.ts`

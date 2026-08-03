# Security hardening for production

*Read this when configuring host/origin validation, CORS, CSP, or handling secrets in Views.*

Production deployments must validate HTTP headers, manage CORS, and prevent View iframes from receiving secrets in tool results (`structuredContent` or result `_meta`).

## Host validation and DNS rebinding

**Localhost-class binds** (`127.0.0.1`, `::1`, `localhost`) automatically reject requests with mismatched `Host` headers. Public binds (`0.0.0.0` behind a reverse proxy) need explicit `allowedHosts`:

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  host: "0.0.0.0",  // Public bind
  allowedHosts: ["api.example.com", "api-staging.example.com"],  // Port-agnostic
});
```

The server rejects requests where the `Host` header does not match any allowed host, preventing DNS rebinding attacks that redirect to internal addresses.

**At localhost:** No explicit config needed; the framework auto-protects.

**At platform edge:** The platform's reverse proxy sets `Host` correctly; your `allowedHosts` list must include the platform's canonical hostname. If your platform assigns a subdomain like `my-app.vercel.app`, add it:

```typescript
allowedHosts: process.env.NODE_ENV === "production"
  ? ["my-app.vercel.app"]
  : undefined,
```

## CORS configuration

CORS is **off by default**. Enable only if Views or external clients need cross-origin access:

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  cors: {
    origin: ["https://app.example.com", "https://chatgpt.openai.com"],
    methods: ["GET", "HEAD", "POST", "OPTIONS"],
    allowedHeaders: ["content-type", "authorization"],
    credentials: true,  // Allow cookies
  },
});
```

**Views and `structuredContent`:** View iframes load assets from `MCP_ASSETS_URL` (read at runtime per request, falling back to `MCP_URL`/the request origin when unset). If assets and MCP endpoints are on different origins, set `cors.origin` to include the View origin.

**ChatGPT integration:** When serving ChatGPT Apps via `server.fetch`, ChatGPT's origin (`https://chatgpt.openai.com`) must be in `cors.origin` if you use `credentials: true`.

## Origin validation

Separate from CORS: `allowedOrigins` validates the `Origin` header on POST requests (non-GET/HEAD only):

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  allowedOrigins: ["https://app.example.com"],  // Port-agnostic
});
```

When unset, origin validation is disabled (SDK-aligned). Localhost-class binds automatically allow `null` origins (sandboxed iframe requests).

## CSP and View asset domains

MCP Apps Views execute JavaScript and load assets. Set `connectDomains`, `resourceDomains`, `frameDomains` in your tool's view configuration to allow View iframes to reach external APIs:

```typescript
export const searchTool = server.tool(
  {
    name: "search",
    description: "Search the catalog",
    inputSchema: z.object({ q: z.string() }),
    outputSchema: z.object({ results: z.array(z.object({ id: z.string() })) }),
    view: {
      name: "search-results",
      description: "Interactive search results",
      csp: {
        connectDomains: ["https://api.example.com"],  // XHR/fetch
        resourceDomains: ["https://cdn.example.com"],  // img src, fonts
        frameDomains: [],  // iframe src (empty = no iframes)
      },
    },
  },
  async ({ q }, ctx) => {
    const results = await search(q);
    return {
      content: [{ type: "text", text: `Found ${results.length} results` }],
      structuredContent: { results },
    };
  }
);
```

On each `resources/read`, the framework merges CSP in this priority order (high to low):

1. Author `view.csp` on the bound tool (above)
2. `CSP_*_DOMAINS` env vars (per category) or the `CSP_URLS` shortcut
3. MCP auto-append: `MCP_URL` → `connectDomains`; the resolved assets origin → `resourceDomains`

`CSP_URLS` and per-category env vars rank above the MCP auto-append; duplicate origins keep the higher-priority entry's position.

Set global domains without touching per-tool code:

```bash
# Shortcut: same domains across all four categories
CSP_URLS=https://api.example.com,https://cdn.example.com

# Or override one category independently
CSP_CONNECT_DOMAINS=https://api.example.com
CSP_RESOURCE_DOMAINS=https://cdn.example.com
CSP_FRAME_DOMAINS=https://embed.example.com
CSP_BASE_URI_DOMAINS=https://myserver.com
```

MCP Apps CSP fields (both on `view.csp` and via env): `connectDomains`, `resourceDomains`, `frameDomains`, `baseUriDomains`.

## Secrets in tool results (`structuredContent` and result `_meta`)

**Do NOT include secrets in `structuredContent`** — Views can read it via `useToolContext()` hooks. Secrets visible in the MCP wire become visible to ChatGPT/Claude/clients.

Separate concerns:

```typescript
// ❌ Wrong: secret in output
return {
  content: [{ type: "text", text: "Order created" }],
  structuredContent: {
    orderId: "123",
    apiKey: process.env.INTERNAL_API_KEY,  // EXPOSED
  },
};

// ✅ Correct: secret stays server-side
const apiKey = process.env.INTERNAL_API_KEY;
const nextOrderId = await getNextOrderId(apiKey);
return {
  content: [{ type: "text", text: `Order created: ${nextOrderId}` }],
  structuredContent: {
    orderId: nextOrderId,  // No secret
  },
};
```

**`_meta` field:** The `_meta` object on results (e.g., `{ content: [...], _meta: { ui: {...} } }`) is returned on the wire and visible to clients. Never store secrets or user-identifying tokens in `_meta`. Use it for View UI hints only (see `references/05-responses/06-meta-and-private-data.md`).

## Request state integrity

When using `input_required` round-trips (elicitation), the client echoes back `requestState`. If state affects authorization or resource access, use a codec to verify it hasn't been tampered with:

```typescript
import { createRequestStateCodec } from "mcp-use";

const requestStateCodec = createRequestStateCodec<{ userId: string }>({
  key: process.env.REQUEST_STATE_SECRET!,  // 32+ bytes; string is UTF-8-encoded (also accepts Uint8Array)
  ttlSeconds: 600,  // Default 600 (10 min); echoed state past its expiry is rejected
});

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  requestState: { verify: requestStateCodec.verify },  // Codec verifies integrity
});

// Minting: seal a payload into the opaque wire string returned from inputRequired({ requestState })
const wireState = await requestStateCodec.mint({ userId: "user-123" });

// In a tool that elicits input, read the verified payload via ctx.requestState()
// (a function, not an object — the seam has already run verify() by the time the handler runs)
server.tool(
  { name: "auth-action", /* ... */ },
  async (params, ctx) => {
    const state = ctx.requestState<{ userId: string }>();  // Verified by codec; undefined on first call
    if (!state?.userId) {
      return { isError: true, content: [{ type: "text", text: "Auth state invalid" }] };
    }
    // Safe to use state.userId
  }
);
```

`createRequestStateCodec` is signed, not encrypted — the payload is integrity-protected but readable by anyone with the wire string. Never put secrets in the payload. `verify()` throws a fixed opaque reason (`'malformed'` / `'mac'` / `'expired'` / `'bind'`) on any failure, never the decoded payload.

## TLS/HTTPS

Always use HTTPS in production. Platforms (Vercel, Cloud Run, Railway) handle TLS termination automatically at the edge. Local Node.js servers behind a reverse proxy (nginx, Caddy) inherit TLS from the proxy.

Never expose plaintext HTTP to the public internet.

## Dependency vulnerabilities

Regularly scan dependencies:

```bash
npm audit
npm audit fix
```

In CI, add a audit step:

```bash
npm audit --audit-level=moderate
```

Use a Software Composition Analysis (SCA) tool (Snyk, Dependabot) for continuous monitoring.

## Logging and monitoring

**`ctx.sendLog(level, data, logger?)` sends an MCP `notifications/message` notification to the connected CLIENT** — it is not a server-side or internal logging channel. Never route sensitive events, secrets, or internal error details through it; a client-visible channel is the wrong place for anything you wouldn't put directly in a tool response. It also does not honor any client-set log-level threshold: it calls the notify transport directly, unlike the SDK's own internal `logging/setLevel`-gated log path — so `sendLog("debug", ...)` reaches the client even if it requested only `"error"` and above. Use it only for status updates the client is meant to see (see `references/14-notifications/`).

For server-side security/audit logging, use a real server-side sink (structured logger, Sentry, DataDog) inside an MCP event listener — the completed result arrives as the listener's second parameter, not `ctx.result`:

```typescript
server.on("mcp:tools/call:complete", async (ctx, result) => {
  if (result.isError) {
    logger.warn("tool_failed", {
      tool: ctx.params.name,
      error: result.content?.[0]?.type === "text" ? result.content[0].text : undefined,
    });
  }
});
```

Never log raw request/response bodies in production at `info` level; use `debug` or `trace` for local development only.

See `references/15-logging/` for detailed logging practices and `references/25-deploy/` for platform-specific secret management.

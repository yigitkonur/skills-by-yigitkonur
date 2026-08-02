# CORS and Origin Validation

*Read this to configure cross-origin access and understand Origin-header protection for sandboxed view iframes.*

## CORS: Response Headers for Browser Requests

CORS (Cross-Origin Resource Sharing) tells browsers whether a request from origin A may read the response from origin B. **CORS is off by default in v2** (no CORS headers sent). Enable it only when you need browser clients on other origins to make requests.

```typescript
// CORS off (default)
new MCPServer({ name: "api", version: "1.0.0" });
// → No CORS headers; browsers block cross-origin requests

// CORS on with defaults
new MCPServer({
  name: "api",
  version: "1.0.0",
  cors: {},  // Enables CORS; reflects request Origin
});

// CORS with explicit configuration
new MCPServer({
  name: "api",
  version: "1.0.0",
  cors: {
    origin: "https://app.example.com",
    credentials: true,
  },
});
```

## CORS Configuration Options

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `enabled` | `boolean` | `true` (when `cors` is set) | Set to `false` to disable CORS headers. |
| `origin` | `string \| string[] \| function` | Reflects request `Origin` header | Single origin, array of origins, or callback returning origin or `null` to reject. `"*"` requires explicit opt-in (not default). |
| `methods` | `string[]` | `["GET", "HEAD", "POST", "OPTIONS"]` | Allowed HTTP methods. |
| `allowedHeaders` | `string[]` | Common MCP + JSON headers | Headers the browser may send in the request. |
| `credentials` | `boolean` | `false` | When `true`, allows `Authorization` header and cookies. Required for bearer tokens. |

## Origin Validation: Request-Side Access Control

Origin validation controls whether the server **accepts** a request based on its `Origin` header, independent of CORS response headers. **Origin validation is ON for non-GET/HEAD requests when `allowedOrigins` is set.**

```typescript
// Origin validation off (default)
new MCPServer({ name: "api", version: "1.0.0" });
// → No Origin header check; all POST requests accepted

// Origin validation on
new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: ["https://app.example.com"],
});
// → POST/PUT/DELETE requests from other origins rejected with 403
```

## Localhost-Class Protection

When you bind to `127.0.0.1`, `localhost`, or `::1`, **localhost-class origins are automatically allowed**. You can add extra hosts without losing local access.

```typescript
// Local development: localhost origins auto-allowed
await server.listen(3000);  // binds 127.0.0.1:3000
// POST from http://localhost:3000 → allowed (localhost)
// POST from http://other-machine:3000 → rejected (not localhost)

// Public deployment with extra origin
new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: ["https://app.example.com"],
});
// POST from https://app.example.com → allowed (in allowedOrigins)
// POST from https://other.com → rejected
// POST with no Origin header → allowed (non-browser clients)
```

## View Iframes & Origin Validation

MCP Apps (views) are sandboxed iframes. When a view makes a POST request to the MCP server, the browser includes an `Origin` header. Origin validation must allow this.

**Important:** Sandboxed view iframes **send `Origin: null`** on same-origin GET requests (asset loads). **POST requests (MCP wire) send the true origin.** Origin validation only checks non-GET/HEAD, so asset GETs are never blocked by Origin validation.

```typescript
// View iframe scenario
// View loaded from: https://api.example.com/mcp/_mcp-use/views/chart/
// Asset GET (iframe fetches CSS): Origin: null → always allowed
// MCP POST (iframe calls tool): Origin: https://api.example.com → validated

new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: ["https://api.example.com"],
  cors: {
    origin: "https://api.example.com",
    credentials: true,
  },
});
// ✓ View iframe POSTs accepted
```

## No Origin Header

Non-browser MCP clients (CLI, SDKs, scripts) don't send an `Origin` header. **These requests always pass Origin validation, regardless of `allowedOrigins`.** Use bearer token authentication to protect tool/resource access if needed.

## Pair CORS with allowedOrigins

CORS headers allow the browser to read the response; `allowedOrigins` decides if the server accepts the request. Both should match:

```typescript
new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: ["https://app.example.com"],
  cors: {
    origin: "https://app.example.com",  // Must match allowedOrigins
    methods: ["GET", "HEAD", "POST", "OPTIONS"],
    credentials: true,
  },
});
```

Mismatches: `allowedOrigins` too strict → server rejects valid requests. `cors.origin` too loose → browser blocks response even if server accepts it. Both must agree on allowed origins.

## Example: Public Server with Multiple View Hosts

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  host: "0.0.0.0",  // Public bind
  allowedOrigins: [
    "https://chat.openai.com",  // ChatGPT
    "https://claude.ai",        // Claude
  ],
  cors: {
    origin: ["https://chat.openai.com", "https://claude.ai"],
    methods: ["GET", "HEAD", "POST", "OPTIONS"],
  },
});
```

See `04-dns-rebinding-and-host-validation.md` for Host-header validation complementing Origin validation.

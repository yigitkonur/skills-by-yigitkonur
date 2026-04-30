# MCP Server Common Errors

Diagnose and fix the most frequent errors encountered when building MCP servers with the `mcp-use` library (current: v1.21.5).

> **Known open bugs (as of v1.21.5):**
> - `ctx.elicit()` result data lands in `result.content` at runtime instead of `result.data` (GitHub #1215 — fix in PR #1216). Workaround: `result.data ?? (result as any).content`.
> - Zod is now a `peerDependency` — ensure `zod@^4.0.0` is in your own `package.json`.

---
### Error: Cannot find module 'mcp-use/server'

**When**: Importing `mcp-use` at compile time or runtime.
**Cause**: `mcp-use` uses Node.js subpath exports. TypeScript needs `"moduleResolution": "node16"` or `"bundler"` in `tsconfig.json`.
**Fix**:
Set `tsconfig.json`:
```json
{
  "compilerOptions": {
    "module": "node16",
    "moduleResolution": "node16"
  }
}
```
Rebuild: `npx tsc --build`. If using `"bundler"` resolution, ensure your bundler supports `exports`.

**Prevention**: Always start projects with `"moduleResolution": "node16"` when targeting Node.js ESM.
---
### Error: Tool not found when calling a registered tool

**When**: Client calls `callTool({ name: "my-tool" })` and gets a "tool not found" error.
**Cause**: Tool was registered after `server.listen()`, the name has a typo, or the tool was registered on a different server instance.
**Fix**:
1. Register all tools *before* calling `server.listen()`.
2. Verify the exact name string — names are case-sensitive.
3. Call `client.listTools()` to confirm what the server actually exposes.

**Prevention**: Register tools immediately after constructing the `MCPServer`, before calling `listen()`.
---
### Error: Server starts but no tools appear in client

**When**: `client.listTools()` returns an empty array despite tools being registered.
**Cause**: Tools were registered after `server.listen()`, or there is an import/instance mismatch (two separate `MCPServer` instances).
**Fix**:
1. Ensure all `server.tool()` calls happen before `server.listen()`.
2. Verify you are not creating multiple `MCPServer` instances.
3. Restart both server and client after changes.

**Prevention**: Register all tools immediately after constructing `MCPServer`.
---
### Error: Invalid schema — Zod validation failures

**When**: Client sends arguments that fail Zod parsing.
**Cause**: Schema mismatch between what the LLM generates and what the tool expects — wrong types, missing required fields, or extra fields with `.strict()`.
**Fix**:
1. Check the Zod error message — it names the failing field and expected type.
2. Add `.describe()` to every field and use `z.coerce` for flexible parsing:
   ```typescript
   const schema = z.object({
     count: z.coerce.number().describe("Number of items to fetch"),
     query: z.string().optional().default("").describe("Search filter"),
   });
   ```
3. Use `.default()` for optional fields with sensible defaults.

**Prevention**: Test every tool with MCP Inspector. Use `.describe()` on all schema fields.
---
### Error: CORS errors with HTTP transport

**When**: Browser-based MCP clients fail to connect to an HTTP/SSE server.
**Cause**: The server does not return `Access-Control-Allow-Origin` headers, or the `cors` config is too restrictive.
**Fix**: Pass a `cors` config to the `MCPServer` constructor (replaces default `origin: "*"` entirely):
```typescript
import { MCPServer } from "mcp-use/server";
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  cors: {
    origin: ["https://your-client-origin.com"],
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "mcp-protocol-version", "mcp-session-id"],
    exposeHeaders: ["mcp-session-id"],
  },
});
await server.listen(3000);
```
Or add a Hono middleware via `server.use()`:
```typescript
server.use("*", async (c, next) => {
  c.header("Access-Control-Allow-Origin", "https://your-client-origin.com");
  c.header("Access-Control-Allow-Headers", "Content-Type, mcp-session-id");
  if (c.req.method === "OPTIONS") return c.text("", 204);
  await next();
});
```

**Prevention**: Always configure CORS when using HTTP-based transports. Include `mcp-session-id` in both `allowHeaders` and `exposeHeaders`.
---
### Error: Session lost between requests (Streamable HTTP)

**When**: Multi-turn interactions fail; server treats each request as a new session.
**Cause**: Streamable HTTP uses `Mcp-Session-Id` header. If the client does not return this header, a new session is created each time.
**Fix**:
1. Ensure your HTTP client reads `Mcp-Session-Id` from the response and sends it back.
2. Use an explicit session store:
   ```typescript
   import { MCPServer, InMemorySessionStore } from "mcp-use/server";
   const server = new MCPServer({
     name: "my-server", version: "1.0.0",
     sessionStore: new InMemorySessionStore(),
   });
   ```

**Prevention**: Use the SDK’s built-in `StreamableHTTPClientTransport` which handles session headers automatically.
---
### Error: 404 Not Found after server restart (v1.21.1+)

**When**: Clients connected before a restart receive `404 Not Found` with a stale `Mcp-Session-Id`.
**Cause**: The in-memory session store loses all sessions on restart.
**Fix**:
1. Use `RedisSessionStore` so sessions survive restarts:
   ```typescript
   import { MCPServer, RedisSessionStore } from "mcp-use/server";
   import { createClient } from "redis";
   const redisClient = createClient({ url: process.env.REDIS_URL });
   await redisClient.connect();
   const server = new MCPServer({
     name: "my-server", version: "1.0.0",
     sessionStore: new RedisSessionStore({ client: redisClient }),
   });
   ```
2. Temporary workaround for legacy clients: set `autoCreateSessionOnInvalidId: true` (deprecated).

**Prevention**: Always use `RedisSessionStore` in production. Per the MCP spec, clients must send a new `InitializeRequest` on 404 for stale sessions.
---
### Error: `ctx.auth` is undefined in tool handler

**When**: Accessing `ctx.auth` inside a tool handler returns `undefined`, even though OAuth is configured.
**Cause**: v1.21.1–v1.21.3 regression — `mountMcp()` stopped wrapping `transport.handleRequest()` in `runWithContext()`, so `AsyncLocalStorage` was never populated for the MCP request lifecycle. Fixed in v1.21.4 by wrapping all `handleRequest()` call sites in `runWithContext(c, ...)`.
**Fix**:
1. Upgrade: `npm install mcp-use@latest` (≥ v1.21.4)
2. If you cannot upgrade immediately, apply the workaround:
   ```typescript
   import { runWithContext } from "mcp-use/server";
   server.app.use("/mcp/*", async (c, next) => {
     return runWithContext(c, () => next());
   });
   ```
3. Verify your handler receives `ctx` as the second argument:
   ```typescript
   import { MCPServer, text, error } from "mcp-use/server";
   import { z } from "zod";
   server.tool(
     { name: "get-profile", description: "Get user profile",
       schema: z.object({ userId: z.string().describe("User ID") }) },
     async (args, ctx) => {
       if (!ctx.auth) return error("Not authenticated");
       return text(JSON.stringify(await db.getProfile(ctx.auth.sub), null, 2));
     }
   );
   ```

**Prevention**: Always guard `ctx.auth` with a null check. Keep `mcp-use` at `^1.21.4` or later.
---
### Error: ENOSPC — System limit for number of file watchers reached

**When**: Dev server with HMR crashes with `ENOSPC: System limit for number of file watchers reached`.
**Cause**: File watcher recursively watches `node_modules`, exhausting the OS inotify limit.
**Fix**:
1. Ignore `node_modules` in watcher config (e.g., `nodemon.json`: `{ "ignore": ["node_modules", "dist"] }`).
2. On Linux, increase the limit: `echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p`.

**Prevention**: Always exclude `node_modules` and `dist` from file watchers.
---
### Error: Connection refused when connecting to server

**When**: Client cannot establish connection to the MCP server.
**Cause**: Server is not running, wrong port, firewall blocking, or the server crashed silently on startup.
**Fix**:
1. Confirm the server process is running: `ps aux | grep node`.
2. Check the port: `lsof -i :3000`.
3. Verify the client is targeting the correct MCP URL, usually `http://localhost:3000/mcp` for local development.

**Prevention**: Add startup logging and a health check for HTTP servers.
---
### Error: Memory leaks with long-running servers

**When**: Server memory usage grows steadily over hours/days.
**Cause**: Unbounded caches, event listeners not removed, accumulating session state.
**Fix**:
1. Profile with `node --inspect` and Chrome DevTools heap snapshots.
2. Add TTL and size limits to caches. Clean up session state on `close` event.
3. Use `WeakMap`/`WeakRef` for object caches where appropriate.

**Prevention**: Implement bounded caches from the start. Monitor `process.memoryUsage().heapUsed`.
---
### Error: Broken local connection after restart

**When**: The client reconnects after a local server restart and sees socket reset / broken pipe style errors.
**Cause**: The old HTTP connection died while the client still held stale session state.
**Fix**:
1. Restart the local client session after the server restart.
2. Re-run `tools/list` or reconnect Inspector so a fresh session is established.
3. If the port changed, update the client URL to the new `http://localhost:<port>/mcp` endpoint.

**Prevention**: Keep the local dev port stable and restart clients after HMR crashes or full server restarts.
---
### Error: OAuth "Unauthorized" — 401 on protected endpoints

**When**: Client connects to an HTTP server with OAuth enabled but gets rejected.
**Cause**: Missing or expired access token, wrong OAuth provider config, or insufficient scopes.
**Fix**:
1. Verify OAuth provider URL and client credentials.
2. Check token expiration — refresh if supported.
3. Confirm scopes match. Inspect the `Authorization` header.

**Prevention**: Log auth failures with detail (not the token). Implement token refresh in the client.
---
### Error: EADDRINUSE — Port already in use

**When**: Server fails to start with `Error: listen EADDRINUSE: address already in use :::3000`.
**Cause**: Another process is already listening on that port. This commonly happens when a previous dev server was killed with `Ctrl+C` but a child process survived, or when a stale `node` process is still holding the port after a crash.
**Fix**:
1. Find what owns the port: `lsof -i :3000`.
2. Kill the stale process in one command: `lsof -ti:3000 | xargs kill`.
3. Or use a different port: `PORT=3001 node dist/index.js`.

**Prevention**: Configure port via environment variable. Add graceful shutdown handlers for `SIGINT`/`SIGTERM` so the port is released on exit. If using `nodemon` or `tsx --watch`, ensure child processes are cleaned up on restart.
---
### Error: TypeScript compilation errors with mcp-use imports

**When**: `tsc` reports errors on `mcp-use` import paths.
**Cause**: Wrong `moduleResolution`, mismatched `@types/node`, or importing from wrong subpath.
**Fix**:
1. Use correct imports: `import { MCPServer, text, error } from "mcp-use/server"` (never from the raw SDK).
2. Set `tsconfig.json`: `"module": "node16"`, `"moduleResolution": "node16"`, `"target": "ES2022"`.
3. Ensure `@types/node` version matches your Node.js major version.

**Prevention**: Always import from `mcp-use/server`. Use recommended `tsconfig.json` settings from the start.
---
### Error: Maximum call stack size exceeded — circular references

**When**: `JSON.stringify()` inside a tool handler throws a stack overflow.
**Cause**: Object contains circular references (common with ORM models, DOM-like structures).
**Fix**: Extract only needed fields, or use a safe serializer:
```typescript
import { text } from "mcp-use/server";
const safe = { id: record.id, name: record.name };
return text(JSON.stringify(safe));
// Or: import { stringify } from "safe-stable-stringify";
```

**Prevention**: Never pass raw ORM models to `JSON.stringify()`. Map to plain DTOs first.
---
### Error: Timeout errors for long-running tools

**When**: Client reports a timeout before the tool handler completes.
**Cause**: Tool performs a slow operation exceeding the client’s timeout threshold.
**Fix**:
1. Increase client timeout if appropriate.
2. Use progress notifications:
   ```typescript
   server.tool(
     { name: "long-task", description: "Process large dataset",
       schema: z.object({ datasetId: z.string().describe("Dataset ID") }) },
     async (args, ctx) => {
       const chunks = await getChunks(args.datasetId);
       for (let i = 0; i < chunks.length; i++) {
         await processChunk(chunks[i]);
         await ctx.reportProgress?.(i + 1, chunks.length, `Chunk ${i + 1}`);
       }
       return text(`Processed ${chunks.length} chunks`);
     }
   );
   ```
3. For very long operations, return a job ID and provide a separate polling tool.

**Prevention**: Use progress reporting. Break massive operations into smaller tools.
---
### Error: Invalid JSON-RPC response

**When**: Client receives a malformed response and fails to parse it.
**Cause**: The client hit the wrong endpoint, a proxy returned HTML, or middleware mutated the response unexpectedly.
**Fix**:
1. Confirm the client uses `/mcp`, not `/`, `/sse`, or a generic app route.
2. Check the raw response body with `curl -i` and confirm it is JSON-RPC, not HTML or an auth redirect.
3. Disable or narrow middleware/proxy rewrites until the MCP response is clean.

**Prevention**: Keep MCP mounted on a dedicated route and test it directly with `curl` before debugging through higher-level clients.
---
### Error: SSE connection drops after 60 seconds

**When**: Legacy SSE transport; client disconnects after ~60 seconds of inactivity.
**Cause**: Reverse proxy (nginx, Cloudflare, ALB) times out idle connections.
**Fix**:
1. Configure proxy timeouts: `proxy_read_timeout 86400s; proxy_send_timeout 86400s;`
2. Or migrate to `httpStream` transport which uses standard request/response.

**Prevention**: Prefer `httpStream` over SSE for production deployments behind proxies.
---
### Error: "Unexpected token" when parsing server output

**When**: Client fails during initial handshake or after first tool call.
**Cause**: `package.json` has `"type": "module"` but entry point uses `require()`, or vice versa.
**Fix**:
1. ESM (`"type": "module"`): use `import`/`export`, add `.js` to relative imports.
2. CJS: remove `"type": "module"`, use `require()`/`module.exports`.
3. Verify `dist/` output matches the module system in `package.json`.

**Prevention**: Decide ESM vs CJS at project init. Use `"type": "module"` with `"module": "node16"` in tsconfig.
---
### Error: Client receives notifications but tool responses are empty

**When**: Tool calls return empty content even though the handler runs.
**Cause**: Handler does not return a value, or returns `undefined`.
**Fix**: Ensure every code path returns via a response helper:
```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";
server.tool(
  { name: "check", description: "Check item existence",
    schema: z.object({ id: z.string().describe("Item ID") }) },
  async (args) => {
    const item = await db.find(args.id);
    if (!item) return error(`Item ${args.id} not found.`);
    return text(JSON.stringify(item, null, 2));
  }
);
```

**Prevention**: Enable `"noImplicitReturns": true` in `tsconfig.json`. Review handlers for missing returns.
---
### Error: `result.data` is undefined after `ctx.elicit()` — open bug in v1.21.5

**When**: Accessing `result.data` inside `if (result.action === 'accept')` after `ctx.elicit()` with a Zod schema returns `undefined`, causing a runtime crash.
**Cause**: Open bug (GitHub #1215, fix tracked in #1216). `createElicitMethod` checks `result.data` as the source but the MCP SDK places user input in `result.content`. The Zod validation step is therefore never reached, so `result.data` stays `undefined` despite TypeScript reporting no type error.
**Workaround** (until a patched release ships):
```typescript
const result = await ctx.elicit(
  "Please provide your information",
  z.object({ firstName: z.string(), lastName: z.string() })
);
if (result.action === 'accept') {
  // Workaround: fall back to result.content when result.data is undefined
  const data = (result.data ?? (result as any).content) as { firstName: string; lastName: string };
  return text(`Hi ${data.firstName} ${data.lastName}`);
}
```
**Fix**: Upgrade `mcp-use` once PR #1216 is merged and released (maps `result.content` to `result.data` for Zod validation).

**Prevention**: Always use the workaround pattern until the bug is confirmed fixed. Watch the GitHub issue for a patched version.
---
### Error: ElicitationDeclinedError — User declined prompt

**When**: User explicitly declines an elicitation request (cancels or rejects the prompt).
**Cause**: The MCP client presented a prompt via `ctx.elicit()` and the user chose to cancel or decline.
**Fix**: Catch the error in your tool handler and return a graceful response:
```typescript
import { ElicitationDeclinedError, text, error } from "mcp-use/server";
import { z } from "zod";

try {
  const result = await ctx.elicit(
    "Are you sure you want to delete this item?",
    z.object({ confirm: z.boolean() }),
  );
  if (result.action !== 'accept') return text("Deletion cancelled.");
  const data = (result.data ?? (result as any).content) as { confirm: boolean };
  if (!data.confirm) return text("Deletion cancelled.");
  await db.delete(args.id);
  return text(`Deleted item ${args.id}`);
} catch (e) {
  if (e instanceof ElicitationDeclinedError) return error("User declined the request");
  throw e;
}
```

**Prevention**: Always wrap `ctx.elicit()` calls in try/catch. Provide a meaningful fallback when declined.
---
### Error: ElicitationTimeoutError — No response within timeout

**When**: User does not respond to an elicitation prompt within the specified timeout period.
**Cause**: Timeout elapsed before user interaction. The error includes a `timeoutMs` property with the configured duration.
**Fix**:
```typescript
import { ElicitationTimeoutError, error } from "mcp-use/server";
import { z } from "zod";
try {
  const result = await ctx.elicit(
    "Please provide input:",
    z.object({ value: z.string() }),
  );
} catch (e) {
  if (e instanceof ElicitationTimeoutError) {
    console.error(`Timed out after ${e.timeoutMs}ms`);
    return error("Request timed out — please try again");
  }
  throw e;
}
```

**Prevention**: Set reasonable timeouts. Provide default behavior when timeouts occur rather than failing the entire tool.
---
### Error: ElicitationValidationError — Schema mismatch

**When**: Data returned from an elicitation prompt does not match the expected Zod schema.
**Cause**: User provided input that fails schema validation. The error has a `cause` property containing the original Zod validation error.
**Fix**:
```typescript
import { ElicitationValidationError, error } from "mcp-use/server";
import { z } from "zod";
try {
  const result = await ctx.elicit(
    "Enter count:",
    z.object({ count: z.number().min(1) }),
  );
} catch (e) {
  if (e instanceof ElicitationValidationError) {
    console.error("Validation failed:", e.cause);
    return error("Invalid input — please check the required format");
  }
  throw e;
}
```

**Prevention**: Use `.describe()` on schema fields so users understand expected formats. Use `z.coerce` where appropriate.
---
### Error: DNS rebinding — 403 Forbidden on valid requests

**When**: Request with a spoofed or unexpected `Host` header hits the server and returns 403.
**Cause**: Server has `allowedOrigins` configured and the `Host` header does not match any allowed origin.
**Fix**: Add your domain to `allowedOrigins`:
```typescript
import { MCPServer } from "mcp-use/server";
const server = new MCPServer({
  name: "my-server", version: "1.0.0",
  allowedOrigins: ["localhost", "myapp.example.com"],
});
```
Test with: `curl -H "Host: evil.com" http://localhost:3000/mcp` → should get 403.

**Prevention**: Always configure `allowedOrigins` explicitly. Use `"*"` only during local development.
---
### Error: CSP violations — Widget content blocked

**When**: Widget content or inline scripts are blocked by the browser’s Content Security Policy.
**Cause**: Widget resources served without proper CSP headers, or inline scripts blocked by default policy.
**Fix**: Configure CSP headers via Hono middleware on `server.app`:
```typescript
server.app.use("*", async (c, next) => {
  c.header("Content-Security-Policy",
    "default-src 'self'; script-src 'self' https://widget-origin.com");
  await next();
});
```

**Prevention**: Set CSP headers early in middleware. Allow specific widget origins rather than using `unsafe-inline`.
---
### Error: Session store connection failure

**When**: `RedisSessionStore` fails to connect or filesystem session store has permission issues.
**Cause**: Redis URL incorrect, Redis not running, or filesystem permissions prevent read/write.
**Fix**:
1. Verify `REDIS_URL` is correct and Redis is reachable: `redis-cli -u $REDIS_URL ping`.
2. Check filesystem permissions for file-based stores.
3. Fall back to `InMemorySessionStore` during development:
   ```typescript
   import { MCPServer, InMemorySessionStore } from "mcp-use/server";
   const server = new MCPServer({
     name: "my-server", version: "1.0.0",
     sessionStore: new InMemorySessionStore(),
   });
   ```

**Prevention**: Add connection error handling with retries. Use `InMemorySessionStore` as a dev fallback.
---
### Error: `mcp-use build` hangs after "Build complete"

**When**: Running `mcp-use build` outputs "Build complete" but the process never exits.
**Cause**: Bug fixed in v1.21.4 — the CLI was missing `process.exit(0)` after the build step completed.
**Fix**:
1. Upgrade: `npm install @mcp-use/cli@latest`
2. If stuck: `Ctrl+C` and rerun after upgrading.

**Prevention**: Keep `@mcp-use/cli` at the latest version.
---
### Error: Missing `zod` peer dependency after upgrading to v1.21.5

**When**: After upgrading `mcp-use` to v1.21.5, TypeScript errors appear on `z.object(...)` or runtime errors about `zod` not being found.
**Cause**: v1.21.5 moved `zod` from a direct dependency to a `peerDependency`. If `zod` is not in your own `package.json`, it may not be installed.
**Fix**:
```bash
npm install zod@^4.0.0
```
Verify `package.json` includes `"zod": "^4.0.0"` in `dependencies`.

**Prevention**: Explicitly declare `zod@^4.0.0` in every project that uses `mcp-use`. This also prevents duplicate Zod type trees when multiple packages depend on different Zod versions.
---
### Error: Deploy failure — `mcp-use deploy` fails

**When**: Running `mcp-use deploy` exits with an error.
**Cause**: Not a git repo, GitHub App not installed, or build errors. Most common: missing `dist/mcp-use.json` build manifest.
**Fix**:
1. Initialize git if needed: `git init && git add -A && git commit -m "initial"`.
2. Install the GitHub App when prompted during first deploy.
3. Run `mcp-use build` first and verify `dist/mcp-use.json` exists.
4. Check build output for TypeScript or dependency errors.

**Prevention**: Always run `mcp-use build` before `mcp-use deploy`. Keep the project in a git repository.
---
### Error: New subdomain / URL on every deploy — custom domain breaks

**When**: Running `mcp-use deploy` succeeds but assigns a new URL each time. Custom domains (CNAMEs) stop working after redeploy.
**Cause**: `.mcp-use/project.json` is missing or not available on the machine running deploy. This file links your local project to a specific cloud deployment. Without it, Manufact Cloud treats each deploy as a brand new project and assigns a new subdomain.
**Fix**:
1. Track the deployment link in git: add `!.mcp-use/project.json` to `.gitignore` (keep the rest of `.mcp-use/` ignored).
2. `git add -f .mcp-use/project.json && git commit && git push`.
3. Redeploy — it will now reuse the existing deployment and URL.
4. If the old deployment was already deleted, you'll need to re-add your custom domain to the new one.

**Prevention**: After the first successful deploy, immediately track `.mcp-use/project.json` in git. This ensures every machine, CI runner, or teammate reuses the same deployment URL. Version bumps in `package.json` do not affect this — only the `project.json` link matters.
---
### Error: "Incompatible auth server: does not support dynamic client registration"

**When**: A third-party MCP client (mcpc, Claude Desktop) attempts to connect to a server using `oauthSupabaseProvider()`.
**Cause**: `SupabaseOAuthProvider` defaults to proxy mode, which serves `/.well-known/oauth-authorization-server` metadata WITHOUT a `registration_endpoint`. Clients that require RFC 7591 Dynamic Client Registration (DCR) reject the server immediately. Additionally, `/.well-known/oauth-protected-resource` points to Supabase as the authorization server, and Supabase itself has no DCR endpoint.
**Fix**:
1. Add a `server.use("*", ...)` wildcard middleware that intercepts `/.well-known/oauth-authorization-server` and `/.well-known/oauth-protected-resource`, returning metadata that points to your own server and includes a `registration_endpoint`.
2. Add a custom `/oauth/register` POST handler that implements RFC 7591 DCR (can be a simple handler that returns a generated `client_id`).
3. Add custom `/oauth/authorize` and `/oauth/token` handlers on custom paths (not `/authorize` or `/token` — those are claimed by mcp-use).
4. See the "Supabase Proxy Mode Pitfalls" section in `authentication.md` for the complete implementation pattern.

**Prevention**: Before choosing `oauthSupabaseProvider()`, verify whether your target MCP clients require DCR. If they do, plan for the custom middleware and handlers from the start.
---
### Error: "Unsupported provider: Provider could not be found" (Supabase)

**When**: User is redirected to Supabase's `/auth/v1/authorize` endpoint during the OAuth flow.
**Cause**: mcp-use's built-in proxy `/authorize` handler forwards the request to Supabase without injecting the `provider` query parameter. Supabase requires `provider=google` (or whichever social provider is configured) to know which OAuth flow to start.
**Fix**:
1. Create a custom authorize handler on a path like `/oauth/authorize` that adds `provider=google` to the Supabase redirect URL.
2. Update your `/.well-known/oauth-authorization-server` metadata to point `authorization_endpoint` at your custom handler.
3. Also map `redirect_uri` to `redirect_to` (Supabase's expected parameter name).

**Prevention**: Never rely on mcp-use's default proxy authorize handler when using Supabase with a social provider. Always build a custom handler that injects the provider parameter.
---
### Error: "bad_json" from Supabase token exchange

**When**: Token exchange (authorization code for access token) against Supabase's `/auth/v1/token` endpoint.
**Cause**: mcp-use's proxy sends the token request with `Content-Type: application/x-www-form-urlencoded`. Supabase's token endpoint requires `Content-Type: application/json` with the request body as JSON, plus an `apikey` header set to the Supabase anon key.
**Fix**:
1. Create a custom `/oauth/token` POST handler.
2. Send the request to Supabase with `Content-Type: application/json` and include the `apikey` header.
3. Translate parameters: `code` to `auth_code`, use `grant_type=pkce`, and do NOT forward `client_id`.
4. Update `/.well-known/oauth-authorization-server` metadata to point `token_endpoint` at your custom handler.

**Prevention**: Always use a custom token handler when integrating with Supabase. The built-in proxy's form-urlencoded encoding is incompatible.
---
### Error: "redirect_uri_mismatch" from Google OAuth via Supabase

**When**: Google OAuth callback fails after user authenticates, returning a redirect URI mismatch error.
**Cause**: Two possible causes:
1. The MCP client uses a dynamic localhost port for its callback (e.g., `http://localhost:54321/oauth/callback`) that is not listed in Supabase's allowed redirect URLs. Supabase falls back to the configured Site URL instead.
2. The `client_id` parameter was forwarded to Supabase, which passed it to Google. Google rejects the unknown client ID.
**Fix**:
1. In Supabase Dashboard > Authentication > URL Configuration > Redirect URLs, add `http://localhost:*/**` to allow dynamic localhost ports.
2. Ensure your custom token handler does NOT forward `client_id` to Supabase.
3. Set the Site URL to your production MCP server URL.

**Prevention**: Always configure Supabase redirect URLs to include localhost wildcards for development/testing. Never forward `client_id` from DCR clients to Supabase.
---
### Error: Deployed server missing recent changes (`mcp-use deploy`)

**When**: After deploying, the production server does not reflect recent code changes.
**Cause**: `mcp-use deploy` clones the repository from GitHub (remote HEAD), not from the local working directory. Uncommitted or unpushed changes are invisible to the deployment process.
**Fix**:
1. Commit all changes: `git add . && git commit -m "description"`
2. Push to remote: `git push`
3. Then deploy: `mcp-use deploy --name my-server --env-file .env`

**Prevention**: Always run `git status` before deploying to verify all changes are committed and pushed. Add a pre-deploy script that checks for clean working tree.
---
### Error: OrbStack port conflict when testing with mcpc

**When**: mcpc fails to start its local OAuth callback server, or connections to the MCP server fail on macOS with OrbStack.
**Cause**: OrbStack (Docker Desktop alternative for macOS) can bind to ports that conflict with mcpc's dynamic localhost port allocation or with the MCP server's port.
**Fix**:
1. Check for port conflicts: `lsof -i :<port>`.
2. Stop OrbStack temporarily, or configure it to avoid the conflicting port range.
3. Use a specific port for the MCP server that does not overlap with OrbStack's allocated range.

**Prevention**: Be aware of OrbStack's port allocation when running local MCP development on macOS. Use `lsof` to diagnose unexpected connection failures.
---
### Warning: "resourceCallbacks undefined" in stderr

**When**: Server starts and prints a warning like `Cannot read properties of undefined (reading 'complete')` or `resourceCallbacks is undefined` to stderr.
**Cause**: mcp-use internally references `callbacks.complete` on resource templates even when no `callbacks` object is provided. This is harmless noise — no resource functionality is broken.
**Fix**: Ignore the warning. It does not affect tool execution or server behavior. If you want to silence it, provide an empty callbacks object when registering resource templates:
```typescript
server.resource({
  name: "my-resource",
  template: "res:///{id}",
  callbacks: { complete: async () => ({ values: [] }) },
}, handler);
```

**Prevention**: This is a known cosmetic issue in mcp-use. No action required unless you are actively using resource template completion.
---
### Warning: `GET /health` returns the Inspector HTML page

**When**: Hitting `GET /health` returns a full HTML page (the MCP Inspector UI) instead of a JSON health response.
**Cause**: mcp-use serves its built-in Inspector on all `GET` requests to the server's base path and sub-paths by default. If you do not explicitly register a `/health` route, the catch-all Inspector handler takes over.
**Fix**: Register an explicit health endpoint using `server.get()` **before** calling `server.listen()`:
```typescript
server.get("/health", (c) => c.json({ status: "ok" }));
await server.listen(3000);
```
Now `GET /health` returns `{"status":"ok"}` and the Inspector remains available at `GET /mcp` (or whichever path you configure).

**Prevention**: Always register explicit `GET` routes for health checks and readiness probes before `listen()`.
---
## Quick Diagnostic Checklist

| Symptom | First check |
|---|---|
| Import errors | `moduleResolution` in tsconfig; importing from `mcp-use/server`? |
| Tools not visible | Tools registered before `listen()`? |
| Garbled responses | `console.log()` on stdout? |
| Connection drops | Proxy timeout settings |
| Memory growth | Unbounded caches or listeners |
| Auth failures | Token expiration and scopes; `mcp-use` ≥ v1.21.4? |
| Port conflicts | `lsof -i :<port>` |
| Timeout | Progress reporting enabled? |
| 404 after restart | Session store persistent? `autoCreateSessionOnInvalidId` (deprecated)? |
| `ctx.auth` undefined | `mcp-use` ≥ v1.21.4? |
| ENOSPC watchers | `node_modules` excluded from watcher? |
| `result.data` undefined after `elicit()` | Open bug #1215 — use `result.data ?? (result as any).content` workaround |
| Elicitation declined | User cancelled the prompt; catch `ElicitationDeclinedError` |
| Elicitation timeout | No response; catch `ElicitationTimeoutError`, check `timeoutMs` |
| Elicitation validation | Schema mismatch; catch `ElicitationValidationError`, check `cause` |
| DNS rebinding 403 | Host header rejected; check `allowedOrigins` config |
| CSP violations | Widget blocked; check CSP headers |
| Session store failure | Redis/fs error; check connection URL and permissions |
| Deploy failure | Build manifest missing; run `mcp-use build` first |
| `mcp-use build` hangs | Upgrade `@mcp-use/cli` to ≥ v1.21.4 |
| `zod` not found after upgrade | Add `"zod": "^4.0.0"` to your own `package.json` (peerDep since v1.21.5) |
| "Incompatible auth server" (DCR) | Supabase proxy mode has no `registration_endpoint`; add custom middleware |
| "Unsupported provider" (Supabase) | Missing `provider=google` param; use custom authorize handler |
| "bad_json" (Supabase token) | Supabase needs JSON body + `apikey` header, not form-urlencoded |
| "redirect_uri_mismatch" (Google) | Add `http://localhost:*/**` to Supabase redirect URLs; don't forward `client_id` |
| Deploy missing changes | `mcp-use deploy` clones from git; commit + push first |
| OrbStack port conflict | Check `lsof -i :<port>`; OrbStack may claim ports |
| `resourceCallbacks undefined` warning | Harmless noise; provide empty `callbacks.complete` to silence |
| `/health` returns HTML | Register explicit `server.get("/health", ...)` before `listen()` |

---

### Error: Protocol Version Mismatch

**When**: Client connects but immediately disconnects or errors with "unsupported version".
**Cause**: The client speaks a newer or older MCP protocol version than the server supports.
**Fix**:
1. Check `mcp-use` version in `package.json`.
2. Ensure client SDK is compatible.
3. Use capability negotiation (handled automatically by `mcp-use`).

**Prevention**: Keep `mcp-use` updated. The library maintains backward compatibility where possible.

---

### Error: Payload Too Large (413)

**When**: Sending a large file or text block to a tool fails.
**Cause**: The transport (HTTP/Stdio) or a proxy (Nginx) has a size limit.
**Fix**:
1. Increase body size limit in Nginx: `client_max_body_size 50M;`.
2. In Node.js, `mcp-use` handles large JSON-RPC messages, but memory limits apply.
3. Use `blob` or `resource` patterns for large data instead of inline arguments.

**Prevention**: Avoid passing megabytes of data as tool arguments. Use references (URLs/paths) instead.

---

### Error: Rate Limit Exceeded (429)

**When**: Client receives 429 errors when calling tools rapidly.
**Cause**: The server or an upstream API (e.g., GitHub, OpenAI) is rate-limiting requests.
**Fix**:
1. Implement backoff/retry in the client.
2. Add caching to the server to reduce upstream calls.
3. Use a token bucket limiter on the server side.

**Prevention**: Document rate limits in tool descriptions. Return `429` with `Retry-After` header.

---

### Error: Gateway Timeout (504)

**When**: Request takes too long, and the load balancer kills it.
**Cause**: Tool execution time exceeds the LB's `proxy_read_timeout`.
**Fix**:
1. Increase timeout in LB config (AWS ALB, Nginx).
2. Optimize tool performance.
3. Switch to async job pattern (return "Job Started", poll for results).

**Prevention**: Keep synchronous tool execution under 30s.

---

### Error: Invalid Character in Header

**When**: Server crashes with `TypeError: Invalid character in header content`.
**Cause**: Passing unsanitized input (like newlines) into HTTP headers.
**Fix**:
1. Sanitize any user input before setting headers.
2. `val.replace(/[\r\n]/g, '')`.

**Prevention**: Never trust user input in headers.

---

### Error: Zombie Processes in Docker

**When**: Container stops but Node.js process keeps running, or signals are ignored.
**Cause**: PID 1 is not an init system, so it doesn't reap zombies or forward signals.
**Fix**:
1. Use `tini` in Dockerfile: `ENTRYPOINT ["/sbin/tini", "--"] CMD ["node", "server.js"]`.
2. Or use `docker run --init`.

**Prevention**: Always use an init process in Docker containers.

---

## Debugging with MCP Inspector

The MCP Inspector is your best friend for diagnosing protocol-level issues.

### 1. Start the Inspector

```bash
npx @mcp-use/inspector --url http://localhost:3000/mcp
```

### 2. Analyze the Traffic

- **Transport Connection**: Green dot indicates a successful HTTP connection.
- **Initialization**: Check `initialize` request/response. Verify `capabilities` and `protocolVersion`.
- **Tool Listing**: Ensure `tools/list` returns what you expect. Check `schema` structures.
- **Tool Execution**: Call a tool. Watch the JSON-RPC trace.
  - **Request**: `tools/call`. Check `name` and `arguments`.
  - **Response**: Check both `content` and `structuredContent`. For tools with `outputSchema` or custom structured output, both surfaces should carry the same essential result; `_meta` should contain only private/client-only data.
  - **Error**: Check `code` and `message`.

### 3. Common Traces

**Success:**
```json
-> {"jsonrpc": "2.0", "method": "tools/call", "params": { ... }, "id": 1}
<- {"jsonrpc": "2.0", "result": { "content": [{ "type": "text", "text": "OK" }] }, "id": 1}
```

**Success that looks empty in structured-output clients:**
```json
<- {
  "jsonrpc": "2.0",
  "result": {
    "content": [{ "type": "text", "text": "# Full scraped markdown..." }],
    "structuredContent": { "metadata": { "successful": 1 } }
  },
  "id": 1
}
```
Fix by mirroring the primary result into `structuredContent` and covering it in `outputSchema`, for example `{ "content": "...", "results": [...], "metadata": {...} }`. Also keep `content[0].text` useful, because content-first clients and adapters may ignore `structuredContent`.

**Failure (Application Error):**
```json
-> {"jsonrpc": "2.0", "method": "tools/call", ...}
<- {"jsonrpc": "2.0", "result": { "content": [], "isError": true }, "id": 1}
```
*Note: `isError: true` inside `result` means the tool ran but returned a functional error.*

**Failure (Protocol Error):**
```json
-> {"jsonrpc": "2.0", "method": "tools/call", ...}
<- {"jsonrpc": "2.0", "error": { "code": -32602, "message": "Invalid params" }, "id": 1}
```
*Note: Top-level `error` object means the protocol request failed (e.g., schema validation).*

---

## Logging Strategies

### 1. Minimal (Production)

```typescript
import { Logger } from "mcp-use";  // Logger is from root package, NOT mcp-use/server
Logger.configure({ level: "info", format: "minimal" });
// Output: [INFO] Server listening on port 3000
```

### 2. Detailed (Debugging)

```typescript
Logger.configure({ level: "debug", format: "detailed" });
// Output: {"level":"debug","message":"Processing request","timestamp":"...","metadata":{...}}
```

### 3. JSON-RPC Tracing

Set `DEBUG=mcp-use:*` env var to see raw protocol frames.

```bash
DEBUG=mcp-use:* node dist/server.js
```

**Output:**
```
mcp-use:transport Incoming message: {"jsonrpc":"2.0","method":"tools/list",...} +0ms
mcp-use:server Sending response: {"jsonrpc":"2.0","result":{...}} +2ms
```

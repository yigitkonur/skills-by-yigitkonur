# MCP Server Common Errors

Diagnose and fix the most frequent errors encountered when building MCP servers with the TypeScript SDK.

---

### Error: Cannot find module '@modelcontextprotocol/sdk/server/mcp.js'

**When**: Importing SDK modules at compile time or runtime.
**Cause**: The SDK uses Node.js subpath exports. TypeScript needs `"moduleResolution": "node16"` or `"bundler"` in `tsconfig.json` to resolve them. Older `"node"` resolution does not follow `exports` maps.
**Fix**:
1. Set `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "module": "node16",
       "moduleResolution": "node16"
     }
   }
   ```
2. Rebuild: `npx tsc --build`.
3. If using `"bundler"` resolution, ensure your bundler supports `exports`.

**Prevention**: Always start projects with `"moduleResolution": "node16"` when targeting Node.js ESM.

---

### Error: Tool not found when calling a registered tool

**When**: Client calls `callTool({ name: "my-tool" })` and gets a "tool not found" error.
**Cause**: Tool was registered after `server.connect()`, or the tool name has a typo, or the tool was registered on a different server instance.
**Fix**:
1. Register all tools *before* calling `server.connect(transport)`.
2. Verify the exact name string — names are case-sensitive.
3. Call `client.listTools()` to confirm what the server actually exposes.

**Prevention**: Register tools immediately after constructing the `McpServer`, before connecting any transport.

---

### Error: Server starts but no tools appear in client

**When**: `client.listTools()` returns an empty array despite tools being registered.
**Cause**: Capability advertisement mismatch. If you use the low-level `Server` class instead of `McpServer`, you must explicitly declare `capabilities: { tools: {} }` in the server options.
**Fix**:
1. If using `McpServer` (high-level): ensure tools are registered before `connect()`.
2. If using `Server` (low-level): pass capabilities explicitly:
   ```typescript
   const server = new Server(
     { name: "my-app", version: "1.0.0" },
     { capabilities: { tools: {} } }
   );
   ```
3. Restart both server and client after changes.

**Prevention**: Prefer `McpServer` — it handles capability advertisement automatically.

---

### Error: Invalid schema — Zod validation failures

**When**: Client sends arguments that fail Zod parsing.
**Cause**: Schema mismatch between what the LLM generates and what the tool expects. Common triggers: wrong types (`"123"` vs `123`), missing required fields, extra fields when `.strict()` is used.
**Fix**:
1. Check the exact Zod error message — it names the failing field and expected type.
2. Add `.describe()` to every field so LLMs know the expected format.
3. Use `.coerce.number()` instead of `z.number()` if clients may send numeric strings.
4. Use `.default()` for optional fields that have sensible defaults.

**Prevention**: Test every tool with MCP Inspector using realistic inputs. Use `.describe()` on all schema fields.

---

### Error: CORS errors with HTTP transport

**When**: Browser-based MCP clients fail to connect to an HTTP/SSE server.
**Cause**: The server does not return `Access-Control-Allow-Origin` headers. Browsers enforce CORS for cross-origin fetch and EventSource requests.
**Fix**:
Add CORS headers to your Express/HTTP setup:
```typescript
import cors from "cors";
app.use(cors({ origin: "https://your-client-origin.com" }));
```
Or for the Streamable HTTP transport, ensure your HTTP framework sends appropriate headers before the SDK handles the request.

**Prevention**: Always configure CORS when using HTTP-based transports. Test with a browser client during development.

---

### Error: Session lost between requests (Streamable HTTP)

**When**: Multi-turn interactions fail; server treats each request as a new session.
**Cause**: Streamable HTTP transport uses a session ID header (`Mcp-Session-Id`). If the client does not return this header on subsequent requests, the server creates a new session each time.
**Fix**:
1. Ensure your HTTP client reads `Mcp-Session-Id` from the response and sends it back.
2. If using a custom HTTP layer, do not strip custom headers.
3. Check that session state is stored in a map keyed by session ID, not globally.

**Prevention**: Use the SDK's built-in `StreamableHTTPClientTransport` which handles session headers automatically.

---

### Error: Connection refused when connecting to server

**When**: Client cannot establish connection to the MCP server.
**Cause**: Server is not running, wrong port, firewall blocking, or the server crashed silently on startup.
**Fix**:
1. Confirm the server process is running: `ps aux | grep node`.
2. Check the port: `lsof -i :3000`.
3. Look at server stderr for startup errors.
4. For stdio transport: ensure the command path in the client config is correct and the binary is executable.
5. For HTTP transport: verify host and port match between client and server.

**Prevention**: Add startup logging to stderr: `console.error("Server listening on port", PORT)`. Use health-check endpoints for HTTP servers.

---

### Error: Memory leaks with long-running servers

**When**: Server memory usage grows steadily over hours/days.
**Cause**: Common culprits: unbounded caches, event listeners not being removed, accumulating session state, closures retaining large objects.
**Fix**:
1. Profile with `node --inspect` and Chrome DevTools heap snapshots.
2. Add TTL and size limits to caches:
   ```typescript
   if (cache.size > 1000) {
     const oldest = cache.keys().next().value;
     cache.delete(oldest);
   }
   ```
3. Clean up session state on disconnect using the `close` event.
4. Use `WeakMap` or `WeakRef` for object caches where appropriate.

**Prevention**: Set memory alarms: `process.memoryUsage().heapUsed`. Implement bounded caches from the start.

---

### Error: EPIPE errors with stdio transport

**When**: Server writes to stdout after the client has disconnected.
**Cause**: The parent process (MCP client) closed its stdin/stdout pipe, but the server still tries to write a response.
**Fix**:
1. Handle the `EPIPE` error on `process.stdout`:
   ```typescript
   process.stdout.on("error", (err) => {
     if (err.code === "EPIPE") {
       process.exit(0); // client disconnected, exit cleanly
     }
   });
   ```
2. Ensure the server shuts down when the transport closes.

**Prevention**: Always listen for pipe errors on stdout/stderr. Use the SDK's transport `close` event to trigger cleanup.

---

### Error: OAuth "Unauthorized" — 401 on protected endpoints

**When**: Client connects to an HTTP server with OAuth enabled but gets rejected.
**Cause**: Missing or expired access token, wrong OAuth provider configuration, or the token does not have the required scopes.
**Fix**:
1. Verify the OAuth provider URL and client credentials in server config.
2. Check token expiration — refresh tokens if supported.
3. Confirm the scopes requested match what the server expects.
4. Inspect the `Authorization` header the client is sending.

**Prevention**: Log authentication failures with detail (but not the token itself). Implement token refresh logic in the client.

---

### Error: EADDRINUSE — Port already in use

**When**: Server fails to start on the configured port.
**Cause**: Another process is already listening on that port, or a previous server instance did not shut down cleanly.
**Fix**:
1. Find the process: `lsof -i :3000` or `netstat -tlnp | grep 3000`.
2. Kill the stale process: `kill <PID>`.
3. Or use a different port: `PORT=3001 node dist/index.js`.

**Prevention**: Use `SO_REUSEADDR` (default in Node.js `net.Server`). Configure port via environment variable. Add graceful shutdown handlers for `SIGINT`/`SIGTERM`.

---

### Error: TypeScript compilation errors with SDK imports

**When**: `tsc` reports errors on SDK import paths.
**Cause**: Multiple issues possible — missing `.js` extensions in imports (required for ESM), wrong `moduleResolution`, or mismatched `@types/node` version.
**Fix**:
1. Always use `.js` extensions in ESM imports, even for `.ts` source files:
   ```typescript
   // ✅ Correct
   import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
   // ❌ Wrong
   import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
   ```
2. Set `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "module": "node16",
       "moduleResolution": "node16",
       "target": "ES2022",
       "outDir": "dist"
     }
   }
   ```
3. Ensure `@types/node` version matches your Node.js major version.

**Prevention**: Use the SDK's recommended `tsconfig.json` settings from the start.

---

### Error: Maximum call stack size exceeded — circular references

**When**: `JSON.stringify()` inside a tool handler throws a stack overflow.
**Cause**: The object being serialized contains circular references (common with ORM models, DOM-like structures, or objects with parent/child back-references).
**Fix**:
1. Extract only the fields you need before serializing:
   ```typescript
   const safe = { id: record.id, name: record.name };
   return { content: [{ type: "text", text: JSON.stringify(safe) }] };
   ```
2. Use a circular-safe serializer as a fallback:
   ```typescript
   import { stringify } from "safe-stable-stringify";
   return { content: [{ type: "text", text: stringify(data) }] };
   ```

**Prevention**: Never pass raw ORM model instances or complex objects to `JSON.stringify()`. Map to plain DTOs first.

---

### Error: Timeout errors for long-running tools

**When**: Client reports a timeout before the tool handler completes.
**Cause**: The tool performs a slow operation (large file processing, external API call, database migration) that exceeds the client's timeout threshold.
**Fix**:
1. Check the client's timeout setting and increase if appropriate.
2. Use progress notifications to keep the connection alive:
   ```typescript
   server.tool("long-task", "Process large dataset.", {
     datasetId: z.string(),
   }, async ({ datasetId }, extra) => {
     const chunks = await getChunks(datasetId);
     for (let i = 0; i < chunks.length; i++) {
       if (extra.signal?.aborted) break;
       await processChunk(chunks[i]);
       await extra.reportProgress(i + 1, chunks.length);
     }
     return { content: [{ type: "text", text: `Processed ${chunks.length} chunks` }] };
   });
   ```
3. For very long operations, return immediately with a job ID and provide a separate polling tool.

**Prevention**: Set realistic expectations in tool descriptions. Use progress reporting. Break massive operations into smaller tools.

---

### Error: Invalid JSON-RPC response

**When**: Client receives a malformed response and fails to parse it.
**Cause**: Something writes to stdout besides the MCP server (e.g., `console.log()`, a library printing debug info, or a child process inheriting stdout).
**Fix**:
1. Replace all `console.log()` with `console.error()` — MCP stdio uses stdout for JSON-RPC:
   ```typescript
   // ❌ BAD — pollutes the JSON-RPC stream
   console.log("Debug info");
   
   // ✅ GOOD — stderr is safe for logging
   console.error("Debug info");
   ```
2. Redirect child process output away from stdout:
   ```typescript
   spawn("command", args, { stdio: ["pipe", "pipe", "inherit"] });
   ```
3. Suppress library debug output: set `DEBUG=""` or configure the logger.

**Prevention**: Never use `console.log()` in stdio MCP servers. Lint for it: `no-console` ESLint rule with `allow: ["error", "warn"]`.

---

### Error: SSE connection drops after 60 seconds

**When**: Using the legacy SSE transport; client disconnects after roughly one minute of inactivity.
**Cause**: Reverse proxy (nginx, Cloudflare, ALB) times out idle connections. SSE requires long-lived connections with keep-alive.
**Fix**:
1. Configure proxy timeouts:
   ```nginx
   proxy_read_timeout 86400s;
   proxy_send_timeout 86400s;
   ```
2. Or migrate to Streamable HTTP transport which uses standard request/response and does not require long-lived connections.

**Prevention**: Prefer Streamable HTTP over SSE for production deployments behind proxies.

---

### Error: "Unexpected token" when parsing server output

**When**: Client fails during initial handshake or after first tool call.
**Cause**: The server's `package.json` has `"type": "module"` but the entry point uses `require()`, or vice versa. Node.js emits a syntax error that contaminates stdout.
**Fix**:
1. If using ESM (`"type": "module"`): use `import`/`export` everywhere, add `.js` to relative imports.
2. If using CJS: remove `"type": "module"` or set it to `"commonjs"`, use `require()`/`module.exports`.
3. Check that the built output in `dist/` matches the module system declared in `package.json`.

**Prevention**: Decide ESM vs CJS at project init. Use `"type": "module"` with `"module": "node16"` in tsconfig for modern projects.

---

### Error: Client receives notifications but tool responses are empty

**When**: Tool calls return `{ content: [] }` even though the handler runs.
**Cause**: The handler does not return a value, or returns `undefined`. The SDK interprets a missing return as an empty response.
**Fix**:
Ensure every code path returns a `CallToolResult`:
```typescript
// ❌ BAD — missing return in else branch
server.tool("check", { id: z.string() }, async ({ id }) => {
  const item = await db.find(id);
  if (item) {
    return { content: [{ type: "text", text: JSON.stringify(item) }] };
  }
  // falls through → undefined
});

// ✅ GOOD — all paths return
server.tool("check", "Check if an item exists.", {
  id: z.string().describe("Item ID"),
}, async ({ id }) => {
  const item = await db.find(id);
  if (!item) {
    return { content: [{ type: "text", text: `Item ${id} not found.` }], isError: true };
  }
  return { content: [{ type: "text", text: JSON.stringify(item, null, 2) }] };
});
```

**Prevention**: Enable `"noImplicitReturns": true` in `tsconfig.json`. Review every handler for early returns and missing else branches.

---

## Quick Diagnostic Checklist

| Symptom | First check |
|---|---|
| Import errors | `moduleResolution` in tsconfig |
| Tools not visible | Tools registered before `connect()`? |
| Garbled responses | `console.log()` on stdout? |
| Connection drops | Proxy timeout settings |
| Memory growth | Unbounded caches or listeners |
| Auth failures | Token expiration and scopes |
| Port conflicts | `lsof -i :<port>` |
| Timeout | Progress reporting enabled? |

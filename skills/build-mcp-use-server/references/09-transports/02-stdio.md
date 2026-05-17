# stdio transport

`mcp-use/server` is HTTP-first. In `mcp-use@1.26.0`, `MCPServer` exposes HTTP listener and Fetch-handler entry points; it does **not** expose a server-side stdio entry point.

Primary-source note: the published package declares `listen(port?)` and `getHandler(opts?)`; the canonical CLI page documents `mcp-use start --port` as the production server command. Sources: `mcp-use@1.26.0/package/dist/src/server/mcp-server.d.ts`; https://manufact.com/docs/typescript/server/cli-reference.

## What not to do

```typescript
await server.listen()      // starts HTTP; it does not switch to stdio
await server.listen(3000)  // HTTP on a TCP port
```

Do not point a spawned-process stdio client at an `mcp-use/server` entry file and expect JSON-RPC over stdin/stdout. The process will start an HTTP server instead.

## Use HTTP when possible

For local desktop testing, run the `mcp-use` server over Streamable HTTP (`03-streamable-http.md`) and configure URL-capable clients to use `/mcp`.

For production parity, build and start the same HTTP surface:

```bash
mcp-use start --port 3000
```

See `03-streamable-http.md` and `../03-cli/05-mcp-use-start.md`.

## If strict stdio is required

Some legacy hosts only support a child process with JSON-RPC over stdin/stdout. That is a different server shape from `mcp-use/server`.

Use one of these instead:

| Need | Path |
|---|---|
| Keep `mcp-use` features | Run local HTTP and configure the client by URL |
| Ship a true stdio binary | Use a separate stdio implementation outside `mcp-use/server` |
| Proxy existing stdio tools behind HTTP | Use `server.proxy(...)` from an HTTP gateway |

The detailed manual fallback lives in `../02-setup/04-manual-stdio-server.md`.

## Logging for raw stdio

In a true stdio server, stdout is reserved for JSON-RPC. Write diagnostics to stderr:

```typescript
console.error('debug message')  // safe for stdio diagnostics
console.log('debug message')    // corrupts JSON-RPC over stdio
```

Do not rely on generic application loggers in raw stdio mode unless you have verified every level writes to stderr.

## Limitations

| Concern | mcp-use server |
|---|---|
| True stdio server | Not supported by `MCPServer` |
| Local URL-based clients | Supported via Streamable HTTP |
| OAuth callbacks | Use HTTP plus a reachable `baseUrl` |
| Browser-rendered widgets | Use HTTP; widgets require fetched assets |
| Notifications, sampling, elicitation | Use stateful Streamable HTTP |

For anything internet-reachable, use Streamable HTTP (`03-streamable-http.md`).

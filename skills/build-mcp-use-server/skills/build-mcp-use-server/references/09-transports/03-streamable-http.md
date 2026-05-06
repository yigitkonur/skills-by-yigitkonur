# Streamable HTTP transport

The primary transport for networked MCP servers. One canonical endpoint (`/mcp`), unified session lifecycle, supports both streamed and request/response modes per request.

## Minimal HTTP server

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

server.tool({ name: 'hello' }, async () => text('Hello!'))

await server.listen(3000)
```

`server.listen(port?)` binds the HTTP server. For port and host resolution, see `../08-server-config/02-network-config.md`.

## The `/mcp` endpoint

| Method | Path | Behavior |
|---|---|---|
| `POST` | `/mcp` | Send a JSON-RPC request. Response is either a single JSON body or an SSE stream, depending on the client's `Accept` header. |
| `GET` | `/mcp` | Open a long-lived SSE stream for server-initiated messages (notifications, progress, sampling). |
| `DELETE` | `/mcp` | Terminate a session (client sends `mcp-session-id`). |
| `HEAD` | `/mcp` | Cheap health check / keep-alive. |

`listen()` automatically mounts all four methods. Do not register custom handlers on `/mcp`.

## Streaming response semantics

The same `POST /mcp` handler serves two response modes, decided per request from the client's `Accept` header:

| `Accept` header | Mode | Used for |
|---|---|---|
| Includes `text/event-stream` | Stateful stream-capable response | Clients that want progress, notifications during the call, sampling, or elicitation |
| Does not include `text/event-stream` | Stateless JSON response | HTTP-only clients and edge proxies |

This is auto-detection and applies per request on Node.js. To force JSON/stateless behavior globally, set `stateless: true` (`04-stateless-mode.md`).

## GET stream behavior

A stateful client opens `GET /mcp` with its `mcp-session-id` header. The server keeps the connection open and pushes:

- Server-to-client notifications (`server.sendNotification(...)`)
- Progress events from in-flight tool calls
- Sampling and elicitation requests

When the connection drops, the client reconnects with the same session ID. Session metadata comes from the configured store (`../10-sessions/`); active stream fan-out comes from the stream manager.

## Headers on the wire

| Direction | Header | Purpose |
|---|---|---|
| Client → server | `Accept` | Selects streamed vs JSON response |
| Client → server | `mcp-session-id` | Identifies an existing session (after init handshake) |
| Client → server | `mcp-protocol-version` | Protocol version negotiation |
| Server → client | `mcp-session-id` | Issued during init handshake |

Override `cors.exposeHeaders` to make `mcp-session-id` readable from browser clients (default config does this - see `../08-server-config/03-cors-and-allowed-origins.md`).

## Browser security

Set `allowedOrigins` whenever the server is reachable from a browser. See `../08-server-config/03-cors-and-allowed-origins.md` for CORS and `../08-server-config/04-dns-rebinding-protection.md` for the attack model.

## Local dev pattern

Bind to `localhost` during development and point URL-capable MCP clients at `/mcp`.

For tunneling to share a localhost server with a remote host, see `../21-tunneling/`.

## Related

- Stateful vs stateless behavior: `04-stateless-mode.md`
- Serverless platforms: `05-serverless-handlers.md`
- Legacy `/sse` alias: `06-sse-alias.md`
- Session stores for stateful HTTP: `../10-sessions/`

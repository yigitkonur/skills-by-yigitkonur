# MCP Protocol Specification Reference

Quick reference for the MCP protocol (version 2025-11-25) as it applies to building servers with the TypeScript SDK.

## Architecture

MCP uses a client-host-server architecture:

- **Host**: LLM application (e.g., Claude Desktop) that creates and manages clients
- **Client**: 1:1 connector between host and a server, handles protocol negotiation
- **Server**: Provides tools, resources, and prompts via MCP primitives

Each host can run multiple clients, each connected to a different server. Servers operate independently and cannot see into other servers or read the full conversation.

## Protocol basics

All messages use JSON-RPC 2.0 over UTF-8 encoding. Three message types:

| Type | Has `id` | Expects response |
|---|---|---|
| Request | Yes | Yes (result or error) |
| Response | Yes (matching request) | No |
| Notification | No | No |

Request IDs MUST NOT be `null` and MUST be unique within a session.

## Lifecycle phases

### 1. Initialization

Client sends `initialize` request with protocol version and capabilities. Server responds with its capabilities. Client then sends `initialized` notification.

```typescript
// The SDK handles this automatically via server.connect(transport)
// You configure capabilities via McpServer constructor:
new McpServer(
  { name: "my-server", version: "1.0.0", description: "Optional description" },
  {
    capabilities: {
      tools: { listChanged: true },
      resources: { subscribe: true, listChanged: true },
      prompts: { listChanged: true },
      logging: {},
    },
    instructions: "Optional instructions for the client",
  }
);
```

### 2. Operation

Both parties respect negotiated capabilities. Clients can call server methods (tools, resources, prompts). Servers can send notifications and request sampling/elicitation.

### 3. Shutdown

- **stdio**: Client closes stdin to server process, waits for exit, sends SIGTERM then SIGKILL
- **HTTP**: Client sends DELETE to the MCP endpoint with session ID, or closes connections

## Capability negotiation

| Side | Capability | Enables |
|---|---|---|
| Server | `tools` | Tool listing and invocation |
| Server | `resources` | Resource listing and reading |
| Server | `prompts` | Prompt listing and retrieval |
| Server | `logging` | Log message emission |
| Server | `completions` | Argument autocompletion |
| Client | `sampling` | Server can request LLM completions |
| Client | `elicitation` | Server can request user input |
| Client | `roots` | Server can query filesystem boundaries |

Sub-capabilities:
- `listChanged`: Server will notify when list changes (tools, resources, prompts)
- `subscribe`: Client can subscribe to individual resource changes

## Server primitives

| Primitive | Control | Use case |
|---|---|---|
| **Tools** | Model-controlled | Functions the LLM can call (API calls, computations, actions) |
| **Resources** | Application-controlled | Data the host can read (files, DB records, API data) |
| **Prompts** | User-controlled | Reusable message templates (slash commands, workflows) |

## Tool specification requirements

- Tool name: 1-128 characters, letters/digits/underscore/hyphen/dot, case-sensitive
- `inputSchema` MUST be valid JSON Schema (defaults to 2020-12 dialect if no `$schema`)
- For parameterless tools: use `{"type": "object", "additionalProperties": false}` (SDK handles this when no `inputSchema` is provided)
- `outputSchema`: optional, when set the handler MUST return `structuredContent` conforming to it
- `annotations`: behavioral hints, not security guarantees — clients MUST treat as untrusted unless from trusted server
- `execution.taskSupport`: `"forbidden"` (default), `"optional"`, or `"required"` — for experimental task-based tools

## Content types in tool results

| Type | Fields | Use |
|---|---|---|
| `text` | `text` | Most common — text/JSON responses |
| `image` | `data` (base64), `mimeType` | Charts, screenshots |
| `audio` | `data` (base64), `mimeType` | Audio clips |
| `resource` | `resource: { uri, text?, blob? }` | Embedded resource content |
| `resource_link` | `uri`, `name?`, `description?`, `mimeType?` | Pointer to readable resource |

All content types support optional annotations: `audience` (`["user"]`, `["assistant"]`, or both), `priority` (0.0-1.0).

## Error codes

| Code | Name | When to use |
|---|---|---|
| -32700 | Parse error | Malformed JSON |
| -32600 | Invalid request | Bad JSON-RPC structure |
| -32601 | Method not found | Capability not declared |
| -32602 | Invalid params | Bad tool name, missing args, invalid cursor |
| -32603 | Internal error | Server-side failure |
| -32000 | Connection closed | Transport closed |
| -32001 | Request timeout | Request timed out |
| -32002 | Resource not found | Unknown resource URI |
| -32042 | URL elicitation required | Server needs URL-mode elicitation first |

For tool execution errors (API failures, validation errors): use `isError: true` in the result, not protocol error codes. This lets the LLM self-correct.

## Icons (2025-11-25)

Servers can expose icons for the implementation, tools, resources, and prompts:

```typescript
{
  icons: [
    { src: "https://example.com/icon.png", mimeType: "image/png", sizes: ["48x48"] },
    { src: "https://example.com/icon.svg", mimeType: "image/svg+xml", sizes: ["any"] },
  ]
}
```

Required MIME support: `image/png`, `image/jpeg`. Recommended: `image/svg+xml`, `image/webp`.

Security: icons MUST use HTTPS or `data:` URIs. Reject `javascript:`, `file:`, `ftp:`, `ws:` schemes. Fetch without credentials.

## Pagination

All list operations (`tools/list`, `resources/list`, `prompts/list`, `resources/templates/list`) support cursor-based pagination:

- Server returns `nextCursor` when more results exist
- Client passes `cursor` in next request
- Cursors are opaque strings — do not parse or persist across sessions
- Page size is server-determined

## Sampling (server requesting LLM completions)

Servers can request the client to run an LLM completion via `server.server.createMessage()`. Requires client to declare `sampling` capability. A human-in-the-loop SHOULD always be available.

2025-11-25 addition: sampling now supports `tools` and `toolChoice` for agentic tool-use loops.

## Elicitation (server requesting user input)

Servers can request user input via `server.server.elicitInput()`. Two modes:
- **Form mode**: Structured data via JSON Schema (flat objects, primitives only). MUST NOT request sensitive info.
- **URL mode**: Navigate user to external URL for sensitive operations (API keys, OAuth). New in 2025-11-25.

## Tasks (experimental, 2025-11-25)

Durable state machines wrapping long-running requests. Enable polling and deferred result retrieval. States: `working` → `input_required` | `completed` | `failed` | `cancelled`.

Use `server.experimental.tasks` — API may change without notice.

## Transport: Streamable HTTP details

- Server MUST provide a single endpoint (e.g., `/mcp`) supporting POST, GET, and DELETE
- POST: Client sends JSON-RPC messages; server responds with JSON or SSE stream
- GET: Client opens SSE stream for server-initiated notifications
- DELETE: Client ends session
- Server MUST validate `Origin` header; respond 403 for invalid origins
- Server MUST return session ID in `Mcp-Session-Id` response header (stateful mode)
- Client MUST include `MCP-Protocol-Version` header on all requests after initialization
- SSE streams support resumability via `Last-Event-ID` header

## Security requirements from spec

1. Servers MUST validate `Origin` header on HTTP to prevent DNS rebinding
2. Servers SHOULD bind only to localhost (127.0.0.1) when running locally
3. Tool annotations are untrusted — clients MUST NOT rely on them for security
4. All HTTP auth endpoints MUST use HTTPS
5. Servers MUST NOT expose user data without consent
6. Servers MUST validate all tool inputs
7. Servers MUST implement rate limiting on tool invocations
8. Access tokens MUST be validated per OAuth 2.1 Section 5.2

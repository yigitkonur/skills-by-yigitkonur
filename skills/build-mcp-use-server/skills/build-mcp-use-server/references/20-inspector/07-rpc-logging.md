# RPC Logging

The Inspector streams every JSON-RPC frame between itself and a connected MCP server in real time. Use it to debug protocol issues, verify request shape, and inspect notifications and errors.

## What is logged

Every frame in either direction:

- **Tool calls** — `tools/call` requests and their responses
- **Resource reads** — `resources/read`, `resources/list`, `resources/templates/list`
- **Prompts** — `prompts/list`, `prompts/get`
- **Notifications** — server-initiated notifications (`notifications/*`)
- **Initialization** — `initialize`, `initialized`
- **Errors** — error responses and connection issues

If it goes over the wire as JSON-RPC, it appears in the panel.

## Opening the panel

1. Open Tools, Resources, or Prompts for a connected server.
2. The **RPC Messages** panel sits at the bottom of the left sidebar (collapsed by default).
3. Click the **RPC Messages** header to expand.
4. Drag the handle above it to resize.

## Message row format

Each message renders as a row:

| Column | Meaning |
|---|---|
| Timestamp | Local time the inspector received the message |
| Direction | `↑ SEND` (inspector → server) or `↓ RECEIVE` (server → inspector) |
| Method | JSON-RPC method (e.g. `tools/call`, `resources/read`, `notifications/tools/list_changed`) |
| Expand toggle | Click row to reveal full JSON payload |

## Message format

Each logged frame:

```ts
{
  id: string;              // Unique message ID (inspector-side)
  serverId: string;        // Connection ID (server URL)
  direction: "SEND" | "RECEIVE";
  method: string;          // JSON-RPC method name
  timestamp: string;       // ISO timestamp
  payload: unknown;        // Full JSON-RPC payload
}
```

The `payload` is the literal JSON-RPC envelope, including `jsonrpc`, `id`, `method`, `params` (for requests/notifications), and `result` or `error` (for responses).

## Reading the wire

Sequence for a typical tool call:

```text
↑ SEND     14:32:01.123  tools/call            {jsonrpc:"2.0", id:42, method:"tools/call", params:{name:"get_weather", arguments:{city:"SF"}}}
↓ RECEIVE  14:32:01.450  tools/call (response) {jsonrpc:"2.0", id:42, result:{content:[…], structuredContent:{…}, _meta:{…}}}
```

Notifications appear without a paired response and have no `id`:

```text
↓ RECEIVE  14:32:02.001  notifications/tools/list_changed  {jsonrpc:"2.0", method:"notifications/tools/list_changed"}
```

## Use cases

### Verify request shape

Click the SEND row to see exactly what the inspector sent. Confirm `arguments` match the tool's input schema and `params.name` matches the registered tool name.

### Verify response structure

Click the RECEIVE row to inspect:

- `result.content` — the LLM-visible text/image/audio array.
- `result.structuredContent` — the typed object passed to widgets via `useWidget` props.
- `result._meta` — server metadata (e.g. `openai/outputTemplate`, `mcp/resourceUri`).

If a widget is not rendering, check `_meta` here first.

### Catch errors

Errors land as RECEIVE frames with `result` replaced by `error`:

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "error": {
    "code": -32602,
    "message": "Invalid params: city is required"
  }
}
```

Standard JSON-RPC error codes apply: `-32700` parse, `-32600` invalid request, `-32601` method not found, `-32602` invalid params, `-32603` internal error.

### Watch HMR and notification flow

After `mcp-use dev` reloads, the panel shows `notifications/tools/list_changed`, `resources/list_changed`, `prompts/list_changed`. If list_changed fires but the inspector doesn't refresh, check that the server emits the notification at all.

### Inspect initialization handshake

Filter on `initialize` to verify protocol version negotiation and capability advertisement.

## See also

- `../05-responses/` — anatomy of `result.content`, `structuredContent`, `_meta`.
- `../14-notifications/` — server-side `list_changed` and other notifications.
- `../23-debug/` — debugging strategies for common protocol problems.

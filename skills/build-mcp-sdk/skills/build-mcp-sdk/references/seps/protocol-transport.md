# SEPs — Protocol, Transport, and Schema

## SEP-1613: JSON Schema 2020-12 as Default Dialect

**Status:** Final

Establishes JSON Schema 2020-12 as the default dialect for all embedded schemas in MCP (tool `inputSchema`, `outputSchema`, elicitation `requestedSchema`).

**Rules:**
- Schemas without `$schema` field MUST conform to 2020-12
- Schemas MAY include `$schema` to declare a different dialect
- `inputSchema` MUST NOT be `null` — for parameterless tools, use `{}` or `{"type": "object"}`
- Clients MUST support at least 2020-12
- Handle unsupported dialects gracefully with appropriate errors

**Breaking keywords from draft-07 → 2020-12:**
- `dependencies` → `dependentSchemas` + `dependentRequired`
- Positional array validation → `prefixItems`

**SDK note:** The TypeScript SDK uses Zod, which auto-converts to JSON Schema via `zod-to-json-schema`. Verify the output conforms to 2020-12.

## SEP-1699: SSE Polling via Server-Side Disconnect

**Status:** Final

Servers can now disconnect SSE streams while work is in-flight, enabling async/polling architectures without holding HTTP connections.

**Protocol:**
1. Server opens SSE stream and immediately sends priming event: `id: <some-id>\ndata: \n\n`
2. Server MAY disconnect at any time after sending the event ID
3. Server SHOULD send `retry` field to control reconnection pacing
4. Client sees disconnect, reconnects with `Last-Event-ID` header
5. Server resumes stream from that event ID

**Rules:**
- Server MUST send priming event with `id` and empty `data` when starting any SSE stream
- Clients MUST respect the `retry` field

**SDK impact:** Transport layer's SSE stream initiation must send the priming event. `InMemoryEventStore` or custom `EventStore` handles replay on reconnect.

## SEP-1319: Decouple Request Payloads from RPC Method Definitions

**Status:** Final

Structural refactoring: all `params` and `result` types are now standalone named schemas (e.g., `CallToolRequestParams`) rather than inline definitions. No wire-format changes.

**Impact:** Payload types become independently importable. Enables future gRPC bindings.

## SEP-1330: Elicitation Enum Schema Improvements

**Status:** Final

Deprecates non-standard `enumNames` property. Introduces four JSON Schema-compliant enum patterns:

**Single-select with display titles (new standard):**
```json
{
  "type": "string",
  "oneOf": [
    { "const": "#FF0000", "title": "Red" },
    { "const": "#00FF00", "title": "Green" }
  ]
}
```

**Multi-select (new):**
```json
{
  "type": "array",
  "minItems": 1,
  "maxItems": 3,
  "items": { "type": "string", "enum": ["Red", "Green", "Blue"] }
}
```

**Multi-select with titles (new):**
```json
{
  "type": "array",
  "items": { "anyOf": [{ "const": "#FF0000", "title": "Red" }, ...] }
}
```

`ElicitResult.content` now supports `string[]` for multi-select responses.

## SEP-1034: Default Values for Elicitation Schemas

**Status:** Final

Adds optional `default` field to `StringSchema`, `NumberSchema`, and `EnumSchema` in elicitation:

```json
{
  "type": "string",
  "title": "Recipients",
  "default": "alice@company.com, bob@company.com"
}
```

Clients supporting defaults SHOULD pre-populate form fields. Fully backward compatible.

## SEP-2133: Extensions Framework

**Status:** Final

Establishes the mechanism for MCP protocol extensions via capability negotiation.

**Extension identifier format:** `{vendor-prefix}/{extension-name}` (e.g., `io.modelcontextprotocol/ui`)

**Capability declaration:**
```json
{
  "capabilities": {
    "extensions": {
      "io.modelcontextprotocol/ui": {
        "mimeTypes": ["text/html;profile=mcp-app"]
      }
    }
  }
}
```

**Server-side capability check:**
```typescript
const hasUI = clientCapabilities?.extensions?.["io.modelcontextprotocol/ui"];
if (hasUI) {
  // Register UI-enhanced tools
} else {
  // Register text-only fallback
}
```

**Governance tiers:**
| Tier | Repository | Maintained by |
|---|---|---|
| Official | `github.com/modelcontextprotocol/ext-*` | Delegated maintainers |
| Experimental | `github.com/modelcontextprotocol/experimental-ext-*` | Working Groups |
| Unofficial | Anywhere | External developers |

**Rules:**
- Extensions MUST be disabled by default in SDKs; require explicit opt-in
- Breaking changes MUST use a new extension identifier
- Official extensions MUST be under Apache 2.0
- If one party supports but the other doesn't, MUST fall back to core protocol or reject with error

## SEP-1865: MCP Apps (Interactive UIs)

**Status:** Final (Extensions Track)

Optional extension enabling servers to deliver interactive HTML UIs via sandboxed iframes.

**Key concepts:**
- `ui://` URI scheme for UI resource declaration
- Content type: `text/html;profile=mcp-app`
- Tools reference UI resources through metadata
- UI ↔ host communication via standard MCP JSON-RPC
- All UI content runs in sandboxed iframes

**Requires extension negotiation per SEP-2133.**

**Reference:** `modelcontextprotocol/ext-apps` repository.

# Schemas, Errors, and Request-Handler Keys

Three independent rewrites that show up across most handler files.

## Zod v3 → Zod v4

v1 supports both Zod v3 and v4 via a runtime compatibility shim. v2 drops the shim and uses Zod v4 exclusively.

```typescript
// v1
import { z } from "zod";

// v2
import * as z from "zod/v4";
```

The import shape is also different — v4 is namespace-only.

## Raw shape → full schema

v1 accepts `ZodRawShape` (a plain object of named Zod fields) as a shorthand for tool input/output schemas. v2 rejects raw shapes outright; you must pass a full `z.object()`.

```typescript
// v1 — raw shape works
server.registerTool("greet", {
  inputSchema: { name: z.string() },
}, handler);

// v2 — full z.object() required
server.registerTool("greet", {
  inputSchema: z.object({ name: z.string() }),
}, handler);
```

The same applies to `outputSchema`, `argsSchema` on prompts, and any other schema field. There is no compatibility path — raw shapes throw at registration time in v2.

## JSON Schema dialect

v1 emits Draft-7 via `zod-to-json-schema`. v2 emits 2020-12 natively via `z.toJSONSchema()`.

If your server publishes JSON Schema externally (e.g. for client-side validation, API contracts, or third-party tooling), check that your consumers handle 2020-12. Most modern validators do; some embedded clients still target Draft-7.

You can drop the `zod-to-json-schema` dependency entirely after migration — the SDK no longer uses it.

## Error class rename

```typescript
// v1
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
throw new McpError(ErrorCode.InvalidParams, "Bad input");

// v2 — wire-protocol errors
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";
throw new ProtocolError(ProtocolErrorCode.InvalidParams, "Bad input");

// v2 — local SDK errors (new)
import { SdkError, SdkErrorCode } from "@modelcontextprotocol/core";
throw new SdkError(SdkErrorCode.NotConnected, "...");
```

The error-code enum is renamed identically (`ErrorCode.X` → `ProtocolErrorCode.X`); enum values are unchanged. A find-replace from `McpError` to `ProtocolError` and `ErrorCode` to `ProtocolErrorCode` covers the rewrite, modulo the import line.

`SdkError` is new — used by the SDK internals to signal local-only failures (not connected, transport closed, etc.) that shouldn't go on the wire. You usually don't need to throw it directly.

## Soft-error pattern is unchanged

`isError: true` on a `CallToolResult` is preserved across versions. Recoverable errors should still come back as tool results, not thrown protocol errors — the LLM self-correction story works the same way.

```typescript
// Both v1 and v2
return { content: [{ type: "text", text: "Error: rate limit hit" }], isError: true };
```

## Request-handler keys: Zod schema → method string

v1 registers low-level request handlers using Zod schema objects. v2 uses method-name strings.

```typescript
// v1
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
server.server.setRequestHandler(CallToolRequestSchema, async (req, extra) => { ... });
server.server.setRequestHandler(ListToolsRequestSchema, async (req, extra) => { ... });

// v2
server.server.setRequestHandler("tools/call", async (req, ctx) => { ... });
server.server.setRequestHandler("tools/list", async (req, ctx) => { ... });
```

Common substitutions:

| v1 schema | v2 method string |
|---|---|
| `CallToolRequestSchema` | `"tools/call"` |
| `ListToolsRequestSchema` | `"tools/list"` |
| `ListResourcesRequestSchema` | `"resources/list"` |
| `ReadResourceRequestSchema` | `"resources/read"` |
| `SubscribeRequestSchema` | `"resources/subscribe"` |
| `UnsubscribeRequestSchema` | `"resources/unsubscribe"` |
| `ListPromptsRequestSchema` | `"prompts/list"` |
| `GetPromptRequestSchema` | `"prompts/get"` |
| `CreateMessageRequestSchema` | `"sampling/createMessage"` |
| `ElicitRequestSchema` | `"elicitation/create"` |

Most servers don't need `setRequestHandler` directly — `registerTool` / `registerResource` / `registerPrompt` cover the typical cases. Only fall through to it for sampling, elicitation, resource subscriptions, or custom protocol extensions.

## Pre-flight checklist for this rewrite

- [ ] All `import { z } from "zod"` rewritten to `import * as z from "zod/v4"`.
- [ ] All `inputSchema: { ... }` raw shapes wrapped in `z.object({ ... })`.
- [ ] All `outputSchema: { ... }` raw shapes wrapped in `z.object({ ... })`.
- [ ] All prompt `argsSchema: { ... }` wrapped in `z.object({ ... })`.
- [ ] `zod-to-json-schema` removed from `package.json`.
- [ ] `McpError` → `ProtocolError`, `ErrorCode` → `ProtocolErrorCode`.
- [ ] Error imports moved from `@modelcontextprotocol/sdk/types.js` to `@modelcontextprotocol/core`.
- [ ] `setRequestHandler(SomeSchema, ...)` calls rewritten to `setRequestHandler("method/name", ...)`.
- [ ] Imports of `*RequestSchema` from `/types.js` removed where no longer needed.
- [ ] If your server published JSON Schema externally, downstream consumers verified for 2020-12 support.

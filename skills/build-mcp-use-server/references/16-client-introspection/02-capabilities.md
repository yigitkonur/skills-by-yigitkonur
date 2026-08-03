# Capabilities and Client Feature Detection

*Read this when checking if a client supports elicitation, views, or other MCP features.*

Query the current request's declared capabilities to adapt tool behavior.

## Methods

### can(capability: string): boolean

Checks if client advertises a specific capability by name.

```typescript
if (ctx.client.can("elicitation")) {
  // Client supports input_required form/url mode
}
```

**Common capabilities:** `"elicitation"`, `"extensions"`, `"roots"`, etc.

### capabilities(): ClientCapabilities

Returns the full capabilities object:

```typescript
const caps = ctx.client.capabilities();
const supportsFormElicitation = caps.elicitation?.form !== undefined;
const supportsUrlElicitation = caps.elicitation?.url !== undefined;
```

**Shape of `ClientCapabilities`:**
```typescript
{
  elicitation?: {
    form?: {};      // Form-mode elicitation supported
    url?: {};       // URL-mode elicitation supported
  };
  extensions?: {
    [id: string]: Record<string, unknown>;  // Extension settings
  };
  // ... other MCP spec capabilities
}
```

## Usage: Elicitation Detection

`inputRequired.elicit()` takes `{ message, requestedSchema }` and builds one `InputRequest`; it must be nested under a key in `inputRequired({ inputRequests: { <key>: ... } })`. The key you choose is the same key you read back from `ctx.inputResponses` (via `acceptedContent()` or `inputResponse()`) on the retried call — there is no separate `correlationKey` field.

```typescript
import { acceptedContent, inputRequired } from "mcp-use";

const confirmSchema = z.object({
  confirmed: z.boolean().describe("Confirm deletion?"),
});

export const confirmDelete = server.tool(
  {
    name: "delete_resource",
    inputSchema: z.object({ resourceId: z.string() }),
  },
  async ({ resourceId }, ctx) => {
    // Check if client supports form-based elicitation
    if (!ctx.client.capabilities().elicitation?.form) {
      return {
        isError: true,
        content: [{ type: "text", text: "Client does not support elicitation." }],
      };
    }

    const confirmation = acceptedContent(
      ctx.inputResponses,
      `delete_${resourceId}`,
      confirmSchema
    );
    if (confirmation === undefined) {
      // Initial call, or the client hasn't returned accepted content yet.
      return inputRequired({
        inputRequests: {
          [`delete_${resourceId}`]: inputRequired.elicit({
            message: `Delete ${resourceId}?`,
            requestedSchema: confirmSchema,
          }),
        },
      });
    }

    if (!confirmation.confirmed) {
      return {
        isError: true,
        content: [{ type: "text", text: "Deletion not confirmed." }],
      };
    }

    // Perform deletion
    await db.delete(resourceId);
    return {
      content: [{ type: "text", text: `Deleted ${resourceId}` }],
    };
  }
);
```

The handler runs again from the top on the retry — read `ctx.inputResponses` before doing any side effect, never assume this is the "second half" of a paused function.

## supportsViews(): boolean

Shorthand for detecting MCP app support:

```typescript
if (ctx.client.supportsViews()) {
  // Client declares io.modelcontextprotocol/ui extension with
  // "text/html;profile=mcp-app" in its mimeTypes
  // Can return structuredContent for views
}
```

Not just extension presence — the actual check requires the extension's `mimeTypes` array to include the MCP App MIME type:
```typescript
const uiExt = ctx.client.extension("io.modelcontextprotocol/ui");
uiExt !== undefined
  && Array.isArray((uiExt as Record<string, unknown>).mimeTypes)
  && (uiExt as { mimeTypes: unknown[] }).mimeTypes.includes("text/html;profile=mcp-app")
```
A client that declares the `io.modelcontextprotocol/ui` extension without that MIME type in `mimeTypes` does **not** satisfy `supportsViews()`.

## extension(id: string)

Get specific extension settings:

```typescript
const uiExt = ctx.client.extension("io.modelcontextprotocol/ui");
if (uiExt && uiExt.mimeTypes?.includes("text/html;profile=mcp-app")) {
  // Client supports MCP apps
}
```

## info(): Client Implementation

Returns client name and version:

```typescript
const clientInfo = ctx.client.info();
console.log(`Client: ${clientInfo.name} v${clientInfo.version}`);
// May be partial for legacy clients
```

## Key points

- **Per-request only.** Capabilities are declared in the current MCP request envelope; they change per call.
- **No session state.** Capabilities are not cached; check them within every callback.
- **Graceful fallback.** Always have a text-only path for clients without the capability.
- **v2 specific.** `ctx.client` (`RequestClientContext`) is a v2 API with no v1 equivalent; do not port v1 session-based capability checks to it.

See `references/16-client-introspection/03-apps-detection.md` for MCP app detection patterns.

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

```typescript
export const confirmDelete = server.tool(
  {
    name: "delete_resource",
    inputSchema: z.object({
      resourceId: z.string(),
      confirmed: z.boolean().optional(),
    }),
  },
  async ({ resourceId, confirmed }, ctx) => {
    if (!confirmed) {
      // Check if client supports form-based elicitation
      if (ctx.client.capabilities().elicitation?.form) {
        return inputRequired.elicit({
          schema: z.object({
            confirmed: z.boolean().describe("Confirm deletion?"),
          }),
          correlationKey: `delete_${resourceId}`,
        });
      } else {
        // Fallback: require deletion via explicit request
        return {
          isError: true,
          content: [
            {
              type: "text",
              text: 'Must supply confirmed: true. Deletion confirmed.',
            },
          ],
        };
      }
    }

    // Perform deletion
    await db.delete(resourceId);
    return {
      content: [{ type: "text", text: `Deleted ${resourceId}` }],
    };
  }
);
```

## supportsViews(): boolean

Shorthand for detecting MCP app support:

```typescript
if (ctx.client.supportsViews()) {
  // Client declares io.modelcontextprotocol/ui extension
  // Can return structuredContent for views
}
```

Equivalent to:
```typescript
ctx.client.extension("io.modelcontextprotocol/ui") !== undefined
```

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
- **v2 specific.** The `RequestClientContext` shape is fixed in v2.0.0-beta.66; future v2.0.z patches will not add new `can()` capabilities.

See `references/16-client-introspection/03-apps-detection.md` for MCP app detection patterns.

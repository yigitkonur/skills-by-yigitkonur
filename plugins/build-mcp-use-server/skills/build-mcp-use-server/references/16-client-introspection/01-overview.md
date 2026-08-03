# Client Introspection Overview

*Read this when detecting client capabilities, views support, or user context in a tool callback.*

Within a tool callback, `ctx.client` provides query methods for the capabilities and features the **current client request** declares. This is per-request metadata, not session-level or user-level state.

## Available Methods

| Method | Returns | Use when |
|--------|---------|----------|
| `can(capability: string)` | `boolean` | Checking if client supports a named feature |
| `capabilities()` | `ClientCapabilities` | Inspecting full capability object |
| `extension(id: string)` | Extension settings \| `undefined` | Detecting MCP app support via `io.modelcontextprotocol/ui` |
| `info()` | Client name/version (partial) | Logging client identity |
| `user()` | `UserContext \| undefined` | Accessing end-user locale, location, etc. (OpenAI/ChatGPT clients only) |
| `supportsViews()` | `boolean` | Detecting MCP app / view support |

## Typical Usage

```typescript
export const complexTool = server.tool(
  { name: "analyze", inputSchema: z.object({ data: z.string() }) },
  async ({ data }, ctx) => {
    // Check capabilities
    if (ctx.client.supportsViews()) {
      // Return structured content for MCP app rendering
      return {
        content: [{ type: "text", text: "Analysis result" }],
        structuredContent: { chart: {...} },
      };
    }

    // Fallback for text-only clients
    return {
      content: [{ type: "text", text: "Analysis result (text)" }],
    };
  }
);
```

## What v2 Renamed

The v1 method `ctx.client.supportsApps()` does not exist in v2 — it was renamed to `ctx.client.supportsViews()`. v1's `ctx.client` also reflected the session-level initialize handshake (stable for the connection's lifetime); v2's `ctx.client` is a per-request snapshot re-derived from every request's metadata, since v2 keeps no session state.

## `ctx.client.user()`: OpenAI End-User Hints

`ctx.client.user()` returns `UserContext | undefined` — normalized, client-reported end-user hints that ChatGPT and other OpenAI-family hosts attach to ordinary requests (not part of the MCP client-info handshake). Requests without recognized metadata return `undefined`. Every call returns a fresh object, including a fresh `location` object.

```typescript
export interface UserContext {
  locale?: string;        // from openai/locale, or legacy webplus/i18n
  userAgent?: string;      // from openai/userAgent
  location?: {
    city?: string;
    region?: string;
    country?: string;
    timezone?: string;
    latitude?: string | number;
    longitude?: string | number;
  };                        // from openai/userLocation
  subject?: string;         // from openai/subject
  conversationId?: string;  // from openai/session
  organizationId?: string;  // from openai/organization
}
```

```typescript
export const localizedGreeting = server.tool(
  { name: "greet", inputSchema: z.object({}) },
  async (_params, ctx) => {
    const caller = ctx.client.user();
    const locale = caller?.locale ?? "en";
    const city = caller?.location?.city;

    return {
      content: [
        {
          type: "text",
          text: city ? `Hello from ${city}! (locale: ${locale})` : `Hello! (locale: ${locale})`,
        },
      ],
    };
  }
);
```

**Do not use this for authentication or authorization.** These hints are client-reported and unverified — for an authenticated identity, use `ctx.auth.user` from OAuth instead (see `references/11-auth/03-ctx-auth-and-user-context.md`).

See `references/16-client-introspection/02-capabilities.md` for detailed usage.

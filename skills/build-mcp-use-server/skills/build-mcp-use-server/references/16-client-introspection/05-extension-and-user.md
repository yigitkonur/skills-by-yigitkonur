# `ctx.client.extension()` and `ctx.client.user()`

Two adjacent surfaces for richer client introspection: raw MCP extension metadata, and per-invocation caller context.

## `ctx.client.extension(id)`

Returns metadata for a named MCP extension, or `undefined` if the client did not declare the extension.

```typescript
const ui = ctx.client.extension("io.modelcontextprotocol/ui");
// e.g. { mimeTypes: ["text/html;profile=mcp-app"] } | undefined
```

| Parameter | Type | Description |
|---|---|---|
| `id` | `string` | Extension identifier (typically reverse-DNS) |

### Common extension IDs

| Extension ID | Purpose | Convenience method |
|---|---|---|
| `io.modelcontextprotocol/ui` | MCP Apps / widgets (SEP-1865) | `ctx.client.supportsApps()` |
| Custom IDs | Vendor-specific extensions | none |

For widgets, prefer `supportsApps()` over reading the extension manually. Use `extension(id)` for vendor-specific metadata or to inspect sub-fields. `ctx.client.user()` is not backed by an extension; it is normalized from per-request `_meta`.

## `ctx.client.user()`

Returns per-invocation caller metadata reported by the client in the request's `_meta`. Returns `undefined` for clients that don't supply recognized user metadata.

```typescript
const caller = ctx.client.user();
if (!caller) return text("Hello! (no caller context)");

const city = caller.location?.city ?? "there";
const greeting = caller.locale?.startsWith("it") ? "Ciao" : "Hello";
return text(`${greeting} from ${city}!`);
```

### `UserContext` fields

| Field | Type | Description |
|---|---|---|
| `subject` | `string \| undefined` | Stable opaque user identifier (`openai/subject`) |
| `conversationId` | `string \| undefined` | Current chat thread ID (`openai/session`) |
| `locale` | `string \| undefined` | BCP-47 locale, e.g. `"it-IT"` (`openai/locale`) |
| `location` | `object \| undefined` | `{ city?, region?, country?, timezone?, latitude?, longitude? }` from `openai/userLocation` |
| `userAgent` | `string \| undefined` | Browser / host user-agent string (`openai/userAgent`) |
| `timezoneOffsetMinutes` | `number \| undefined` | UTC offset in minutes (`timezone_offset_minutes`) |

`location.latitude` and `location.longitude` are strings in the published type declarations.

## Trust boundary — never use for access control

`user()` data is **client-reported and unverified**. A malicious client can fake any field. Use it for personalization (greetings, locale, timezone) but **never** for authorization decisions.

For verified identity, use OAuth (`ctx.auth`) — see `../11-auth/`.

| Use `user()` for | Don't use `user()` for |
|---|---|
| Locale-aware greetings | Authentication |
| Timezone-aware formatting | Authorization |
| City-based defaults | Tenancy isolation |
| Telemetry attribution | Billing / quota enforcement |

## ChatGPT multi-tenant model

ChatGPT establishes a **single MCP session for all users** of a deployed app. The session ID is shared. To distinguish users, use `subject`; to distinguish chats, use `conversationId`.

```typescript
// Session hierarchy in ChatGPT:
// 1 MCP session   — ctx.session.sessionId         (shared across ALL users)
//   N subjects    — ctx.client.user()?.subject    (one per ChatGPT user account)
//     M threads   — ctx.client.user()?.conversationId  (one per chat)

server.tool({ name: "identify", schema: z.object({}) }, async (_a, ctx) => {
  const caller = ctx.client.user();
  return object({
    mcpSession:   ctx.session.sessionId,
    user:         caller?.subject ?? null,
    conversation: caller?.conversationId ?? null,
  });
});
```

### Anti-pattern: using `sessionId` as user ID in ChatGPT

```typescript
// BAD — same sessionId for all ChatGPT users
const userId = ctx.session.sessionId;

// GOOD — one subject per user
const userId = ctx.client.user()?.subject ?? "anonymous";
```

## Locale: `user().locale` vs `useWidget().locale`

| Source | Where it lives | When detected |
|---|---|---|
| `ctx.client.user()?.locale` | Server-side | Session start, from user account |
| `useWidget().locale` | Client-side (widget) | Inside the widget, browser-aware |

Inside a widget, prefer `useWidget().locale` — it's fresher and reflects browser preferences. Outside a widget (plain tool handlers), use `ctx.client.user()?.locale`.

## Personalization example

```typescript
server.tool(
  { name: "greet-user", schema: z.object({}) },
  async (_args, ctx) => {
    const caller = ctx.client.user();
    if (!caller) return text("Hello!");

    const city     = caller.location?.city ?? "there";
    const greeting = caller.locale?.startsWith("fr") ? "Bonjour"
                   : caller.locale?.startsWith("es") ? "Hola"
                   : caller.locale?.startsWith("it") ? "Ciao"
                   : "Hello";

    return text(`${greeting} from ${city}!`);
  }
);
```

## Combining with extension metadata

```typescript
server.tool({ name: "smart", schema: z.object({}) }, async (_a, ctx) => {
  const { name, version } = ctx.client.info();
  const isAppsClient      = ctx.client.supportsApps();
  const ui                = ctx.client.extension("io.modelcontextprotocol/ui");
  const caller            = ctx.client.user();

  return object({
    client:        { name, version },
    capabilities:  { apps: isAppsClient, sampling: ctx.client.can("sampling") },
    uiExtension:   ui,
    user:          caller ? { subject: caller.subject, locale: caller.locale } : null,
  });
});
```

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Using `user()?.subject` for auth | Use OAuth and `ctx.auth` |
| Trusting `user().location.city` blindly | Treat as advisory; client can fake it |
| Crashing on `caller.location.city` (no `?.`) | Use optional chaining everywhere |
| Re-reading `ctx.client.user()` in a hot loop | Cache once at the top of the handler |
| Putting `user().subject` in client-visible logs | Treat as opaque PII — log a hash or partial |

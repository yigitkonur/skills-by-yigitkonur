# Canonical Anchor — `mcp-use/mcp-i18n-adaptive`

Reference repository for client-aware user context and widget host-context adaptation:

**https://github.com/mcp-use/mcp-i18n-adaptive**

## What it demonstrates

| Pattern | Where to look |
|---|---|
| Client name/version via `ctx.client.info()` | `index.ts` (`detect-caller`) |
| Per-invocation user context via `ctx.client.user()` | `index.ts` (`detect-caller`) |
| Widget-side locale/timezone/viewport context via `useWidget()` | `resources/context-display/widget.tsx` |
| Widget props schema | `resources/context-display/types.ts` |
| Repo-level feature statement and run instructions | `README.md` |

This repo does **not** demonstrate `ctx.client.can(...)` or `ctx.client.supportsApps()`; use the package declarations for those APIs.

## Patterns worth copying

### 1. Server-side locale detection

```typescript
const user = ctx.client.user();
const info = ctx.client.info();

return object({
  userId: user?.subject ?? null,
  conversationId: user?.conversationId ?? null,
  locale: user?.locale ?? null,
  location: user?.location ?? null,
  client: {
    name: info?.name ?? "unknown",
    version: info?.version ?? "unknown",
  },
});
```

### 2. Widget viewport adaptation

Widgets read viewport and host context from `useWidget()` and adapt layout. The widget pulls `locale`, `timeZone`, `userAgent`, `safeArea`, `maxWidth`, `maxHeight`, `hostInfo`, `hostCapabilities`, `theme`, and `displayMode`.

### 3. Widget response shape

```typescript
return widget({
  props: {
    greeting: "Hello!",
    timestamp: new Date().toISOString(),
    sampleNumbers: [1234.56, 9876543.21, 0.005],
    sampleDates: [new Date().toISOString()],
  },
  output: text("Context display loaded"),
});
```

### 4. Safe-area aware UI in widgets

The widget reads `safeArea?.insets` from `useWidget()` and renders an inset visualization using those values.

## How to use this anchor

When teaching or implementing client-adaptive behavior:

1. Explain the API surface from `01-overview.md` through `05-extension-and-user.md`.
2. Show the canonical layout from `mcp-i18n-adaptive`.
3. Add `ctx.client.can(...)` and `ctx.client.supportsApps()` checks from the package API when the implementation needs sampling, elicitation, roots, or widgets.

The demo is useful for the shape of a small host-context-aware mcp-use server. Do not copy nonexistent paths or infer capability-gating patterns from it.

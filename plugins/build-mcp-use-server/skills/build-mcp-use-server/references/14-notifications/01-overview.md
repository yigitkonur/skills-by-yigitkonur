# Notifications Overview

Notifications are server-to-client one-way messages with no response. mcp-use exposes a small surface for sending them, plus standard MCP-defined notification types (progress, list_changed, resource updates).

> **Stateful only.** Notifications require a persistent session — SSE or StreamableHTTP transport. They are silently dropped in stateless mode. See `06-when-notifications-fail.md`.

## The surface

| API | Scope | Use when |
|---|---|---|
| `server.sendNotification(method, params)` | All clients | Broadcasting events to every active session |
| `server.sendNotificationToSession(id, method, params)` | One client | Targeting a specific session by ID |
| `ctx.sendNotification(method, params)` | Current client | Notifying only the caller from inside a tool handler |
| `ctx.reportProgress?.(progress, total?, msg?)` | Current client | Reporting progress in a long-running tool when the request has a progress token |
| `server.notifyResourceUpdated(uri)` | Subscribers | A subscribed resource's content changed |
| `server.sendToolsListChanged()` | All clients | Tool list was added/removed dynamically |
| `server.sendResourcesListChanged()` | All clients | Resource list was added/removed dynamically |
| `server.sendPromptsListChanged()` | All clients | Prompt list was added/removed dynamically |
| `server.onRootsChanged(cb)` | Server handler | Receiving root changes from clients |
| `server.listRoots(sessionId)` | Server-initiated request | Asking a client for its current roots |
| `server.getActiveSessions()` | Server | Listing connected session IDs |

## Where each section lives

| Topic | File |
|---|---|
| `server.sendNotification` and custom methods | `02-server-send-notification.md` |
| Progress tokens, `ctx.reportProgress` | `03-progress-tokens.md` |
| `list_changed` events | `04-list-changed-events.md` |
| Roots (client-side state) | `05-roots.md` |
| Stateless mode and detection | `06-when-notifications-fail.md` |
| Reference example repo | `canonical-anchor.md` |

## Notification vs subscription

| | Notification | Subscription |
|---|---|---|
| **Purpose** | Broadcast arbitrary events | Track changes to a specific resource URI |
| **Targeting** | All clients (or one session) | Only clients that subscribed |
| **Protocol** | `notifications/*` (server → client) | `resources/subscribe` (client → server) → `resources/updated` |
| **Use case** | Status updates, custom events | Data sync, document/widget refresh |

Subscriptions are documented under resources — see `../06-resources/`. The sole "notification" surface for subscriptions is `server.notifyResourceUpdated(uri)`, called when the resource's content changes.

## Minimal example

```typescript
import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({ name: "demo", version: "1.0.0" });

server.tool(
  { name: "start-job", description: "Start a job and notify the caller." },
  async (_args, ctx) => {
    await ctx.sendNotification("custom/job-started", {
      jobId: "j_42",
      startedAt: Date.now(),
    });
    return text("Job started.");
  }
);
```

## Naming convention

`sendNotification` accepts any method string; mcp-use does not enforce a prefix. Use `custom/<domain>/<action>` for your application events, and use client-specific prefixes such as `ui/notifications/*` only when that client protocol expects them. Reserve `notifications/*` for MCP protocol methods.

| Pattern | Example | Notes |
|---|---|---|
| `custom/<domain>/<action>` | `custom/billing/invoice-created` | Easy to filter by prefix |
| `custom/<domain>/v2` | `custom/analytics/v2` | Bump suffix when payload shape changes |
| `ui/notifications/<event>` | `ui/notifications/size-changed` | MCP Apps UI bridge convention; do not use for unrelated app events |

## Related

- Sampling auto-progress: `../13-sampling/05-progress-during-sampling.md`
- Per-tool logging: `../15-logging/02-ctx-log.md`
- Resource subscriptions in detail: `../06-resources/`

**Canonical doc:** https://manufact.com/docs/typescript/server/notifications

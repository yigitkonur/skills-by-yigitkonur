# Stateless mode

Stateless mode disables sessions, SSE streams, and features that require remembering a client between calls. Each `POST /mcp` is handled without session tracking.

For the conceptual difference between stateful and stateless, see `../01-concepts/04-stateful-vs-stateless.md`.

## How to enable

| Path | Effect |
|---|---|
| `new MCPServer({ ..., stateless: true })` | Force stateless globally |
| Deno runtime default | Constructor sets stateless when Deno is detected |
| Node.js per-request auto-detection | Requests without `text/event-stream` in `Accept` are handled statelessly |
| Non-Deno serverless / edge | Set `stateless: true` explicitly unless you have durable session and stream storage |

Force only when you want to lock the mode regardless of the client. Otherwise leave `stateless` unset and let auto-detection handle it.

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  stateless: true,  // forces stateless for every request
})
```

## What becomes unavailable

In stateless mode, these features are not supported:

| Feature | Reason | Reference |
|---|---|---|
| Notifications | No SSE channel back to the client | `../14-notifications/` |
| Progress reporting | Same - no channel for `ctx.reportProgress(...)` | `../14-notifications/` |
| Sampling | `ctx.sample(...)` requires a stream | `../13-sampling/` |
| Elicitation | `ctx.elicit(...)` requires a stream | `../12-elicitation/` |
| Resource subscriptions | `resources/subscribe` and `server.notifyResourceUpdated(...)` need session state | `../06-resources/06-subscriptions.md` |
| Streaming tool props | Partial tool-input streaming requires a stream-capable session | `../18-mcp-apps/streaming-tool-props/01-overview.md` |

If your tools call any of the above, do not use stateless mode.

## What still works

| Feature | Status |
|---|---|
| Tools (request/response) | Yes |
| Resources (one-shot read) | Yes |
| Prompts | Yes |
| OAuth | Yes - auth state is per-request |
| Custom HTTP routes | Yes |

## When to choose stateless

| Scenario | Mode |
|---|---|
| Tools-only server, no progress, no notifications | Stateless (simpler) |
| Edge / serverless deploy, no external session store | Stateless (set explicitly unless Deno already defaults it) |
| Need progress reporting, notifications, sampling, elicitation, or subscriptions | Stateful - see `../10-sessions/` |
| Both - some tools need state, others don't | Stateful with state opt-in |

## Stateful on serverless

If you need stateful features on Vercel / Cloudflare Workers / Supabase Edge / Deno Deploy, you must:

1. Use `RedisSessionStore` and `RedisStreamManager` (in-memory state does not survive cold starts or fan-out across instances).
2. Configure the platform for long-lived connections where SSE is required.

See `../10-sessions/` for store options and `05-serverless-handlers.md` for platform notes.

## Forcing stateful

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  stateless: false,  // force stateful for every request
})
```

Forcing stateful on a runtime that defaults to stateless does not remove platform limits. Validate long-lived streams, session storage, and fan-out before relying on stateful MCP features.

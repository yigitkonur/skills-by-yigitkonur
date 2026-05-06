# Stateful vs stateless

Transport (`03-transports-overview.md`) tells you *how* clients reach the server. Statefulness tells you *whether the server remembers them between calls*.

## Stateless

Each request is independent. No session ID, no per-client state, no notifications, no sampling, no elicitation, no resource subscriptions. The server is a pure function of input.

- Default for serverless deployments (Vercel, Cloudflare Workers, Supabase Edge, AWS Lambda).
- Auto-detected by `mcp-use` **only when running under Deno** (per the `MCPServer` constructor docs: `stateless` is "auto-detected for Deno"). Every other serverless runtime — Vercel, Cloudflare Workers, Supabase Edge, AWS Lambda — needs `stateless: true` set explicitly.
- Can be forced via `new MCPServer({ stateless: true })`.

## Stateful

The server tracks each client by session ID. Required for:

- **Notifications** — `server.sendNotification()` and `ctx.reportProgress()` (`14-notifications/`).
- **Resource subscriptions** — `subscribeToResource` / `notifyResourceUpdated` (`06-resources/06`).
- **Sampling** — `ctx.sample()` (`13-sampling/`).
- **Elicitation** — `ctx.elicit()` (`12-elicitation/`).
- **Streaming tool props** — partial-input streaming to widgets (`18-mcp-apps/streaming-tool-props/`).
- **Progress tokens** — long-running tools that emit progress (`14-notifications/03`).

Sessions are persisted in a **session store** (`10-sessions/stores/`): memory (default), filesystem (single-node persistence), or Redis (distributed).

## Picking the mode

| You need | Mode |
|---|---|
| Tools only, fire-and-forget | Stateless |
| Progress, subscriptions, sample, elicit, widgets that stream | Stateful |
| Both — some tools need state, others don't | Stateful (state is opt-in per tool) |
| Serverless deploy with no state needs | Stateless |
| Serverless deploy with state needs | Stateful + Redis store + Redis StreamManager (`10-sessions/04`) |

## Read next

- `10-sessions/01-overview.md`
- `09-transports/04-stateless-mode.md`

**Canonical doc:** https://manufact.com/docs/typescript/server/session-management

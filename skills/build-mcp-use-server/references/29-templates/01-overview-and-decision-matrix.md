# Templates: Overview and Decision Matrix

Six starter scaffolds. Pick by transport target, deployment model, and whether widgets are involved. Every template uses `mcp-use/server` and Zod v4.

## Decision matrix

| If you need... | Use template | Transport | Stateful? | Widgets? |
|---|---|---|---|---|
| Local dev, single tool, fastest start | `02-minimal-stdio.md` | stdio (and HTTP via `mcp-use dev`) | No | No |
| HTTP server with Docker, env config, modular tool registration | `03-production-http.md` | Streamable HTTP | Optional | No |
| Tools that render React widgets in ChatGPT / MCP clients | `04-mcp-apps-widget.md` | Streamable HTTP | Yes (per session) | Yes |
| Edge / serverless deployment (Supabase, Deno Deploy) | `05-serverless-deno.md` | Streamable HTTP (stateless) | No | Optional |
| Add MCP to an existing Express/Fastify app | `06-side-car-existing-app.md` | Streamable HTTP on a separate port | Optional | No |

## When to graduate

- Start with `02-minimal-stdio` when prototyping. The same `index.ts` runs under stdio (Claude Desktop) and HTTP (Inspector) without changes.
- Move to `03-production-http` once you have more than one tool, env-driven config, or a CI/CD target.
- Pick `04-mcp-apps-widget` when a tool's output is better as a UI than as text. Widgets are auto-discovered from `resources/`.
- Pick `05-serverless-deno` for cold-start-friendly deploys. Deno + `npm:` specifiers, no `node_modules` to ship.
- Pick `06-side-car-existing-app` when the host app must keep its current routes and you only want to add MCP.

## Cross-cutting choices

| Concern | See |
|---|---|
| Transport details (stdio vs HTTP, stateful vs stateless) | `../09-transports/` |
| Session and progress notifications | `../10-sessions/`, `../14-notifications/` |
| OAuth provider selection (Auth0 / Supabase / WorkOS) | `../11-auth/` |
| Adding REST routes alongside MCP | `../17-advanced/` (Hono passthrough) |
| Production checklist | `../24-production/` |

## Multi-server gateway

Composing multiple upstream MCP servers behind one endpoint is not a template — it is a workflow. See `../30-workflows/06-multi-server-proxy-gateway.md`.

## Real-world skeletons

For richer references that go beyond scaffolds, route to `../31-canonical-examples/`. Those files point at the official `mcp-use/*` repos that every template here distills from.

**Canonical doc:** [manufact.com/docs/home/templates](https://manufact.com/docs/home/templates)

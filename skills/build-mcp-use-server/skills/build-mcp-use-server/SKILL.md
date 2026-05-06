---
name: build-mcp-use-server
description: Use skill if you are building or extending TypeScript MCP servers with mcp-use — tools, schemas, responses, auth, sessions, transports, MCP Apps widgets, ChatGPT Apps, Inspector, deploy.
---

# Build mcp-use Server

Use this skill for any `mcp-use` server work — tool servers, MCP Apps widgets, OAuth-protected servers, multi-server proxies, ChatGPT Apps, Inspector debugging, deployment. This skill replaces the legacy split between `build-mcp-use-server` and `build-mcp-use-apps-widgets`.

## When to use this skill vs neighbors

- **This skill:** anything you build, extend, or audit using `mcp-use/server` (tools, resources, prompts, MCP Apps widgets, OAuth, sessions, transports, deploy).
- **`build-mcp-use-client`:** building a client app that connects to an MCP server via the `mcp-use` client SDK.
- **`build-mcp-use-agent`:** building an `MCPAgent` that orchestrates multiple MCP servers with an LLM.
- **`build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2`:** building servers with the raw `@modelcontextprotocol/sdk` (no `mcp-use`).

If the user is mixing — e.g. an `mcp-use` server _plus_ an `MCPAgent` client — start here for the server half and route to the agent skill for the client half.

## Core rules

- Import server APIs from `mcp-use/server`. The one common exception is `Logger`, which comes from `mcp-use`.
- Declare `zod` in the project's own dependencies. Do not assume `mcp-use` provides it.
- Use `mcp-use` HTTP, stdio, or serverless patterns. Do not hand-wire raw SDK transports.
- Work in the actual package, fixture, or subdirectory you will change. If the user named a monorepo package or fixture path, scan that path directly.
- Never claim the server is scaffolded, installed, or runnable when the environment is read-only, notes-only, or missing prerequisites you cannot add in this run.

## Workflow

### 1. Lock the target path and execution mode

Identify the concrete path you will inspect and edit.

- If the user named a fixture, package, or subdirectory, use that path instead of the repo root.
- Detect both project state and execution limits before choosing an implementation path:
  - Is there already an `mcp-use` server here?
  - Does it already have MCP Apps widgets, OAuth, sessions, custom transports?
  - Is this an implementation-capable run or a plan-only run?

Treat the run as **plan-only** when any of these are true:

- the environment is read-only or notes-only
- package installation is blocked
- required prerequisites are missing and you cannot add them in this run
- the user asked for analysis or a concrete implementation plan rather than code changes

For plan-only runs, keep gathering enough context to produce an exact implementation plan. Do not fabricate edits, installs, or validation results.

### 2. Scan what already exists

Inspect the target path for:

- `package.json` with `mcp-use`, `zod`, `@mcp-use/cli`, `@mcp-use/react`
- imports from `mcp-use/server` and `mcp-use/react`
- `new MCPServer(...)` and `server.uiResource(...)`
- registered tools, resources, prompts, widget responses
- `resources/` folder with widget `.tsx` files
- existing host entry files: `index.ts`, `src/index.ts`, `src/server.ts`, `src/mcp-server.ts`
- deployment/runtime clues: `.mcp-use/`, Docker, edge-function folders, auth config, env files, health routes
- widget signals: `widgetMetadata`, `useWidget`, `useCallTool`, `McpUseProvider`, `text/html;profile=mcp-app`, `text/html+skybridge`

Summarize:

- target path
- existing server vs no server
- has MCP Apps widgets vs tools-only
- implementation-capable vs plan-only
- likely server shape
- chosen entry file

### 3. Choose the right branch

#### Branch A — Existing `mcp-use` server

Do not rebuild from scratch. Audit and improve the live implementation in this order:

1. **Tools and schemas** → `references/04-tools/`
2. **Responses** → `references/05-responses/`
3. **Resources and prompts** → `references/06-resources/` + `references/07-prompts/`
4. **Server config and transports** → `references/08-server-config/` + `references/09-transports/`
5. **Sessions** → `references/10-sessions/` + `references/10-sessions/stores/`
6. **Auth** → `references/11-auth/` + `references/11-auth/providers/`
7. **Advanced primitives** (elicit/sample/notify/log/client-introspection) → `references/12-elicitation/` through `references/16-client-introspection/`
8. **Proxy / gateway** → `references/17-advanced/`
9. **MCP Apps widgets** → `references/18-mcp-apps/` + sub-clusters
10. **Production reliability** → `references/24-production/` + `references/26-anti-patterns/`
11. **Deploy** → `references/25-deploy/` + `references/25-deploy/platforms/`

Then either implement the highest-value fixes, or — if plan-only — produce a prioritized change plan with exact files, commands, and validation steps.

#### Branch B — No `mcp-use` server, repo gives enough context

Infer the server from the existing code or spec.

Common signals:

- REST or Hono/Express/Fastify endpoints that should become MCP tools
- CLI commands that map naturally to tools
- data sources that should become resources
- a README, issue, or fixture that clearly defines the behavior
- a frontend that clearly wants a widget UI → MCP Apps branch

Choose the entrypoint deliberately:

- scaffolded `create-mcp-use-app` project → keep root `index.ts` (`references/02-setup/02-scaffold-with-create-mcp-use-app.md`)
- brand-new manual server → default to `src/server.ts` (`references/02-setup/05-manual-http-server.md`)
- existing app already using `src/index.ts` or another host entry → keep the host entry and add `src/mcp-server.ts` (`references/02-setup/06-add-to-existing-app.md`)
- widget-driven application → `references/02-setup/03-template-flags.md` mcp-apps template + `references/18-mcp-apps/`

Use canonical setup before writing code:

- `references/02-setup/01-prerequisites.md`
- `references/02-setup/02-scaffold-with-create-mcp-use-app.md`
- `references/02-setup/03-template-flags.md`
- `references/29-templates/` for full layouts

#### Branch C — Underspecified

Ask only the missing questions needed to proceed. Skip anything the user or repo already answered.

Prioritize:

- what data, service, or UI the server exposes
- transport/runtime target (stdio / streamable-http / serverless)
- auth requirements (none / DCR / OAuth proxy)
- tools vs resources vs prompts
- MCP Apps widget vs tools-only
- deployment target
- whether sampling, elicitation, or notifications are required

Ask one question at a time unless the user clearly wants a batch questionnaire.

### 4. Preflight setup

Use `references/02-setup/01-prerequisites.md` as the canonical setup matrix. Make these explicit instead of assuming them:

- Node 18+ available, Node 22 LTS preferred when matching current examples
- `package.json` uses `"type": "module"`
- `mcp-use` and `zod` installed in dependencies
- `@mcp-use/cli` present for CLI/HMR workflows unless the scaffold included it
- `@mcp-use/react` present if building MCP Apps widgets
- chosen entry file matches the project type

If prerequisites are missing and you cannot add them, switch to plan-only output.

### 5. Build or extend

Default sequence:

1. choose entry file and runtime shape (`references/02-setup/`)
2. create or refine `MCPServer` config (`references/08-server-config/`)
3. register tools with precise Zod schemas (`references/04-tools/`)
4. add resources or prompts only when they improve the interface (`references/06-resources/`, `references/07-prompts/`)
5. add advanced features only when needed: auth (`references/11-auth/`), sessions (`references/10-sessions/`), notifications (`references/14-notifications/`), elicit/sample (`references/12-elicitation/`, `references/13-sampling/`), MCP Apps widgets (`references/18-mcp-apps/`), proxy (`references/17-advanced/`)
6. add health routes, deliberate logging (`references/15-logging/`), graceful shutdown (`references/24-production/01-graceful-shutdown.md`)

### 6. Validate honestly

For implementation-capable runs, validate with the smallest relevant set:

- `mcp-use dev` and/or `mcp-use start` (`references/03-cli/`)
- MCP Inspector — full surface area at `references/20-inspector/`
- curl initialize → list → call (`references/22-validate/02-curl-handshake.md`)
- type generation: `mcp-use generate-types` (`references/03-cli/07-mcp-use-generate-types.md`)
- build/deploy preflight when relevant (`references/25-deploy/02-pre-deploy-checklist.md`)
- widget-specific surfaces: protocol toggle, CSP mode, device panels (`references/20-inspector/11-protocol-toggle-and-csp-mode.md`, `references/20-inspector/12-device-and-locale-panels.md`)

For plan-only runs, provide:

- exact entry file(s)
- exact install commands
- exact scripts or config changes
- exact tools/resources/prompts/widgets to add
- exact validation commands to run later

## Decision rules

- Prefer improving an existing server over replacing it.
- Keep the host app's entrypoint when adding MCP to an existing app; use `src/mcp-server.ts` unless there is a strong reason not to.
- Use `text()`, `object()`, `error()`, `mix()`, `widget()`, and the other helpers instead of hand-built MCP payloads.
- Default to a concise, complete `content` response for broad conversational compatibility. Add `structuredContent` only when the tool has an `outputSchema`, typed/programmatic consumers, Code Mode, widget props, or another real downstream parser requirement.
- If a tool returns both `content` and `structuredContent`, keep them semantically equivalent and put every essential result in both surfaces.
- Use `_meta` only for private, large, or UI-only data. Treat `structuredContent` as potentially model-visible.
- Use `error()` for expected failures and `throw` for truly unexpected failures.
- Treat notifications as stateful-only unless you have explicitly verified the transport model supports them.
- Guard `ctx.elicit()` with `ctx.client.can("elicitation")`.
- Guard `ctx.sample()` with `ctx.client.can("sampling")`.
- Guard widget-only behavior with `ctx.client.supportsApps()`.
- For MCP Apps widgets: `tool.widget.name` must match `resources/<name>/widget.tsx`. Always provide a text `message` fallback. Treat widget `props` as model-visible; put private data in `metadata` / `_meta`.
- Wrap the widget root in `McpUseProvider`. Use `useCallTool()`, never raw `fetch()`.
- Declare CSP domains in `widgetMetadata.metadata.csp`. Use `Image` for public assets.
- Prefer `type: "mcpApps"` on `server.uiResource()` for dual-protocol (ChatGPT + MCP Apps) support; `type: "appsSdk"` is deprecated.
- For deployed widget builds, set `baseUrl` or `MCP_URL` so widget asset URLs resolve correctly.

## Guardrails

- Never import server primitives from `@modelcontextprotocol/sdk` directly.
- Never omit `zod` from the project's own dependencies.
- Never use `z.any()` or `z.unknown()` when a concrete schema is possible.
- Never leave schema fields undocumented; use `.describe()` on every field the model must fill.
- Never fall back to a repo-wide scan if the user named a narrower target path.
- Never claim success in a blocked environment.
- Never put secrets in source, logs, or widget state.
- Never skip `allowedOrigins` and CORS decisions for public HTTP servers.
- Never put the primary answer only in one result surface when returning both `content` and `structuredContent`; mirror the essential fields.
- Never access `window.openai` directly from a widget — use the `useWidget` / `useCallTool` hooks.
- Never delegate widget rendering decisions; always handle the `isPending` state explicitly.
- Never embed an `mcp-use` server as middleware inside another framework's app — extend the MCP server's own routes (`references/08-server-config/05-middleware-and-custom-routes.md`) or run it side-by-side (`references/02-setup/06-add-to-existing-app.md`).
- Never skip running `mcp-use generate-types` after schema changes if the project consumes generated types.

## Output contract

Unless the user wants another format, report work in this order:

1. target path and scan summary
2. chosen branch and entrypoint decision
3. implementation or exact plan
4. validation results or explicit blocker
5. key reference files used (cluster paths, not individual files)

## Reference routing — by cluster

Each cluster has numbered files; read in numeric order or jump to the topic you need. Files are ~50–200 lines each, one concept per file.

### Foundations

- **`01-concepts/`** — what mcp-use is, server vs client vs agent, transport overview, stateful vs stateless, MCP Apps vs widgets terminology, this skill vs neighbors
- **`02-setup/`** — prerequisites, scaffold, manual stdio/http server, side-car, package scripts, tsconfig, env vars
- **`03-cli/`** — every CLI command (one file per command), flags, `mcp-use org`, device-flow login, `MCP_DEBUG_LEVEL`, env vars

### Core primitives

- **`04-tools/`** — tool registration, Zod schemas (single source), `.describe()`, annotations, `ctx`, validation pipeline · canonical: `mcp-use/mcp-recipe-finder`
- **`05-responses/`** — decision table + every helper · `widget()` lives in `18-mcp-apps/server-surface/01` · canonical: `mcp-use/mcp-media-mixer`
- **`06-resources/`** — static, templates, binary/image, URI conventions, subscriptions · canonical: `mcp-use/mcp-resource-watcher`
- **`07-prompts/`** — static, templates, `completable()` (single home), prompt engineering

### Server runtime

- **`08-server-config/`** — `MCPServer` constructor, network, CORS + `allowedOrigins` (single source), DNS rebinding, middleware/custom routes, CSP (non-widget), shutdown
- **`09-transports/`** — overview, stdio, streamable-http, stateless mode, serverless handlers, SSE alias
- **`10-sessions/`** — lifecycle, stream manager, distributed Redis, retention, multi-tenant · `stores/`: memory / filesystem / redis / custom
- **`11-auth/`** — DCR vs proxy, `ctx.auth`, permission guards, browser flow, refresh, scopes, debug · `providers/`: auth0 / better-auth / workos / keycloak / supabase / oauth-proxy / custom

### Advanced protocol

- **`12-elicitation/`** — `ctx.elicit()`: form mode, URL mode, multi-step, anti-patterns
- **`13-sampling/`** — `ctx.sample()`: string vs extended API, model preferences, callbacks, progress
- **`14-notifications/`** — `server.sendNotification()`, progress tokens, list-changed, roots, when-it-fails · canonical: `mcp-use/mcp-progress-demo`
- **`15-logging/`** — `ctx.log`, server `Logger`, `MCP_DEBUG_LEVEL`, Winston migration
- **`16-client-introspection/`** — single home for `ctx.client.*` (info, can, supportsApps, extension, user) · canonical: `mcp-use/mcp-i18n-adaptive`
- **`17-advanced/`** — `server.proxy()`, gateway composition, session-based proxy, mcp-use vs raw SDK · canonical: `mcp-use/mcp-multi-server-hub`

### MCP Apps widgets (the merged cluster)

- **`18-mcp-apps/`** — what MCP Apps are, MCP Apps vs ChatGPT Apps SDK, vocabulary, when to use vs tools-only, host capability detection
- **`18-mcp-apps/server-surface/`** — `widget()`, `server.uiResource()`, tool `widget` config, `baseUrl` and asset serving, CSP metadata, `widgetMetadata` export, `resources/` folder conventions
- **`18-mcp-apps/widget-react/`** — `McpUseProvider`, `MCPClientProvider`, `useWidget`, `useCallTool`, `Image`, `ErrorBoundary`, `ThemeProvider`, `WidgetControls`, state persistence, display modes, host context, follow-up messages, `openExternal`, `notifyIntrinsicHeight`
- **`18-mcp-apps/streaming-tool-props/`** — three-phase render, state machine, fallback, server-side no-setup · canonical: `mcp-use/mcp-chart-builder`
- **`18-mcp-apps/chatgpt-apps/`** — protocol overview, `window.openai` API, skybridge MIME, CSP format diffs, dual-protocol, `appsSdk` deprecation, runtime detection
- **`18-mcp-apps/widget-recipes/`** — 8 patterns: weather dashboard, todo list, form builder, live data, image gallery, timer, markdown editor, chatbot
- **`18-mcp-apps/widget-anti-patterns/`** — secrets in state, missing `isPending` guard, direct `window.openai`, missing CSP, state mutations, `fetch` instead of `callTool`
- canonical (foundational): `mcp-use/mcp-widget-gallery`

### Integrations and tooling

- **`19-nextjs-drop-in/`** — `--mcp-dir` flag, shared aliases + Tailwind, `server-only` shimming, deploying as a Vercel route
- **`20-inspector/`** — full mirror of canonical 13 inspector pages: overview, CLI, connection settings, URL params, shortcuts, command palette, RPC logging, integration, debugging ChatGPT Apps, self-hosting, protocol toggle + CSP mode, device/locale panels, changelog
- **`21-tunneling/`** — when to tunnel, debugging remote clients

### Validate, debug, ship

- **`22-validate/`** — Inspector walkthrough, curl handshake, Claude Desktop, VSCode/Cursor, Add-to-Client, unit testing
- **`23-debug/`** — `MCP_DEBUG_LEVEL`, observability/Langfuse, perf profiling, transport debugging, load testing, widget debugging
- **`24-production/`** — graceful shutdown, env config, lazy init, error strategy, health routes, rate limiting, streaming large results, feature flags
- **`25-deploy/`** — decision matrix, pre-deploy checklist, Docker, Claude Desktop distribution, `mcp-use org` · `platforms/`: mcp-use Cloud, Supabase, Google Cloud Run, Vercel, Fly, Cloudflare Workers, Deno Deploy
- **`26-anti-patterns/`** — tight do-X-not-Y catalog: SDK misuse, tool design, schemas, responses, security/CORS
- **`27-troubleshooting/`** — error catalog (greppable), quick diagnostic table, OAuth/Supabase issues, widget rendering, CSP violations, decision tree
- **`28-migration/`** — from `@modelcontextprotocol/sdk`, mcp-use v1→v2, SSE→Streamable HTTP, `appsSdk`→`mcpApps`, DCR→proxy mode shift

### Templates, workflows, canonical examples

- **`29-templates/`** — copyable scaffolds: minimal stdio, production HTTP, MCP Apps widget, serverless Deno, side-car
- **`30-workflows/`** — 15 end-to-end recipes covering common shapes (Vercel tool server, Redis streaming, OAuth+Supabase, Postgres, GitHub wrapper, multi-server proxy, elicit+sample, ticker, webhook, Next.js add-on, plus 5 widget workflows modeled on canonical repos)
- **`31-canonical-examples/`** — one file per official `mcp-use/*` repo (12 repos), what each demonstrates, load-bearing files, which clusters reference it. Read `00-how-to-use-this-cluster.md` first.

## Navigation note

The cluster routing above is the canonical navigation surface. Use `references/00-reference-index.md` or `rg --files references` when you need an exact filename; the remaining inventory is covered by `references/**/*.md`.

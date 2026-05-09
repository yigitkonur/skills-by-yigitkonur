---
name: build-mcp-use-server
description: Use skill if you are building or extending TypeScript MCP servers with mcp-use — tools, schemas, responses, auth, sessions, transports, MCP Apps widgets, ChatGPT Apps, Inspector, deploy.
---

# Build mcp-use Server

Use this skill for `mcp-use/server` mechanics: tool servers, resources, prompts, MCP Apps widgets, OAuth-protected servers, sessions, transports, Inspector debugging, and deployment. Start from the trigger boundary and intent table, not the numbered reference folders.

## Trigger boundary

Use this skill for work that imports from `mcp-use/server` or needs the server-side `mcp-use` API surface:

- `MCPServer`, `server.tool`, `server.resource`, `server.prompt`, `server.uiResource`
- response helpers such as `text()`, `object()`, `mix()`, `error()`, `widget()`
- server auth, session stores, transports, Inspector, deploy, and MCP Apps widget registration

Do **not** use this skill as the primary guide for:

- custom apps using `MCPClient` to connect to servers — use `build-mcp-use-client`
- `MCPAgent` LLM orchestration over one or more servers — use `build-mcp-use-agent`
- raw official SDK servers without `mcp-use` — use `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2`
- layer placement, import direction, composition root design, config seams, or handler/presenter placement — use `apply-clean-mcp-architecture` first, then return here for mechanics

Numbered folders under `references/` are local organization, not a required `01` to `31` reading sequence. Pick the intent route first. Inside a chosen cluster, read numeric files in order only when the files form a sequence.

## Coordinate with neighboring skills

- **`apply-clean-mcp-architecture` owns structure:** where files live, import direction, layer boundaries, composition root, config seam, handler/presenter placement. Its detailed contract is in its `coordinate-with-build-mcp-use-server.md` reference.
- **This skill owns mechanics:** exact `mcp-use/server` APIs, Zod schemas, response helpers, auth/session/transport config, widget CSP, Inspector usage, deploy mechanics.
- **Blended request:** load `apply-clean-mcp-architecture` first for placement, then this skill for API mechanics.

Examples:

| Request | Route |
|---|---|
| Add a new tool to a clean-layered repo | `apply-clean-mcp-architecture` for `handlers/`, use case, presenter, and bootstrap placement; then this skill for `server.tool`, Zod schema, response helper, and validation. |
| Add OAuth to an existing clean architecture server | `apply-clean-mcp-architecture` for `infrastructure/auth` and config wiring; then this skill for DCR vs proxy, provider config, `ctx.auth`, and OAuth debugging. |
| Decide whether a widget belongs in the server | `apply-clean-mcp-architecture` for placement and ownership; then this skill for MCP Apps vs tools-only, `server.uiResource`, `widget()`, and CSP. |
| Debug wire-level handshake failures | This skill first: `references/27-troubleshooting/06-decision-tree.md`, `references/22-validate/02-curl-handshake.md`, and Inspector. Architecture is secondary unless the fix touches layers. |

Positive routing:

- **`build-mcp-use-client`:** custom apps that connect to MCP servers with `MCPClient`, list/call tools, read resources, handle callbacks, or mount client-side React providers.
- **`build-mcp-use-agent`:** `MCPAgent` LLM orchestration over one or more MCP servers.
- **`build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2`:** raw official SDK servers, especially strict stdio or direct transport control.
- **`apply-clean-mcp-architecture`:** TypeScript MCP server layer placement and clean architecture.
- **`test-by-mcpc-cli`:** live CLI verification after a server is running.
- **`optimize-agent-ergonomics`:** broader agent-facing MCP/CLI surface design or audit before choosing a framework, or after a server exists and needs ergonomics review.

## Detect intent

| Intent | Start here | Then read |
|---|---|---|
| Extend an existing `mcp-use` server | `scripts/audit-server-readiness.sh.md` | `references/04-tools/01-overview.md`, `references/05-responses/01-overview-decision-table.md`, `references/08-server-config/01-mcp-server-constructor.md`, `references/22-validate/` |
| Greenfield HTTP tool server | `scripts/scaffold-mcp-use-server.sh.md` or `references/02-setup/05-manual-http-server.md` | `references/04-tools/01-overview.md`, `references/05-responses/01-overview-decision-table.md`, `references/22-validate/02-curl-handshake.md` |
| Strict stdio requirement | `references/02-setup/04-manual-stdio-server.md` | `references/09-transports/02-stdio.md`, then route to `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2` |
| MCP Apps / ChatGPT widget | `references/30-workflows/11-streaming-chart-widget.md` or `references/30-workflows/12-progress-and-elicit-widget.md` | `references/18-mcp-apps/01-what-are-mcp-apps.md`, `references/18-mcp-apps/server-surface/01-widget-helper.md`, `references/18-mcp-apps/widget-react/01-mcpuseprovider.md`, `references/20-inspector/11-protocol-toggle-and-csp-mode.md` |
| Next.js drop-in | `references/30-workflows/10-add-mcp-to-existing-nextjs-app.md` | `references/19-nextjs-drop-in/01-overview.md`, `references/19-nextjs-drop-in/03-shared-aliases-and-tailwind.md`, `references/19-nextjs-drop-in/04-server-only-shimming.md`, `references/19-nextjs-drop-in/05-deploying-as-vercel-route.md` |
| Auth / OAuth | `references/11-auth/01-overview-decision-matrix.md` | `references/11-auth/02-dcr-vs-proxy-mode.md`, `references/11-auth/03-ctx-auth-object.md`, `references/11-auth/08-debugging-checklist.md`, `references/27-troubleshooting/03-oauth-and-supabase-issues.md` |
| Sessions, streaming, notifications, sampling, elicitation | `references/30-workflows/02-stateful-redis-streaming-server.md` | `references/10-sessions/01-overview.md`, `references/14-notifications/01-overview.md`, `references/13-sampling/01-overview.md`, `references/12-elicitation/01-overview.md` |
| Deploy or production hardening | `references/25-deploy/01-decision-matrix.md` | `references/25-deploy/02-pre-deploy-checklist.md`, `references/24-production/05-health-routes.md`, `references/24-production/01-graceful-shutdown.md`, relevant `references/25-deploy/platforms/*.md` |
| Troubleshoot a concrete error | `references/00-symptom-index.md` | `references/27-troubleshooting/06-decision-tree.md`, `references/27-troubleshooting/01-error-catalog.md`, then the exact cluster named by the symptom |
| Migrate from raw SDK or older `mcp-use` | `references/28-migration/01-from-modelcontextprotocol-sdk.md` or `references/28-migration/02-mcp-use-v1-to-v2.md` | `references/17-advanced/03-mcp-use-vs-official-sdk.md`, `references/09-transports/01-overview.md`, affected setup/auth/widget references |

Use `references/00-reference-index.md` only when the intent table is not specific enough or you need an exact filename.

## Core rules

- Import server APIs from `mcp-use/server`. The common exception is `Logger`, which comes from `mcp-use`.
- Declare `zod` in the project's own dependencies. Do not rely on `mcp-use` to provide it.
- Use `mcp-use` HTTP, Fetch/serverless, session, auth, and widget patterns. Do not hand-wire raw SDK transports.
- Treat strict stdio as a raw-SDK requirement, not an `mcp-use/server` branch.
- Work in the actual package, fixture, or subdirectory the user named. Do not widen to a repo-wide scan unless the target path is unknown.
- Prefer improving an existing server over replacing it.
- Never claim the server is scaffolded, installed, runnable, or verified when the environment is read-only, plan-only, or missing prerequisites you cannot add.
- For version-sensitive claims, read `references/00-version-drift.md` before editing examples, command docs, or migration guidance.

## Workflow

### 1. Lock target path and execution mode

Identify the concrete path to inspect and edit. If the user named a fixture, package, or subdirectory, use that path.

Treat the run as **plan-only** when the environment is read-only, package installation is blocked, required prerequisites are missing and cannot be added, or the user asked for analysis rather than code. Plan-only output must include exact files, install commands, implementation steps, and validation commands. It must not claim runtime validation.

### 2. Scan what already exists

Inspect the target path for:

- `package.json` with `mcp-use`, `zod`, `@mcp-use/cli`, `@mcp-use/react`
- imports from `mcp-use/server` and `mcp-use/react`
- `new MCPServer(...)`, `server.tool`, `server.resource`, `server.prompt`, `server.uiResource`
- widget signals: `resources/`, `widgetMetadata`, `useWidget`, `useCallTool`, `McpUseProvider`, `text/html;profile=mcp-app`, `text/html+skybridge`
- runtime signals: `.mcp-use/`, Docker, edge-function folders, auth config, session stores, health routes

For existing servers, run `scripts/audit-server-readiness.sh` when filesystem access is available. Its usage is documented in `scripts/audit-server-readiness.sh.md`.

Summarize target path, existing server vs no server, tools-only vs widgets, implementation-capable vs plan-only, likely server shape, and chosen entry file.

### 3. Choose the branch

**Existing server:** do not rebuild. Follow the intent row that matches the requested change, then audit nearby mechanics: tools/schemas, responses, resources/prompts, config/transports, sessions, auth, widgets, production, deploy.

**No server but enough repo context:** infer the server from REST endpoints, CLI commands, data sources, README/issue text, or a frontend that clearly needs a widget. Choose entrypoint deliberately:

- scaffolded project -> keep root `index.ts`
- manual HTTP server -> default `src/server.ts`
- empty greenfield HTTP package -> `scripts/scaffold-mcp-use-server.sh` is allowed
- existing app owns `src/index.ts` or `src/server.ts` -> add `src/mcp-server.ts`
- Next.js drop-in -> follow `references/19-nextjs-drop-in/`
- strict stdio -> route out to raw SDK skills

**Underspecified:** ask only for missing information that blocks implementation: exposed data/service/UI, transport/runtime, auth, tools/resources/prompts, widget vs tools-only, deploy target, and advanced primitives.

### 4. Preflight setup

Use `references/02-setup/01-prerequisites.md` as the setup matrix:

- Node 18+ available; Node 22 LTS preferred for current examples.
- `package.json` uses `"type": "module"`.
- `mcp-use` and `zod` are dependencies.
- `@mcp-use/cli` is present for CLI/HMR/build/start/deploy/typegen workflows unless scaffolded.
- `@mcp-use/react` is present only when building widgets.
- chosen entry file matches project shape.

Run `scripts/check-mcp-use-version.sh` when a package exists and dependency drift matters. Its usage is documented in `scripts/check-mcp-use-version.sh.md`.

If prerequisites are missing and cannot be added, switch to plan-only output.

### 5. Build or extend

Default sequence:

1. choose entry file and runtime shape (`references/02-setup/`)
2. create or refine `MCPServer` config (`references/08-server-config/`)
3. register tools with precise Zod schemas (`references/04-tools/`)
4. add resources or prompts only when they improve the interface (`references/06-resources/`, `references/07-prompts/`)
5. add auth, sessions, notifications, sampling, elicitation, widgets, or proxy only when the intent requires them
6. add health/readiness, logging, graceful shutdown, and deploy hardening when shipping beyond local dev

### 6. Validate

Pick the smallest validation set that proves the changed behavior. Do not imply a higher rung than observed.

- read-only scan: files inspected, no runtime exercised
- typecheck/build: `npm run typecheck`, `npm run build`, or project equivalent
- `mcp-use dev` / `mcp-use start`: server starts locally
- Inspector: tools/resources/prompts/widgets observed and callable
- curl handshake: initialize, tools/list, tools/call on `/mcp`
- `test-by-mcpc-cli`: named `mcpc` session connected and commands run
- deployed endpoint: health/readiness plus live MCP call against the deployed URL

For widgets, verify the text fallback and, when possible, Inspector CSP mode. For deploys, verify `references/25-deploy/02-pre-deploy-checklist.md`, `/health`, and `/ready`.

## Decision rules

- Use response helpers instead of hand-built MCP payloads.
- Default to concise complete `content`. Add `structuredContent` when there is an `outputSchema`, a typed/programmatic consumer, Code Mode, widget props, or another real parser.
- Keep `content` and `structuredContent` semantically equivalent when returning both.
- Put private, bulky, or UI-only data in `_meta`; treat ordinary `structuredContent` as potentially model-visible.
- Use `error()` for expected failures and `throw` for unexpected failures.
- Guard `ctx.elicit()` with `ctx.client.can("elicitation")`.
- Guard `ctx.sample()` with `ctx.client.can("sampling")`.
- Guard widget-only behavior with `ctx.client.supportsApps()`.
- For MCP Apps widgets, `tool.widget.name` must match `resources/<name>/widget.tsx`; always provide a text fallback.
- Wrap widget roots in `McpUseProvider`. Use `useCallTool()`, not raw `fetch()`, for MCP tool calls from widgets.
- Declare CSP domains in `widgetMetadata.metadata.csp`.
- Prefer `type: "mcpApps"` on `server.uiResource()` for dual-protocol support; `type: "appsSdk"` is deprecated.

## Guardrails

- Never import server primitives from `@modelcontextprotocol/sdk` directly.
- Never omit `zod` from the project's own dependencies.
- Never use `z.any()` or `z.unknown()` when a concrete schema is possible.
- Never leave schema fields undocumented; use `.describe()` on model-filled fields.
- Never put secrets in source, logs, widget props, widget state, or model-visible structured content.
- Never skip `allowedOrigins` and CORS decisions for public HTTP servers.
- Never access `window.openai` directly from a widget; use `useWidget` / `useCallTool`.
- Never embed an `mcp-use` server as middleware inside another framework's app. Extend the MCP server's own routes or run it side-by-side.
- Never skip `mcp-use generate-types` after schema changes if the project consumes generated widget types.

## Validate honestly

Report the exact rung reached:

| Rung | Evidence |
|---|---|
| Read-only scan | Files and references inspected; no command ran against code. |
| Static validation | Typecheck, lint, build, or generated types passed. |
| Local runtime | `mcp-use dev` or `mcp-use start` ran and exposed `/mcp`. |
| Inspector | Inspector connected; relevant surface observed or called. |
| curl handshake | `initialize`, `tools/list`, and at least one relevant `tools/call` succeeded. |
| `mcpc` live test | `test-by-mcpc-cli` session name and commands are reported. |
| Deployed endpoint | health/readiness and live MCP operation verified against public URL. |

If using `test-by-mcpc-cli`, name the session and list the exact commands. For plan-only runs, mark runtime validation blocked and provide exact commands to run later.

## Output contract

Unless the user asks for another format, report:

1. target path and scan summary
2. chosen branch and entrypoint decision
3. implementation or exact plan
4. validation rung reached, commands run, and blockers
5. if widgets changed: text fallback and CSP-mode verification state
6. if deploy/production changed: health/readiness and pre-deploy checklist state
7. key references used, with exact paths for the route actually followed

## Reference routing

Start with intent or symptoms; use inventory only as fallback.

- **Symptom index:** `references/00-symptom-index.md`
- **Version drift policy:** `references/00-version-drift.md`
- **Full inventory:** `references/00-reference-index.md`
- **Bundled scripts:** `scripts/check-mcp-use-version.sh.md`, `scripts/audit-server-readiness.sh.md`, `scripts/scaffold-mcp-use-server.sh.md`
- **Foundations:** `references/01-concepts/*.md`
- **Setup:** `references/02-setup/*.md`
- **CLI:** `references/03-cli/*.md`
- **Tools:** `references/04-tools/*.md`
- **Responses:** `references/05-responses/*.md`
- **Resources:** `references/06-resources/*.md`
- **Prompts:** `references/07-prompts/*.md`
- **Server config:** `references/08-server-config/*.md`
- **Transports:** `references/09-transports/*.md`
- **Sessions:** `references/10-sessions/*.md`, `references/10-sessions/stores/*.md`
- **Auth:** `references/11-auth/*.md`, `references/11-auth/providers/*.md`
- **Advanced protocol:** `references/12-elicitation/*.md`, `references/13-sampling/*.md`, `references/14-notifications/*.md`, `references/15-logging/*.md`, `references/16-client-introspection/*.md`, `references/17-advanced/*.md`
- **MCP Apps widgets:** `references/18-mcp-apps/*.md`, `references/18-mcp-apps/server-surface/*.md`, `references/18-mcp-apps/widget-react/*.md`, `references/18-mcp-apps/streaming-tool-props/*.md`, `references/18-mcp-apps/chatgpt-apps/*.md`, `references/18-mcp-apps/widget-recipes/*.md`, `references/18-mcp-apps/widget-anti-patterns/*.md`
- **Next.js and Inspector:** `references/19-nextjs-drop-in/*.md`, `references/20-inspector/*.md`
- **Remote debugging:** `references/21-tunneling/*.md`
- **Validate/debug:** `references/22-validate/*.md`, `references/23-debug/*.md`, `references/27-troubleshooting/*.md`
- **Production/deploy:** `references/24-production/*.md`, `references/25-deploy/*.md`, `references/25-deploy/platforms/*.md`
- **Anti-patterns and migration:** `references/26-anti-patterns/*.md`, `references/28-migration/*.md`
- **Templates/workflows/examples:** `references/29-templates/*.md`, `references/30-workflows/*.md`, `references/31-canonical-examples/*.md`

Migration note: legacy references to `build-mcp-use-apps-widgets` point to content now housed in `references/18-mcp-apps/`. Do not route new work to that legacy name.

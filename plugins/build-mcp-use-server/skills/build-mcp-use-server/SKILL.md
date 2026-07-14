---
name: build-mcp-use-server
description: "Use if building TypeScript MCP servers with mcp-use/server — server.tool, ctx.auth, transports."
---

# Build mcp-use Server

Server-side mechanics for `mcp-use/server` TypeScript MCP servers. This skill owns API surface; sister skills own structure, clients, agents, and raw SDK.

## When to use this skill

Trigger when the target code or request involves any of these:

- *Imports from `mcp-use/server` (`MCPServer`, `text`, `object`, `mix`, `error`, `widget`, `Logger`).*
- *Defining or refining `server.tool()`, `server.resource()`, `server.prompt()`, `server.uiResource()` with Zod schemas.*
- *Server-side `ctx` work — `ctx.auth`, `ctx.elicit()`, `ctx.sample()`, `ctx.notify()`, `ctx.client.can()`, `ctx.client.supportsApps()`.*
- *Configuring transports (Streamable HTTP, stateless, stdio), session stores, OAuth (DCR or proxy), CORS, allowedOrigins, DNS rebinding.*
- *MCP Apps / ChatGPT Apps widgets — `widgetMetadata`, `text/html;profile=mcp-app`, `text/html+skybridge`, `McpUseProvider`, `useCallTool`, `useWidget`, CSP.*
- *Running `mcp-use dev`, `mcp-use build`, `mcp-use start`, `mcp-use deploy`, `mcp-use generate-types`, or debugging via Inspector / curl handshake on `/mcp`.*
- *Hardening for production: health/readiness routes, graceful shutdown, rate limits, deploy to mcp-use Cloud, Vercel, Cloud Run, Fly, Cloudflare Workers, Deno Deploy, Supabase.*
- *Migrating from raw `@modelcontextprotocol/sdk` server code, `mcp-use` v1, or `appsSdk` widgets to current `mcp-use/server`.*

Do **not** use this skill when:

- *The code imports `MCPClient`, `MCPSession`, `mcp-use/browser`, or `mcp-use/react` for app-side use — route to `build-mcp-use-client`.*
- *The work is `MCPAgent` LLM orchestration over MCP tools — route to `build-mcp-use-agent`.*
- *The user wants raw `@modelcontextprotocol/sdk` server primitives or strict stdio without `mcp-use` — route to `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2`.*
- *The question is layer placement, import direction, composition root, or handler/use-case structure — route to `build-clean-mcp-architecture` first, then return for mechanics.*

## Coordinate with neighboring skills

| Skill | Owns | Handoff |
|---|---|---|
| `build-clean-mcp-architecture` | Folder layout, import direction, layer boundaries, composition root, config seam, handler/presenter placement. | Read first for placement; this skill second for `server.tool` and response helpers. See `references/00-clean-architecture-coordination.md`. |
| `build-mcp-use-client` | `MCPClient`, `MCPSession`, browser/react client mounting, code mode. | Hand off as soon as the target code stops importing `mcp-use/server`. |
| `build-mcp-use-agent` | `MCPAgent` orchestration where an LLM picks tools. | Hand off when the work is agent loop, not server mechanics. |
| `build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2` | Raw official SDK servers, stdio-only constraints, low-level transports. | Hand off if the user explicitly forbids `mcp-use` or needs raw SDK primitives. |
| `test-by-mcpc-cli` | Live `mcpc` session verification once a server runs. | Use after this skill produces a running server. |

Numbered folders under `references/` are local organization. Pick the intent route first; read numbered files in sequence only inside one cluster when the order matters.

## Detect intent

| Intent | Start here | Then read |
|---|---|---|
| Extend an existing `mcp-use` server | `scripts/audit-server-readiness.sh.md` | `references/04-tools/01-overview.md`, `references/05-responses/01-overview-decision-table.md`, `references/08-server-config/01-mcp-server-constructor.md`, `references/22-validate/01-mcp-inspector-walkthrough.md` |
| Greenfield HTTP tool server | `scripts/scaffold-mcp-use-server.sh.md` or `references/02-setup/05-manual-http-server.md` | `references/04-tools/01-overview.md`, `references/05-responses/01-overview-decision-table.md`, `references/22-validate/02-curl-handshake.md` |
| Strict stdio requirement | `references/02-setup/04-manual-stdio-server.md` | `references/09-transports/02-stdio.md`, then route to `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2` |
| MCP Apps / ChatGPT widget | `references/30-workflows/11-streaming-chart-widget.md` or `references/30-workflows/12-progress-and-elicit-widget.md` | `references/18-mcp-apps/01-what-are-mcp-apps.md`, `references/18-mcp-apps/server-surface/01-widget-helper.md`, `references/18-mcp-apps/widget-react/01-mcpuseprovider.md`, `references/20-inspector/11-protocol-toggle-and-csp-mode.md` |
| Next.js drop-in | `references/30-workflows/10-add-mcp-to-existing-nextjs-app.md` | `references/19-nextjs-drop-in/01-overview.md`, `references/19-nextjs-drop-in/03-shared-aliases-and-tailwind.md`, `references/19-nextjs-drop-in/04-server-only-shimming.md`, `references/19-nextjs-drop-in/05-deploying-as-vercel-route.md` |
| Auth / OAuth | `references/11-auth/01-overview-decision-matrix.md` | `references/11-auth/02-dcr-vs-proxy-mode.md`, `references/11-auth/03-ctx-auth-object.md`, `references/11-auth/08-debugging-checklist.md`, `references/27-troubleshooting/03-oauth-and-supabase-issues.md` |
| Sessions, streaming, notifications, sampling, elicitation | `references/30-workflows/02-stateful-redis-streaming-server.md` | `references/10-sessions/01-overview.md`, `references/14-notifications/01-overview.md`, `references/13-sampling/01-overview.md`, `references/12-elicitation/01-overview.md` |
| Deploy or production hardening | `references/25-deploy/01-decision-matrix.md` | `references/25-deploy/02-pre-deploy-checklist.md`, `references/24-production/05-health-routes.md`, `references/24-production/01-graceful-shutdown.md`, relevant `references/25-deploy/platforms/*.md` |
| Troubleshoot a concrete error | `references/00-symptom-index.md` | `references/27-troubleshooting/06-decision-tree.md`, `references/27-troubleshooting/01-error-catalog.md`, then the exact cluster named by the symptom |
| Migrate from raw SDK or older `mcp-use` | `references/28-migration/01-from-modelcontextprotocol-sdk.md` or `references/28-migration/02-mcp-use-v1-to-v2.md` | `references/17-advanced/03-mcp-use-vs-official-sdk.md`, `references/09-transports/01-overview.md`, `references/28-migration/03-sse-to-streamable-http.md`, `references/28-migration/04-appssdk-to-mcpapps.md`, `references/28-migration/05-dcr-vs-proxy-mode-shift.md` |

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
- **Clean architecture handoff:** `references/00-clean-architecture-coordination.md`
- **Version drift policy:** `references/00-version-drift.md`
- **Full inventory:** `references/00-reference-index.md`
- **Bundled scripts:** `scripts/check-mcp-use-version.sh.md`, `scripts/audit-server-readiness.sh.md`, `scripts/scaffold-mcp-use-server.sh.md`
- **Foundations:** `references/01-concepts/01-what-is-mcp-use.md`, `references/01-concepts/02-server-vs-client-vs-agent.md`, `references/01-concepts/03-transports-overview.md`, `references/01-concepts/04-stateful-vs-stateless.md`, `references/01-concepts/05-mcp-spec-version-history.md`, `references/01-concepts/06-mcp-apps-vs-widgets-terminology.md`, `references/01-concepts/07-this-skill-vs-build-mcp-use-client.md`
- **Setup:** `references/02-setup/01-prerequisites.md`, `references/02-setup/02-scaffold-with-create-mcp-use-app.md`, `references/02-setup/03-template-flags.md`, `references/02-setup/04-manual-stdio-server.md`, `references/02-setup/05-manual-http-server.md`, `references/02-setup/06-add-to-existing-app.md`, `references/02-setup/07-package-scripts.md`, `references/02-setup/08-tsconfig-and-types.md`, `references/02-setup/09-env-vars.md`
- **CLI:** `references/03-cli/01-overview.md`, `references/03-cli/02-create-mcp-use-app.md`, `references/03-cli/03-mcp-use-dev.md`, `references/03-cli/04-mcp-use-build.md`, `references/03-cli/05-mcp-use-start.md`, `references/03-cli/06-mcp-use-deploy.md`, `references/03-cli/07-mcp-use-generate-types.md`, `references/03-cli/08-mcp-use-org-list-and-switch.md`, `references/03-cli/09-mcp-use-introspect.md`, `references/03-cli/10-mcp-use-serve.md`, `references/03-cli/11-mcp-use-generate-docs.md`, `references/03-cli/12-flag-reference.md`, `references/03-cli/13-device-flow-login.md`, `references/03-cli/14-environment-variables.md`
- **Tools:** `references/04-tools/01-overview.md`, `references/04-tools/02-registering-a-tool.md`, `references/04-tools/03-zod-schemas.md`, `references/04-tools/04-describe-and-annotations.md`, `references/04-tools/05-the-ctx-object.md`, `references/04-tools/06-validation-pipeline.md`, `references/04-tools/07-input-schema-vs-output-schema.md`, `references/04-tools/08-tool-anti-patterns.md`, `references/04-tools/canonical-anchor.md`
- **Responses:** `references/05-responses/01-overview-decision-table.md`, `references/05-responses/02-text-and-markdown.md`, `references/05-responses/03-object-and-mix.md`, `references/05-responses/04-html-css-javascript-xml.md`, `references/05-responses/05-image-audio-video-binary.md`, `references/05-responses/06-stream-and-file.md`, `references/05-responses/07-error-handling.md`, `references/05-responses/08-content-vs-structured-content.md`, `references/05-responses/09-meta-private-data.md`, `references/05-responses/canonical-anchor.md`
- **Resources:** `references/06-resources/01-overview.md`, `references/06-resources/02-static-resources.md`, `references/06-resources/03-resource-templates.md`, `references/06-resources/04-binary-and-image.md`, `references/06-resources/05-uri-conventions.md`, `references/06-resources/06-subscriptions.md`, `references/06-resources/canonical-anchor.md`
- **Prompts:** `references/07-prompts/01-overview.md`, `references/07-prompts/02-static-prompts.md`, `references/07-prompts/03-prompt-templates.md`, `references/07-prompts/04-completable-arguments.md`, `references/07-prompts/05-prompt-engineering.md`
- **Server config:** `references/08-server-config/01-mcp-server-constructor.md`, `references/08-server-config/02-network-config.md`, `references/08-server-config/03-cors-and-allowed-origins.md`, `references/08-server-config/04-dns-rebinding-protection.md`, `references/08-server-config/05-middleware-and-custom-routes.md`, `references/08-server-config/06-csp-headers-non-widget.md`, `references/08-server-config/07-shutdown-and-lifecycle.md`
- **Transports:** `references/09-transports/01-overview.md`, `references/09-transports/02-stdio.md`, `references/09-transports/03-streamable-http.md`, `references/09-transports/04-stateless-mode.md`, `references/09-transports/05-serverless-handlers.md`, `references/09-transports/06-sse-alias.md`
- **Sessions:** `references/10-sessions/01-overview.md`, `references/10-sessions/02-lifecycle.md`, `references/10-sessions/03-stream-manager.md`, `references/10-sessions/04-distributed-stream-manager-redis.md`, `references/10-sessions/05-retention-and-cleanup.md`, `references/10-sessions/06-multi-tenant-and-chatgpt.md`, `references/10-sessions/stores/01-overview.md`, `references/10-sessions/stores/02-memory.md`, `references/10-sessions/stores/03-filesystem.md`, `references/10-sessions/stores/04-redis.md`, `references/10-sessions/stores/05-custom-store.md`
- **Auth:** `references/11-auth/01-overview-decision-matrix.md`, `references/11-auth/02-dcr-vs-proxy-mode.md`, `references/11-auth/03-ctx-auth-object.md`, `references/11-auth/04-permission-guards.md`, `references/11-auth/05-browser-oauth-flow.md`, `references/11-auth/06-refresh-tokens.md`, `references/11-auth/07-scopes-supported-config.md`, `references/11-auth/08-debugging-checklist.md`, `references/11-auth/providers/01-auth0.md`, `references/11-auth/providers/02-better-auth.md`, `references/11-auth/providers/03-workos.md`, `references/11-auth/providers/04-keycloak.md`, `references/11-auth/providers/05-supabase.md`, `references/11-auth/providers/06-oauth-proxy.md`, `references/11-auth/providers/07-custom.md`
- **Advanced protocol:** `references/12-elicitation/01-overview.md`, `references/12-elicitation/02-form-mode.md`, `references/12-elicitation/03-url-mode.md`, `references/12-elicitation/04-multi-step-workflows.md`, `references/12-elicitation/05-anti-patterns.md`, `references/13-sampling/01-overview.md`, `references/13-sampling/02-string-vs-extended-api.md`, `references/13-sampling/03-model-preferences.md`, `references/13-sampling/04-callbacks.md`, `references/13-sampling/05-progress-during-sampling.md`, `references/14-notifications/01-overview.md`, `references/14-notifications/02-server-send-notification.md`, `references/14-notifications/03-progress-tokens.md`, `references/14-notifications/04-list-changed-events.md`, `references/14-notifications/05-roots.md`, `references/14-notifications/06-when-notifications-fail.md`, `references/14-notifications/canonical-anchor.md`, `references/15-logging/01-overview.md`, `references/15-logging/02-ctx-log.md`, `references/15-logging/03-server-logger.md`, `references/15-logging/04-mcp-debug-level.md`, `references/15-logging/05-winston-migration.md`, `references/16-client-introspection/01-overview.md`, `references/16-client-introspection/02-info-and-version.md`, `references/16-client-introspection/03-can-capabilities.md`, `references/16-client-introspection/04-supports-apps.md`, `references/16-client-introspection/05-extension-and-user.md`, `references/16-client-introspection/canonical-anchor.md`, `references/17-advanced/01-server-proxy-and-gateway.md`, `references/17-advanced/02-session-based-proxy.md`, `references/17-advanced/03-mcp-use-vs-official-sdk.md`, `references/17-advanced/canonical-anchor.md`
- **MCP Apps widgets — overview:** `references/18-mcp-apps/01-what-are-mcp-apps.md`, `references/18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md`, `references/18-mcp-apps/03-vocabulary.md`, `references/18-mcp-apps/04-when-to-use-vs-tools-only.md`, `references/18-mcp-apps/05-host-capability-detection.md`, `references/18-mcp-apps/canonical-anchor.md`
- **MCP Apps — server surface:** `references/18-mcp-apps/server-surface/01-widget-helper.md`, `references/18-mcp-apps/server-surface/02-uiresource-registration.md`, `references/18-mcp-apps/server-surface/03-tool-widget-config.md`, `references/18-mcp-apps/server-surface/04-baseurl-and-asset-serving.md`, `references/18-mcp-apps/server-surface/05-csp-metadata.md`, `references/18-mcp-apps/server-surface/06-widget-metadata-export.md`, `references/18-mcp-apps/server-surface/07-resources-folder-conventions.md`
- **MCP Apps — widget React:** `references/18-mcp-apps/widget-react/01-mcpuseprovider.md`, `references/18-mcp-apps/widget-react/02-mcpclientprovider.md`, `references/18-mcp-apps/widget-react/03-usewidget-hook.md`, `references/18-mcp-apps/widget-react/04-usecalltool-hook.md`, `references/18-mcp-apps/widget-react/05-image-component.md`, `references/18-mcp-apps/widget-react/06-errorboundary.md`, `references/18-mcp-apps/widget-react/07-themeprovider.md`, `references/18-mcp-apps/widget-react/08-widgetcontrols.md`, `references/18-mcp-apps/widget-react/09-state-persistence.md`, `references/18-mcp-apps/widget-react/10-display-modes.md`, `references/18-mcp-apps/widget-react/11-host-context.md`, `references/18-mcp-apps/widget-react/12-followup-messages.md`, `references/18-mcp-apps/widget-react/13-open-external.md`, `references/18-mcp-apps/widget-react/14-notify-intrinsic-height.md`
- **MCP Apps — streaming, ChatGPT, recipes, anti-patterns:** `references/18-mcp-apps/streaming-tool-props/01-overview.md`, `references/18-mcp-apps/streaming-tool-props/02-state-machine.md`, `references/18-mcp-apps/streaming-tool-props/03-three-phase-render.md`, `references/18-mcp-apps/streaming-tool-props/04-fallback-for-non-streaming-hosts.md`, `references/18-mcp-apps/streaming-tool-props/05-server-side-no-setup.md`, `references/18-mcp-apps/streaming-tool-props/canonical-anchor.md`, `references/18-mcp-apps/chatgpt-apps/01-protocol-overview.md`, `references/18-mcp-apps/chatgpt-apps/02-window-openai-api.md`, `references/18-mcp-apps/chatgpt-apps/03-skybridge-mime.md`, `references/18-mcp-apps/chatgpt-apps/04-csp-format-differences.md`, `references/18-mcp-apps/chatgpt-apps/05-dual-protocol-via-mcpapps.md`, `references/18-mcp-apps/chatgpt-apps/06-deprecation-of-appssdk.md`, `references/18-mcp-apps/chatgpt-apps/07-runtime-detection.md`, `references/18-mcp-apps/widget-recipes/01-weather-dashboard.md`, `references/18-mcp-apps/widget-recipes/02-todo-list-with-state.md`, `references/18-mcp-apps/widget-recipes/03-form-builder.md`, `references/18-mcp-apps/widget-recipes/04-live-data-stream.md`, `references/18-mcp-apps/widget-recipes/05-image-gallery.md`, `references/18-mcp-apps/widget-recipes/06-timer.md`, `references/18-mcp-apps/widget-recipes/07-markdown-editor.md`, `references/18-mcp-apps/widget-recipes/08-chatbot.md`, `references/18-mcp-apps/widget-anti-patterns/01-secrets-in-widget-state.md`, `references/18-mcp-apps/widget-anti-patterns/02-not-guarding-with-ispending.md`, `references/18-mcp-apps/widget-anti-patterns/03-direct-window-openai-access.md`, `references/18-mcp-apps/widget-anti-patterns/04-missing-csp.md`, `references/18-mcp-apps/widget-anti-patterns/05-widget-state-mutations.md`, `references/18-mcp-apps/widget-anti-patterns/06-fetch-instead-of-callTool.md`
- **Next.js drop-in:** `references/19-nextjs-drop-in/01-overview.md`, `references/19-nextjs-drop-in/02-mcp-dir-flag.md`, `references/19-nextjs-drop-in/03-shared-aliases-and-tailwind.md`, `references/19-nextjs-drop-in/04-server-only-shimming.md`, `references/19-nextjs-drop-in/05-deploying-as-vercel-route.md`
- **Inspector and tunneling:** `references/20-inspector/01-overview.md`, `references/20-inspector/02-cli.md`, `references/20-inspector/03-connection-settings.md`, `references/20-inspector/04-url-parameters.md`, `references/20-inspector/05-keyboard-shortcuts.md`, `references/20-inspector/06-command-palette.md`, `references/20-inspector/07-rpc-logging.md`, `references/20-inspector/08-integration.md`, `references/20-inspector/09-debugging-chatgpt-apps.md`, `references/20-inspector/10-self-hosting.md`, `references/20-inspector/11-protocol-toggle-and-csp-mode.md`, `references/20-inspector/12-device-and-locale-panels.md`, `references/20-inspector/13-changelog-pointer.md`, `references/21-tunneling/01-overview.md`, `references/21-tunneling/02-when-to-tunnel.md`, `references/21-tunneling/03-debugging-remote-clients.md`
- **Validate / debug / troubleshoot:** `references/22-validate/01-mcp-inspector-walkthrough.md`, `references/22-validate/02-curl-handshake.md`, `references/22-validate/03-claude-desktop-integration.md`, `references/22-validate/04-vscode-cursor-integration.md`, `references/22-validate/05-add-to-client-button.md`, `references/22-validate/06-unit-testing-tools.md`, `references/23-debug/01-debug-flag-and-tiered-levels.md`, `references/23-debug/02-observability-langfuse.md`, `references/23-debug/03-perf-profiling.md`, `references/23-debug/04-transport-debugging.md`, `references/23-debug/05-load-testing.md`, `references/23-debug/06-widget-debugging.md`, `references/27-troubleshooting/01-error-catalog.md`, `references/27-troubleshooting/02-quick-diagnostic-table.md`, `references/27-troubleshooting/03-oauth-and-supabase-issues.md`, `references/27-troubleshooting/04-widget-rendering-issues.md`, `references/27-troubleshooting/05-csp-violations.md`, `references/27-troubleshooting/06-decision-tree.md`
- **Production / deploy / platforms:** `references/24-production/01-graceful-shutdown.md`, `references/24-production/02-env-config.md`, `references/24-production/03-lazy-init.md`, `references/24-production/04-error-strategy.md`, `references/24-production/05-health-routes.md`, `references/24-production/06-rate-limiting.md`, `references/24-production/07-streaming-large-results.md`, `references/24-production/08-feature-flags.md`, `references/25-deploy/01-decision-matrix.md`, `references/25-deploy/02-pre-deploy-checklist.md`, `references/25-deploy/03-docker.md`, `references/25-deploy/04-claude-desktop-distribution.md`, `references/25-deploy/05-cli-and-org-management.md`, `references/25-deploy/platforms/01-mcp-use-cloud.md`, `references/25-deploy/platforms/02-supabase.md`, `references/25-deploy/platforms/03-google-cloud-run.md`, `references/25-deploy/platforms/04-vercel.md`, `references/25-deploy/platforms/05-fly.md`, `references/25-deploy/platforms/06-cloudflare-workers.md`, `references/25-deploy/platforms/07-deno-deploy.md`
- **Anti-patterns and migration:** `references/26-anti-patterns/01-sdk-misuse.md`, `references/26-anti-patterns/02-tool-design.md`, `references/26-anti-patterns/03-schemas.md`, `references/26-anti-patterns/04-responses.md`, `references/26-anti-patterns/05-security-and-cors.md`, `references/28-migration/01-from-modelcontextprotocol-sdk.md`, `references/28-migration/02-mcp-use-v1-to-v2.md`, `references/28-migration/03-sse-to-streamable-http.md`, `references/28-migration/04-appssdk-to-mcpapps.md`, `references/28-migration/05-dcr-vs-proxy-mode-shift.md`
- **Templates / workflows / canonical examples:** `references/29-templates/01-overview-and-decision-matrix.md`, `references/29-templates/02-minimal-stdio.md`, `references/29-templates/03-production-http.md`, `references/29-templates/04-mcp-apps-widget.md`, `references/29-templates/05-serverless-deno.md`, `references/29-templates/06-side-car-existing-app.md`, `references/30-workflows/01-stateless-vercel-tool-server.md`, `references/30-workflows/02-stateful-redis-streaming-server.md`, `references/30-workflows/03-oauth-protected-supabase-server.md`, `references/30-workflows/04-postgres-database-tool-server.md`, `references/30-workflows/05-github-api-wrapper-with-cache.md`, `references/30-workflows/06-multi-server-proxy-gateway.md`, `references/30-workflows/07-elicitation-and-sampling-server.md`, `references/30-workflows/08-real-time-stock-ticker.md`, `references/30-workflows/09-webhook-handler-with-notifications.md`, `references/30-workflows/10-add-mcp-to-existing-nextjs-app.md`, `references/30-workflows/11-streaming-chart-widget.md`, `references/30-workflows/12-progress-and-elicit-widget.md`, `references/30-workflows/13-resource-watcher-with-subscriptions.md`, `references/30-workflows/14-multi-server-hub-with-audit.md`, `references/30-workflows/15-i18n-adaptive-widget.md`, `references/31-canonical-examples/00-how-to-use-this-cluster.md`, `references/31-canonical-examples/01-mcp-widget-gallery.md`, `references/31-canonical-examples/02-mcp-recipe-finder.md`, `references/31-canonical-examples/03-mcp-chart-builder.md`, `references/31-canonical-examples/04-mcp-media-mixer.md`, `references/31-canonical-examples/05-mcp-progress-demo.md`, `references/31-canonical-examples/06-mcp-resource-watcher.md`, `references/31-canonical-examples/07-mcp-multi-server-hub.md`, `references/31-canonical-examples/08-mcp-i18n-adaptive.md`, `references/31-canonical-examples/09-mcp-diagram-builder.md`, `references/31-canonical-examples/10-mcp-slide-deck.md`, `references/31-canonical-examples/11-mcp-maps-explorer.md`, `references/31-canonical-examples/12-mcp-huggingface-spaces.md`

Migration note: legacy references to `build-mcp-use-apps-widgets` point to content now housed in `references/18-mcp-apps/`. Do not route new work to that legacy name.

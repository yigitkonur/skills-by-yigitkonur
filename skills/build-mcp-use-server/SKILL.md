---
name: build-mcp-use-server
description: "Use skill if you are building TypeScript MCP servers with mcp-use v2 — MCPServer tools, views (MCP Apps), oauth providers, streamable HTTP, deploys, or migrating v1 servers."
---

# Build mcp-use Server

Server-side mechanics for **mcp-use v2** TypeScript MCP servers (the `beta` npm dist-tag line). This skill owns the v2 API surface; sister skills own structure, clients, agents, and the raw SDK. v1 (`mcp-use/server`, npm `latest`) appears here only as migration material.

## When to use this skill

Trigger when the target code or request involves any of these:

- *Importing `MCPServer` from `mcp-use` (root), or code still importing `mcp-use/server` that must move to v2.*
- *Defining tools (definition-first `{ name, description, inputSchema, outputSchema }` + callback), resources, or prompts with zod v4 / Standard Schema.*
- *Server-side `ctx` work — `ctx.auth`, `ctx.sendLog`, `ctx.reportProgress`, `ctx.sendNotification`, `ctx.client.capabilities()`, `ctx.requestState`, elicitation re-entry.*
- *OAuth via `mcp-use/oauth/*` providers (clerk, auth0, workos, supabase, keycloak, better-auth) or `oauthCustomProvider`.*
- *MCP Apps / ChatGPT Apps views — `views/<name>/view.tsx`, the tool `view` field, `structuredContent` props, CSP metadata, `mcp-use/react` hooks (`useToolContext`, `useCallTool`, `useViewState`).*
- *Streamable HTTP serving — `server.listen`, `server.fetch`, `toNodeHandler` (`mcp-use/node`), `withMcpUse`/`createNextHandler` (`mcp-use/next`).*
- *Running `mcp-use dev | build | typecheck | start | deploy`, the Inspector, tunneling, or the curl handshake on `/mcp`.*
- *Production hardening and deploys: mcp-use Cloud, Vercel, Cloudflare Workers, Google Cloud Run, Supabase, Deno, Bun, Hono, Railway, Docker.*
- *Migrating from `mcp-use` v1, raw `@modelcontextprotocol/sdk` servers, or OpenAI Apps-SDK widgets.*

Do **not** use this skill when:

- *The code is app-side `MCPClient` / browser / react client mounting — route to `build-mcp-use-client`.*
- *The work is `MCPAgent` LLM orchestration over MCP tools — route to `build-mcp-use-agent`.*
- *The user wants raw official SDK primitives or strict stdio without mcp-use — route v1 `@modelcontextprotocol/sdk` work to `build-mcp-server-sdk-v1`, and split-package v2 `@modelcontextprotocol/{core,server,client}` work to `build-mcp-server-sdk-v2` (mcp-use v2 cannot serve stdio).*
- *The question is layer placement, import direction, or composition-root structure — route to `build-clean-mcp-architecture` first (see `references/00-clean-architecture-coordination.md`), then return here for mechanics.*

## Version stance

This skill teaches **v2** (verified against `mcp-use@2.0.0-beta.66`; exact pins and drift policy in `references/00-version-drift.md`). Detect which world the project is in before applying anything:

- `from "mcp-use/server"` anywhere → v1 project → start at `references/28-migration/02-v1-to-v2-overview.md`.
- Root `MCPServer` import, `views/`, `mcp-use/oauth/*` → v2 project → apply this skill directly.
- Bare `npm install mcp-use` installs v1 (`latest`); v2 needs the `beta` tag.

## Coordinate with neighboring skills

| Skill | Owns | Handoff |
|---|---|---|
| `build-clean-mcp-architecture` | Folder layout, import direction, layer boundaries, composition root. | Read first for placement; this skill second for APIs. See `references/00-clean-architecture-coordination.md`. |
| `build-mcp-use-client` | `MCPClient`, browser/react client mounting, code mode. | Hand off when the code stops being the server. |
| `build-mcp-use-agent` | `MCPAgent` orchestration where an LLM picks tools. | Hand off when the work is the agent loop. |
| `build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2` | Raw official SDK servers, stdio-only constraints. | Hand off if the user forbids mcp-use or needs stdio. |
| `convert-mcp-sdk-v1-to-v2` | Raw-SDK v1→v2 conversions. | Hand off for raw-SDK migrations; this skill covers mcp-use migrations. |
| `test-by-mcpc-cli` | Live `mcpc` session verification once a server runs. | Use after this skill produces a running server. |

## Detect intent

| Intent | Start here | Then read |
|---|---|---|
| Extend an existing v2 server | `scripts/audit-server-readiness.sh.md` | `references/04-tools/01-overview.md`, `references/05-responses/01-overview-decision-table.md`, `references/08-server-config/01-mcp-server-constructor.md`, `references/22-validate/01-inspector-walkthrough.md` |
| v1 project detected | `references/28-migration/02-v1-to-v2-overview.md` | `references/28-migration/03-v1-to-v2-imports-server-and-tools.md`, `references/28-migration/04-v1-to-v2-responses-and-helpers.md`, then per-area migration files |
| Greenfield HTTP tool server | `references/02-setup/02-scaffold-with-create-mcp-use-app.md` or `references/02-setup/04-manual-http-server.md` | `references/04-tools/02-registering-a-tool.md`, `references/05-responses/01-overview-decision-table.md`, `references/22-validate/02-curl-handshake.md`, `references/30-workflows/01-greenfield-tool-server-to-vercel.md` |
| MCP Apps view / ChatGPT app | `references/18-mcp-apps/canonical-anchor.md` | `references/18-mcp-apps/server-surface/01-tool-view-field.md`, `references/18-mcp-apps/view-react/01-setup-and-providers.md`; if the host/model must act on mounted UI, `references/18-mcp-apps/view-react/09-useviewtool.md`; then `references/30-workflows/02-views-app-chart-widget.md`, `references/20-inspector/08-debugging-chatgpt-apps.md` |
| Next.js drop-in | `references/19-nextjs-drop-in/01-overview-withmcpuse.md` | `references/19-nextjs-drop-in/02-route-and-file-placement.md`, `references/30-workflows/05-nextjs-drop-in.md` |
| Auth / OAuth | `references/11-auth/01-overview.md` | `references/11-auth/02-attaching-a-provider.md`, the provider file under `references/11-auth/providers/`, `references/11-auth/06-debugging-checklist.md` |
| Wrap a REST API | `references/17-advanced/03-openapi-fromopenapi.md` | `references/30-workflows/06-openapi-to-mcp.md` |
| Compose/proxy other MCP servers | `references/17-advanced/01-proxy-and-gateway.md` | `references/17-advanced/02-proxy-auth-and-namespacing.md`, `references/30-workflows/07-proxy-gateway.md` |
| State, notifications, elicitation | `references/01-concepts/04-stateless-model-and-request-state.md` | `references/10-sessions/03-state-patterns-without-sessions.md`, `references/14-notifications/01-overview.md`, `references/12-elicitation/01-overview.md`, `references/30-workflows/08-elicitation-input-required-flow.md` |
| Deploy or production hardening | `references/25-deploy/01-decision-matrix.md` | `references/25-deploy/02-pre-deploy-checklist.md`, the platform file under `references/25-deploy/platforms/`, `references/24-production/04-security-hardening.md` |
| Troubleshoot a concrete error | `references/00-symptom-index.md` | `references/27-troubleshooting/02-quick-diagnostic-table.md`, `references/27-troubleshooting/06-decision-tree.md` |

Use `references/00-reference-index.md` only when the intent table is not specific enough and you need an exact filename.

## Core rules

- Import `MCPServer` and server APIs from `mcp-use` (root). `mcp-use/server` does not exist in v2.
- Install the `beta` tag: `mcp-use@beta`, `@mcp-use/cli@beta`, scaffold with `create-mcp-use-app@beta`. Require Node >= 22.22.2 and ESM; install a `StandardSchemaWithJSON` library in the project (this skill's examples use zod v4).
- Return raw MCP result envelopes (`CallToolResult` etc.). The v1 helpers still exported are deprecated — only `references/05-responses/07-deprecated-v1-helpers.md` teaches them, for migration.
- v2 is stateless per request: no session stores in the shipped beta, no post-response push, no `ctx.sample()`. Cross-request state goes through the `requestState` codec or your own store.
- Serve over Streamable HTTP only (`/mcp` by default). Strict stdio is a raw-SDK requirement — route out.
- For views: `views/<name>/view.tsx`, tool-level `view` field, `outputSchema` required, props via `structuredContent`, hooks from `mcp-use/react`.
- Work in the actual package or subdirectory the user named; prefer improving an existing server over replacing it.
- Never claim the server is scaffolded, runnable, or verified in a read-only or plan-only run.
- For version-sensitive claims, read `references/00-version-drift.md` before editing examples or migration guidance.

## Workflow

### 1. Lock target path and execution mode

Identify the concrete path to inspect and edit. Treat the run as **plan-only** when the environment is read-only, installs are blocked, or the user asked for analysis. Plan-only output must include exact files, install commands, implementation steps, and validation commands — and must not claim runtime validation.

### 2. Scan what already exists

Inspect the target for:

- `package.json`: `mcp-use` version (1.x = v1, 2.x = v2), `zod` major, `"type": "module"`, `@mcp-use/cli`
- imports: `mcp-use` root vs `mcp-use/server` (v1 signal), `mcp-use/oauth/*`, `mcp-use/react`, `mcp-use/next`
- server shape: `new MCPServer(...)`, tool definitions, `views/` directory, `view:` fields, `oauth` config
- runtime signals: `.mcp-use/build/`, Docker, platform config, custom routes, middleware

For existing servers run `scripts/audit-server-readiness.sh` (usage: `scripts/audit-server-readiness.sh.md`). For version drift run `scripts/check-mcp-use-version.sh` (usage: `scripts/check-mcp-use-version.sh.md`).

Summarize: target path, v1 vs v2, existing server vs none, tools-only vs views, implementation-capable vs plan-only, chosen entry file.

### 3. Choose the branch

**v1 project:** do not extend v1 — migrate first via `references/28-migration/02-v1-to-v2-overview.md` unless the user explicitly wants v1 maintenance (then say the skill's guidance is v2 and scope the change narrowly).

**Existing v2 server:** follow the intent row for the requested change, then audit nearby mechanics (tools/schemas, results, config, auth, views, deploy).

**No server:** scaffold with `create-mcp-use-app@beta` (`scripts/scaffold-mcp-use-server.sh` automates it) or hand-build from `references/02-setup/04-manual-http-server.md`. For an existing app, add a side-car per `references/02-setup/05-add-to-existing-app.md`; for Next.js follow `references/19-nextjs-drop-in/`.

**Underspecified:** infer from the existing project when possible; ask only for user-owned choices that block implementation (the exposed service/data, auth policy, tools-only vs. views, or deploy target).

### 4. Build or extend

Default sequence:

1. entry file and runtime shape (`references/02-setup/`, `references/09-transports/04-runtime-adapters-node-next-fetch.md`)
2. `MCPServer` config (`references/08-server-config/`)
3. tools with precise zod v4 schemas (`references/04-tools/`)
4. resources/prompts only when they improve the interface (`references/06-resources/`, `references/07-prompts/`)
5. auth, notifications, elicitation, views, proxy — only when the intent requires them
6. custom health routes, logging, security hardening when shipping beyond local dev (`references/24-production/`)

### 5. Validate

Pick the smallest set that proves the changed behavior; report only the rung reached.

- read-only scan: files inspected, nothing executed
- static: `mcp-use typecheck` / `npm run build`
- local runtime: `mcp-use dev` serving `/mcp`; its CLI-owned listener auto-mounts Inspector at `/mcp/inspector` unless `--no-inspector` is set. Direct `server.listen()`, `server.fetch`, embedded Next.js handlers, and plain `mcp-use start` do not auto-mount it.
- Inspector: surface observed and called (`references/22-validate/01-inspector-walkthrough.md`)
- curl protocol probe: use the native modern wire (no `initialize`) from `references/09-transports/02-streamable-http.md`, or the legacy compatibility handshake (`initialize`, `tools/list`, `tools/call`) in `references/22-validate/02-curl-handshake.md`; legacy POSTs require `Accept: application/json, text/event-stream`.
- unit: `server.fetch(new Request(...))` tests (`references/22-validate/04-unit-testing-server-fetch.md`)
- live client: `mcp-use client`, tunnel, or `test-by-mcpc-cli` session (`references/22-validate/03-connect-real-clients.md`)
- deployed: health route plus a live MCP call against the public URL

For views, verify the text fallback (`content`) and, when possible, Inspector CSP mode (`references/23-debug/03-view-debugging.md`). For deploys, walk `references/25-deploy/02-pre-deploy-checklist.md`.

## Decision rules

- Return concise complete `content` always; add `structuredContent` when there is an `outputSchema`, a typed consumer, or view props — and keep the two semantically equivalent.
- Put private or bulky data in `_meta`; treat `structuredContent` as model-visible (`references/05-responses/06-meta-and-private-data.md`).
- Expected failures return `isError` envelopes; unexpected failures throw (`references/05-responses/05-error-handling.md`).
- Guard the exact elicitation mode before returning `input_required`: check `ctx.client.capabilities().elicitation?.form` for `inputRequired.elicit(...)` and `.url` for `inputRequired.elicitUrl(...)` (`references/12-elicitation/01-overview.md`, `references/16-client-introspection/02-capabilities.md`).
- Need model-side generation? The host generates, the tool validates — sampling is gone (`references/13-sampling/01-sampling-removed-in-v2.md`).
- Views: `view.name` must match the one-level `views/<name>/view.tsx` folder; `outputSchema` is mandatory; declare domains in `view.csp`; use `useCallTool` for View → server and `useViewTool` for host/model → mounted View, never raw `fetch`.
- One server definition serves both MCP Apps and ChatGPT hosts — never hand-roll `window.openai` (`references/18-mcp-apps/chatgpt-apps/01-dual-protocol.md`).

## Guardrails

- In an mcp-use server, do not mix in raw official SDK server primitives (`@modelcontextprotocol/sdk` v1 or `@modelcontextprotocol/{core,server}` v2); route a raw-SDK implementation to the matching sibling skill instead.
- Never install bare `mcp-use` for a v2 project — that is v1; pin the `beta` tag.
- Never use zod v3, CommonJS, or Node < 22 with v2.
- Never use `z.any()`/`z.unknown()` where a concrete schema is possible; `.describe()` every model-filled field.
- Never teach or write v1 response helpers in new code; raw envelopes only.
- Never put secrets in source, logs, `structuredContent`, view props, or view state.
- Decide Host validation, Origin validation, and CORS separately: localhost `listen()` auto-enables Host checks; `server.fetch()` needs explicit `allowedHosts`; Origin checks require `allowedOrigins`; CORS headers require `cors` (`references/08-server-config/03-cors-and-allowed-origins.md`, `references/08-server-config/04-dns-rebinding-and-host-validation.md`).
- Never embed the MCP server as middleware inside another framework's app — use the runtime adapters or side-car patterns.
- Never claim session persistence exists in shipped v2 — see `references/10-sessions/01-overview-stateless-truth.md`.

## Validate honestly

| Rung | Evidence |
|---|---|
| Read-only scan | Files and references inspected; nothing ran. |
| Static validation | `mcp-use typecheck` / build passed. |
| Local runtime | `mcp-use dev`/`start` served `/mcp`. |
| Inspector | Connected; surface observed or called. |
| curl handshake | initialize, tools/list, and a relevant tools/call succeeded. |
| Live client | `mcp-use client` / `mcpc` session named with commands run. |
| Deployed endpoint | Health + live MCP operation verified on the public URL. |

For plan-only runs, mark runtime validation blocked and provide the exact commands to run later.

## Output contract

Unless the user asks for another format, report:

1. target path, v1-or-v2 verdict, and scan summary
2. chosen branch and entrypoint decision
3. implementation or exact plan
4. validation rung reached, commands run, and blockers
5. if views changed: text fallback and CSP verification state
6. if deploy/production changed: platform deployment ID, source branch/SHA when available, terminal conclusion, exact dashboard/platform URL, checklist state, and live health/operation evidence
7. key references used, with exact paths for the route actually followed

## Reference routing

Start with intent or symptoms; use the inventory only as fallback.

- **Symptom index:** `references/00-symptom-index.md`
- **Version drift:** `references/00-version-drift.md`
- **Clean architecture handoff:** `references/00-clean-architecture-coordination.md`
- **Full inventory:** `references/00-reference-index.md`
- **Bundled scripts:** `scripts/check-mcp-use-version.sh.md`, `scripts/audit-server-readiness.sh.md`, `scripts/scaffold-mcp-use-server.sh.md`
- **Concepts:** `references/01-concepts/01-what-is-mcp-use.md`, `references/01-concepts/02-server-vs-client-vs-agent.md`, `references/01-concepts/03-transports-overview.md`, `references/01-concepts/04-stateless-model-and-request-state.md`, `references/01-concepts/05-mcp-spec-version-history.md`, `references/01-concepts/06-mcp-apps-and-views-terminology.md`, `references/01-concepts/07-this-skill-vs-build-mcp-use-client.md`
- **Setup:** `references/02-setup/01-prerequisites.md`, `references/02-setup/02-scaffold-with-create-mcp-use-app.md`, `references/02-setup/03-template-flags.md`, `references/02-setup/04-manual-http-server.md`, `references/02-setup/05-add-to-existing-app.md`, `references/02-setup/06-package-scripts.md`, `references/02-setup/07-tsconfig-and-types.md`, `references/02-setup/08-env-vars.md`
- **CLI:** `references/03-cli/01-overview.md`, `references/03-cli/02-create-mcp-use-app.md`, `references/03-cli/03-mcp-use-dev.md`, `references/03-cli/04-mcp-use-build-and-typecheck.md`, `references/03-cli/05-mcp-use-start.md`, `references/03-cli/06-mcp-use-deploy-and-cloud.md`, `references/03-cli/07-login-and-org.md`, `references/03-cli/08-client-and-screenshot.md`, `references/03-cli/09-flag-reference.md`, `references/03-cli/10-environment-variables.md`
- **Tools:** `references/04-tools/01-overview.md`, `references/04-tools/02-registering-a-tool.md`, `references/04-tools/03-schemas-standard-schema-and-zod-v4.md`, `references/04-tools/04-describe-and-annotations.md`, `references/04-tools/05-the-ctx-object.md`, `references/04-tools/06-validation-pipeline.md`, `references/04-tools/07-input-schema-vs-output-schema.md`, `references/04-tools/08-tool-anti-patterns.md`, `references/04-tools/canonical-anchor.md`
- **Results:** `references/05-responses/01-overview-decision-table.md`, `references/05-responses/02-text-and-content-blocks.md`, `references/05-responses/03-structured-content-and-output-schema.md`, `references/05-responses/04-images-audio-binary-resources.md`, `references/05-responses/05-error-handling.md`, `references/05-responses/06-meta-and-private-data.md`, `references/05-responses/07-deprecated-v1-helpers.md`, `references/05-responses/canonical-anchor.md`
- **Resources:** `references/06-resources/01-overview.md`, `references/06-resources/02-static-resources.md`, `references/06-resources/03-resource-templates.md`, `references/06-resources/04-binary-and-image.md`, `references/06-resources/05-uri-conventions.md`, `references/06-resources/06-subscriptions-listen.md`, `references/06-resources/canonical-anchor.md`
- **Prompts:** `references/07-prompts/01-overview.md`, `references/07-prompts/02-static-prompts.md`, `references/07-prompts/03-prompt-templates.md`, `references/07-prompts/04-completable-arguments.md`, `references/07-prompts/05-prompt-engineering.md`
- **Server config:** `references/08-server-config/01-mcp-server-constructor.md`, `references/08-server-config/02-network-basepath-and-endpoints.md`, `references/08-server-config/03-cors-and-allowed-origins.md`, `references/08-server-config/04-dns-rebinding-and-host-validation.md`, `references/08-server-config/05-middleware.md`, `references/08-server-config/06-custom-routes.md`, `references/08-server-config/07-lifecycle-listen-fetch-shutdown.md`
- **Transports:** `references/09-transports/01-overview.md`, `references/09-transports/02-streamable-http.md`, `references/09-transports/03-stateless-and-request-state.md`, `references/09-transports/04-runtime-adapters-node-next-fetch.md`, `references/09-transports/05-no-stdio-and-sse-history.md`
- **Sessions/state:** `references/10-sessions/01-overview-stateless-truth.md`, `references/10-sessions/02-session-storage-roadmap.md`, `references/10-sessions/03-state-patterns-without-sessions.md`, `references/10-sessions/04-multi-instance-and-scaling.md`
- **Auth:** `references/11-auth/01-overview.md`, `references/11-auth/02-attaching-a-provider.md`, `references/11-auth/03-ctx-auth-and-user-context.md`, `references/11-auth/04-permission-guards.md`, `references/11-auth/05-custom-provider-oauthcustomprovider.md`, `references/11-auth/06-debugging-checklist.md`, `references/11-auth/07-oauth-proxy-removed.md`, `references/11-auth/providers/01-clerk.md`, `references/11-auth/providers/02-auth0.md`, `references/11-auth/providers/03-workos.md`, `references/11-auth/providers/04-supabase.md`, `references/11-auth/providers/05-keycloak.md`, `references/11-auth/providers/06-better-auth.md`
- **Elicitation:** `references/12-elicitation/01-overview.md`, `references/12-elicitation/02-form-mode.md`, `references/12-elicitation/03-url-mode.md`, `references/12-elicitation/04-multi-round-and-request-state.md`, `references/12-elicitation/05-anti-patterns.md`
- **Sampling:** `references/13-sampling/01-sampling-removed-in-v2.md`
- **Notifications:** `references/14-notifications/01-overview.md`, `references/14-notifications/02-ctx-sendnotification.md`, `references/14-notifications/03-progress-reporting.md`, `references/14-notifications/04-list-changed-events.md`, `references/14-notifications/05-subscriptions-delivery.md`, `references/14-notifications/canonical-anchor.md`
- **Logging:** `references/15-logging/01-overview.md`, `references/15-logging/02-ctx-sendlog.md`, `references/15-logging/03-server-and-request-logging.md`
- **Client introspection:** `references/16-client-introspection/01-overview.md`, `references/16-client-introspection/02-capabilities.md`, `references/16-client-introspection/03-apps-detection.md`, `references/16-client-introspection/canonical-anchor.md`
- **Advanced:** `references/17-advanced/01-proxy-and-gateway.md`, `references/17-advanced/02-proxy-auth-and-namespacing.md`, `references/17-advanced/03-openapi-fromopenapi.md`, `references/17-advanced/04-mcp-use-vs-official-sdk.md`, `references/17-advanced/canonical-anchor.md`
- **MCP Apps:** `references/18-mcp-apps/01-what-are-mcp-apps.md`, `references/18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md`, `references/18-mcp-apps/03-vocabulary-views.md`, `references/18-mcp-apps/04-when-to-use-vs-tools-only.md`, `references/18-mcp-apps/05-host-capability-detection.md`, `references/18-mcp-apps/anti-patterns.md`, `references/18-mcp-apps/canonical-anchor.md`
- **MCP Apps server surface:** `references/18-mcp-apps/server-surface/01-tool-view-field.md`, `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md`, `references/18-mcp-apps/server-surface/03-viewconfig.md`, `references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md`, `references/18-mcp-apps/server-surface/05-csp-metadata.md`
- **MCP Apps react:** `references/18-mcp-apps/view-react/01-setup-and-providers.md`, `references/18-mcp-apps/view-react/02-usetoolcontext.md`, `references/18-mcp-apps/view-react/03-usecalltool.md`, `references/18-mcp-apps/view-react/04-useviewstate-and-model-context.md`, `references/18-mcp-apps/view-react/05-display-modes.md`, `references/18-mcp-apps/view-react/06-followups-and-open-external.md`, `references/18-mcp-apps/view-react/07-host-context-files-and-size.md`, `references/18-mcp-apps/view-react/08-theme-and-components.md`, `references/18-mcp-apps/view-react/09-useviewtool.md`
- **ChatGPT apps:** `references/18-mcp-apps/chatgpt-apps/01-dual-protocol.md`, `references/18-mcp-apps/chatgpt-apps/02-legacy-window-openai-and-skybridge.md`, `references/18-mcp-apps/chatgpt-apps/03-csp-differences.md`, `references/18-mcp-apps/chatgpt-apps/04-runtime-detection.md`
- **Next.js:** `references/19-nextjs-drop-in/01-overview-withmcpuse.md`, `references/19-nextjs-drop-in/02-route-and-file-placement.md`, `references/19-nextjs-drop-in/03-views-in-nextjs.md`, `references/19-nextjs-drop-in/04-deploying-on-vercel.md`
- **Inspector:** `references/20-inspector/01-overview.md`, `references/20-inspector/02-cli.md`, `references/20-inspector/03-connection-settings.md`, `references/20-inspector/04-url-parameters.md`, `references/20-inspector/05-keyboard-shortcuts-and-palette.md`, `references/20-inspector/06-integration-and-add-to-client.md`, `references/20-inspector/07-self-hosting.md`, `references/20-inspector/08-debugging-chatgpt-apps.md`, `references/20-inspector/09-changelog-pointer.md`
- **Tunneling:** `references/21-tunneling/01-overview.md`, `references/21-tunneling/02-when-to-tunnel-and-debugging.md`
- **Validate:** `references/22-validate/01-inspector-walkthrough.md`, `references/22-validate/02-curl-handshake.md`, `references/22-validate/03-connect-real-clients.md`, `references/22-validate/04-unit-testing-server-fetch.md`
- **Debug:** `references/23-debug/01-debugging-workflow.md`, `references/23-debug/02-transport-debugging.md`, `references/23-debug/03-view-debugging.md`
- **Production:** `references/24-production/01-env-config.md`, `references/24-production/02-error-strategy.md`, `references/24-production/03-health-and-custom-routes.md`, `references/24-production/04-security-hardening.md`, `references/24-production/05-scaling-stateless.md`
- **Deploy:** `references/25-deploy/01-decision-matrix.md`, `references/25-deploy/02-pre-deploy-checklist.md`, `references/25-deploy/03-docker.md`, `references/25-deploy/04-cli-and-org-management.md`, `references/25-deploy/platforms/01-mcp-use-cloud.md`, `references/25-deploy/platforms/02-vercel.md`, `references/25-deploy/platforms/03-cloudflare-workers.md`, `references/25-deploy/platforms/04-google-cloud-run.md`, `references/25-deploy/platforms/05-supabase.md`, `references/25-deploy/platforms/06-deno.md`, `references/25-deploy/platforms/07-bun.md`, `references/25-deploy/platforms/08-hono.md`, `references/25-deploy/platforms/09-railway.md`, `references/25-deploy/platforms/10-runtime-patterns.md`
- **Anti-patterns:** `references/26-anti-patterns/01-sdk-misuse.md`, `references/26-anti-patterns/02-tool-design.md`, `references/26-anti-patterns/03-schemas.md`, `references/26-anti-patterns/04-results.md`, `references/26-anti-patterns/05-security-and-cors.md`
- **Troubleshooting:** `references/27-troubleshooting/01-error-catalog.md`, `references/27-troubleshooting/02-quick-diagnostic-table.md`, `references/27-troubleshooting/03-oauth-issues.md`, `references/27-troubleshooting/04-view-rendering-issues.md`, `references/27-troubleshooting/05-csp-violations.md`, `references/27-troubleshooting/06-decision-tree.md`
- **Migration:** `references/28-migration/01-from-modelcontextprotocol-sdk.md`, `references/28-migration/02-v1-to-v2-overview.md`, `references/28-migration/03-v1-to-v2-imports-server-and-tools.md`, `references/28-migration/04-v1-to-v2-responses-and-helpers.md`, `references/28-migration/05-v1-to-v2-auth.md`, `references/28-migration/06-v1-to-v2-widgets-to-views.md`, `references/28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md`, `references/28-migration/08-appssdk-to-mcp-apps.md`
- **Templates:** `references/29-templates/01-overview-and-decision-matrix.md`, `references/29-templates/02-template-mcp-server.md`, `references/29-templates/03-template-mcp-apps.md`, `references/29-templates/04-template-blank-and-manual.md`
- **Workflows:** `references/30-workflows/01-greenfield-tool-server-to-vercel.md`, `references/30-workflows/02-views-app-chart-widget.md`, `references/30-workflows/03-oauth-protected-server-clerk.md`, `references/30-workflows/04-supabase-oauth-and-deploy.md`, `references/30-workflows/05-nextjs-drop-in.md`, `references/30-workflows/06-openapi-to-mcp.md`, `references/30-workflows/07-proxy-gateway.md`, `references/30-workflows/08-elicitation-input-required-flow.md`
- **Canonical examples:** `references/31-canonical-examples/00-how-to-use-this-cluster.md`, `references/31-canonical-examples/01-chart-builder.md`, `references/31-canonical-examples/02-diagram-builder.md`, `references/31-canonical-examples/03-example-inventory.md`

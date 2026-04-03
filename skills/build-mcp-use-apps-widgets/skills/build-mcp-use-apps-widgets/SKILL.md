---
name: build-mcp-use-apps-widgets
description: >-
  Use skill if you are building or fixing an mcp-use server that renders React widgets and needs useWidget, useCallTool, streaming, CSP, or ChatGPT/MCP Apps compatibility.
---

# Build MCP Apps & Widgets

Build or repair `mcp-use` apps that return React widgets from `resources/` and run in ChatGPT plus MCP Apps hosts such as Claude and Goose.

> Not building UI? Use `build-mcp-use-server`.
> Building a client that connects to MCP servers? Use `build-mcp-use-client`.

## Trigger boundary

Use this skill when the task is about:

- creating a new `mcp-use` widget app from scratch
- adding widgets to an existing `mcp-use` server
- fixing `useWidget`, `useCallTool`, `widget()`, `widgetMetadata`, CSP, theme, streaming, or display-mode behavior
- shipping the same widget flow to ChatGPT and MCP Apps-compatible clients

Do not use this skill when:

- the task is a plain MCP server with no widgets
- the task is an MCP client app that connects to existing servers
- the user only needs a raw non-widget transport or SDK explanation

## Operating defaults

- Node 18+ is supported. Prefer Node 22 LTS when you want the closest match to current examples.
- Install `zod` explicitly alongside `mcp-use`.
- `mcp-use` is HTTP-first here: `server.listen()` serves `/mcp`; this workflow does not assume stdio transport.
- Default layout: root `index.ts`, `resources/<widget-name>/widget.tsx`, shared code in `src/lib/`.
- Keep `.mcp-use/**/*` in `tsconfig.json` so generated tool types are available to widget code.

## Workflow

### 1. Detect the starting point

- Inspect the current working tree first.
- Look for an existing widget app: `mcp-use` dependency, `resources/` folders with `widget.tsx`, `widgetMetadata` exports, `mcp-use/react` imports, and tools with `widget: { name: ... }`.
- Branch early:
  - Existing app present: audit and fix it in place.
  - No widget app present: gather only the missing product decisions, then scaffold the smallest working slice.

### 2. If an app already exists, audit it across four passes

- Cover these areas even if you do the work sequentially:
  - Server bindings and schemas: tool definitions, `widget()` responses, `output`/`message`, Zod descriptions, `baseUrl`, middleware, auth.
  - Widget lifecycle and host integration: `useWidget`, `isPending`, `isStreaming`, theming, `McpUseProvider`, `Image`, `widgetMetadata`.
  - Widget-to-tool flows: `useCallTool`, `callTool`, persistent state, follow-up messages, display modes, subscriptions or notifications if present.
  - Deployment and verification: Inspector flow, CSP, transport, production config, common failure cases.
- If the runtime supports safe parallel delegation, you can split those passes. If it does not, do them one by one. Do not depend on delegation.
- Prioritize fixes in this order:
  - broken install or build
  - widget does not render or crashes on pending state
  - tool and widget folder are mis-bound
  - widget has no useful text fallback for non-widget clients
  - CSP, `baseUrl`, or host-specific compatibility gaps
  - deployment and hardening gaps
- Apply fixes directly. Do not stop at a review list unless the user explicitly asked for review-only output.

### 3. If no widget app exists, build the smallest working baseline first

- Ask only the questions needed to define one working vertical slice. Stop once these are clear:
  - what the first widget shows
  - whether the widget must call another tool from inside the UI
  - whether external APIs, auth, or deployment constraints are already required
- For a greenfield app, prefer the scaffolded path:
  - `npx create-mcp-use-app <name> --template mcp-apps --no-skills`
- Run the first build gate immediately after scaffolding:
  - `npm install`
  - `npm run build`
  - `npx mcp-use generate-types`
- Do not add product features on top of a failing template.
- If the generated demo widget or demo tool blocks the build on current dependencies, replace or remove that demo before adding custom logic.

### 4. Use the minimal architecture that proves the flow

- Start with one widget-bound tool and one plain follow-up tool callable from the widget.
- Put shared business logic and validation in `src/lib/`.
- From a root `index.ts` entrypoint, import files under `src/` with Node ESM relative `.js` paths such as `./src/lib/math.js`.
- Keep widgets in `resources/<widget-name>/widget.tsx`; the folder name must match `tool.widget.name`.
- Use [minimal-interactive-widget.md](references/examples/minimal-interactive-widget.md) when the user needs the smallest calculator/form-style pattern that edits local state and calls a non-widget tool from the UI.
- Only add extra widgets, auth, subscriptions, or deployment-specific complexity after the baseline flow works.

### 5. Verify before stopping

- Run `npm run build`.
- Run `npx mcp-use generate-types`.
- Run `npx mcp-use dev`.
- Open the Inspector at `http://localhost:3000/inspector` and exercise at least one widget-bound tool.
- If a host-specific feature could not be verified in the current environment, say exactly what was not tested.

## Critical rules

1. `tool.widget.name` must match `resources/<name>/widget.tsx` exactly.
2. Always give the LLM and text-only clients a useful `message` or `output`; `props` alone is not enough.
3. Always guard widget rendering with `isPending` before you trust `props`.
4. Treat streaming preview as optional. ChatGPT does not expose `partialToolInput`, so the widget must still work with only `isPending`.
5. Use `useCallTool()` or `useWidget().callTool()` for widget-to-tool calls. Do not use raw `fetch()` against MCP endpoints.
6. Wrap the widget root in `McpUseProvider`. If the widget uses React Router, add `BrowserRouter` manually inside that provider.
7. Declare every external domain in `widgetMetadata.metadata.csp`. Missing domains fail silently in hosted widget iframes.
8. Set `baseUrl` or `MCP_URL` for deployed builds so widget assets and CSP resolve correctly.
9. Use `Image` for files from `public/` instead of raw `<img>`.
10. Keep secrets, tokens, and other sensitive data out of widget props and widget state.
11. Prefer `type: "mcpApps"` for dual-protocol compatibility; do not start new work with `type: "appsSdk"`.
12. Keep shared code browser-safe if you import it into widget bundles; otherwise keep it server-only in `src/lib/`.

## Reference routing

Load the smallest relevant set for the branch you are in.

### Start here

| Situation | Read |
|---|---|
| Fastest greenfield path, scaffold verification, or first-run build gate | `references/guides/quick-start.md`, `references/examples/project-templates.md`, `references/examples/minimal-interactive-widget.md` |
| Need a larger end-to-end server or widget example after the baseline works | `references/examples/server-recipes.md`, `references/examples/widget-recipes.md` |

### Server and build surface

| Situation | Read |
|---|---|
| Tool definitions, Zod schemas, annotations, `widget` config | `references/guides/tools-and-schemas.md` |
| `widget()`, `text()`, `object()`, `mix()`, MIME behavior | `references/guides/response-helpers.md` |
| Server config, `baseUrl`, CORS, middleware, env vars | `references/guides/server-configuration.md` |
| Resources, prompts, or `uiResource()` decisions | `references/guides/resources-and-prompts.md` |
| Session stores or stream managers | `references/guides/session-management.md` |
| OAuth or `ctx.auth` | `references/guides/authentication.md` |
| HTTP vs serverless transport, proxying, `/mcp` behavior | `references/guides/transports.md` |
| CLI commands, `generate-types`, `dev`, `build`, `deploy` | `references/guides/cli-reference.md` |
| Capability checks, proxy patterns, advanced server features | `references/guides/advanced-features.md` |

### Widget surface

| Situation | Read |
|---|---|
| Core widget lifecycle, host context, `useWidget`, `useCallTool` | `references/guides/widgets-and-ui.md` |
| `McpUseProvider`, `Image`, `ErrorBoundary`, `WidgetMetadata` | `references/guides/widget-components.md` |
| Streaming preview, `partialToolInput`, three-phase rendering | `references/guides/streaming-and-preview.md` |
| ChatGPT compatibility, metadata mapping, migration from `appsSdk` | `references/guides/chatgpt-apps-flow.md` |

### Interaction and orchestration

| Situation | Read |
|---|---|
| `ctx.elicit()` or `ctx.sample()` inside tools | `references/guides/elicitation-and-sampling.md` |
| Notifications, progress, resource subscriptions, roots | `references/guides/notifications-and-subscriptions.md` |
| Multi-widget composition, follow-up patterns, widget state patterns | `references/patterns/mcp-apps-patterns.md` |

### Testing, deployment, and failure recovery

| Situation | Read |
|---|---|
| Inspector workflow, curl checks, widget debugging | `references/guides/testing-and-debugging.md` |
| Deployment targets and production environment choices | `references/patterns/deployment.md` |
| Production reliability, caching, rate limiting, distributed Redis patterns | `references/patterns/production-patterns.md` |
| Common implementation mistakes to avoid | `references/patterns/anti-patterns.md` |
| Exact error messages and concrete fixes | `references/troubleshooting/common-errors.md` |

## Guardrails

- Do not assume delegation or subagents exist.
- Do not keep a broken scaffold and pile custom code on top of it.
- Do not return a widget response with no meaningful text fallback.
- Do not access `window.openai` directly; use the `mcp-use/react` hooks.
- Do not skip `npm run build` and `npx mcp-use generate-types`.
- Do not use `fetch()` from the widget to talk to your own MCP server when a tool call is the right abstraction.
- Do not store secrets or privileged backend-only data in widget state.
- Do not default to `server.uiResource()` when `resources/<name>/widget.tsx` plus a custom tool gives a cleaner result.

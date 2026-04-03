---
name: build-mcp-use-server
description: Use skill if you are building or extending TypeScript MCP servers with the mcp-use library — tools, Zod schemas, resources, prompts, transports, OAuth, sessions, testing, and deployment.
---

# Build MCP Use Server

Use this skill for server-side `mcp-use` work. It covers building new MCP servers, extending existing ones, and tightening an existing server against `mcp-use` conventions. If the user's main task is a full widget or MCP App UI, use `build-mcp-use-apps-widgets` instead.

Core rules:

- Import server APIs from `mcp-use/server`. The one common exception is `Logger`, which comes from `mcp-use`.
- Declare `zod` in the project's own dependencies. Do not assume `mcp-use` provides it.
- Use `mcp-use` HTTP or serverless patterns. Do not hand-wire raw SDK transports.
- Work in the actual package, fixture, or subdirectory you will change. If the user named a monorepo package or fixture path, scan that path directly.
- Never claim the server is scaffolded, installed, or runnable when the environment is read-only, notes-only, or missing prerequisites you cannot add in this run.

## Workflow

### 1. Lock the target path and execution mode

Start by identifying the concrete path you will inspect and edit.

- If the user named a fixture, package, or subdirectory, use that path instead of the repo root.
- Detect both project state and execution limits before choosing an implementation path:
  - Is there already an `mcp-use` server here?
  - Is this an implementation-capable run or a plan-only run?

Treat the run as **plan-only** when any of these are true:

- the environment is read-only or notes-only
- package installation is blocked
- required prerequisites are missing and you cannot add them in this run
- the user asked for analysis or a concrete implementation plan rather than code changes

For plan-only runs, keep gathering enough context to produce an exact implementation plan. Do not fabricate edits, installs, or validation results.

### 2. Scan what already exists

Inspect the target path for:

- `package.json` with `mcp-use`, `zod`, or `@mcp-use/cli`
- imports from `mcp-use/server`
- `new MCPServer(...)`
- registered tools, resources, prompts, or widget responses
- existing host entry files such as `index.ts`, `src/index.ts`, `src/server.ts`, or `src/mcp-server.ts`
- deployment/runtime clues such as `.mcp-use/`, Docker, edge-function folders, auth config, env files, or existing health routes

Summarize:

- target path
- existing server vs no server
- implementation-capable vs plan-only
- likely server shape
- chosen entry file

### 3. Choose the right branch

#### Branch A — Existing `mcp-use` server

Do not rebuild from scratch. Audit and improve the live implementation yourself.

Cover these areas in order:

1. tools and schemas
   - names, descriptions, `.describe()`, specificity, annotations, response helpers
2. server configuration and transport
   - `MCPServer` config, CORS, `allowedOrigins`, transport mode, middleware, `baseUrl`, env handling
3. resources, prompts, notifications, sampling, elicitation, advanced features
   - whether the server exposes the right primitives and guards client capabilities correctly
4. production readiness
   - error handling, logging, session strategy, shutdown, testing coverage, deployment shape

Then either:

- implement the highest-value fixes, or
- if the run is plan-only, produce a prioritized change plan with exact files, commands, and validation steps

#### Branch B — No `mcp-use` server, but the repo gives enough context

Infer the server from the existing code or spec.

Common signals:

- REST or Hono/Express/Fastify endpoints that should become MCP tools
- CLI commands that map naturally to tools
- data sources that should become resources
- a README, issue, or fixture that clearly defines the behavior

Choose the entrypoint deliberately:

- scaffolded `create-mcp-use-app` project: keep root `index.ts`
- brand-new manual server: default to `src/server.ts`
- existing app already using `src/index.ts` or another host entry: keep the host entry and add `src/mcp-server.ts`

Use the canonical setup and example sources before writing code:

- `references/guides/quick-start.md`
- `references/examples/project-templates.md`
- `references/examples/server-recipes.md`

If the requested server is small and generic, start from the smallest matching example rather than inventing a new structure. The minimal calculator server in `references/guides/quick-start.md` is the default tiny-tool recipe.

#### Branch C — No usable context and the request is underspecified

Ask only the missing questions needed to proceed. Skip anything the user or repo already answered.

Prioritize:

- what data or service the server exposes
- transport/runtime target
- auth requirements
- tools vs resources vs prompts
- deployment target
- whether sampling, elicitation, or widgets are required

Ask one question at a time unless the user clearly wants a batch questionnaire.

### 4. Preflight setup before implementation

Use `references/guides/quick-start.md` as the canonical setup matrix.

Make these prerequisites explicit instead of assuming them:

- Node 18+ is available, with Node 22 LTS preferred when matching current examples
- `package.json` uses `"type": "module"`
- `mcp-use` and `zod` are installed in dependencies
- `@mcp-use/cli` is present for CLI/HMR workflows unless the scaffold already included it
- the chosen entry file matches the project type

If prerequisites are missing and you cannot add them in this run, switch to plan-only output.

### 5. Build or extend the server

Default sequence:

1. choose the entry file and runtime shape
2. create or refine `MCPServer` config
3. register tools with precise Zod schemas
4. add resources or prompts only when they genuinely improve the interface
5. add auth, session storage, notifications, sampling, elicitation, proxying, or widgets only when the use case requires them
6. add health routes, deliberate logging, and graceful shutdown for HTTP servers

### 6. Validate honestly

For implementation-capable runs, validate with the smallest relevant set:

- `mcp-use dev` and/or `mcp-use start`
- MCP Inspector
- curl initialize -> list -> call flow over `/mcp`
- type generation or typecheck
- build or deploy preflight when relevant

For plan-only runs, provide:

- exact entry file(s)
- exact install commands
- exact scripts or config changes
- exact tools/resources/prompts to add
- exact validation commands to run later

## Decision rules

- Prefer improving an existing server over replacing it.
- Keep the host app's entrypoint when adding MCP to an existing app; use `src/mcp-server.ts` unless there is a strong reason not to.
- Use `text()`, `object()`, `error()`, `mix()`, `widget()`, and the other helpers instead of hand-built MCP payloads.
- Use `error()` for expected failures and `throw` for truly unexpected failures.
- Treat notifications as stateful-only unless you have explicitly verified the transport model supports them.
- Guard `ctx.elicit()` with `ctx.client.can("elicitation")`.
- Guard `ctx.sample()` with `ctx.client.can("sampling")`.
- Suggest `build-mcp-use-apps-widgets` when the user's real problem is a client-side MCP App or widget UI, not the server.

## Guardrails

- Never import server primitives from `@modelcontextprotocol/sdk` directly.
- Never omit `zod` from the project's own dependencies.
- Never use `z.any()` or `z.unknown()` when a concrete schema is possible.
- Never leave schema fields undocumented; use `.describe()` on every field the model must fill.
- Never fall back to a repo-wide scan if the user named a narrower target path.
- Never claim success in a blocked environment.
- Never put secrets in source or logs.
- Never skip `allowedOrigins` and CORS decisions for public HTTP servers.

## Output contract

Unless the user wants another format, report work in this order:

1. target path and scan summary
2. chosen branch and entrypoint decision
3. implementation or exact plan
4. validation results or explicit blocker
5. key reference files used

## Reference routing

Use the smallest relevant set.

### Start here

- `references/guides/quick-start.md`
  - canonical entrypoint, dependency, and script matrix
  - minimal calculator server
- `references/examples/project-templates.md`
  - full scaffold, manual, and existing-app layouts
- `references/examples/server-recipes.md`
  - copyable working server patterns

### Core server design

- `references/guides/tools-and-schemas.md`
- `references/guides/response-helpers.md`
- `references/guides/resources-and-prompts.md`
- `references/guides/server-configuration.md`
- `references/guides/transports.md`
- `references/guides/session-management.md`

### Advanced capabilities

- `references/guides/authentication.md`
- `references/guides/elicitation-and-sampling.md`
- `references/guides/notifications-and-subscriptions.md`
- `references/guides/advanced-features.md`
- `references/guides/widgets-and-ui.md`

### Build, test, and ship

- `references/guides/cli-reference.md`
- `references/guides/testing-and-debugging.md`
- `references/patterns/production-patterns.md`
- `references/patterns/deployment.md`
- `references/patterns/anti-patterns.md`
- `references/troubleshooting/common-errors.md`

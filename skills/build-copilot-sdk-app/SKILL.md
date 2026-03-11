---
name: build-copilot-sdk-app
description: Use skill if you are building or extending a TypeScript app with @github/copilot-sdk, including session flows, streaming, tools, hooks, custom agents, BYOK, or MCP-backed Copilot runtime integration.
---

# Build Copilot SDK App

Use this skill when the job is to build a real TypeScript/Node application around `@github/copilot-sdk`. Start with the smallest viable Copilot SDK shape, then add hooks, custom agents, MCP servers, persistence, or BYOK only when the task truly requires them.

## Trigger boundary

### Activate when

- The repo is TypeScript/Node and will import or change `@github/copilot-sdk`
- The task involves `CopilotClient`, `createSession`, `resumeSession`, `send`, `sendAndWait`, session events, custom tools, hooks, `mcpServers`, `customAgents`, or `provider`
- The user needs to choose between request/response, streaming, tool calling, delegated agents, resumable sessions, headless CLI service mode, or BYOK
- The app must control approvals, user input, session persistence, model selection, or MCP-backed tool access inside a Copilot SDK runtime

### Do not use when

- The main job is generic TypeScript typing, linting, or compiler configuration with no Copilot SDK boundary question; use `develop-typescript`
- The main job is implementing an MCP server rather than consuming MCP tools from a Copilot SDK app
- The task is about Copilot review config, agent instruction files, or PR review methodology; use `init-copilot-review`, `init-agent-config`, or `review-pr`
- The user needs Python, Go, or .NET SDK guidance instead of a TypeScript/Node implementation path
- The request is generic AI app advice that does not depend on Copilot SDK APIs

## Core operating rule

Classify the app shape first. Prove the simplest session flow works first. Only then add higher-order surfaces such as hooks, custom agents, MCP servers, persistence, headless service mode, or BYOK.

## Choose the right Copilot SDK path first

| Need | Start with | Do not start with | Route |
|---|---|---|---|
| Local prototype or embedded assistant in one Node app | `new CopilotClient()` + one `createSession()` | headless CLI, multi-client pooling, custom agents | `references/client/setup-and-options.md`, `references/sessions/create-and-configure.md` |
| Streaming UX | `streaming: true` + pre-registered event handlers | polling `sendAndWait()` for deltas | `references/events/streaming-patterns.md` |
| Tool-calling assistant | `defineTool` + Zod + explicit permission handler | hooks or custom agents as the first abstraction | `references/tools/define-tool-zod.md`, `references/tools/tool-results-and-errors.md`, `references/permissions/permission-handler.md` |
| Interactive or approval-heavy agent | `onUserInputRequest` + permission rules + one session | assuming `ask_user` exists by default | `references/permissions/user-input-handler.md`, `references/permissions/permission-handler.md`, `references/sessions/create-and-configure.md` |
| Policy, sanitization, audit, or per-tool guardrails | hooks + permission handler | giant system prompts or tool wrappers for everything | `references/hooks/pre-tool-use.md`, `references/permissions/permission-handler.md` |
| Distinct delegated roles | `customAgents` with precise descriptions and tool scopes | a custom agent for ordinary branching or prompt wording | `references/agents/custom-agents.md` |
| External tools via MCP | `mcpServers` with explicit server/tool exposure | building the MCP server in this task | `references/agents/mcp-servers.md` |
| Your own model/provider billing or credentials | `provider` + explicit `model` + provider-specific env/token setup | GitHub-hosted auth defaults or implicit model selection | `references/auth/byok-providers.md`, `references/auth/environment-variables.md` |
| Long-lived backend service or multi-request chat API | stable `sessionId` + `resumeSession()` + headless CLI only if sharing across requests/processes | random session IDs or per-request child CLI spawning | `references/sessions/persistence-and-resume.md`, `references/patterns/backend-service.md` |

## Default workflow

1. **Classify the runtime shape before reading broadly.**
   - local prototype or embedded assistant
   - streaming chat or live UI
   - tool-calling assistant
   - interactive or approval-heavy agent
   - policy-controlled agent
   - delegated multi-agent workflow
   - MCP-augmented assistant
   - resumable or multi-request service
   - BYOK or provider-managed deployment

2. **Establish the minimum viable SDK skeleton first.**
   - choose client transport and auth boundary
   - create one session
   - supply `onPermissionRequest`
   - add `onUserInputRequest` only if the app should surface `ask_user`
   - decide `sendAndWait()` versus `send()`
   - register required event handlers before sending messages
   - clean up with `disconnect()` and `client.stop()`

3. **Add complexity in this order unless the task clearly proves otherwise.**
   - client transport and auth
   - session config and message flow
   - streaming events
   - custom tools
   - hooks
   - custom agents
   - MCP servers
   - persistence, headless service mode, queueing, or plan/autopilot flows
   - BYOK provider configuration

4. **Prefer SDK defaults until a real requirement forces an override.**
   - bundled CLI + stdio by default
   - `systemMessage.mode: "append"` by default
   - GitHub-hosted auth and models by default
   - session-level tools and MCP exposure before agent-private scoping
   - one session before multi-client or session-pool designs

5. **Load the smallest reference bundle that answers the next decision.**
   - If the first bundle is insufficient, read one adjacent reference, not the whole tree.
   - Keep `SKILL.md` steering-focused; let the reference files carry API detail.

## Decision rules

### Client transport and lifecycle

- Use default stdio client startup for local apps, prototypes, CLIs, and single-process services.
- Use `cliUrl` only when connecting to an already-running headless CLI service or another persistent server boundary.
- Never mix `cliUrl` with `useStdio`, `cliPath`, `githubToken`, or `useLoggedInUser`.
- Pass auth and environment through `githubToken` or `env`; never hardcode tokens or pass secrets through CLI args.

### Sessions and messaging

- Always supply `onPermissionRequest` on both `createSession()` and `resumeSession()`.
- Register `onUserInputRequest` only when the app should let the assistant ask the user questions.
- Use `sendAndWait()` for simple request/response turns.
- Use `send()` when you need streaming, progress tracking, queueing, steering, or explicit abort behavior.
- Set a stable `sessionId` only if you need resume, persistence, or cross-request continuity. Otherwise let the SDK generate it.
- Use `disconnect()` to preserve session state and release resources; use `deleteSession()` only for deliberate cleanup.

### Streaming and event handling

- If you need delta events, set `streaming: true`.
- Register `session.on()` handlers before `send()` or `sendAndWait()` when startup or delta events matter.
- Treat `session.idle` as the end-of-turn boundary.
- Keep event handlers fast; wrap async side effects with their own error handling.

### Tools

- Prefer a few well-named tools with strong schemas over many vague tools.
- Use `defineTool()` for TypeScript/Zod inference; keep tool names short, specific, and `snake_case`.
- Return `ToolResultObject` for expected failures or structured results the model should see.
- Throw only for truly unexpected failures; thrown details are not exposed to the model.

### Hooks

- Use hooks for policy, sanitization, argument rewriting, audit, and lightweight context injection.
- Keep hook code fast and deterministic; slow I/O in hooks adds latency to every tool call.
- If the logic is really orchestration, retry management, or business workflow, move it out of hooks and into the app or tool handler.

### Custom agents

- Add custom agents only when there are genuinely distinct roles with different prompts or tool surfaces.
- Write highly specific `description` fields; delegation quality depends on them.
- Restrict tools per agent when safety or specialization matters.
- Use `infer: false` for destructive or explicit-only agents.
- If a single session prompt plus tools already solves the task, do not invent custom agents.

### MCP integration

- Use session-level `mcpServers` for shared tools across the whole session.
- Use agent-private `mcpServers` only when one agent needs isolated external tools.
- Expose only the tools the model actually needs; avoid `*` unless breadth is intentional.
- When restricting access, use namespaced tool names like `<server>/<tool>`.
- This skill covers consuming MCP servers from a Copilot SDK app, not implementing the server itself.

### BYOK and model selection

- Use GitHub-hosted auth and models unless the user explicitly needs provider-owned billing, credentials, or model inventory.
- If the user only needs a specific Copilot-hosted model, call `listModels()` and set `model` before considering BYOK.
- When `provider` is set, `model` is mandatory.
- Re-provide provider credentials on every resume; BYOK credentials are not persisted.
- Be precise about provider shape:
  - OpenAI-compatible endpoints use `type: "openai"` and usually need `/v1`
  - native Azure OpenAI uses `type: "azure"` with host-only `baseUrl`
  - bearer tokens are static and must be refreshed by your app
- If the provider owns model discovery, use `onListModels` deliberately.

## Do this, not that

| Need | Do this | Not that | Route |
|---|---|---|---|
| Simple assistant turn | one session + `sendAndWait()` | custom agents or queued orchestration from the start | `references/sessions/create-and-configure.md` |
| Streaming output | `streaming: true` and handlers before send | expecting `assistant.message_delta` without streaming enabled | `references/events/streaming-patterns.md` |
| Permissions in automation | explicit `onPermissionRequest`; use `approveAll` only in trusted contexts | assuming the SDK has a default approval policy | `references/permissions/permission-handler.md` |
| User clarification | explicit `onUserInputRequest` with choice/freeform handling | assuming `ask_user` works without a handler | `references/permissions/user-input-handler.md` |
| Tool design | `defineTool()` + Zod + actionable results/errors | raw ad hoc tool objects or vague `run/process/do` names | `references/tools/define-tool-zod.md`, `references/tools/tool-results-and-errors.md` |
| Safety and policy | fast hooks or permission rules | long-running network or database work inside hooks | `references/hooks/pre-tool-use.md`, `references/permissions/permission-handler.md` |
| App-specific behavior | `systemMessage.mode: "append"` | `replace` unless you intentionally want to remove SDK guardrails | `references/sessions/system-messages.md` |
| Shared external tool access | session-level `mcpServers` | duplicating the same MCP config under every agent | `references/agents/mcp-servers.md`, `references/sessions/create-and-configure.md` |
| Delegation | precise custom agents with clear tool scopes | using custom agents as a substitute for ordinary prompt decomposition | `references/agents/custom-agents.md` |
| Resumable workflow | stable `sessionId`, `disconnect()`, `resumeSession()` | random session IDs or concurrent resumes with no locking | `references/sessions/persistence-and-resume.md` |
| Provider-owned model path | `provider` + exact `model` + env/token setup | mixing GitHub auth defaults with BYOK assumptions | `references/auth/byok-providers.md`, `references/auth/environment-variables.md` |

## Recovery paths when the abstraction is wrong

- **The design jumped straight to custom agents.** Collapse back to one session with tools and event handlers. Re-introduce custom agents only if there are distinct roles with different prompts or tool scopes.
- **Hooks are carrying business logic or slow async work.** Move that logic into the app layer or the tool handler. Keep hooks as fast interception points.
- **BYOK was chosen but the app really just needs Copilot-hosted models.** Remove `provider`, use the normal GitHub auth path, and choose a model from `listModels()`.
- **A local prototype started growing headless-service complexity.** Return to default stdio client setup until the app truly needs shared CLI state or multi-process access.
- **`systemMessage: { mode: "replace" }` broke tools or guardrails.** Switch back to `append` unless a pure LLM-as-API flow is explicitly intended.
- **MCP tools are missing or not callable.** Verify server `tools` exposure, auth headers or env, and namespaced tool names before changing prompts.
- **Resumed sessions behave inconsistently.** Re-check stable `sessionId`, re-provide permissions and provider config on resume, and add app-level locking if multiple workers can touch the same session.
- **Mid-turn correction is turning into prompt spam.** Use `mode: "immediate"` only for concise course corrections; otherwise abort and start a fresh turn.

## Start with these reading sets

- **First TypeScript app or local prototype** → `references/client/setup-and-options.md` + `references/sessions/create-and-configure.md` + `references/permissions/permission-handler.md`
- **Streaming chat or live UX** → `references/sessions/create-and-configure.md` + `references/events/streaming-patterns.md`
- **Custom tool-calling assistant** → `references/tools/define-tool-zod.md` + `references/tools/tool-results-and-errors.md` + `references/permissions/permission-handler.md`
- **Interactive or approval-heavy agent** → `references/permissions/user-input-handler.md` + `references/permissions/permission-handler.md` + `references/sessions/create-and-configure.md`
- **Policy-controlled agent or hook-based guardrails** → `references/hooks/pre-tool-use.md` + `references/permissions/permission-handler.md` + `references/sessions/system-messages.md`
- **Resumable or multi-request backend service** → `references/sessions/persistence-and-resume.md` + `references/patterns/backend-service.md` + `references/client/setup-and-options.md`
- **Queueing, steering, or plan/autopilot flows** → `references/patterns/steering-and-queueing.md` + `references/patterns/plan-autopilot-mode.md`
- **Custom agents with MCP-backed tools** → `references/agents/custom-agents.md` + `references/agents/mcp-servers.md` + `references/sessions/create-and-configure.md`
- **BYOK or provider-managed deployment** → `references/auth/byok-providers.md` + `references/auth/environment-variables.md` + `references/sessions/persistence-and-resume.md`

## Final reminder

Do not load every reference file. Pick the smallest path that matches the current Copilot SDK job, get one session working end-to-end, and expand only when the next decision truly needs more surface area.

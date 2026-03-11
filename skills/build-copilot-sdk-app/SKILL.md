---
name: build-copilot-sdk-app
description: Use skill if you are building or extending a TypeScript app with @github/copilot-sdk, including session flows, streaming, tools, hooks, custom agents, BYOK, or MCP-backed Copilot runtime integration.
---

# Build Copilot SDK App

Use this skill when the job is to build a real TypeScript/Node application around `@github/copilot-sdk`. Start with the smallest viable Copilot SDK shape, then add hooks, custom agents, MCP servers, persistence, or BYOK only when the task truly requires them.

## Trigger boundary

### Activate when

- The repo is TypeScript/Node and will import or change `@github/copilot-sdk`
- The task involves `CopilotClient`, `createSession`, `resumeSession`, `send`, `sendAndWait`, `joinSession`, session events, custom tools, hooks, `mcpServers`, `customAgents`, `provider`, `defineTool`, `approveAll`, or session RPC methods
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
| Tool-calling with raw JSON Schema | `Tool` object with inline `inputSchema` | Zod when schemas come from external spec or codegen | `references/tools/json-schema-tools.md`, `references/tools/tool-results-and-errors.md` |
| Overriding a built-in tool | `defineTool` + `overridesBuiltInTool: true` | registering a conflicting name without the override flag | `references/tools/override-builtin-tools.md`, `references/tools/define-tool-zod.md` |
| Interactive or approval-heavy agent | `onUserInputRequest` + permission rules + one session | assuming `ask_user` exists by default | `references/permissions/user-input-handler.md`, `references/permissions/permission-handler.md`, `references/sessions/create-and-configure.md` |
| Fine-grained permission routing | narrow on `kind` discriminant per permission request | blanket `approveAll` when only some kinds need auto-approval | `references/permissions/permission-kinds.md`, `references/permissions/permission-handler.md` |
| Policy, sanitization, audit, or per-tool guardrails | hooks + permission handler | giant system prompts or tool wrappers for everything | `references/hooks/pre-tool-use.md`, `references/permissions/permission-handler.md` |
| Post-tool result transformation or audit | `onPostToolUse` hook to redact, reshape, or log results | modifying tool handlers for cross-cutting audit concerns | `references/hooks/post-tool-use.md`, `references/hooks/pre-tool-use.md` |
| Prompt rewriting, expansion, or policy enforcement | `onUserPromptSubmitted` hook before the model sees the message | system prompt hacks or manual message munging | `references/hooks/user-prompt-submitted.md` |
| Session startup/teardown resources | `onSessionStart`/`onSessionEnd` lifecycle hooks | ad hoc init code scattered outside the session boundary | `references/hooks/session-lifecycle-hooks.md` |
| Error classification, monitoring, or retry | `onErrorOccurred` hook with error-type routing | wrapping every tool call in try/catch for monitoring | `references/hooks/error-handling-hook.md` |
| Distinct delegated roles | `customAgents` with precise descriptions and tool scopes | a custom agent for ordinary branching or prompt wording | `references/agents/custom-agents.md` |
| CLI extensions (custom tools, hooks, events via child process) | Node.js ES module extension forked by the CLI | in-process monkey-patching or CLI wrapper scripts | `references/agents/cli-extensions.md` |
| Reusable prompt modules loaded at session creation | Skills directory with `SKILL.md` per skill | duplicating prompt text across sessions manually | `references/agents/skills-system.md` |
| External tools via MCP | `mcpServers` with explicit server/tool exposure | building the MCP server in this task | `references/agents/mcp-servers.md` |
| Your own model/provider billing or credentials | `provider` + explicit `model` + provider-specific env/token setup | GitHub-hosted auth defaults or implicit model selection | `references/auth/byok-providers.md`, `references/auth/environment-variables.md` |
| GitHub OAuth token lifecycle | `githubToken` with PAT, OAuth app, or GitHub App token | hardcoded tokens or secrets in CLI args | `references/auth/github-oauth.md`, `references/auth/environment-variables.md` |
| Long-lived backend service or multi-request chat API | stable `sessionId` + `resumeSession()` + headless CLI only if sharing across requests/processes | random session IDs or per-request child CLI spawning | `references/sessions/persistence-and-resume.md`, `references/patterns/backend-service.md` |
| Long autonomous sessions that exceed context window | `infiniteSession` config with compaction thresholds | manually summarizing and restarting sessions | `references/sessions/infinite-sessions.md`, `references/sessions/create-and-configure.md` |
| Parallel agent execution within a session | fleet mode for decomposable independent tracks | sequential single-agent when work is parallelizable | `references/patterns/fleet-mode.md`, `references/patterns/backend-service.md` |
| Multiple clients observing or acting on the same session | multi-client broadcast with `joinSession()` | assuming events are private to the creating client | `references/patterns/multi-client.md`, `references/patterns/backend-service.md` |
| Autonomous iteration with fresh context per loop | Ralph loop: disk-state + fresh session + backpressure | keeping everything in one growing context window | `references/patterns/ralph-loop.md`, `references/patterns/backend-service.md` |
| Production scaling and isolation | choose isolation model (process, session, CLI) first | scaling without deciding isolation topology | `references/patterns/scaling.md`, `references/patterns/backend-service.md` |
| Session workspace file read/write/list | `session.rpc` workspace methods | direct filesystem access bypassing workspace boundary | `references/patterns/workspace-files.md`, `references/types/rpc-methods.md` |
| Client transport selection (stdio, socket, remote) | match transport to deployment model | mixing `cliUrl` with stdio flags | `references/client/transport-modes.md`, `references/client/setup-and-options.md` |
| Client health checks and lifecycle management | `getStatus()`, `getAuthStatus()`, connection state events | polling or guessing CLI readiness | `references/client/lifecycle-and-health.md`, `references/client/setup-and-options.md` |

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

- Use default stdio client startup for local apps, prototypes, CLIs, and single-process services. See `references/client/transport-modes.md` for the three transport options (stdio, socket, remote).
- Use `cliUrl` only when connecting to an already-running headless CLI service or another persistent server boundary.
- Never mix `cliUrl` with `useStdio`, `cliPath`, `githubToken`, or `useLoggedInUser`.
- Pass auth and environment through `githubToken` or `env`; never hardcode tokens or pass secrets through CLI args. For GitHub OAuth token types and scopes, see `references/auth/github-oauth.md`.
- Monitor client health with `getStatus()` and `getAuthStatus()`; react to `ConnectionState` changes. See `references/client/lifecycle-and-health.md`.

### Sessions and messaging

- Always supply `onPermissionRequest` on both `createSession()` and `resumeSession()`.
- Register `onUserInputRequest` only when the app should let the assistant ask the user questions.
- Use `sendAndWait()` for simple request/response turns.
- Use `send()` when you need streaming, progress tracking, queueing, steering, or explicit abort behavior.
- Set a stable `sessionId` only if you need resume, persistence, or cross-request continuity. Otherwise let the SDK generate it.
- Use `disconnect()` to preserve session state and release resources; use `deleteSession()` only for deliberate cleanup.
- For sessions that may exceed context limits, enable `infiniteSession` compaction. See `references/sessions/infinite-sessions.md`.

### Streaming and event handling

- If you need delta events, set `streaming: true`.
- Register `session.on()` handlers before `send()` or `sendAndWait()` when startup or delta events matter.
- Treat `session.idle` as the end-of-turn boundary.
- Keep event handlers fast; wrap async side effects with their own error handling.
- For detailed event categories, see the event reference routing table below.

### Tools

- Prefer a few well-named tools with strong schemas over many vague tools.
- Use `defineTool()` for TypeScript/Zod inference; keep tool names short, specific, and `snake_case`.
- Use raw JSON Schema (`references/tools/json-schema-tools.md`) when schemas come from OpenAPI specs, codegen, or external definitions.
- To replace a built-in tool, set `overridesBuiltInTool: true`. See `references/tools/override-builtin-tools.md`.
- Return `ToolResultObject` for expected failures or structured results the model should see.
- Throw only for truly unexpected failures; thrown details are not exposed to the model.

### Hooks

- Use hooks for policy, sanitization, argument rewriting, audit, and lightweight context injection.
- Keep hook code fast and deterministic; slow I/O in hooks adds latency to every tool call.
- `onPreToolUse` intercepts before execution; `onPostToolUse` transforms results after. See `references/hooks/post-tool-use.md`.
- `onUserPromptSubmitted` rewrites or filters user messages before the model sees them. See `references/hooks/user-prompt-submitted.md`.
- `onSessionStart`/`onSessionEnd` bracket session lifecycle for resource setup and teardown. See `references/hooks/session-lifecycle-hooks.md`.
- `onErrorOccurred` classifies and routes runtime errors. See `references/hooks/error-handling-hook.md`.
- If the logic is really orchestration, retry management, or business workflow, move it out of hooks and into the app or tool handler.

### Custom agents

- Add custom agents only when there are genuinely distinct roles with different prompts or tool surfaces.
- Write highly specific `description` fields; delegation quality depends on them.
- Restrict tools per agent when safety or specialization matters.
- Use `infer: false` for destructive or explicit-only agents.
- If a single session prompt plus tools already solves the task, do not invent custom agents.
- For CLI-level extensions that add tools and hooks as child processes, see `references/agents/cli-extensions.md`.
- For reusable prompt modules loaded at session creation, see `references/agents/skills-system.md`.

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

### Permissions

- Narrow permission decisions on `kind` discriminant before accessing metadata. See `references/permissions/permission-kinds.md` for all permission kinds and their fields.
- Use `approveAll` only in trusted/automated contexts; prefer per-kind routing in production.

## Do this, not that

| Need | Do this | Not that | Route |
|---|---|---|---|
| Simple assistant turn | one session + `sendAndWait()` | custom agents or queued orchestration from the start | `references/sessions/create-and-configure.md` |
| Streaming output | `streaming: true` and handlers before send | expecting `assistant.message_delta` without streaming enabled | `references/events/streaming-patterns.md` |
| Permissions in automation | explicit `onPermissionRequest`; use `approveAll` only in trusted contexts | assuming the SDK has a default approval policy | `references/permissions/permission-handler.md` |
| Per-kind permission routing | narrow on `kind`, then approve/deny per category | flat approve/deny logic ignoring permission kind | `references/permissions/permission-kinds.md`, `references/permissions/permission-handler.md` |
| User clarification | explicit `onUserInputRequest` with choice/freeform handling | assuming `ask_user` works without a handler | `references/permissions/user-input-handler.md` |
| Tool design | `defineTool()` + Zod + actionable results/errors | raw ad hoc tool objects or vague `run/process/do` names | `references/tools/define-tool-zod.md`, `references/tools/tool-results-and-errors.md` |
| Tool schema from external specs | raw JSON Schema `Tool` object with `inputSchema` | force-converting OpenAPI schemas to Zod | `references/tools/json-schema-tools.md` |
| Replacing a built-in tool | `defineTool` with `overridesBuiltInTool: true` | registering a same-name tool without the override flag | `references/tools/override-builtin-tools.md` |
| Safety and policy | fast hooks or permission rules | long-running network or database work inside hooks | `references/hooks/pre-tool-use.md`, `references/permissions/permission-handler.md` |
| Post-tool audit or redaction | `onPostToolUse` hook for result transformation | duplicating redaction logic in every tool handler | `references/hooks/post-tool-use.md` |
| Prompt augmentation or filtering | `onUserPromptSubmitted` hook | rewriting messages in the app layer after send | `references/hooks/user-prompt-submitted.md` |
| Session resource init/cleanup | `onSessionStart`/`onSessionEnd` lifecycle hooks | scattered init code outside session boundary | `references/hooks/session-lifecycle-hooks.md` |
| Error monitoring and retry | `onErrorOccurred` hook with error-type routing | wrapping every tool call in try/catch for telemetry | `references/hooks/error-handling-hook.md` |
| App-specific behavior | `systemMessage.mode: "append"` | `replace` unless you intentionally want to remove SDK guardrails | `references/sessions/system-messages.md` |
| Shared external tool access | session-level `mcpServers` | duplicating the same MCP config under every agent | `references/agents/mcp-servers.md`, `references/sessions/create-and-configure.md` |
| Delegation | precise custom agents with clear tool scopes | using custom agents as a substitute for ordinary prompt decomposition | `references/agents/custom-agents.md` |
| CLI-level extensibility | Node.js extension module forked by CLI | in-process patching or wrapper scripts around the CLI | `references/agents/cli-extensions.md` |
| Reusable prompt injection | skills loaded from `SKILL.md` directories at session creation | copy-pasting prompt text across sessions | `references/agents/skills-system.md` |
| Resumable workflow | stable `sessionId`, `disconnect()`, `resumeSession()` | random session IDs or concurrent resumes with no locking | `references/sessions/persistence-and-resume.md` |
| Long autonomous session | `infiniteSession` with compaction thresholds | manually summarizing and restarting when context fills | `references/sessions/infinite-sessions.md` |
| Provider-owned model path | `provider` + exact `model` + env/token setup | mixing GitHub auth defaults with BYOK assumptions | `references/auth/byok-providers.md`, `references/auth/environment-variables.md` |
| GitHub token auth | `githubToken` with correct token type and scopes | hardcoded tokens or secrets in CLI args | `references/auth/github-oauth.md` |
| Transport selection | match transport mode to deployment model | mixing stdio flags with `cliUrl` | `references/client/transport-modes.md`, `references/client/setup-and-options.md` |
| Client health monitoring | `getStatus()`, `getAuthStatus()`, connection state events | polling or guessing CLI readiness | `references/client/lifecycle-and-health.md` |
| Parallel agent execution | fleet mode for independent parallelizable tracks | sequential single-agent for decomposable work | `references/patterns/fleet-mode.md` |
| Multi-client session observation | `joinSession()` with broadcast-aware handlers | assuming events are private to the creating client | `references/patterns/multi-client.md` |
| Autonomous iteration loops | Ralph loop with disk-state and fresh context per iteration | growing one context window indefinitely | `references/patterns/ralph-loop.md` |
| Production scaling | choose isolation model first, then scale | scaling without deciding isolation topology | `references/patterns/scaling.md` |
| Workspace file operations | `session.rpc` workspace methods | direct filesystem access bypassing workspace boundary | `references/patterns/workspace-files.md` |

## Recovery paths when the abstraction is wrong

- **The design jumped straight to custom agents.** Collapse back to one session with tools and event handlers. Re-introduce custom agents only if there are distinct roles with different prompts or tool scopes.
- **Hooks are carrying business logic or slow async work.** Move that logic into the app layer or the tool handler. Keep hooks as fast interception points. See `references/hooks/post-tool-use.md` and `references/hooks/error-handling-hook.md` for correct hook scope.
- **BYOK was chosen but the app really just needs Copilot-hosted models.** Remove `provider`, use the normal GitHub auth path (`references/auth/github-oauth.md`), and choose a model from `listModels()`.
- **A local prototype started growing headless-service complexity.** Return to default stdio client setup (`references/client/transport-modes.md`) until the app truly needs shared CLI state or multi-process access.
- **`systemMessage: { mode: "replace" }` broke tools or guardrails.** Switch back to `append` unless a pure LLM-as-API flow is explicitly intended.
- **MCP tools are missing or not callable.** Verify server `tools` exposure, auth headers or env, and namespaced tool names before changing prompts.
- **Resumed sessions behave inconsistently.** Re-check stable `sessionId`, re-provide permissions and provider config on resume, and add app-level locking if multiple workers can touch the same session.
- **Mid-turn correction is turning into prompt spam.** Use `mode: "immediate"` only for concise course corrections; otherwise abort and start a fresh turn.
- **Context window is filling up in long sessions.** Enable `infiniteSession` compaction (`references/sessions/infinite-sessions.md`) or switch to a Ralph loop pattern (`references/patterns/ralph-loop.md`).
- **Scaling hit single-process limits.** Evaluate isolation patterns in `references/patterns/scaling.md`; consider fleet mode (`references/patterns/fleet-mode.md`) or multi-client architecture (`references/patterns/multi-client.md`).
- **Client connection drops or health is unknown.** Use `getStatus()`/`getAuthStatus()` and subscribe to connection state changes. See `references/client/lifecycle-and-health.md`.

## Type reference routing

When the task requires looking up exact SDK type signatures, property shapes, or method signatures, load the relevant type reference file:

| Need | Type reference file | Covers |
|---|---|---|
| Client setup, connection, model listing, lifecycle events | `references/types/client-types.md` | `CopilotClientOptions` (14 props), `ConnectionState`, `GetAuthStatusResponse`, `GetStatusResponse`, `ModelInfo`/`ModelCapabilities`/`ModelPolicy`/`ModelBilling`, `ReasoningEffort`, `SessionMetadata`, `SessionContext`, `SessionListFilter`, `SessionLifecycleEvent`, `ForegroundSessionInfo`, all 18 `CopilotClient` methods, `client.rpc` getter |
| Session config, messaging, MCP, agents, provider | `references/types/session-types.md` | `SessionConfig` (23 props), `ResumeSessionConfig`, `MessageOptions`, `SystemMessageConfig`, `ProviderConfig`, `InfiniteSessionConfig`, `MCPServerConfig` (local/remote), `CustomAgentConfig`, `AssistantMessageEvent`, all 11 `CopilotSession` methods, `session.rpc` getter (20 methods) |
| Tools, results, schemas, defineTool, approveAll | `references/types/tool-types.md` | `Tool<TArgs>`, `ToolHandler`, `ToolInvocation`, `ToolResultObject`, `ToolBinaryResult`, `ToolResult`, `ToolResultType`, `ZodSchema`, `ToolCallRequestPayload`, `ToolCallResponsePayload`, `defineTool()`, `approveAll` |
| Hooks — pre/post tool, prompt, session lifecycle, errors | `references/types/hook-types.md` | `SessionHooks`, `BaseHookInput`, all 6 hook Input/Output interfaces, all 6 handler type aliases |
| Session events — all 59 event types and data shapes | `references/types/event-types.md` | `SessionEvent` discriminated union, `SessionEventType`, `SessionEventPayload<T>`, `TypedSessionEventHandler<T>`, all 59 event types with data fields |
| RPC methods — client and session scoped | `references/types/rpc-methods.md` | 4 server RPC methods (`ping`, `models.list`, `tools.list`, `account.getQuota`), 20 session RPC methods, `PermissionRequestResult` 5-variant union |

## Event reference routing

When you need event-specific details beyond what `references/types/event-types.md` covers, load the category-specific event reference:

| Event category | Reference file | Covers |
|---|---|---|
| Agent hierarchy, skill invocations, slash commands | `references/events/agent-events.md` | subagent spawn/complete, skill invocation, command events |
| LLM response lifecycle, streaming text, reasoning, usage | `references/events/assistant-events.md` | `assistant.turn_start`, `assistant.message_delta`, `assistant.message`, reasoning, usage accounting |
| Hook execution and plan mode transitions | `references/events/hook-events.md` | hook lifecycle, multi-client coordination, plan mode events |
| Permission requests and resolution broadcasts | `references/events/permission-events.md` | `permission.requested`, `permission.completed`, broadcast behavior |
| Session state, compaction, handoffs, shutdown | `references/events/session-lifecycle-events.md` | `session.idle`, context changes, compaction, session shutdown |
| System messages, notifications, abort, queue changes | `references/events/system-events.md` | system-level infrastructure events |
| Tool execution lifecycle (request → execute → result) | `references/events/tool-events.md` | `tool.call_start`, `tool.call_end`, `toolCallId` correlation |
| User messages, askUser, elicitation input | `references/events/user-input-events.md` | user message events, askUser flow, form-based elicitation |

## Start with these reading sets

- **First TypeScript app or local prototype** → `references/client/setup-and-options.md` + `references/sessions/create-and-configure.md` + `references/permissions/permission-handler.md`
- **Streaming chat or live UX** → `references/sessions/create-and-configure.md` + `references/events/streaming-patterns.md` + `references/types/event-types.md`
- **Custom tool-calling assistant** → `references/tools/define-tool-zod.md` + `references/tools/tool-results-and-errors.md` + `references/types/tool-types.md`
- **Tool schemas from external specs** → `references/tools/json-schema-tools.md` + `references/tools/override-builtin-tools.md` + `references/types/tool-types.md`
- **Interactive or approval-heavy agent** → `references/permissions/user-input-handler.md` + `references/permissions/permission-handler.md` + `references/permissions/permission-kinds.md`
- **Policy-controlled agent or hook-based guardrails** → `references/hooks/pre-tool-use.md` + `references/hooks/post-tool-use.md` + `references/types/hook-types.md`
- **Full hook suite (prompt, lifecycle, errors)** → `references/hooks/user-prompt-submitted.md` + `references/hooks/session-lifecycle-hooks.md` + `references/hooks/error-handling-hook.md`
- **Resumable or multi-request backend service** → `references/sessions/persistence-and-resume.md` + `references/patterns/backend-service.md` + `references/client/setup-and-options.md`
- **Long autonomous sessions** → `references/sessions/infinite-sessions.md` + `references/patterns/ralph-loop.md` + `references/patterns/fleet-mode.md`
- **Production scaling and multi-client** → `references/patterns/scaling.md` + `references/patterns/multi-client.md` + `references/client/transport-modes.md`
- **Queueing, steering, or plan/autopilot flows** → `references/patterns/steering-and-queueing.md` + `references/patterns/plan-autopilot-mode.md` + `references/types/rpc-methods.md`
- **Workspace file operations** → `references/patterns/workspace-files.md` + `references/types/rpc-methods.md`
- **Custom agents with MCP-backed tools** → `references/agents/custom-agents.md` + `references/agents/mcp-servers.md` + `references/types/session-types.md`
- **CLI extensions and skills** → `references/agents/cli-extensions.md` + `references/agents/skills-system.md` + `references/agents/custom-agents.md`
- **BYOK or provider-managed deployment** → `references/auth/byok-providers.md` + `references/auth/environment-variables.md` + `references/types/session-types.md`
- **GitHub OAuth and token management** → `references/auth/github-oauth.md` + `references/auth/environment-variables.md` + `references/client/setup-and-options.md`
- **Client transport and health** → `references/client/transport-modes.md` + `references/client/lifecycle-and-health.md` + `references/types/client-types.md`
- **Event deep-dive for a specific category** → start with `references/types/event-types.md`, then load the category-specific file from the event reference routing table above
- **Type lookup or signature verification** → start with the specific type reference file from the type reference routing table above

## Final reminder

Do not load every reference file. Pick the smallest path that matches the current Copilot SDK job, get one session working end-to-end, and expand only when the next decision truly needs more surface area. When you need exact type signatures, use the type reference routing table above to load only the relevant type file. When you need event-specific details, use the event reference routing table to load only the relevant event category file.

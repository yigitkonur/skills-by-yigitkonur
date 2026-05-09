---
name: build-copilot-sdk-app
description: Use skill if you are building directly on @github/copilot-sdk for Copilot SDK sessions, tools, streaming, hooks, custom agents, or BYOK.
---

# Build Copilot SDK App

Build Node/TypeScript apps directly on `@github/copilot-sdk`, the GitHub Copilot SDK agent runtime. The SDK is public preview, so treat installed package types as the API contract and use docs for product/auth policy context.

## Trigger boundary

Use this skill only for applications that import `@github/copilot-sdk` and create Copilot SDK clients, sessions, tools, commands, hooks, custom agents, MCP-backed agents, streaming UIs, or BYOK provider sessions.

Do not use this skill for:

- LangChain.js or LangGraph TypeScript agents — use `build-langchain-ts-app`
- `mcp-use` `MCPAgent` applications — use `build-mcp-use-agent`
- Kernel browser automation via `@onkernel/sdk` — use `build-kernel-ts-sdk`
- Effect-TS applications without Copilot SDK — use `build-effect-ts-v3`
- Generic OpenAI, Vercel AI SDK, or provider-SDK chatbots that do not import `@github/copilot-sdk`

## Source-of-truth gate

Before writing version-sensitive code, check the selected package:

```bash
npm view @github/copilot-sdk version dist-tags engines --json
npm pack @github/copilot-sdk@latest
```

Source priority:

1. Installed `node_modules/@github/copilot-sdk/dist/*.d.ts`, or a freshly packed npm package, for TypeScript signatures.
2. The package `README.md` for package-specific examples.
3. Official GitHub Docs for public-preview status, availability, auth concepts, and BYOK policy.
4. These references only after freshness has been checked.

Audit baseline: on 2026-05-08, npm reported `latest = 0.3.0`, `prerelease = 1.0.0-beta.3`, and `engines.node = >=20.0.0`. Do not bake those in as permanent facts. Prefer the installed package engine over docs snippets when they disagree.

The package includes bundled CLI support via `@github/copilot`; a global `copilot` command is useful for interactive auth and external server workflows, but is not always a separate prerequisite for stdio clients.

## Quick start

For a deterministic scaffold:

```bash
bash scripts/scaffold-copilot-app.sh my-copilot-app
cd my-copilot-app
npm install
npm run typecheck
npm start
```

For an existing project:

```bash
npm pkg set type=module
npm pkg set scripts.start="tsx src/index.ts"
npm install @github/copilot-sdk tsx zod
bash path/to/scripts/check-copilot-auth.sh .
```

## Minimal GitHub-auth session

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient();

try {
  await client.start();
  const auth = await client.getAuthStatus();
  if (!auth.isAuthenticated) {
    throw new Error("Authenticate with Copilot CLI or set COPILOT_GITHUB_TOKEN / GH_TOKEN / GITHUB_TOKEN.");
  }

  const session = await client.createSession({
    model: process.env.COPILOT_MODEL ?? "gpt-5",
    onPermissionRequest: approveAll,
  });

  try {
    const response = await session.sendAndWait({ prompt: "What is 2 + 2?" });
    console.log(response?.data.content ?? "(no response)");
  } finally {
    await session.disconnect();
  }
} finally {
  await client.stop();
}
```

## Reference routing

| Need | Read |
|---|---|
| Client construction, stdio/TCP/external server, CLI path, lifecycle | `references/client-and-transport.md` |
| GitHub auth, `gitHubToken`, env tokens, BYOK providers, Azure endpoint split | `references/auth-and-byok.md` |
| Session lifecycle, `send`, `sendAndWait`, resume, compaction, `onEvent` | `references/sessions.md` |
| Streaming UI, early handlers, event catalog from `dist/generated/session-events.d.ts` | `references/events-and-streaming.md` |
| Hooks for prompt/tool/session/error interception | `references/hooks.md` |
| Custom tools, Zod/raw schemas, `skipPermission`, slash `commands`, handler errors | `references/tools-and-schemas.md` |
| Permission decisions, `approveAll`, user input, elicitation handlers | `references/permissions-and-user-input.md` |
| Custom agents, `defaultAgent`, agent-level MCP servers and skills, sub-agent events | `references/agents-mcp-skills.md` |
| Plan/autopilot, fleet mode, multi-client, backend service and scaling patterns | `references/advanced-patterns.md` |
| Exact interface names and selected type shapes | `references/types-reference.md` |
| Auth/package preflight helper | `scripts/check-copilot-auth.sh.md` |
| Minimal project scaffold helper | `scripts/scaffold-copilot-app.sh.md` |

## Non-negotiable rules

- Stay inside Copilot SDK. Route non-Copilot agent frameworks to the sibling skills above.
- Verify the installed package or freshly packed `latest` before using exact signatures.
- Use Node that satisfies `@github/copilot-sdk` `engines.node`; current baseline is Node 20+.
- Use `await client.start()` before `client.getAuthStatus()`; `createSession` can auto-start, but status calls require a connected client in current stable.
- Always pass `onPermissionRequest` on `createSession` and `resumeSession`.
- Spell GitHub token options as `gitHubToken` when current TypeScript types require it, even if a docs page shows `githubToken`.
- For BYOK, always pass both `provider` and `model`; current package docs say the SDK throws without `model`.
- Treat BYOK credentials as static key or static bearer-token auth unless current docs add a refresh API. Provider billing and rate limits apply.
- Use `approveAll` only for local demos or intentionally unattended tools. It approves file writes, shell commands, MCP calls, URL access, custom tools, and memory operations.
- Register event handlers before `send()`. Use `onEvent` when you must catch early session creation events.
- Use `onElicitationRequest` when the app must answer structured form prompts; event observation alone does not answer them.
- Keep event guidance generated from `dist/generated/session-events.d.ts`; do not hard-code event-count claims.
- Use Copilot SDK custom agents for Copilot sub-agent orchestration. Use LangGraph or `mcp-use` when the app is not built on Copilot SDK.
- Always clean up: `await session.disconnect()` before `await client.stop()` on script/server shutdown paths.
- Do not claim production readiness beyond current GitHub public-preview statements.

## Final checks

Report:

- Package version and dist-tag checked.
- Auth mode used: signed-in user, `gitHubToken`, env token, external CLI server, or BYOK.
- BYOK provider and `model`, when applicable.
- Files created or changed.
- Commands run: install, typecheck/test, start, scaffold/auth helpers.
- Verification rung actually reached.
- Runtime paths not exercised because auth or provider credentials were unavailable.

Verify:

- `npm run typecheck` or equivalent passes.
- Minimal `sendAndWait` or streaming path is exercised when credentials exist.
- `session.disconnect()` and `client.stop()` are present on shutdown paths.
- Examples compile against the selected package version.

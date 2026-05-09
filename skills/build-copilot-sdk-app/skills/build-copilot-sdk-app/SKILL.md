---
name: build-copilot-sdk-app
description: Use skill if you are building a TypeScript or Node app on @github/copilot-sdk with sessions, custom tools, hooks, agents, BYOK providers, or streaming events.
---

# Build Copilot SDK App

Build Node/TypeScript apps directly on `@github/copilot-sdk` — the GitHub Copilot SDK agent runtime. The package is in **public preview**, so the installed `dist/*.d.ts` files are the API contract, not the docs page.

## When to use

*Italicized phrases below match real triggers. If any one fits, the skill applies.*

- *importing `@github/copilot-sdk` or constructing `new CopilotClient(...)`*
- *creating `client.createSession({ model, onPermissionRequest })` or calling `session.sendAndWait`*
- *registering custom tools, slash `commands`, hooks (`onToolUse`, `onSessionStart`, etc.), or sub-agents*
- *streaming Copilot events (`session.onEvent`, `session-events.d.ts`) into a UI*
- *wiring BYOK providers (`provider` + `model`) — Anthropic, OpenAI, Azure, Bedrock, Vertex*
- *using `gitHubToken` / `COPILOT_GITHUB_TOKEN` / external `copilot` CLI as the auth path*
- *adding agent-level MCP servers or skills via Copilot SDK custom agents*
- *writing fleet-mode, multi-client, plan/autopilot, or backend-service patterns on Copilot SDK*

### Do NOT use when

- the project imports **LangChain.js / LangGraph TS** instead → use `build-langchain-ts-app`
- the project uses **`mcp-use` `MCPAgent`** → use `build-mcp-use-agent`
- the project uses **`@onkernel/sdk`** for browser automation → use `build-kernel-ts-sdk`
- the project is **generic OpenAI / Vercel AI SDK / Anthropic SDK** without `@github/copilot-sdk` → use a generic SDK skill, not this one

If `package.json` does not list `@github/copilot-sdk` and no source file imports from it, this skill is the wrong tool.

## Source-of-truth gate (run before writing version-sensitive code)

```bash
npm view @github/copilot-sdk version dist-tags engines --json
ls node_modules/@github/copilot-sdk/dist/*.d.ts || npm pack @github/copilot-sdk@latest
```

Source priority — in order:

1. Installed `node_modules/@github/copilot-sdk/dist/*.d.ts` (or freshly packed `latest`) for TypeScript signatures.
2. The package `README.md` for package-specific examples.
3. Official GitHub Docs for public-preview status, auth concepts, BYOK policy.
4. The `references/` files in this skill — only after freshness has been checked.

Audit baseline (2026-05-08): npm reported `latest = 0.3.0`, `prerelease = 1.0.0-beta.3`, `engines.node = >=20.0.0`. Do not bake these in. When the installed package and a docs snippet disagree, the installed package wins.

## Non-negotiable rules

These are the rules that break apps when ignored. Keep them at the top of mind.

| # | Rule | Why |
|---|---|---|
| 1 | Stay inside Copilot SDK; route other agent frameworks to sibling skills. | This skill assumes Copilot SDK semantics. |
| 2 | Use Node satisfying `engines.node` (currently `>=20`). | Older Node breaks `dist/*` imports. |
| 3 | `await client.start()` before `client.getAuthStatus()`. | `createSession` may auto-start, but status needs a connected client. |
| 4 | Always pass `onPermissionRequest` on `createSession` and `resumeSession`. | Without it, permission events block the loop. |
| 5 | Spell the GitHub token option as `gitHubToken` when the installed types require it. | Docs sometimes show `githubToken`; types win. |
| 6 | For BYOK, always pass both `provider` **and** `model`. | The SDK throws without `model`. |
| 7 | Treat BYOK credentials as static key/bearer — no refresh API today. | Provider billing & rate limits apply. |
| 8 | `approveAll` is for local demos only — it green-lights writes, shells, MCP, URLs, custom tools, memory. | Never ship it. |
| 9 | Register event handlers **before** `send()`; use `onEvent` for early session-creation events. | Late handlers miss early events. |
| 10 | Use `onElicitationRequest` to answer structured form prompts — observation alone does not respond. | Elicitation blocks until answered. |
| 11 | Generate event guidance from `dist/generated/session-events.d.ts`; never hard-code event counts. | The catalog changes between releases. |
| 12 | On shutdown: `await session.disconnect()` then `await client.stop()`. | Skipping leaks stdio/TCP handles. |
| 13 | Do not claim production readiness beyond GitHub's current public-preview statements. | Public preview = breaking changes expected. |

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

Read the reference file that matches the task. Each is self-contained and verified against the SDK's TypeScript surface.

| Task | Read |
|---|---|
| Construct `CopilotClient`, choose stdio/TCP/external-server transport, lifecycle (`start`/`stop`) | `references/client-and-transport.md` |
| Auth: `gitHubToken`, `COPILOT_GITHUB_TOKEN` / `GH_TOKEN`, BYOK providers, Azure endpoint split | `references/auth-and-byok.md` |
| Session lifecycle: `send`, `sendAndWait`, resume, compaction, `onEvent` | `references/sessions.md` |
| Streaming UI, early handlers, event catalog from `dist/generated/session-events.d.ts` | `references/events-and-streaming.md` |
| Hooks: prompt/tool/session/error interception | `references/hooks.md` |
| Custom tools, Zod or raw schemas, `skipPermission`, slash `commands`, handler errors | `references/tools-and-schemas.md` |
| Permission decisions: `approveAll`, user input, elicitation handlers | `references/permissions-and-user-input.md` |
| Custom agents, `defaultAgent`, agent-level MCP servers and skills, sub-agent events | `references/agents-mcp-skills.md` |
| Plan/autopilot, fleet mode, multi-client, backend service patterns | `references/advanced-patterns.md` |
| Exact interface names and selected type shapes from `dist/*.d.ts` | `references/types-reference.md` |

### Helper scripts (in `scripts/`)

| Script | Use for | Doc |
|---|---|---|
| `scripts/check-copilot-auth.sh` | Preflight: check installed package, Node version, auth env vars | `scripts/check-copilot-auth.sh.md` |
| `scripts/scaffold-copilot-app.sh` | Deterministic minimal Copilot SDK project scaffold | `scripts/scaffold-copilot-app.sh.md` |

## Final checks before reporting done

Report the following — explicitly, not implied:

- Package version + dist-tag actually checked.
- Auth mode used (signed-in user / `gitHubToken` / env token / external CLI server / BYOK).
- BYOK `provider` and `model` when applicable.
- Files created or changed.
- Commands run (install, typecheck/test, start, scaffold/auth helpers).
- Verification rung actually reached — do not imply rungs you did not hit.
- Runtime paths not exercised because credentials were unavailable.

Verify:

- `npm run typecheck` (or equivalent) passes.
- A minimal `sendAndWait` or streaming path runs when credentials exist.
- `session.disconnect()` and `client.stop()` are present on every shutdown path.
- Examples compile against the selected package version.

# Brainstorming a New MCP from Scratch

Interview flow the subagent runs **before** touching code or any other decision tree. Collects intent, converts it to an architecture sketch, picks a framework, and routes to the right companion skill. Run this whenever the user says "I want to build an MCP server" and the repo has no MCP yet.

## Decision Tree

```
START: User wants to build a new MCP server
|
+-- Q1: End-user task in one sentence?
|   +-- unclear / restates the API  --> pause; run design-phase.md question set first
|
+-- Q2: Does an official CLI / well-maintained SDK already cover it?
|   +-- YES --> read ../patterns/mcp-vs-cli.md; MCP may not be the primitive
|   +-- NO  --> continue
|
+-- Q3: Local or remote?
|   +-- Local stdio (user's machine, one process)
|   |   --> Official TS SDK v1 (stdio-canonical)
|   |   --> Install build-mcp-server-sdk-v1
|   +-- Remote HTTP
|       +-- New project, HTTP-first, want modern DX --> mcp-use server (install build-mcp-use-server)
|       +-- Mixed stdio + HTTP, widest compatibility --> Official TS SDK v1 (install build-mcp-server-sdk-v1)
|       +-- Willing to try beta, new project only    --> Official TS SDK v2 (read build-mcp-server-sdk-v2 SKILL.md first)
|
+-- Q4..Q12: auth, stateful, clients, tool count, destructive, distribution, advanced features, success metric
|
+-- OUTPUT: architecture sketch (template below). Request user approval before any code is written.
```

## Interview Questions (ask verbatim; adapt only to reference user-supplied context)

1. **User intent** — "Describe the outcome your users want, not endpoints. What is the end-user task this MCP enables in one sentence?"
2. **Target consumer** — "Who connects to this MCP? Solo developer, one internal team (<=10 people), B2B SaaS customers (scoped per tenant), or a public marketplace?"
3. **Underlying service** — "Does the system you're wrapping already have an official CLI (`gh`, `kubectl`, `aws`, `az`, `stripe`) or a well-maintained SDK? If yes, read `../patterns/mcp-vs-cli.md` first — MCP may not be the right primitive."
4. **Local vs remote** — "Is the MCP running on the user's machine (stdio, one process) or hosted somewhere (HTTP)? Almost everything new in 2026 is remote Streamable HTTP; stdio is local dev tools."
5. **Auth profile** — "How does the server know who the caller is? (a) no auth / single-user local, (b) static API key env var, (c) OAuth 2.1 + PKCE for multi-user, (d) OAuth + CIMD/DCR for public marketplace."
6. **Stateful or stateless** — "Does any tool need to remember state across calls within a session? If no, default to stateless — avoids session-management complexity."
7. **Target clients** — "Which MCP clients must this support? Claude Desktop/Code only, or cross-client (Cursor, Windsurf, VS Code)? Some features only work in VS Code — see `../patterns/client-compatibility.md`."
8. **Expected tool count** — "How many tools do you expect at launch? At 1 year? Over 20 = consider toolsets or a Codemode `search`/`execute` pair; see `tool-count.md` and `../patterns/mcp-vs-cli.md`."
9. **Destructive operations** — "Will any tool mutate external state, send messages, or delete data? Those need guard params or human-confirmation flows; see `../patterns/agentic-patterns.md`."
10. **Distribution** — "Where will this MCP live? Internal only, Smithery/Glama marketplace, Docker MCP Catalog, NPM, or no distribution (git clone)?"
11. **Advanced protocol features** — "Do you need sampling or elicitation? If yes, client support is uneven — see `../patterns/advanced-protocol.md` before committing."
12. **Success metric** — "How will you know this MCP is working 3 months from now? Tool-call success rate, task completion in <N steps, cost per session, user retention."

## Framework Picker

| Framework | Best for | Transport | stdio | OAuth | Maturity | Install command |
|---|---|---|---|---|---|---|
| **mcp-use server** | New remote MCP in TypeScript, HTTP-first, widgets/UI, modern DX | Streamable HTTP (native), SSE fallback | No — mcp-use is HTTP-only; use the official SDK if you need stdio | Built-in OAuth helpers | GA; default for new remote servers | `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-use-server` |
| **Official TS SDK v1** (`@modelcontextprotocol/sdk`) | stdio MCPs, local dev tools, Claude Desktop plugins, anything shipping as `npx` | stdio + Streamable HTTP | Yes — canonical stdio path | BYO or via wrapper (e.g. Cloudflare `workers-oauth-provider`) | GA, widely adopted | `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-server-sdk-v1` |
| **Official TS SDK v2 beta** (`@modelcontextprotocol/server`) | New projects willing to adopt the split-package v2 API; cleaner ergonomics | stdio + Streamable HTTP | Yes | Client-side only (server-side OAuth removed; use `better-auth`) | **Beta** — API may shift; not production-default. Read `build-mcp-server-sdk-v2` SKILL.md before picking | `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/build-mcp-server-sdk-v2` |
| **SKIP — use CLI / skills** | Agent already has a well-maintained CLI / SDK access; static guidance would suffice | N/A | N/A | N/A | N/A | See `../patterns/mcp-vs-cli.md` |

## Architecture-Sketch Template

After Q1-Q12, produce this sketch verbatim and ask the user to approve before any code is written.

```
# MCP Architecture Sketch — <project-name>

## Problem statement (1-2 sentences)
<end-user outcome, not API endpoints>

## User intents (1-3)
1. <intent 1>
2. <intent 2>
3. <intent 3>

## Tools (target count: <N>)
- <tool_name_1> — <one-line purpose>
- <tool_name_2> — <one-line purpose>

## Schema approach
<flat / nested / z.coerce / enum strategy — routes to ../patterns/schema-design.md>

## Response format
<text / YAML / TSV / structuredContent — routes to ../patterns/tool-responses.md>

## Auth
<none / API key / OAuth 2.1 + PKCE / OAuth + CIMD — routes to security-posture.md and ../patterns/security.md>

## Transport
<stdio / Streamable HTTP>

## Target clients
<Claude Desktop, Claude Code, Cursor, VS Code, ...>

## Framework choice
<mcp-use / official SDK v1 / v2 beta> — rationale:

## Distribution
<internal / Smithery / Docker Catalog / NPM / none> — routes to ../patterns/deployment-platforms.md

## Success metric (3 months out)
<measurable outcome>

## Next steps
1. User approves this sketch.
2. Install <companion skill name> (exact install command from the picker above).
3. After the first tool lands, run `../../SKILL.md` optimize flow against the prototype.
```

## Routing After This Tree

- Tool granularity and intent-based design → `design-phase.md`
- Tool count >10, progressive discovery, toolsets → `tool-count.md`
- Response format choice → `response-format.md`
- Auth / threat model depth → `security-posture.md`, `../patterns/security.md`, `../patterns/threat-catalog.md`
- Scaling and multi-server composition → `scaling.md`, `../patterns/composition.md`
- Production readiness → `production-readiness.md`, `../patterns/transport-and-ops.md`
- CLI / skills / bash would dominate → `../patterns/mcp-vs-cli.md`
- Client feature parity (sampling, elicitation, VS Code extras) → `../patterns/client-compatibility.md`, `../patterns/advanced-protocol.md`
- Destructive / approval flows → `../patterns/agentic-patterns.md`, `../patterns/prompt-gates.md`

## When to Re-evaluate

- Tool count crosses the next cliff (10 / 20 / 40 / 100) → revisit `tool-count.md` and `../patterns/mcp-vs-cli.md`.
- Target-client mix changes (Cursor or Windsurf added) → re-check `../patterns/client-compatibility.md`.
- Sampling or elicitation discovered mid-build → `../patterns/advanced-protocol.md`.
- Cost per session exceeds budget → `../patterns/context-engineering.md` and `../patterns/mcp-vs-cli.md` Pattern 3.
- Single-user scope grows to multi-tenant → `security-posture.md` and `../patterns/security.md` (OBO / CIMD).
- Trust incident or security concern → `../patterns/threat-catalog.md` + `../patterns/security.md`.
- Beta v2 framework API changes land → re-read `build-mcp-server-sdk-v2` SKILL.md; consider falling back to v1.

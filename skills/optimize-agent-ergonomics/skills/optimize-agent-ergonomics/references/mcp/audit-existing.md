# Mode A-MCP — Audit an existing MCP server

Audit an MCP server with the **Explore → Diagnose → Present → Optimize** ritual. Read the code before suggesting patterns. Tie every finding to a real file and line. Surface findings one at a time with options. Apply only after explicit user approval. Verify after applying. This file is the entry point for every MCP audit; the surface-agnostic ritual lives in `../common/audit-rhythm.md` — read it once, then return here for MCP specifics.

## Workflow

```
1. Explore — read the MCP code; map out tools, schemas, transport, auth, session model
2. Diagnose — classify findings by category; cross-link to the relevant decision tree
3. Present — surface findings one at a time with options
4. Optimize — apply only after the user picks; show diff; suggest verification
```

Skipping any phase corrupts the rest. **Pattern-fitting before reading the code is worse than no audit at all.**

## Phase 1 — Explore

Read the repo before asking the user a single question. Generic questions waste their time; cited questions earn answers.

### Locate the server

```bash
tree . -I node_modules --dirsfirst -L 3
rg -n -l "McpServer|FastMCP|server\\.tool|@tool|@mcp\\.tool|registerTool|Server\\(" . -g '!node_modules'
```

If `tree` is missing → `find . -maxdepth 3 -type d`. If `rg` is missing → `grep -R`.

If nothing MCP-shaped appears after searching repo root and the usual server directories (`src/`, `server/`, `servers/`, `app/`, `apps/`, `packages/`, `services/`, `mcp/`), stop. Report the missing prerequisite. **Do not invent a server to keep going.** If the user wants a new one, switch to `architect-new.md`.

If multiple MCP servers exist, stop and ask which is in scope. **Never blend findings across servers.**

### Read the files in this order

1. **Manifest** — `package.json`, `pyproject.toml`. Note SDK version (`@modelcontextprotocol/sdk` v1 vs `@modelcontextprotocol/server` v2 vs `mcp-use`), Zod version, Node engine.
2. **Entry point** — find the file with `new Server(...)` or `FastMCP(...)`. Note transport (`StdioServerTransport`, Streamable HTTP, SSE).
3. **Tool registrations** — every `server.tool(...)`, `@tool`, `registerTool`. Count them. Group by intent.
4. **Schemas** — Zod / JSONSchema / Pydantic. Flag any nesting >1 level, any param count >6.
5. **Error handling** — search for `isError`, `throw`, custom error envelopes.
6. **Transport / auth config** — OAuth, session middleware, CORS, rate limits.

```bash
rg -n "server\\.tool|@tool|registerTool|def .*tool|tool\\(" . -g '!node_modules'
rg -n -l "z\\.|inputSchema|BaseModel|Field\\(|pydantic|jsonschema" . -g '!node_modules'
rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
rg -n "isError|throwError|McpError|JSON-RPC" . -g '!node_modules'
rg -n "oauth|bearer|session|cors|rate.?limit" . -gi '!node_modules'
```

### Capture call traces if available

Ask the user for any of the following — they sharpen findings dramatically:
- An MCP Inspector session log.
- A `mcpc` invocation transcript.
- A production log for a representative session.
- An agent transcript that failed on a tool call.

If none are available, audit from code alone — but flag this as a context limitation in the findings.

## Phase 2 — Diagnose

Classify every observation into one of the categories below. Each category maps to a decision tree; the tree narrows to a specific pattern file. **Do not write the recommendation yet — the user picks.**

| Category | Symptoms | Route |
|---|---|---|
| Tool design | 30 tools, REST 1:1, vague names, agents pick wrong tool | `decision-trees/tool-count.md` → `patterns/tools.md` |
| Schema | Deeply nested input, parse failures, hallucinated params | `patterns/schema-design.md` |
| Response format | Raw API JSON, large payloads, no `structuredContent` | `decision-trees/response-format.md` → `patterns/tools.md` |
| Error semantics | Protocol errors for business logic; recovery hints missing | `decision-trees/error-strategy.md` → `patterns/error-handling.md` |
| Security | No auth on remote; user tokens forwarded; SSRF; PII leaked | `decision-trees/security-posture.md` → `patterns/security.md`, `patterns/auth-identity.md`, `patterns/threat-catalog.md` |
| Scaling | One process under load; no caching; long-running blocking calls | `decision-trees/scaling.md` → `patterns/transport-and-ops.md`, `patterns/session-and-state.md`, `patterns/caching-economics.md` |
| Production-readiness | No tests; no health endpoint; no telemetry; SSE on remote | `decision-trees/production-readiness.md` → `patterns/transport-and-ops.md`, `patterns/testing.md` |
| Advanced protocol | Sampling / elicitation silently dropped on non-supporting clients | `patterns/advanced-protocol.md`, `patterns/client-compatibility.md` |
| Distribution | Publishing to v0 of the official registry; no namespacing | `patterns/registry-and-distribution.md` |

Findings should cite specific files and line numbers. Severity is your call: **Critical** (security, data loss, prod failure), **High** (agent-blocking ergonomics), **Medium** (cost or token waste), **Low** (style, polish).

## Phase 3 — Present

Surface findings **one at a time** in severity order. Wait for the user's decision before moving on. Format:

```
### Finding [N]: [Title]
Dimension: [category]   Severity: Critical / High / Medium / Low
File(s): path/to/file.ts:line

Current state: [their actual code snippet]
Issue: [why it's suboptimal — reference the pattern]
Options:
  - A (recommended): [description + tradeoff]
  - B: [description + tradeoff]
  - C (minimal change): [description + tradeoff]
Should I apply this? (yes / no / show me option X first)
```

Rules:
- Quote real code, not hypotheticals.
- Reference the pattern file that backs the recommendation.
- Offer ≥2 options; mark one as recommended; one should be a minimal change so the user can opt for cheap relief.
- Do not stack findings. One at a time.
- If the user is unavailable for follow-up, switch to **draft mode**: surface the full prioritized finding set with explicit assumptions, but **do not apply anything**.

## Phase 4 — Optimize

Only after explicit user approval:

1. Show the diff before writing it.
2. Apply the edit.
3. Suggest a verification step. Default options:
   - MCP Inspector against the modified tool.
   - `test-by-mcpc-cli` against the live server.
   - A unit test the audit added or revised.
4. Move to the next finding.

Verification is non-negotiable. Mode A ends with all approved findings applied **and** verified — not with a list of edits the user has to test on their own.

## The 15 common MCP pitfalls

Use this as the diagnostic checklist during Phase 1 + 2.

| # | Pitfall | Fix routes to |
|---|---|---|
| 1 | Wrapping every REST endpoint as a tool (1:1 surface) | `patterns/tools.md` (intent-based design) |
| 2 | Deeply nested JSON schemas (>1 level) | `patterns/schema-design.md` |
| 3 | Returning raw API JSON | `patterns/tools.md` (response shape) |
| 4 | Throwing protocol errors for business failures | `decision-trees/error-strategy.md`, `patterns/error-handling.md` |
| 5 | No input validation server-side | `patterns/security.md` |
| 6 | Eagerly registering 20–30+ tools | `decision-trees/tool-count.md`, `patterns/progressive-discovery.md` |
| 7 | Vague tool descriptions | `patterns/tools.md` (descriptions section), `../common/descriptions-as-prompts.md` |
| 8 | No tests before production | `patterns/testing.md` |
| 9 | Using SSE for new remote deployments | `patterns/transport-and-ops.md` (Streamable HTTP only) |
| 10 | Ignoring session cleanup on disconnect | `patterns/session-and-state.md` |
| 11 | Invalidating provider prompt cache on every turn | `patterns/caching-economics.md` |
| 12 | Assuming every client supports sampling / elicitation / roots | `patterns/advanced-protocol.md`, `patterns/client-compatibility.md` |
| 13 | Forwarding user tokens to upstream APIs | `patterns/auth-identity.md` (OBO with audience check) |
| 14 | Publishing to v0 of the official registry | `patterns/registry-and-distribution.md` |
| 15 | Picking a deployment platform before counting cold starts or session needs | `patterns/transport-and-ops.md` |

## Per-category exploration commands

Run only the ones relevant to the categories you suspect.

### Tool design

```bash
# Count tools
rg -c "server\\.tool\\(|@tool|registerTool" --no-filename . -g '!node_modules' | paste -sd+ | bc 2>/dev/null

# Inspect tool names and shapes
rg -n "server\\.tool\\(" -A 4 . -g '!node_modules' | head -200
```

### Schema depth

```bash
# Find deeply nested Zod
rg -n "z\\.object\\(\\{[^}]*z\\.object" . -g '!node_modules'

# Pydantic deep nesting
rg -n "BaseModel" -A 30 . -g '!node_modules' | rg -n "List\\[|Dict\\[|: List|: Dict"
```

### Error model

```bash
# Look for protocol error abuse
rg -n "throw new Error|raise.*Exception|JSON-RPC|code:.*-32" . -g '!node_modules'

# Confirm isError usage
rg -n "isError" . -g '!node_modules'
```

### Security

```bash
# Auth in code
rg -n "oauth|bearer|authoriz|api[_-]?key" -i . -g '!node_modules'

# SSRF / private IPs
rg -n "fetch\\(|axios\\.get|http\\.get|requests\\.get" . -g '!node_modules' | head -50
rg -n "127\\.0\\.0\\.1|localhost|10\\.\\d|192\\.168" . -g '!node_modules'

# Token forwarding
rg -n "Authorization.*\\$\\{|headers\\[.Authorization.\\]" . -g '!node_modules'
```

### Transport and ops

```bash
# Detect SSE on remote
rg -n "SSEServerTransport|text/event-stream" . -g '!node_modules'

# Health endpoints
rg -n "/health|/healthz|/readiness|/liveness" . -g '!node_modules'

# Rate limits
rg -n "rate.?limit|throttle|bucket" -i . -g '!node_modules'
```

## Diagnose questions to ask the user

Once the code map is in your head, ask 2–3 cited questions. Examples:

- *"`packages/customer-mcp/tools/search.ts:42` — `search_users` takes 14 parameters including `filters.dateRange.start`. Are all 14 used in practice, or are most optional?"*
- *"`server.ts:88` — the `delete_record` tool throws `McpError` on a missing ID. Should that be `isError: true` with a recovery hint instead?"*
- *"`tools/list.ts:12` registers 31 tools at startup. What is the model running this — Claude, GPT-4, Gemini? The sweet-spot caps differ per model."*
- *"No `/health` endpoint found. Is this server deployed behind a load balancer? If yes, the LB has no readiness signal."*

## Anti-patterns during the audit

- **Pattern-fitting without reading.** Reciting "use progressive discovery" before counting actual tools is malpractice.
- **Bulk recommendations.** Walls of findings overwhelm; the user accepts none.
- **Skipping verification.** "It will work" is not verification.
- **Auditing two servers in one pass.** Findings blend; recommendations conflict.
- **Asking generic questions.** "How do you handle errors?" is bad. "On line 42, `delete_record` throws `McpError` — was that intentional?" is good.
- **Ignoring the threat model on a remote server.** A remote MCP without auth is a finding all by itself.
- **Treating thresholds as verdicts.** Tool count, parameter count, latency are diagnostic cues. The user's context might justify the deviation — surface it, then let them decide.
- **Forgetting to verify after applying.** The audit ends with a green test, not a green diff.

## Cross-links

- The universal Explore → Diagnose → Present → Optimize ritual: `../common/audit-rhythm.md`.
- The surface-agnostic principles every audit applies: `../common/output-contracts.md`, `../common/error-strategy.md`, `../common/descriptions-as-prompts.md`.
- The CLI counterpart for an analogous audit on a CLI tool: `../cli/audit-checklist.md`.

## When to escalate to a redesign

If the audit surfaces a foundational mistake — wrong surface (CLI would have been better; route to `../common/decide-surface.md`), wrong SDK choice (v2 beta can't ship to the user's clients), wrong transport (SSE on a 2026 deploy) — stop the optimization pass. Surface that finding alone, give the user the redesign option, and only resume incremental optimization if they accept the patch path.

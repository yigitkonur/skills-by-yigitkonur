---
name: optimize-mcp-server
description: Use skill if you are optimizing, auditing, or enhancing an MCP server's tool quality, error handling, security, context efficiency, or production readiness for any MCP SDK.
---

# MCP Server Optimization Patterns

Evaluate and enhance any MCP server — FastMCP, mcp-use, official SDK, or custom — against 113 battle-tested patterns across 15 quality dimensions.

## How This Skill Works

This skill does NOT apply patterns automatically. It follows a strict exploration-first protocol:

1. **Explore** — Read the user's codebase to understand their MCP server architecture
2. **Diagnose** — Identify optimization opportunities across 15 quality dimensions
3. **Present** — Show findings as critical decisions with options and trade-offs
4. **Optimize** — Only after user approval, provide specific code changes

**Prerequisite:** This skill requires a real MCP server codebase. If exploration cannot find an MCP server entry point, tool registration, schema, or transport after searching the repo root and the most likely server directories surfaced by the tree (`src/`, `server/`, `servers/`, `app/`, `apps/`, `packages/`, `services/`, `mcp/`), stop and report the missing prerequisite. Do not invent a server just to continue the audit.

## Phase 1: Explore the Codebase

Before asking a single question, understand what exists. Run these explorations:

```bash
# Map the project structure
tree . -I node_modules --dirsfirst -L 3

# Find MCP server entry points
rg -n -l "McpServer|FastMCP|server\\.tool|@tool|@mcp\\.tool|registerTool|Server\\(" . -g '!node_modules'

# Find tool definitions
rg -n "server\\.tool|@tool|registerTool|def .*tool|tool\\(" . -g '!node_modules'

# Count tools
rg -n "server\\.tool|@tool|registerTool|def .*tool|tool\\(" . -g '!node_modules'

# Find schema definitions (Zod, JSON Schema, Pydantic)
rg -n -l "z\\.|inputSchema|BaseModel|Field\\(|pydantic|jsonschema" . -g '!node_modules'

# Check error handling patterns
rg -n "isError|throw|raise|catch|except" . -g '!node_modules' | head -30

# Check transport configuration
rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
```

If `tree` is unavailable, replace it with `find . -maxdepth 3 -type d | sort`. If `rg` is unavailable, use `grep -R` with the same repo-root scope.

After the search pass, read files in this order:
- package manifests and runtime config (`package.json`, `pyproject.toml`, lockfiles, env examples) to identify SDK, entry command, and deployment shape
- MCP server entry points and bootstrapping files
- tool registration and handler files
- schema/model definitions and validation helpers
- transport, auth, and deployment config files

If you find multiple MCP servers or packages, stop after inventory and scope them before diagnosing:
- list each candidate server with its root path, SDK, transport, and rough tool count
- ask the user which server is in scope, unless they explicitly asked for a repo-wide audit
- do not merge findings across multiple servers into one blended assessment

If those searches return no MCP server signals, stop with a prerequisite report:
- where you searched
- what server indicators were absent
- what file(s) or directory path the user needs to provide

## Phase 2: Diagnostic Questions

After exploring, ask targeted questions based on what you found. Do NOT ask generic questions — reference specific files and patterns you discovered.

If the user is unavailable for follow-up, you may produce **draft findings** with explicit assumptions and 2-3 option sets, but you still must not apply any optimization until the user approves a concrete option.

**Template** (adapt based on what you found):

```
I explored your MCP server and found:
- [X] tools defined in [files]
- Schemas use [flat/nested] structure with [Zod/Pydantic/raw JSON Schema]
- Error handling: [isError pattern / throw pattern / mixed]
- Transport: [stdio/HTTP/SSE]

Based on this, I have questions about [2-3 specific areas]:

1. [Question referencing a specific file/pattern you found]
   Example: "In `packages/customer-mcp/tools/search.ts:42`, your `search_users` tool accepts 14 parameters
   including nested `filters.dateRange.start`. Are all 14 params used in most calls,
   or are many optional?"

2. [Question about their deployment/usage context]
   Example: "You're using stdio transport — is this local-only, or do you need to
   support multiple concurrent clients?"

3. [Question about their pain points]
   Example: "I see no error recovery guidance in your tool responses. Are you seeing
   agents retry failed calls without improving their approach?"
```

## Phase 3: Optimization Assessment

After the user answers, or after you have stated assumptions for draft mode, evaluate their server against the relevant dimensions. Present findings as a prioritized list of critical decisions.

Only raise a finding when you can tie it to actual code evidence, stated deployment context, or an explicit assumption. The thresholds in the reference docs are diagnostic cues, not automatic defects. If the context needed to judge a pattern is missing, ask about it first or mark the finding as a draft assumption.

**Format each finding as:**

````
### Finding [N]: [Title]
**Dimension**: [which of 15 categories]
**Severity**: Critical / High / Medium / Low
**File(s)**: `path/to/file.ts:line`

**Current state** (what you found in their code):
```[language]
// Their actual code snippet
```

**Issue**: [Why this is suboptimal — reference the specific pattern]

**Options**:
- **Option A** [recommended]: [description + trade-off]
- **Option B**: [description + trade-off]
- **Option C** (minimal change): [description + trade-off]

**Should I optimize this?** (yes / no / show me the code for option [X] first)
````

Interactive mode: present findings one at a time, starting with the highest severity, and wait for user decision before moving to the next.

Draft mode when the user is unavailable: present the full prioritized finding set in one pass, label every assumption clearly, and stop before Phase 4.

## Phase 4: Apply Optimization

Only after explicit user approval. For each approved optimization:

1. Show the exact diff (before → after)
2. Explain what changes and why
3. Apply the change
4. Suggest a verification step:
   ```
   To verify this optimization works:
   - Run: npx @modelcontextprotocol/inspector@latest
   - Call the modified tool with [test input]
   - Check that [expected behavior]
   ```

## Decision Tree — What Aspect Needs Optimization?

```
What aspect of your MCP server needs optimization?
│
├── Tool interface quality
│   ├── Tools feel like API wrappers ────────── references/patterns/tool-design.md
│   ├── Models pick wrong tools ─────────────── references/patterns/tool-descriptions.md
│   └── Responses don't guide next action ───── references/patterns/tool-responses.md
│
├── Input/output reliability
│   ├── Schema parse failures ───────────────── references/patterns/schema-design.md
│   ├── Errors don't help model recover ─────── references/patterns/error-handling.md
│   └── Response format choice ──────────────── references/decision-trees/response-format.md
│
├── Security posture
│   ├── Prompt injection vectors ────────────── references/patterns/security.md
│   └── Full security audit ─────────────────── references/decision-trees/security-posture.md
│
├── Context & performance
│   ├── Context window exhaustion ───────────── references/patterns/context-engineering.md
│   ├── Too many tools (20+) ────────────────── references/decision-trees/tool-count.md
│   ├── Progressive discovery needed ────────── references/patterns/progressive-discovery.md
│   └── Transport bottlenecks ───────────────── references/decision-trees/production-readiness.md
│
├── Architecture
│   ├── Multi-server coordination ───────────── references/patterns/composition.md
│   ├── Workflow ordering ───────────────────── references/patterns/agentic-patterns.md
│   ├── Scaling decisions ───────────────────── references/decision-trees/scaling.md
│   └── Response steering ──────────────────── references/patterns/prompt-gates.md
│
└── Operations & testing
    ├── Testing coverage ────────────────────── references/patterns/testing.md
    ├── Session/state management ────────────── references/patterns/session-and-state.md
    ├── Production readiness ────────────────── references/patterns/transport-and-ops.md
    └── Resources/prompts usage ─────────────── references/patterns/resources-and-prompts.md
```

## Quick Reference Card

| You want to...                        | Start here                                                                                       |
|---------------------------------------|--------------------------------------------------------------------------------------------------|
| Evaluate tool interface quality       | `references/patterns/tool-design.md` then `references/patterns/tool-descriptions.md`             |
| Fix schema parse failures             | `references/patterns/schema-design.md` then `references/decision-trees/design-phase.md`          |
| Improve error recovery                | `references/decision-trees/error-strategy.md` then `references/patterns/error-handling.md`       |
| Harden security posture               | `references/decision-trees/security-posture.md` then `references/patterns/security.md`           |
| Reduce context/token usage            | `references/patterns/context-engineering.md`                                                     |
| Manage 20+ tools                      | `references/decision-trees/tool-count.md` then `references/patterns/progressive-discovery.md`    |
| Optimize tool responses               | `references/patterns/tool-responses.md` then `references/decision-trees/response-format.md`      |
| Evaluate agent workflows              | `references/patterns/agentic-patterns.md` then `references/patterns/prompt-gates.md`             |
| Assess multi-server architecture      | `references/decision-trees/scaling.md` then `references/patterns/composition.md`                 |
| Validate with tests                   | `references/patterns/testing.md`                                                                 |
| Check production readiness            | `references/decision-trees/production-readiness.md` then `references/patterns/transport-and-ops.md` |
| Review resources and prompts usage    | `references/patterns/resources-and-prompts.md`                                                   |
| Audit session/state management        | `references/patterns/session-and-state.md`                                                       |

## Common Pitfalls

| #  | Pitfall                                          | What goes wrong                                               | Fix                                                                                      |
|----|--------------------------------------------------|---------------------------------------------------------------|------------------------------------------------------------------------------------------|
| 1  | Wrapping every REST endpoint as a tool           | Too many tools, LLM confused                                  | Design around user intent (`references/patterns/tool-design.md`)                         |
| 2  | Deeply nested JSON schemas                       | LLM generates malformed parameters                            | Flatten to max 1 level, under 6 params (`references/patterns/schema-design.md`)          |
| 3  | Returning raw API JSON as tool response          | Wastes tokens, LLM misinterprets fields                       | Curate and summarize responses (`references/patterns/tool-responses.md`)                 |
| 4  | Throwing protocol-level errors for tool failures | LLM cannot reason about the error or retry                    | Use `isError` in result content (`references/patterns/error-handling.md`)                |
| 5  | No input validation                              | Prompt injection, crashes on bad input                        | Validate all inputs server-side (`references/patterns/security.md`)                      |
| 6  | Registering 30+ tools at once                    | Context window bloat, poor tool selection                     | Use progressive discovery (`references/patterns/progressive-discovery.md`)               |
| 7  | Vague tool descriptions                          | LLM picks the wrong tool or misuses parameters                | Write descriptions as prompt engineering (`references/patterns/tool-descriptions.md`)    |
| 8  | No tests before production                       | Silent regressions, broken schemas                            | Add tool-level and integration tests (`references/patterns/testing.md`)                  |
| 9  | Using SSE for new remote deployments             | Will break when SSE support is removed                        | Use Streamable HTTP (`references/patterns/transport-and-ops.md`)                         |
| 10 | Ignoring session cleanup                         | Memory leaks, stale state across conversations                | Implement session lifecycle management (`references/patterns/session-and-state.md`)      |

## Reference Routing Table

Complete mapping of every reference file to its use case.

### Pattern Files

| File                                              | Read when...                                                                  |
|---------------------------------------------------|-------------------------------------------------------------------------------|
| `references/patterns/tool-design.md`              | Evaluating tool granularity, checking intent-based design, auditing naming     |
| `references/patterns/tool-descriptions.md`        | Diagnosing tool selection issues, improving description quality                |
| `references/patterns/tool-responses.md`           | Optimizing what tools return, choosing output format, reducing token usage     |
| `references/patterns/schema-design.md`            | Fixing schema parse failures, reducing required params, flattening schemas    |
| `references/patterns/error-handling.md`            | Improving error recovery, fixing retry loops, adding circuit breakers         |
| `references/patterns/security.md`                 | Auditing injection vectors, adding auth, sandboxing, hardening                |
| `references/patterns/context-engineering.md`       | Diagnosing token budget issues, optimizing context window usage               |
| `references/patterns/progressive-discovery.md`     | Managing 20+ tools, implementing dynamic tool loading                         |
| `references/patterns/agentic-patterns.md`          | Evaluating agent loops, multi-step workflows, checking ordering constraints   |
| `references/patterns/composition.md`               | Assessing multi-server setups, gateway patterns, server federation            |
| `references/patterns/prompt-gates.md`              | Auditing tool response authority, adding approval workflows, guardrails       |
| `references/patterns/resources-and-prompts.md`     | Checking resource/prompt utilization, evaluating data exposure strategy       |
| `references/patterns/session-and-state.md`         | Auditing session lifecycle, diagnosing state leaks, checking cleanup          |
| `references/patterns/testing.md`                   | Setting up eval-driven development, regression testing, CI integration        |
| `references/patterns/transport-and-ops.md`         | Evaluating transport choice, deployment config, monitoring, connection mgmt   |

### Decision Tree Files

| File                                               | Read when...                                                                 |
|----------------------------------------------------|------------------------------------------------------------------------------|
| `references/decision-trees/design-phase.md`        | Evaluating initial architecture decisions, cross-model schema portability     |
| `references/decision-trees/tool-count.md`          | Assessing how many tools to expose and how to organize them                  |
| `references/decision-trees/error-strategy.md`      | Choosing between error-handling approaches (fail-fast, retry, fallback)      |
| `references/decision-trees/security-posture.md`    | Evaluating threat model and choosing security measures                       |
| `references/decision-trees/scaling.md`             | Assessing growth plans, multi-server setups, load distribution               |
| `references/decision-trees/production-readiness.md`| Running pre-deploy checklist, evaluating operational readiness                |
| `references/decision-trees/response-format.md`     | Choosing between text, structured data, or mixed-content responses           |

## Guardrails

When applying these patterns, follow these rules:

- **Explore before asking.** Run tree/grep/read on the codebase before asking any questions. Your questions must reference specific files and patterns you found.
- **Ask before optimizing.** Never apply a pattern without presenting it as a finding with options and getting explicit user approval.
- **In interactive mode, one finding at a time.** Present findings by severity and wait for user decision before the next.
- **Use draft mode only when follow-up is unavailable.** In draft mode, assumptions must be explicit and no code changes are applied.
- **Show real code.** Every finding must reference the user's actual code with file paths and line numbers — never hypothetical examples.
- **Scope one server at a time.** If a repo contains multiple MCP servers, inventory them first and ask which one is in scope unless the user requested a repo-wide comparison.
- **Treat thresholds as heuristics, not verdicts.** Tool-count, parameter-count, and latency guidance must be grounded in the observed code and target deployment, not applied mechanically.
- **Verify after applying.** Every optimization gets a verification step (MCP Inspector, test command, or manual check).
- **Do not create one tool per API endpoint.** Map tools to user intents. If tool names mirror REST routes, the design needs rethinking.
- **Do not use deeply nested schemas.** If a parameter requires more than one level of nesting, restructure. LLMs generate flat structures far more reliably.
- **Do not return raw upstream API responses.** Always curate, summarize, and format tool output for LLM consumption.
- **Do not use protocol-level errors for business logic failures.** Reserve protocol errors for transport and framework issues only.
- **Do not register all tools eagerly when you have 20+.** Use progressive discovery to load tools on demand.
- **Do not skip input validation.** Every tool parameter must be validated server-side. Never trust LLM-generated input.
- **Do not use SSE for new remote deployments.** SSE is deprecated. Use Streamable HTTP.
- **Do not ignore tool description quality.** Descriptions are the primary mechanism the LLM uses to select tools. Treat them as prompt engineering.
- **Do not store sensitive data in tool responses.** Anything returned from a tool enters the LLM context and may surface in outputs.
- **Do not deploy without tests.** At minimum, test that each tool handles valid input, invalid input, and upstream failures correctly.

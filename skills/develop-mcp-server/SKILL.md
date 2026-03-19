---
name: develop-mcp-server
description: Use skill if you are optimizing or improving an MCP server's tool design, error handling, security, or production readiness with battle-tested patterns for any MCP SDK.
---

# MCP Server Optimization Patterns

This skill helps you evaluate and optimize MCP servers against 15 quality dimensions. Whether you're using FastMCP, mcp-use, the official TypeScript/Python SDK, or any other MCP framework, these patterns apply universally. Each dimension has specific anti-patterns to detect, decision trees to navigate, and proven patterns to apply.

113 battle-tested patterns. 7 decision trees. Framework-agnostic.

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

## Main Decision Tree

Identify what aspect of the MCP server needs optimization, then follow the corresponding branch.

```
What aspect of your MCP server needs optimization?
│
├── Tool interface quality
│   ├── Tools feel like API wrappers, not user intents ─── references/patterns/tool-design.md
│   ├── Models pick wrong tools or misuse params ──────── references/patterns/tool-descriptions.md
│   └── Responses don't guide the model's next action ──── references/patterns/tool-responses.md
│
├── Input/output reliability
│   ├── Schema parse failures or type mismatches ──────── references/patterns/schema-design.md
│   │   └── Need cross-model portability? ──────────────── references/decision-trees/design-phase.md
│   ├── Errors don't help the model recover ────────────── references/patterns/error-handling.md
│   │   └── Agents stuck in retry loops? ───────────────── references/decision-trees/error-strategy.md
│   └── Choosing response format (JSON/YAML/TSV) ──────── references/decision-trees/response-format.md
│
├── Security posture
│   ├── Prompt injection via tool responses ────────────── references/patterns/security.md
│   ├── Overprivileged service accounts ────────────────── references/patterns/security.md
│   └── Full security evaluation ───────────────────────── references/decision-trees/security-posture.md
│
├── Context & performance
│   ├── Context window filling up too fast ─────────────── references/patterns/context-engineering.md
│   ├── Too many tools (20+) degrading accuracy ────────── references/decision-trees/tool-count.md
│   ├── Need progressive tool discovery ────────────────── references/patterns/progressive-discovery.md
│   └── Transport/throughput bottlenecks ───────────────── references/decision-trees/production-readiness.md
│
├── Architecture
│   ├── Multi-server coordination ──────────────────────── references/patterns/composition.md
│   ├── Agent workflow ordering ────────────────────────── references/patterns/agentic-patterns.md
│   ├── Scaling beyond single server ───────────────────── references/decision-trees/scaling.md
│   └── Tool response steering behavior ────────────────── references/patterns/prompt-gates.md
│
└── Operations & testing
    ├── Not confident tools work correctly ─────────────── references/patterns/testing.md
    ├── Session/state management ───────────────────────── references/patterns/session-and-state.md
    ├── Production deployment readiness ────────────────── references/patterns/transport-and-ops.md
    └── Resources and prompts underutilized ────────────── references/patterns/resources-and-prompts.md
```

## How to Evaluate an MCP Server

1. **Identify symptoms** -- What's going wrong? (wrong tool selection, parse failures, security concerns, context exhaustion, slow responses)
2. **Route to dimension** -- Use the decision tree above to find the relevant quality dimension
3. **Read the decision tree** -- Each dimension has a decision tree in `references/decision-trees/` that narrows the diagnosis
4. **Apply patterns** -- Each pattern file in `references/patterns/` contains specific anti-patterns to look for and proven fixes
5. **Verify improvement** -- Use the testing patterns to validate changes

## Interactive Steering Protocol

**Never apply patterns silently. Always ask first.**

### Step 1: Diagnose

Before routing to any pattern, ask the user:
- What MCP SDK/framework are you using? (FastMCP, mcp-use, official SDK, other)
- What symptoms are you seeing? (wrong tool selection, parse failures, context exhaustion, security concerns, performance issues)
- How many tools does your server expose?

### Step 2: Evaluate and Present Options

For each applicable pattern, present it as a choice:
- Show the anti-pattern (what they likely have now) with a code example from their context
- Show 2-3 improvement options with trade-offs
- Recommend one option and explain why

Example interaction:

```
I found that your `search_users` tool uses a nested schema with 12 parameters.
This typically causes ~30% lower parse success across models.

**Option A**: Flatten to 6 top-level params (recommended -- highest compatibility)
**Option B**: Split into `search_users` + `filter_users` (better if filters are rarely used)
**Option C**: Keep nested but add z.coerce for type safety (minimal change)

Which approach fits your use case? Or would you like to see code examples for each?
```

### Step 3: Confirm Before Applying

Before any implementation:
- Show the specific code changes as a diff preview
- Ask: "Should I apply this pattern? (yes / no / modify)"
- If the user says modify, ask what they want changed

### What NOT to Do

- Do NOT silently refactor tool schemas without asking
- Do NOT apply all patterns at once -- prioritize by impact and ask which to tackle first
- Do NOT assume the user wants maximum optimization -- they may have constraints you don't know about

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

- **Always ask before applying.** Never assume the user wants a pattern applied without confirmation.
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

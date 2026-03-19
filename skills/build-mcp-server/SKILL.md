---
name: build-mcp-server
description: Use skill if you are building, improving, or debugging an MCP server and need battle-tested patterns for tool design, schema design, error handling, security, context engineering, or production deployment.
---

# Advanced MCP Server Patterns

113 battle-tested patterns across 15 categories for building production-grade MCP servers.

## Quick Reference Card

| You want to...                        | Start here                                                                                       |
|---------------------------------------|--------------------------------------------------------------------------------------------------|
| Design a new MCP server               | `references/decision-trees/design-phase.md` then `references/patterns/tool-design.md`            |
| Write better tool descriptions        | `references/patterns/tool-descriptions.md`                                                       |
| Structure tool responses              | `references/patterns/tool-responses.md`                                                          |
| Define tool schemas                   | `references/patterns/schema-design.md`                                                           |
| Handle errors properly                | `references/decision-trees/error-strategy.md` then `references/patterns/error-handling.md`       |
| Secure your server                    | `references/decision-trees/security-posture.md` then `references/patterns/security.md`           |
| Optimize context/token usage          | `references/patterns/context-engineering.md`                                                     |
| Manage 20+ tools                      | `references/decision-trees/tool-count.md` then `references/patterns/progressive-discovery.md`    |
| Build agent workflows                 | `references/patterns/agentic-patterns.md` then `references/patterns/prompt-gates.md`             |
| Compose multiple servers              | `references/patterns/composition.md`                                                             |
| Use resources and prompts             | `references/patterns/resources-and-prompts.md`                                                   |
| Manage sessions and state             | `references/patterns/session-and-state.md`                                                       |
| Test your MCP server                  | `references/patterns/testing.md`                                                                 |
| Deploy to production                  | `references/decision-trees/production-readiness.md` then `references/patterns/transport-and-ops.md` |
| Choose a response format              | `references/decision-trees/response-format.md` then `references/patterns/tool-responses.md`      |
| Scale architecture                    | `references/decision-trees/scaling.md` then `references/patterns/composition.md`                 |

## Main Decision Tree

Identify which phase of MCP development the user is in, then follow the corresponding branch.

### Phase 1: Designing a New MCP Server

The user is starting from scratch or planning a new server.

1. **Start with the design-phase decision tree** -- `references/decision-trees/design-phase.md`
   - Walks through: scope definition, tool granularity, naming conventions
2. **Define tools around user intent** -- `references/patterns/tool-design.md`
   - Intent-based design, not API-endpoint wrapping
   - One tool per user goal, composable primitives
3. **Write descriptions that guide the LLM** -- `references/patterns/tool-descriptions.md`
   - Descriptions are prompt engineering; every word matters
4. **Design flat schemas** -- `references/patterns/schema-design.md`
   - Under 6 parameters, no deep nesting, smart defaults

### Phase 2: Improving Existing Tools

The user has a working server but tools produce poor results or confuse the LLM.

1. **Fix tool responses first** -- `references/patterns/tool-responses.md`
   - Every response is a prompt to the LLM -- structure it accordingly
   - Use YAML/TSV over JSON to save tokens
2. **Refine error reporting** -- `references/patterns/error-handling.md`
   - Use `isError` in result content, not protocol-level errors
   - Include actionable remediation in error messages
3. **Sharpen descriptions** -- `references/patterns/tool-descriptions.md`
   - Add when-to-use and when-not-to-use guidance
   - Include example parameter values in descriptions

### Phase 3: Fixing Reliability and Errors

The user faces flaky tools, unclear failures, or inconsistent behavior.

1. **Adopt an error strategy** -- `references/decision-trees/error-strategy.md`
   - Choose between fail-fast, retry, fallback, and circuit-breaker patterns
2. **Implement error-handling patterns** -- `references/patterns/error-handling.md`
   - Structured error responses, retry hints, partial-result handling
3. **Add test coverage** -- `references/patterns/testing.md`
   - Tool-level unit tests, integration tests, LLM-in-the-loop evals

### Phase 4: Securing Your Server

The user needs to harden a server against misuse, injection, or data leakage.

1. **Assess security posture** -- `references/decision-trees/security-posture.md`
   - Threat model: prompt injection, data exfiltration, privilege escalation
2. **Apply security patterns** -- `references/patterns/security.md`
   - Input validation, prompt injection defense, sandboxing, audit logging
   - Principle of least privilege for tool capabilities

### Phase 5: Optimizing Performance

The user's server works but is slow, expensive, or burns through context.

1. **Optimize context usage** -- `references/patterns/context-engineering.md`
   - Tool definitions consume ~15% of context -- budget accordingly
   - Summarize large responses, use pagination, compress output
2. **Tune transport and operations** -- `references/patterns/transport-and-ops.md`
   - Connection pooling, caching, batching, streaming
3. **Manage session state** -- `references/patterns/session-and-state.md`
   - Stateless vs. stateful designs, session lifecycle, cleanup

### Phase 6: Scaling Tool Count (20+ Tools)

The user's server has grown to many tools and the LLM struggles to pick the right one.

1. **Evaluate tool count strategy** -- `references/decision-trees/tool-count.md`
   - Thresholds: under 10 is fine, 10-20 needs grouping, 20+ needs progressive discovery
2. **Implement progressive discovery** -- `references/patterns/progressive-discovery.md`
   - Dynamic tool registration, tool menus, capability namespacing
3. **Reduce context pressure** -- `references/patterns/context-engineering.md`
   - Lazy-load tool definitions, abbreviate descriptions for non-primary tools

### Phase 7: Multi-Server Architecture

The user is composing multiple MCP servers or integrating with a broader system.

1. **Plan scaling architecture** -- `references/decision-trees/scaling.md`
   - Gateway patterns, server federation, load distribution
2. **Apply composition patterns** -- `references/patterns/composition.md`
   - Server chaining, shared state protocols, cross-server tool references
3. **Coordinate sessions** -- `references/patterns/session-and-state.md`
   - Cross-server session management, state synchronization

### Phase 8: Agent Workflow Design

The user is building agent loops, multi-step workflows, or autonomous tool chains.

1. **Design agentic patterns** -- `references/patterns/agentic-patterns.md`
   - Tool sequencing, planning tools, checkpoint/rollback
2. **Add prompt gates** -- `references/patterns/prompt-gates.md`
   - Human-in-the-loop confirmation, approval workflows, guardrails
3. **Use resources and prompts** -- `references/patterns/resources-and-prompts.md`
   - Expose data as resources, use prompt templates for complex workflows

### Phase 9: Testing and Evaluation

The user needs to validate their MCP server before shipping.

1. **Follow the testing patterns** -- `references/patterns/testing.md`
   - Unit tests for individual tools, integration tests for tool chains
   - LLM evaluation: does the model pick the right tool and use it correctly?
   - Regression suites for schema changes

### Phase 10: Deploying to Production

The user is preparing their server for real-world traffic.

1. **Run the production readiness checklist** -- `references/decision-trees/production-readiness.md`
   - Health checks, monitoring, graceful degradation, versioning
2. **Configure transport and operations** -- `references/patterns/transport-and-ops.md`
   - SSE is deprecated -- use Streamable HTTP for remote servers
   - stdio for local, Streamable HTTP for remote
   - Connection management, timeouts, backpressure
3. **Choose response format** -- `references/decision-trees/response-format.md`
   - Text vs. structured data vs. mixed content responses

## Key Principles

These are the most impactful patterns across the entire collection. Internalize these before diving into reference files.

### 1. Every Tool Response Is a Prompt to the LLM

The text your tool returns goes directly into the LLM's context and shapes its next action. Structure responses as if you are writing a prompt: be clear, include relevant context, omit noise. A well-formatted tool response prevents follow-up tool calls and improves answer quality.

See: `references/patterns/tool-responses.md`

### 2. Design Around User Intent, Not API Endpoints

Do not create one MCP tool per REST endpoint. Instead, ask: "What is the user trying to accomplish?" One user goal should map to one tool, even if it orchestrates multiple API calls behind the scenes.

See: `references/patterns/tool-design.md`

### 3. Keep Schemas Flat, Under 6 Parameters

Deeply nested schemas confuse LLMs. Flatten objects, use smart defaults to reduce required parameters, and never exceed 6 parameters per tool. If you need more, the tool is doing too much -- split it.

See: `references/patterns/schema-design.md`

### 4. Use isError in Result Content, Not Protocol-Level Errors

Protocol-level errors signal transport/framework failures. For tool-level failures (API returned 404, invalid input, etc.), return a normal result with `isError: true` and an actionable message. This lets the LLM understand and recover from the error.

See: `references/patterns/error-handling.md`

### 5. Tool Definitions Eat ~15% of Context -- Budget Accordingly

Every tool you register consumes context tokens for its name, description, and schema. With 20+ tools, this becomes a significant chunk of the context window. Use progressive discovery, abbreviate descriptions, and lazy-load tools that are rarely needed.

See: `references/patterns/context-engineering.md`, `references/patterns/progressive-discovery.md`

### 6. Default to YAML or TSV Over JSON for Token Efficiency

When returning structured data, YAML and TSV use significantly fewer tokens than JSON (no braces, no quotes on keys). This matters when tool responses are large or called frequently.

See: `references/patterns/tool-responses.md`, `references/patterns/context-engineering.md`

### 7. SSE Is Deprecated -- Use Streamable HTTP for Remote Servers

Server-Sent Events transport is deprecated in the MCP specification. For remote servers, use Streamable HTTP. For local integrations, stdio remains the standard. Plan transport choice early as it affects architecture.

See: `references/patterns/transport-and-ops.md`

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
| `references/patterns/tool-design.md`              | Designing new tools, deciding tool granularity, naming tools                  |
| `references/patterns/tool-descriptions.md`        | Writing or improving tool descriptions, fixing tool selection issues           |
| `references/patterns/tool-responses.md`           | Structuring what tools return, choosing output format, reducing token usage    |
| `references/patterns/schema-design.md`            | Defining tool parameters, fixing schema issues, reducing required params      |
| `references/patterns/error-handling.md`            | Implementing error responses, retry logic, partial failures, circuit breakers |
| `references/patterns/security.md`                 | Hardening against injection, adding auth, auditing, sandboxing                |
| `references/patterns/context-engineering.md`       | Reducing token usage, optimizing context window, managing large responses     |
| `references/patterns/progressive-discovery.md`     | Managing 20+ tools, dynamic tool loading, capability namespacing              |
| `references/patterns/agentic-patterns.md`          | Building agent loops, multi-step workflows, planning tools, checkpoints      |
| `references/patterns/composition.md`               | Combining multiple servers, gateway patterns, server federation              |
| `references/patterns/prompt-gates.md`              | Adding human-in-the-loop, approval workflows, safety guardrails              |
| `references/patterns/resources-and-prompts.md`     | Exposing data as resources, creating prompt templates, resource subscriptions |
| `references/patterns/session-and-state.md`         | Managing sessions, stateful vs stateless, cross-request state, cleanup       |
| `references/patterns/testing.md`                   | Writing tests, evaluation strategies, regression testing, CI integration     |
| `references/patterns/transport-and-ops.md`         | Choosing transport, deployment config, monitoring, connection management      |

### Decision Tree Files

| File                                               | Read when...                                                                 |
|----------------------------------------------------|------------------------------------------------------------------------------|
| `references/decision-trees/design-phase.md`        | Starting a new server and need to make initial architecture decisions        |
| `references/decision-trees/tool-count.md`          | Deciding how many tools to expose and how to organize them                   |
| `references/decision-trees/error-strategy.md`      | Choosing between error-handling approaches (fail-fast, retry, fallback)      |
| `references/decision-trees/security-posture.md`    | Assessing threat model and choosing security measures                        |
| `references/decision-trees/scaling.md`             | Planning for growth, multi-server setups, load distribution                  |
| `references/decision-trees/production-readiness.md`| Preparing for production launch, running pre-deploy checklist                |
| `references/decision-trees/response-format.md`     | Choosing between text, structured data, or mixed-content responses           |

## Guardrails

When applying these patterns, avoid the following:

- **Do not create one tool per API endpoint.** Map tools to user intents. If your tool names mirror your REST routes, you are doing it wrong.
- **Do not use deeply nested schemas.** If a parameter requires more than one level of nesting, restructure. LLMs generate flat structures far more reliably.
- **Do not return raw upstream API responses.** Always curate, summarize, and format tool output for LLM consumption.
- **Do not use protocol-level errors for business logic failures.** Reserve protocol errors for transport and framework issues only.
- **Do not register all tools eagerly when you have 20+.** Use progressive discovery to load tools on demand.
- **Do not skip input validation.** Every tool parameter must be validated server-side. Never trust LLM-generated input.
- **Do not use SSE for new remote deployments.** SSE is deprecated. Use Streamable HTTP.
- **Do not ignore tool description quality.** Descriptions are the primary mechanism the LLM uses to select tools. Treat them as prompt engineering.
- **Do not store sensitive data in tool responses.** Anything returned from a tool enters the LLM context and may surface in outputs.
- **Do not deploy without tests.** At minimum, test that each tool handles valid input, invalid input, and upstream failures correctly.

# MCP vs CLI: Should This Be An MCP Server?

Use this guide before optimizing an MCP server when the real question may be whether the workflow belongs in MCP at all.

Status: refreshed on April 15, 2026.

## 1. Fast Recommendation

Do not assume every agent-accessible integration should be an MCP server.

Default recommendations:
- keep the workflow in CLI when it is developer-facing, command-shaped, and already well served by a strong CLI
- keep or build MCP when the requirement is governed remote access, typed discovery, or stateful sessions
- choose a hybrid when MCP should own auth or approvals, but CLI should own execution
- choose a skill when the missing piece is workflow guidance, not a new runtime surface

If you are auditing an existing MCP server and any of the following are true, open this document before touching schemas or tool descriptions:
- the repo already depends on a mature first-party CLI
- the server mostly shells out to local commands
- the tools are thin wrappers over REST endpoints
- the workload is mostly one-shot and stateless
- the pain is token cost, auth flakiness, or unused tool bloat

## 2. What The Official Docs Establish

| Documented fact | Why it matters |
|---|---|
| MCP is a JSON-RPC protocol with `stdio` and Streamable HTTP transports. | MCP is a protocol decision, not just a transport detail. It can be local or remote, but it always adds protocol semantics. |
| MCP servers expose tools with typed `inputSchema`, plus resources and prompts. | Keep MCP when discoverable, typed tool contracts are part of the product value. |
| HTTP-based MCP auth is specified around OAuth 2.1 style flows and metadata discovery; `stdio` should use environment credentials instead. | MCP is strongest for governed remote access. Local shell-style credential handling is not where it shines. |
| Anthropic and OpenAI document approvals, allowlists, deferred loading, and strong warnings about untrusted third-party servers. | MCP deserves the overhead when trust boundaries and approvals are part of the requirement. |
| Shell and local-shell tools execute in the caller's runtime, with safety coming from sandboxing, hooks, allowlists, and permission prompts. | CLI-first is operationally simpler, but the caller owns the local blast radius. |

Primary docs:
- [Model Context Protocol architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP transports spec, November 25, 2025](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP authorization spec, June 18, 2025](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Anthropic MCP connector](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector)
- [OpenAI MCP guide](https://developers.openai.com/api/docs/mcp)
- [OpenAI MCP and connectors](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
- [Claude Code security](https://docs.anthropic.com/en/docs/claude-code/security)

## 3. Use MCP When The Protocol Features Are The Product

An MCP server is justified when the protocol gives you something a CLI cannot give cleanly.

Strong MCP signals:
- per-user OAuth, token refresh, approval, or revocation
- multi-tenant SaaS or user-specific data boundaries
- multiple clients or models need the same tool surface
- the workflow depends on remote discovery and typed schemas
- the tool maintains state across calls
- the integration is remote-first and connector-like rather than process-like

Good MCP examples:
- SaaS connectors where end users bring their own account
- governed write operations with approval steps
- browser or session-based automation
- shared internal platform tools consumed by several agent runtimes

If those requirements are absent, be skeptical that the server should exist.

## 4. Choose CLI Instead When The Work Is Really Command Execution

Do not keep an MCP server just because the agent can call tools. Keep it only if the protocol layer is earning its keep.

Strong CLI signals:
- a mature CLI already exists
- the workflow is mostly stateless and one-shot
- the operator is a developer in a trusted environment
- shell composition, files, pipes, and redirects are central to the task
- JSON output and non-interactive flags already solve the data contract
- the main value is cheap execution, not typed remote discovery

Good CLI examples:
- `gh`, `git`, `kubectl`, `aws`, `docker`, `jq`, `curl`, `stripe`
- repo maintenance, deployment, infra inspection, CI helpers
- batch transforms where the shell can do the mechanical work once the model decides the plan

If your MCP server mostly maps one remote endpoint to one tool, and a good CLI already exists, shrinking or replacing the MCP layer is usually the correct optimization.

## 5. Use A Skill Instead When The Missing Piece Is Workflow Knowledge

Do not build an MCP server to explain how to use existing tools.

Use a skill when:
- the runtime capability already exists as CLI or API
- the agent needs a playbook, order of operations, or house rules
- the problem is routing, not transport
- the system only needs static guidance or lightweight dynamic context injection

Examples:
- "When triaging GitHub issues, prefer `gh --json` with these fields."
- "For deploy checks, run these five commands, then stop if this exit code appears."

That is a skill plus CLI problem, not an MCP server problem.

## 6. Hybrid Patterns That Usually Beat Pure MCP

### 6.1 MCP Control Plane, CLI Execution Plane

Use MCP for:
- auth
- approval
- tool discovery
- tenant isolation

Use CLI for:
- read-heavy operations
- local transforms
- batch processing
- shell-native execution

This is the right architecture when you need a governed remote interface for agents, but the real work is still cheap command execution.

### 6.2 CLI First, MCP For Stateful Or Governed Calls

Use CLI for:
- simple reads
- local automation
- developer workflows

Use MCP only for:
- session-heavy operations
- governed writes
- user-scoped remote access

This is the most pragmatic split for coding agents.

### 6.3 MCP Gateway With CLI Backend

If the CLI is excellent but governance is mandatory, keep the CLI behind the wall and put the wall in MCP:
- gateway handles auth, audit, policy, and approval
- backend execution uses CLI or shell wrappers
- agent sees a controlled tool surface instead of raw shell

This is better than exposing broad shell access through policy exceptions alone.

## 7. Kill Criteria: Signs The MCP Server Is The Wrong Abstraction

Treat these as red flags, not automatic verdicts:

- the server is a thin wrapper around an existing CLI with no additional auth or discovery value
- the server eagerly exposes dozens of endpoint-level tools that agents barely use
- the workflow is local, single-tenant, and developer-only
- the main problem is "the agent needs instructions" rather than "the system needs governed access"
- tool definitions dominate context cost before the first call
- most tool responses are raw upstream JSON instead of curated results
- auth problems, timeouts, and schema bloat are the biggest complaints in practice

If several of these are true, the best optimization may be to reduce the MCP surface, move parts back to CLI, or replace the server with a skill plus CLI workflow.

## 8. Keep Criteria: Signs The MCP Server Is Worth Optimizing

Invest in the server when several of these are true:
- users connect personal or tenant-scoped accounts
- the system needs approval and audit semantics at the tool layer
- stateful sessions are central to the tool design
- the same tool surface serves multiple clients or models
- schema-driven discovery materially improves tool use
- the operator cannot assume shell access or CLI literacy

In those cases, optimize the server rather than migrating away from MCP.

## 9. If You Keep MCP, Optimize In This Order

1. Confirm the server is justified against the criteria above.
2. Shrink the exposed tool surface before rewriting handlers.
3. Add progressive discovery, lazy loading, or gateway filtering when tool count is high.
4. Curate tool outputs so the model sees task-shaped responses, not raw upstream payloads.
5. Fix auth, approval, and transport reliability before polishing descriptive text.
6. Separate protocol errors from business-logic failures.

This order matters. A beautifully described server with the wrong abstraction boundary is still the wrong server.

## 10. Current Evidence And Caveats

### 10.1 Benchmark signal

The strongest current public benchmark I found is Scalekit's March 11, 2026 comparison of GitHub tasks using Claude Sonnet 4:
- 75 total benchmark runs
- same tasks and prompts, only the tool interface changed
- CLI medians ranged from 1,365 to 8,750 tokens
- direct MCP medians ranged from 32,279 to 82,835 tokens
- CLI completed 25 of 25 runs in the reported setup
- the tested direct MCP path completed 18 of 25 runs

Source:
- [Scalekit, March 11, 2026](https://www.scalekit.com/blog/mcp-vs-cli-use)

### 10.2 What that benchmark means

It does not prove that "MCP is bad."

It does show:
- large, eagerly loaded MCP surfaces have real token and reliability cost
- CLI is the better default when a strong CLI already exists
- MCP needs filtering, deferred loading, or gateway patterns to stay competitive for developer tooling

### 10.3 Practitioner signal from Reddit

Across the Reddit threads reviewed on April 15, 2026, the recurring pattern was:

Common pro-CLI themes:
- better debugging
- lower token cost
- stronger results for mature CLIs in coding workflows

Common pro-MCP themes:
- OAuth and per-user access
- customer-facing and non-technical surfaces
- stateful tools and reusable connectors

Common complaints about MCP:
- auth drift
- timeouts
- schema bloat
- low-quality community servers

Common complaints about CLI:
- permission friction
- quoting and shell expansion
- broader local blast radius without strong controls

Representative discussions:
- [r/AI_Agents: The Truth About MCP vs CLI](https://www.reddit.com/r/AI_Agents/comments/1rjtp3q/the_truth_about_mcp_vs_cli/)
- [r/ClaudeAI: Switched from MCPs to CLIs](https://www.reddit.com/r/ClaudeAI/comments/1sakut1/switched_from_mcps_to_clis_for_claude_code_and/)
- [r/mcp: MCP vs CLI for AI agents](https://www.reddit.com/r/mcp/comments/1roc96a/mcp_vs_cli_for_ai_agents_when_to_use_each/)
- [r/devsecops: Securing MCP in production](https://www.reddit.com/r/devsecops/comments/1py3qn8/securing_mcp_in_production/)

Treat these threads as practitioner evidence, not controlled benchmarks.

## 11. Security Note

MCP is not automatically safer than CLI, and CLI is not automatically simpler in production.

The real distinction is where you want control:
- CLI concentrates power in the local runtime, then constrains it with sandboxing, allowlists, hooks, and permissions
- MCP concentrates control in a mediated protocol surface, then constrains it with auth, approvals, policy, and server trust

If untrusted inputs, sensitive data, and state-changing actions can meet in one autonomous flow, apply a stricter security model. Meta's "Rule of Two" is a useful framing tool even though it is not MCP-specific:
- [Meta, October 31, 2025](https://ai.meta.com/blog/practical-ai-agent-security/)

## 12. Decision Rules To Apply In This Skill

When you are using `optimize-agentic-mcp`, apply these rules:

1. Before optimizing the server, decide whether the workflow should remain in MCP at all.
2. Recommend CLI when a mature CLI already covers the workflow and protocol features are not central.
3. Recommend a skill when the missing piece is workflow guidance, not runtime capability.
4. Recommend hybrid when auth and governance need MCP but execution still looks like deterministic command work.
5. Recommend MCP only when protocol features are clearly justified by the user or deployment model.

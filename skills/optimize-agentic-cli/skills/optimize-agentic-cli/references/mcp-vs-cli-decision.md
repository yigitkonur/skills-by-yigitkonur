# MCP vs CLI Decision Guide

Use this guide when deciding whether an agent workflow should stay CLI-first, move to MCP, or split across both.

Status: refreshed on April 15, 2026.

## 1. Recommended Default

Start with a CLI when all of these are true:
- a mature CLI already exists
- the workflow is mostly stateless and command-shaped
- the agent can rely on machine-readable output, semantic exit codes, and non-interactive flags
- the operator is a developer or a trusted local runtime

Promote the workflow to MCP when any of these become dominant:
- per-user OAuth, tenant isolation, revocation, approvals, or audit trails
- no credible CLI exists, or shell parsing would be a poor fit
- the agent needs typed discovery across many remote capabilities
- the tool surface is stateful across calls

Use a hybrid when:
- MCP should own auth, approvals, or discovery, but execution can stay in CLI
- read and batch-transform steps are cheap in CLI, but write steps need governed remote access
- you need both a developer-friendly operator surface and a governed agent-facing surface

Skills are a fourth option. If the agent mainly needs workflow guidance for existing tools, add a skill and keep the runtime surface as CLI.

## 2. What the Official Docs Establish

| Documented fact | Why it matters for the decision |
|---|---|
| MCP is a JSON-RPC protocol with `stdio` and Streamable HTTP transports. | MCP is not "just remote tools." It can be local or remote, but it always adds a protocol layer. |
| MCP servers expose typed discovery through `tools/list`, `inputSchema`, resources, and prompts. | Choose MCP when schema-level discovery and machine-readable tool contracts are the point. |
| HTTP-based MCP authorization is specified around OAuth 2.1 style metadata and bearer tokens; `stdio` transports should use environment credentials instead. | MCP is much better matched to governed remote access than to local shell-style credential handling. |
| Anthropic and OpenAI both document approvals, allowlists, deferred loading, and strong warnings about untrusted servers. | MCP earns its cost when you need approval and trust boundaries, not just a way to run commands. |
| Shell and local-shell tools run in the caller's own runtime, with safety coming from sandboxing, allowlists, hooks, and permissions. | CLI-first is usually simpler and cheaper, but the caller owns the blast radius. |

Primary docs:
- [Model Context Protocol architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP transports spec, November 25, 2025](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP authorization spec, June 18, 2025](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [Anthropic MCP connector](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector)
- [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [OpenAI MCP guide](https://developers.openai.com/api/docs/mcp)
- [OpenAI local shell](https://developers.openai.com/api/docs/guides/tools-local-shell)
- [GitHub Copilot CLI programmatic reference](https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-cli-reference/cli-programmatic-reference)

## 3. Fast Decision Matrix

| Question | Preferred surface | Why |
|---|---|---|
| Is there already a good first-party CLI with JSON output and non-interactive flags? | CLI | Lower token cost, simpler debugging, better model familiarity. |
| Is the workflow mostly one-shot or stateless? | CLI | Process execution is enough; a protocol adds overhead without much benefit. |
| Does the workflow need per-user auth, tenant isolation, approval, or revocation? | MCP | Those are protocol and gateway problems, not shell ergonomics problems. |
| Does the tool keep state across calls: browser sessions, transactions, remote cursors? | MCP | Session continuity is native to MCP-style tool interfaces. |
| Does the agent only need instructions for how to use existing CLIs and APIs? | Skill + CLI | This is workflow knowledge, not a new runtime protocol. |
| Do you want governed discovery but cheap execution? | Hybrid | Use MCP for control plane, CLI for execution plane. |

## 4. When To Stay CLI-First

Choose CLI when most of the value comes from process execution and command composition.

Strong CLI signals:
- the service already has a mature CLI such as `gh`, `kubectl`, `aws`, `docker`, `git`, `jq`, `stripe`, or `vercel`
- the workflow is local, developer-facing, and single-tenant
- the model can work from a known command vocabulary plus `--help`
- shell composition, files, pipes, and redirects are central to the job
- the data path is short enough that plain JSON output is sufficient

CLI is especially strong for:
- coding agents operating in repos
- CI and automation jobs
- one-shot read and mutate operations
- batch transforms where the model reasons once, then the shell does the work

Do not call the CLI path "done" unless it has:
- pure machine output on stdout
- progress and operator noise on stderr
- semantic exit codes
- non-interactive flags such as `--yes`, `--no-input`, or `--output json`
- deterministic auth handling for headless runs

If those are missing, fix the CLI before you decide the architecture is the problem.

## 5. When MCP Is The Better Abstraction

Choose MCP when the value comes from governed access, typed discovery, or durable state.

Strong MCP signals:
- users connect their own accounts and permissions through OAuth
- the system is multi-tenant and actions happen on behalf of different users
- multiple clients or models need the same tool surface
- the agent needs discoverable schemas rather than shell-oriented affordances
- the tool keeps state across calls, or the workflow spans approvals and long-lived sessions
- there is no strong CLI equivalent and a shell wrapper would mostly reimplement a remote API

MCP is especially strong for:
- enterprise SaaS integrations
- customer-facing tools with scoped access
- browser or session-driven automation
- remote connectors reused across products and agent runtimes

MCP is a poor fit when:
- the server mostly shells out to an existing CLI without adding meaningful auth or discovery value
- the server mirrors dozens of thin REST endpoints directly into tools
- the users are developers who already live in a terminal and do not need a mediated remote surface

## 6. When A Hybrid Beats Either Extreme

The highest-leverage pattern is often not pure CLI or pure MCP.

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

This is the right split when an operator surface already exists as CLI, but the agent surface needs governance.

### 6.2 Skill + CLI

Use a skill when the missing piece is not runtime capability but judgment and workflow.

Examples:
- "For GitHub triage, prefer `gh --json` and summarize with `jq`."
- "For deploy validation, run these four commands in order and stop on this exit code."

That is cheaper and simpler than building an MCP server whose only job is to explain how to use an existing CLI.

### 6.3 CLI First, MCP Fallback

This pattern works when most operations are stateless, but a small subset is stateful or governed:
1. try CLI first
2. route stateful or approval-gated operations to MCP
3. keep the boundary explicit in the skill or system instructions

## 7. Current Evidence And Caveats

### 7.1 Documented benchmark signal

The strongest current public benchmark I found is Scalekit's March 11, 2026 comparison of GitHub tasks using Claude Sonnet 4:
- 75 total benchmark runs
- same tasks and prompts, with only the tool interface changing
- CLI medians ranged from 1,365 to 8,750 tokens
- direct MCP medians ranged from 32,279 to 82,835 tokens
- CLI completed 25 of 25 runs in the reported setup
- the tested direct MCP path completed 18 of 25 runs

Source:
- [Scalekit, March 11, 2026](https://www.scalekit.com/blog/mcp-vs-cli-use)

### 7.2 What that benchmark does not prove

Do not overgeneralize it.

The caveats matter:
- it focused on GitHub tasks
- it used a large GitHub MCP tool catalog
- some failures were connection or timeout issues, not protocol impossibilities
- it shows the cost of a specific MCP surface, not a universal ceiling for all MCP designs

The correct takeaway is narrower:
- CLI is the better default when a strong CLI already exists
- bloated or eagerly loaded MCP surfaces carry real cost
- gateway filtering and deferred loading materially change the tradeoff

### 7.3 Practitioner signal from Reddit

Across the Reddit threads reviewed on April 15, 2026, the pattern was consistent:

Common pro-CLI themes:
- lower token usage
- easier debugging
- better results with mature CLIs like `gh`, `kubectl`, and `aws`
- fewer moving parts for coding agents

Common pro-MCP themes:
- per-user OAuth
- governed remote access
- non-technical user surfaces
- stateful tools and shared connectors

Common CLI complaints:
- permission prompts
- quoting and shell expansion friction
- broad local access if safeguards are weak

Common MCP complaints:
- auth drift
- timeouts
- schema bloat
- low-quality community servers

Treat this as practitioner evidence, not a controlled study.

Representative discussions:
- [r/ClaudeAI: Switched from MCPs to CLIs](https://www.reddit.com/r/ClaudeAI/comments/1sakut1/switched_from_mcps_to_clis_for_claude_code_and/)
- [r/AI_Agents: The Truth About MCP vs CLI](https://www.reddit.com/r/AI_Agents/comments/1rjtp3q/the_truth_about_mcp_vs_cli/)
- [r/ClaudeCode: CLI permission requests vs MCP](https://www.reddit.com/r/ClaudeCode/comments/1rwz2km/to_everyone_touting_the_benefits_of_cli_tooling/)
- [r/mcp: MCPs, CLIs, and skills](https://www.reddit.com/r/mcp/comments/1rtsl9z/mcps_clis_and_skills_when_to_use_what/)

## 8. Migration Paths

| Current state | Move to | When |
|---|---|---|
| Raw shell commands with brittle parsing | Agent-ready CLI | You already have the right abstraction, but the contract is weak. |
| Good CLI plus repeated workflow mistakes | Skill + CLI | The runtime is fine; the agent needs better routing and examples. |
| CLI with growing auth and governance demands | MCP or MCP gateway | The problem is no longer just execution; it is custody and policy. |
| Large MCP server with thin endpoint wrappers | Smaller MCP, hybrid, or CLI | The server is carrying protocol tax without enough protocol value. |
| MCP that mostly wraps a local CLI | Skill + CLI, or MCP gateway with CLI backend | Keep only the part that adds auth, approval, or discovery value. |

## 9. Decision Rules To Apply In This Skill

When you are using `optimize-agentic-cli`, apply these rules:

1. Default to keeping the workflow in CLI if the core problem is output quality, exit codes, auth ergonomics, or non-interactive behavior.
2. Recommend MCP only when the requirements clearly justify protocol features: per-user auth, typed remote discovery, shared multi-client use, or stateful sessions.
3. Recommend a skill when the problem is mainly workflow guidance rather than runtime access.
4. Recommend a hybrid when auth and governance pull toward MCP but the work itself still looks like cheap, deterministic command execution.
5. State explicitly whether your recommendation is based on documented facts, benchmark evidence, or practitioner reports.

# decide-surface — CLI vs MCP, decided by workload

The single canonical CLI-vs-MCP decision file. Before writing a tool description, picking a schema, drafting an architecture sketch, or "modernizing" an existing tool, decide the surface — and decide it from the workload, not from which technology felt newer last week. Refreshed 2026-04-15 as the single cross-surface decision source.

## Workload-first rubric

Ask the workload questions first. The surface falls out.

| Question | Answer | Surface signal |
|---|---|---|
| Who calls the tool? | A developer in a terminal | CLI |
| Who calls the tool? | An agent acting on behalf of a remote end-user | MCP |
| What state must persist between calls? | None — every call is independent | CLI |
| What state must persist between calls? | Session-scoped, multi-turn, server-side | MCP |
| What auth model fits? | Local env-var credentials, single tenant | CLI |
| What auth model fits? | Per-user OAuth, tenant isolation, revocation, audit | MCP |
| What's the call frequency? | Episodic — handful per task, shell-composable | CLI |
| What's the call frequency? | Many per session, schema-typed, discoverable | MCP |
| Does a mature CLI already exist? | Yes (`gh`, `kubectl`, `aws`, `stripe`) | CLI |
| Does a mature CLI already exist? | No, and a shell wrapper would mostly reimplement a remote API | MCP |
| Does the agent need to be told *how* to use the tool? | Yes, but the runtime already exists | Skill + CLI |
| Does the agent need governed remote discovery? | Yes — typed schemas, per-user scope, multi-client | MCP |

Bias to keep an existing strong CLI; promote to MCP only when the protocol features are the product (typed remote discovery, OAuth, sessions, tenant isolation). When the CLI is solid but the auth model needs governance, the answer is hybrid (control plane MCP, execution plane CLI), not migration.

## The two clean defaults

### Stay CLI when

- A mature first-party CLI already exists (`gh`, `kubectl`, `aws`, `docker`, `git`, `jq`, `stripe`, `vercel`).
- The workflow is mostly stateless and command-shaped.
- The agent only needs process execution plus stable parsing.
- The operator is a developer or a trusted local runtime.
- Shell composition (pipes, files, redirects) is central to the task.
- The data path is short enough that a JSON envelope on stdout is sufficient.

CLI is especially strong for: coding agents in repos, CI and automation, one-shot read/mutate, batch transforms where the model reasons once and the shell does the work.

A CLI is **not** "agent-ready" yet unless it has: pure machine output on stdout, progress on stderr, semantic exit codes, non-interactive flags (`--yes`, `--no-input`, `--json`), deterministic auth for headless runs. If any of those are missing, fix the CLI before deciding the architecture is the problem.

### Move to MCP when

- Per-user OAuth, tenant isolation, revocation, approvals, or audit trails are part of the requirement.
- No credible CLI exists, or shell parsing would be a poor fit (e.g., long-lived sessions).
- The agent needs typed discovery across many remote capabilities (`tools/list` + `inputSchema`).
- The tool surface is stateful across calls (browser sessions, transactions, remote cursors).
- Multiple clients or models need the same tool surface and would otherwise reinvent it each time.

MCP is especially strong for: SaaS connectors where end-users bring their own account, governed write operations with approval steps, browser/session automation, shared internal platform tools.

## What the official docs establish (for citation)

| Documented fact | Why it matters for the decision |
|---|---|
| MCP is a JSON-RPC protocol with `stdio` and Streamable HTTP transports. | MCP is a protocol decision, not just transport — it always adds protocol semantics. |
| MCP servers expose typed discovery via `tools/list`, `inputSchema`, resources, and prompts. | Choose MCP when schema-level discovery is the point. |
| HTTP-based MCP authorization is specified around OAuth 2.1 + bearer tokens; `stdio` should use environment credentials. | MCP is matched to governed remote access, not local shell credential handling. |
| Anthropic and OpenAI document approvals, allowlists, deferred loading, and warnings about untrusted servers. | MCP earns its cost when trust boundaries matter. |
| Shell and local-shell tools run in the caller's runtime, with safety from sandboxing, allowlists, hooks, and permissions. | CLI-first is operationally simpler, but the caller owns the blast radius. |

Primary docs:
- [Model Context Protocol architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP transports spec, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP authorization spec, 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [Anthropic MCP connector](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector)
- [Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [OpenAI MCP guide](https://developers.openai.com/api/docs/mcp)
- [OpenAI local shell](https://developers.openai.com/api/docs/guides/tools-local-shell)
- [GitHub Copilot CLI programmatic reference](https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-cli-reference/cli-programmatic-reference)

## Hybrid: when neither extreme wins

The highest-leverage pattern is often hybrid.

### Pattern: MCP control plane + CLI execution plane

```
Agent  ──tools/list──>  MCP Gateway  ──>  Auth + approval + tenant isolation
         │                  │
         │                  └──spawns──>  Local CLI process
         │                                 ↓
         └────────────────────────  stdout JSON envelope
```

Use MCP for: auth, approval, tool discovery, tenant isolation. Use CLI for: read-heavy operations, local transforms, batch processing, shell-native execution. Right architecture when an operator surface already exists as CLI but the agent surface needs governance.

### Pattern: Skill + CLI

When the missing piece is judgment and workflow, not runtime capability, write a skill instead of an MCP server.

Examples:
- "For GitHub triage, prefer `gh --json` and summarize with `jq`."
- "For deploy validation, run these four commands in order; stop on this exit code."

Cheaper and simpler than an MCP server whose only job is to explain how to use an existing CLI.

### Pattern: CLI first, MCP fallback

Most operations stateless and developer-facing — keep them in CLI. The small subset that's stateful or governed routes through MCP. Keep the boundary explicit in the skill or system instructions.

### Pattern: MCP gateway with CLI backend

CLI is excellent but governance is mandatory. Keep the CLI behind the wall and put the wall in MCP: gateway handles auth, audit, policy, approval; backend execution uses CLI or shell wrappers; agent sees a controlled tool surface instead of raw shell.

## Evidence: the Scalekit benchmark, 2026-03-11

The strongest current public benchmark on CLI vs MCP token cost.

Source: [Scalekit, MCP vs CLI use comparison, 2026-03-11](https://www.scalekit.com/blog/mcp-vs-cli-use) — accessed 2026-04-15.

Setup:
- 75 total benchmark runs.
- Same GitHub tasks and prompts; only the tool interface changed.
- Claude Sonnet 4.

Numbers:

| Surface | Median tokens (range) | Completed runs |
|---|---|---|
| CLI (`gh`) | 1,365 — 8,750 | 25 / 25 |
| Direct MCP (large GitHub MCP catalog) | 32,279 — 82,835 | 18 / 25 |

What this proves narrowly:
- Bloated, eagerly-loaded MCP surfaces carry real token cost.
- CLI is the better default when a strong CLI already exists.
- Some MCP failures were connection or timeout, not protocol impossibilities.

What this does **not** prove:
- "MCP is bad" universally — it isn't.
- That a tightly-scoped MCP would lose this benchmark — gateway filtering and progressive discovery materially change the tradeoff.
- That the result generalizes outside GitHub-shaped tasks.

The correct takeaway is narrower: when a strong CLI already exists, MCP must justify its protocol cost with protocol value (auth, discovery, sessions, multi-client). When that justification is real, MCP wins. When it isn't, CLI wins.

## Practitioner signal (Reddit, 2026-04-15)

Triangulating with community discussion (treat as practitioner evidence, not controlled study):

| Pro-CLI themes | Pro-MCP themes |
|---|---|
| Lower token usage | Per-user OAuth |
| Easier debugging | Governed remote access |
| Better results with mature CLIs (`gh`, `kubectl`, `aws`) | Non-technical user surfaces |
| Fewer moving parts for coding agents | Stateful tools and shared connectors |

| CLI complaints | MCP complaints |
|---|---|
| Permission prompts | Auth drift |
| Quoting / shell expansion friction | Timeouts |
| Broad local blast radius if safeguards weak | Schema bloat |
|  | Low-quality community servers |

Representative threads (accessed 2026-04-15):
- [r/ClaudeAI: Switched from MCPs to CLIs](https://www.reddit.com/r/ClaudeAI/comments/1sakut1/switched_from_mcps_to_clis_for_claude_code_and/)
- [r/AI_Agents: The Truth About MCP vs CLI](https://www.reddit.com/r/AI_Agents/comments/1rjtp3q/the_truth_about_mcp_vs_cli/)
- [r/ClaudeCode: CLI permission requests vs MCP](https://www.reddit.com/r/ClaudeCode/comments/1rwz2km/to_everyone_touting_the_benefits_of_cli_tooling/)
- [r/mcp: MCPs, CLIs, and skills](https://www.reddit.com/r/mcp/comments/1rtsl9z/mcps_clis_and_skills_when_to_use_what/)

## Vignettes

### Vignette 1 — coding agent in a repo

Workload: agent edits files, runs tests, commits, opens PRs in the user's local repo.

Auth: developer's local git config + GitHub PAT in env.
State: none beyond filesystem.
Audience: developer.

Decision: **CLI** (`gh`, `git`, project-specific test runners). Promoting to MCP would add protocol cost without adding value. If the team needs governance over what the agent commits, add a hook or a code-review gate, not an MCP.

### Vignette 2 — multi-tenant SaaS connector

Workload: end-user installs the integration in their workspace; agent acts on their behalf against their tenant.

Auth: per-user OAuth with refresh tokens.
State: session-scoped (cursor pagination, tenant context).
Audience: end-user via a connected agent.

Decision: **MCP**. This is exactly what the protocol was designed for. CLI would force per-tenant credential plumbing and lose the discovery layer.

### Vignette 3 — internal platform tool already shipping a CLI

Workload: internal devs use the existing `myco` CLI; new requirement is "agent should be able to use it from Claude Desktop and Cursor."

Auth: existing per-user CLI auth via env var; works headless.
State: stateless.
Audience: internal devs through agents.

Decision: **Skill + CLI**. Write a skill that documents the agent-usable subset of `myco` (`--json` outputs, exit codes, common flag combinations). Don't reimplement the CLI as MCP tools.

### Vignette 4 — CLI exists but governance now required

Workload: same internal `myco` CLI, but now the team needs per-user OAuth, audit trails, and approval gates for production writes.

Decision: **Hybrid**. MCP gateway owns auth + approval + audit. Backend execution is `myco` shelled out from the gateway. Don't migrate the implementation, wrap it.

### Vignette 5 — research / SEO frontier exploration

Workload: agent runs many search waves, looking for source diversity and intent gaps.

Auth: server-side API keys.
State: optional (continuation budget across waves).
Audience: any agent.

Decision: **either, with bias to CLI**. Read-only research workflows fit CLI well (`research-cli serp "query" --json`); MCP only earns its keep if multiple clients consume the same tool surface or if continuation state has to live server-side. See `agent-cognitive-load.md` for the budget framing.

## Migration paths

| Current state | Move to | When |
|---|---|---|
| Raw shell commands with brittle parsing | Agent-ready CLI | Right abstraction, weak contract — fix the contract. |
| Good CLI + repeated workflow mistakes | Skill + CLI | Runtime is fine; agent needs better routing and examples. |
| CLI with growing auth and governance demands | MCP, or MCP gateway over CLI backend | Problem is no longer execution; it's custody and policy. |
| Large MCP server with thin endpoint wrappers | Smaller MCP, hybrid, or CLI | Server is paying protocol tax without enough protocol value. |
| MCP that mostly wraps a local CLI | Skill + CLI, or MCP gateway with CLI backend | Keep only the part that adds auth, approval, or discovery value. |
| MCP server with 50+ tools dumping raw API responses | Tightened MCP (toolsets + curated responses) or hybrid | The cost is a tool-design problem; rebuild the surface. |

## Common mistakes

**"We should use MCP because it's newer."**
Newer is not better when the workload is a coding agent in a repo. Reject this framing — ask what the workload is. If a strong CLI already exists and the auth model is local, MCP adds cost without adding value. The Scalekit benchmark above is the citation when someone insists on MCP for a CLI-shaped workload.

**"We should write a CLI because MCP is too complex."**
Complexity is not the question; workload is. If the requirement is per-user OAuth and tenant isolation, MCP is the correct cost. A CLI in this case ships brittle credential plumbing and ad-hoc auth, then becomes harder than the MCP would have been.

**"Let's wrap our REST API 1:1 as MCP tools."**
This is the most common MCP failure mode. Notion's own post-mortem (`notion.com/blog/notions-hosted-mcp-server-an-inside-look`) called it out: "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." Wrap user intents, not endpoints. See `descriptions-as-prompts.md` and `../mcp/patterns/tools.md`.

**"We need to choose between CLI and MCP — pick one."**
False dichotomy. Hybrid is often correct. The same business logic can ship as a CLI binary AND as an MCP server, sharing the underlying handler. Pick the surfaces by workload, not by ideology.

**"The decision tree is the entry point."**
No — the workload is the entry point. The surface is downstream of the workload. If you open with "is this a CLI or MCP?", you've already wasted a turn.

## Decision rules to apply

When using `optimize-agent-ergonomics`:

1. Default to keeping the workflow in CLI if the core problem is output quality, exit codes, auth ergonomics, or non-interactive behavior.
2. Recommend MCP only when the requirements clearly justify protocol features: per-user auth, typed remote discovery, shared multi-client use, or stateful sessions.
3. Recommend a skill when the problem is mainly workflow guidance rather than runtime access.
4. Recommend a hybrid when auth and governance pull toward MCP but the work itself still looks like cheap, deterministic command execution.
5. State explicitly whether the recommendation is based on documented facts (cite them), benchmark evidence (cite Scalekit + date), or practitioner reports (mark as practitioner signal).
6. Never blanket-recommend MCP over CLI or vice versa. The decision is workload-dependent.

## Cross-references

- For the design questions that precede surface selection, read `design-thinking.md` (the 8 questions; surface choice is downstream of all 8).
- For how to write descriptions on either surface once the surface is fixed, read `descriptions-as-prompts.md`.
- For surface-specific deep dives, route to `../cli/architect-new.md` or `../mcp/architect-new.md`.
- For evidence on how production vendors ship across both surfaces (e.g., GitHub's CLI and GitHub's MCP), read `exemplars.md`.

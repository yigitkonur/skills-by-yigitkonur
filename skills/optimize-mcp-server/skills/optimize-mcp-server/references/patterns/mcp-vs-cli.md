# MCP vs CLI, Skills, and Bash: When Each Wins

15 patterns for deciding when an MCP server is the right primitive and when to use CLI/bash/skills instead.

The 2025–2026 consensus moved from "wrap everything in MCP" to a layered model: **Skills teach the workflow, CLI/bash executes it, MCP is reserved for authenticated multi-tenant services and non-CLI integrations.** These patterns encode that shift, the measurements behind it, and the hybrids that survive the reframe. Raw token-budget numbers for tool definitions live in `context-engineering.md`; this file reuses them only to pick between primitives.

---

## Pattern 1: Default to CLI When a Working CLI Already Exists

If the target service ships a first-party CLI, wrapping it in an MCP server usually loses on every axis: context cost, latency, reviewability, and cost per conversation. A CLI's stdout is already a compressed, post-processed representation of the API; re-serializing it through JSON-RPC adds overhead without adding capability.

Jannik Reinhard's "list all non-compliant Intune devices to CSV" benchmark measured a **35× context reduction** for the CLI path. MCP path over Microsoft Graph MCP: ~145,000 tokens for 50 devices across tool-definition injection, schema references, and response envelopes. Same task delegated to `mgc`, `az`, and PowerShell from a bash loop: ~4,150 tokens. On a 128K window, MCP left ~82K free; CLI left ~121K (95%) free for reasoning.

```bash
# CLI path — the agent writes and runs this directly
mgc devices list --filter "complianceState eq 'noncompliant'" --top 50 \
  | jq -r '.value[] | [.id,.deviceName,.operatingSystem] | @csv' \
  > noncompliant.csv
```

**When to use:** any task where a `*`-suffixed CLI covers the endpoint set (`gh`, `az`, `mgc`, `aws`, `kubectl`, `gcloud`, `op`, `doctl`, `heroku`, `stripe`, `supabase`). Always check `allowed-tools: Bash(<cli>:*)` as a precondition before reaching for an MCP.

**Source:** [Jannik Reinhard — Why CLI tools are beating MCP for AI agents](https://jannikreinhard.com/2026/02/22/why-cli-tools-are-beating-mcp-for-ai-agents/), 2026-02.

---

## Pattern 2: Budget Per-Tool Cost at ~590 Tokens and Cap Exposed Surface

Every MCP tool definition costs **500–750 tokens** on average before the first user turn. Jannik measured GitHub MCP at 93 tools / ~55K tokens (~590 tok/tool). Anthropic's advanced-tool-use post reports GitHub at 35 tools / ~26K tokens (~740 tok/tool) and a 58-tool / 5-server enterprise setup at ~55K tokens. `context-engineering.md` covers descriptor trimming; this pattern tells you the architectural cap.

If a candidate MCP would push combined tool definitions past the Tool Search 10%-of-context threshold (≈12.8K tokens on a 128K window), you have three choices: ship Tool Search, switch to a meta-tool gateway (Pattern 11), or move the workflow out of MCP.

| Exposed tools | Typical token cost | Safe? |
|---------------|--------------------|-------|
| ≤ 15          | 7K–11K             | Yes   |
| 16–30         | 11K–22K            | Only with Tool Search or PTC |
| 31–60         | 22K–45K            | Requires gateway/meta-tools |
| 60+           | 45K–135K+          | Will trip descriptor bloat; migrate |

**Source:** [Jannik Reinhard — Why CLI tools are beating MCP for AI agents](https://jannikreinhard.com/2026/02/22/why-cli-tools-are-beating-mcp-for-ai-agents/), 2026-02; [Anthropic — Advanced tool use with Claude](https://www.anthropic.com/engineering/advanced-tool-use), 2025-11.

---

## Pattern 3: Watch the 134K-Token Baseline and Per-Conversation Dollar Cost

Anthropic's advanced-tool-use post reports an enterprise MCP configuration where tool definitions consumed **134K tokens before the first user turn** — more than a full 128K context window on older models. Dead Neurons priced this at ~$0.40 per conversation on input tokens for tool schemas alone, before any user message or tool call.

If your deployment leaves tool definitions static across every conversation, multiply that per-conversation cost by your call volume to decide whether protocol-level optimization (PTC, Tool Search, gateway) or moving to CLI/skills is the cheaper fix.

**When to use:** cost-model any MCP deployment that would exceed 50K tokens of tool definitions at steady state.

**Source:** [Anthropic — Advanced tool use with Claude](https://www.anthropic.com/engineering/advanced-tool-use), 2025-11; [Dead Neurons — Forget MCP, Bash Is All You Need](https://deadneurons.substack.com/p/forget-mcp-bash-is-all-you-need), 2026-02.

---

## Pattern 4: Enable Tool Search Before Migrating Off MCP

Claude Code v2.1.7 ships Tool Search, which auto-enables when tool definitions would exceed 10% of the context window. It reduces exposure from 77K → 8.7K tokens (**85% cut**) and lifts MCP-eval accuracy from 49% → 74% on Opus 4 and 79.5% → 88.1% on Opus 4.5. This is a protocol-native fix; try it before paying the cost of migrating a working MCP to CLI.

```jsonc
// claude-code settings — Tool Search kicks in above the descriptor budget
{
  "mcp": {
    "toolSearch": { "enabled": true, "thresholdPercent": 10 }
  }
}
```

**When to use:** existing MCP with >15 tools and measurable descriptor bloat, before touching the server code.
**When NOT to use:** per-tool cost is fine but each call's result envelope is the bottleneck (Pattern 7 instead).

**Source:** [Layered — MCP tool schema bloat, the hidden token tax and how to fix it](https://layered.dev/mcp-tool-schema-bloat-the-hidden-token-tax-and-how-to-fix-it/), 2026-01.

---

## Pattern 5: Use Programmatic Tool Calling for Fan-Out / Filter / Aggregate

If the workflow is "call N tools, join their results, filter to a summary," use **Programmatic Tool Calling (PTC)** rather than sequential tool calls. Anthropic's expense-audit benchmark — 20 people × 2000+ line items / 50KB raw — compressed to 1KB results. Average tokens 43,588 → 27,297 (−37%). Internal-knowledge accuracy rose 25.6% → 28.5%; GIA 46.5% → 51.2%. The pattern eliminates 19+ inference passes in a 20-tool workflow by letting the model write one orchestration script that the MCP runtime executes.

PTC is a hybrid: MCP still exposes the primitives, but the model invokes them from inside generated code instead of through JSON-RPC round trips. This is the protocol-level answer to "too many sequential calls."

**When to use:** fan-out across ≥5 records, any reduce/filter/join step, batch mutations with shared structure.
**When NOT to use:** single-step lookup, human-approval gates between calls, operations that must be individually audited in the transcript.

**Source:** [Anthropic — Advanced tool use with Claude](https://www.anthropic.com/engineering/advanced-tool-use), 2025-11.

---

## Pattern 6: Measure Pipeline Length as a Cost Multiplier

Every inference pass costs dollars; every bash pipe costs microseconds. Dead Neurons: *"A five-step pipeline that costs fractions of a cent in bash can cost dollars when each step requires a model inference pass."* ITFuture's reproducible benchmark made this concrete — a 5-record memory update via direct tool calls took **42.7s**; the same work expressed as generated code completed in **<1ms**. Tokens fell 6,000 → 300 (95%). Scaled to 50 records, the gap was 430,000×.

Rule of thumb: for any workflow >3 dependent steps, cost-model both paths. If the steps are all deterministic data transforms, push them into bash or a single PTC call. If one step requires model judgment, keep that step as a tool call and bash the rest.

**When to use:** any transformation pipeline, any batch operation.
**When NOT to use:** workflows where each step needs model reasoning on the previous step's semantics, not just its shape.

**Source:** [ITFuture reproducible benchmark on r/ClaudeCode](https://reddit.com/r/ClaudeCode/comments/1qmv7ww/), 2025-11; [Dead Neurons — Forget MCP, Bash Is All You Need](https://deadneurons.substack.com/p/forget-mcp-bash-is-all-you-need), 2026-02.

---

## Pattern 7: Treat the 500–2000 Token MCP Call Floor as a Budget Line

Practitioner data from r/ClaudeAI measures every MCP call at **500–2000 tokens of overhead** (schema reference + serialized request + JSON envelope), even when the actual payload is ~200 tokens. A 20-fetch session carries 10K–40K of pure envelope. Switching the same workload to a CLI dropping results to disk: 45K → 3K overhead; agent completion rate rose from ~35% to 90%+.

Use this as a threshold: if a common workflow involves >10 tool calls and each returns <500 tokens of real data, envelope cost dominates the real work and the primitive is wrong.

**When to use:** auditing an existing MCP that feels "slow even though each call is small."
**When NOT to use:** workflows with 1–3 tool calls per turn and substantial payloads.

**Source:** [r/ClaudeAI — MCP overhead measurements](https://reddit.com/r/ClaudeAI/comments/1sbz4zz/), 2025-11.

---

## Pattern 8: Replace 30+ Schema Tools with One Code-Input Tool

Armin Ronacher's `pexpect-mcp` and `playwrightess` demonstrate the extreme consolidation path: a **single MCP tool that accepts Python or JS source**, maintains a stateful session, and returns stdout/stderr/console. Playwright MCP shrinks from ~30 tool definitions to 1. Initial debug drops from 45s with 7 tool calls to <5s with 1 call on replay.

```python
@server.tool()
async def playwright_exec(code: str, session_id: str | None = None) -> dict:
    """Run JS against a stateful Playwright session. Return console, errors, page state."""
    sess = sessions.get(session_id) or sessions.new()
    return await sess.run(code)
```

**When to use:** session-oriented domains (debuggers, browsers, REPLs, kernels), tools that share a single implicit context object, workflows where the model benefits from composing primitives.
**When NOT to use:** untrusted code inputs without sandboxing, multi-tenant services where code-as-input becomes an injection vector, discoverability-sensitive APIs where each method needs its own contract.

**Source:** [Armin Ronacher — MCP is a prison; code is the way out](https://lucumr.pocoo.org/2025/8/18/code-mcps/), 2025-08.

---

## Pattern 9: Audit Tool Coverage vs Usage — Expect 70% Dead Weight

Speakeasy's Playwright-MCP analysis found that on a SauceDemo e-commerce run the agent **used 8 of 26 exposed tools and still took unnecessary screenshots** compared with a curated 3-tool subset. Frontier LLMs degrade around ~30 tools; smaller models around ~19. Most MCP servers expose a superset because the underlying API has that many endpoints, not because the agent needs them all.

Audit rule: for each tool, count actual invocations in a week of real traces. Drop or gate any tool with <5% of total calls. Ronacher's version: *"many MCP servers don't need to exist. They're either bad API wrappers or truly replaceable by a skill."*

**When to use:** any MCP with >15 exposed tools.
**When NOT to use:** server still in pre-1.0 and usage data is not meaningful yet.

**Source:** [Speakeasy — Playwright tool proliferation](https://www.speakeasy.com/blog/playwright-tool-proliferation), 2025-01; [Speakeasy — Skills vs MCP](https://www.speakeasy.com/blog/skills-vs-mcp), 2026-02.

---

## Pattern 10: Use Skills for Workflow Knowledge, Not Tool Access

Claude Code Skills — now a portable **Agent Skills Open Standard** across Claude Code, Cursor, Amp, goose, OpenCode, Letta, GitHub, VS Code, and OpenAI Codex (added 2025-12-20) — are the right primitive for "how to do X." Their budget profile beats MCP for static playbooks: 1,536-char description limit, 500-line SKILL.md cap, 5,000 tokens re-attached per invocation, 25K combined re-attach budget, 1% context window with 8,000-char fallback.

Skills use progressive disclosure: metadata at startup, body on activation, scripts never enter context at all. Supporting scripts are *executed, not loaded*. Shell preprocessing with `` !`command` `` and fenced `!` blocks injects dynamic context without a tool call.

**When to use:** runbooks, coding-standard enforcement, evals playbooks, domain-specific review rules, "when X then Y" knowledge that doesn't need OAuth.
**When NOT to use:** anything that requires per-user auth, per-call rate-limit accounting, or centralized observability. Those are MCP's job.

**Source:** [code.claude.com — Agent Skills](https://code.claude.com/docs/en/skills), 2025-12; [Simon Willison — Agent Skills](https://simonwillison.net/2025/Dec/19/agent-skills/), 2025-12.

---

## Pattern 11: Ship `allowed-tools`, `context: fork`, and Shell Preprocessing as a Unit

Skills become serious alternatives to MCP once you use all three capabilities together:

- **`allowed-tools`** gives each skill a least-privilege capability manifest (e.g. `allowed-tools: Bash(git:*) Bash(jq:*) Read`). Pre-approved for the activation, no MCP auth overhead.
- **`context: fork`** isolates a skill into a subagent; the parent pays only for the final summary. Any skill whose intermediate state would exceed ~25K tokens should fork.
- **Shell preprocessing** injects live state into the skill body before the model reads it: `` !`gh pr view $ARGUMENTS --json` `` puts current PR state into the prompt with zero tool calls.

```markdown
---
name: triage-pr
allowed-tools: Bash(gh:*) Bash(jq:*) Read
context: fork
---

Current PR state:
!`gh pr view $ARGUMENTS --json title,body,files,reviews`

Apply repo review rules from references/rules.md to the diff above.
```

This combination replaces a large class of MCP servers (GitHub, Linear, JIRA read-only queries, eval dashboards) with zero protocol overhead.

**Source:** [code.claude.com — Agent Skills](https://code.claude.com/docs/en/skills), 2025-12; [Simon Willison — Agent Skills](https://simonwillison.net/2025/Dec/19/agent-skills/), 2025-12.

---

## Pattern 12: Keep MCP for OAuth, Multi-Tenancy, and Non-CLI SaaS

Speakeasy: *"under ~5 developers, skills + direct API calls beat MCP; past org scale, MCP wins on credential custody, blast radius, centralized updates, structured schema."* Dead Neurons, which otherwise argues against MCP: *"The one thing MCP does well is authentication. MCP may survive as an interface layer handling authentication in chat UIs."*

Reserve MCP for workloads where at least one of these is true:

- Multi-tenant SaaS with per-user OAuth (Linear, Notion, Figma, internal tools)
- No credible first-party CLI and no reasonable path to `curl` the API directly
- Centralized blast-radius control (one audit log, one kill switch, one update path)
- Structured schema consumption by non-Claude agents that expect JSON-RPC

**When NOT to use:** solo developer, CLI already covers the endpoints, static playbook with no per-user state.

**Source:** [Speakeasy — Skills vs MCP](https://www.speakeasy.com/blog/skills-vs-mcp), 2026-02; [Dead Neurons — Forget MCP, Bash Is All You Need](https://deadneurons.substack.com/p/forget-mcp-bash-is-all-you-need), 2026-02.

---

## Pattern 13: Track `tools/get_schema` + Lazy Hydration as the Protocol-Native Fix

MCP Issue #1978 proposes a `minimal` flag on `tools/list` plus on-demand `tools/get_schema` fetches. Practical footprint: **~5K tokens upfront, ~400 tokens per schema fetched**. SEP-1576 analysis of GitHub's 60 tools shows 60% share identical `owner` and 65% share identical `repo` parameters, making `$ref` dedup a free win. A MySQL MCP using lazy hydration reported 91% savings (54,604 → 4,899 tokens for 106 tools).

Track this before you commit to a bespoke gateway. If the protocol converges on lazy hydration, the gateway becomes redundant; if it doesn't, Pattern 14 is the fallback.

**When to use:** future-proofing an MCP roadmap, choosing between protocol-native and home-grown solutions.

**Source:** [Layered — MCP tool schema bloat](https://layered.dev/mcp-tool-schema-bloat-the-hidden-token-tax-and-how-to-fix-it/), 2026-01.

---

## Pattern 14: Hybrid A — Skills Describe, MCP Executes, CLI Fills Gaps

The production-grade layered architecture from Speakeasy and Block Goose. Skills encode judgment; MCP handles authenticated live-data fetch; CLI steps (`kubectl logs`, `jq`, `awk`) drop into shell blocks inside the skill.

Example — an incident-triage skill:

```markdown
---
name: triage-incident
allowed-tools: Bash(kubectl:*) Bash(jq:*)
---

1. Call `list_recent_deploys` (MCP tool, needs auth) and pick the deploy window.
2. Pull logs for the suspect pod:
   !`kubectl logs -n prod <pod> --since=30m | tail -500`
3. Apply references/playbook.md to the combined evidence.
4. If mitigation is needed, call `create_rollback` (MCP tool, needs approval).
```

**When to use:** org-scale runbooks with live services, anything that mixes authenticated writes with free-text reasoning over logs.

**Source:** [Speakeasy — Skills vs MCP](https://www.speakeasy.com/blog/skills-vs-mcp), 2026-02.

---

## Pattern 15: Hybrid B — Code Execution with MCP (Anthropic Canonical)

Expose MCP tools as TypeScript/Python files on disk. The agent discovers them via the filesystem and composes them in generated code; responses flow tool-to-tool **without re-entering the model context**. Anthropic's benchmarked reduction: 150K → 2K tokens (98.7%).

```python
# agent generates and runs this; MCP tools are imported, not round-tripped
from mcp_tools.linear import search_issues
from mcp_tools.github import list_prs

issues = search_issues(status="open", label="regression")
prs = list_prs(state="open")
joined = [(i, next((p for p in prs if p.linked_issue == i.id), None)) for i in issues]
return [(i.title, p.url if p else None) for i, p in joined][:10]
```

This is Hybrid A's more aggressive sibling: it keeps MCP's auth and discovery but eliminates envelope cost entirely.

**When to use:** fan-out/aggregate/filter across multiple MCP services in one turn, data-heavy joins, any workflow currently burning >10 sequential tool calls.
**When NOT to use:** workloads that require per-call human approval or audit entries.

**Source:** [Anthropic — Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp), 2025-11; [Simon Willison — Code execution with MCP](https://simonwillison.net/2025/Nov/4/code-execution-with-mcp/), 2025-11.

---

## Pattern 16: Hybrid C — Meta-Tool Gateway for 100+ Tool Universes

Bifrost's "meta-tool gateway" result: **508 tools behind 4 meta-tools** (`list_servers` / `get_tool_signature` / `get_docs` / `execute`). Input tokens 75.1M → 5.4M; $377 → $29 per test run. Scaling curve: 58% savings at 96 tools, 84% at 251, **92% at 508**.

This is the pattern for enterprise MCP catalogs that can't be pruned. Until `tools/get_schema` lands (Pattern 13), a gateway is the only way to expose 100+ tools without descriptor bloat swamping the window.

**When to use:** 100+ tool catalogs across multiple MCP servers, enterprise marketplaces, long-tail tool discovery where Tool Search's 10% threshold isn't enough.
**When NOT to use:** under 30 tools total — the indirection costs more than it saves.

**Source:** [r/Anthropic — We cut MCP token costs by 92%](https://reddit.com/r/Anthropic/comments/1skmbyp/we_cut_mcp_token_costs_by_92_by_not_sending_tool/), 2025-11.

---

## Pattern 17: The MCP-vs-CLI-vs-Skills-vs-Hybrid Decision Rubric

Score each axis 1–5. Higher score pushes toward that column. Sum columns; highest sum wins.

| Axis | MCP | CLI/bash | Skills | Hybrid (MCP+skill / PTC) |
|------|-----|----------|--------|--------------------------|
| **Task type** — first-party CLI already exists                         | 1 | 5 | 2 | 3 |
| **Task type** — static playbook / "how to do X"                        | 1 | 2 | 5 | 3 |
| **Task type** — OAuth per user / multi-tenant SaaS                     | 5 | 1 | 1 | 4 |
| **Task type** — fan-out / aggregate / filter across ≥5 records         | 1 | 3 | 2 | 5 |
| **Context pressure** — tool defs would exceed 10% of window            | 1 | 5 | 4 | 4 |
| **Context pressure** — loop ≥10 iterations in a single turn            | 1 | 4 | 3 | 5 |
| **Latency budget** — sub-second step required                          | 1 | 5 | 4 | 3 |
| **Latency budget** — pipeline ≥3 dependent steps                       | 1 | 4 | 3 | 5 |
| **Reversibility** — must be replayable without re-inference            | 1 | 5 | 4 | 3 |
| **Reversibility** — mutating with high blast radius                    | 5 | 1 | 2 | 4 |
| **Auth surface** — multi-tenant, centralized observability needed      | 5 | 1 | 2 | 4 |
| **Auth surface** — single dev, local credentials                       | 1 | 5 | 4 | 2 |
| **Auth surface** — vendor has no CLI and no public API wrapper         | 5 | 1 | 2 | 4 |

**Flowchart (prose):**

1. Does a working first-party CLI exist? → **CLI**.
2. Is it static guidance / a playbook? → **Skill**.
3. Does it require OAuth plus multi-tenant access? → **MCP** (consider Hybrid A).
4. Does it need ≥3 dependent tool calls, batch, or filter? → **PTC** (Hybrid B).
5. Is it a recurring multi-step workflow with both judgment and live data? → **Hybrid A (skill + MCP + CLI)**.
6. None of the above, and tool-def cost is already >10% of window? → **Tool Search** first, then migrate if still bloated.
7. 100+ tool catalog? → **Meta-tool gateway** (Hybrid C).

---

## Pattern 18: Contrarian Voices — Arguments FOR Keeping MCP

The "kill MCP" consensus overshoots in two places. Both deserve to show up in any audit.

- **Auth and governance are not bash's job.** Dead Neurons concedes: *"The one thing MCP does well is authentication. MCP may survive as an interface layer handling authentication in chat UIs."* Enterprise governance — audit trails, kill switches, SSO-bound credentials — has no free-tier equivalent in "just run bash." Source: [Dead Neurons — Forget MCP, Bash Is All You Need](https://deadneurons.substack.com/p/forget-mcp-bash-is-all-you-need), 2026-02.
- **"X is all you need" is wrong.** Cra.mr 2026-01: MCP is a layer, not a competitor to skills or bash. *Real* problem: bad MCPs — thin API wrappers, over-exposed tool sets. Multi-tenant SaaS and non-CLI integrations (Figma, Notion, internal APIs) have no credible alternative. Source: [cra.mr — MCP, Skills, and Agents](https://cra.mr/mcp-skills-and-agents/), 2026-01.

---

## Pattern 19: Contrarian Voices — Arguments AGAINST MCP

Take these seriously before investing in a bespoke MCP:

- **"The OS is the runtime MCP is reinventing"** — Dead Neurons 2026-02: the protocol *"keeps reinventing the OS."* Deferred loading is *"just running a binary when you need it."* PTC is *"what shell scripts have done since 1977."* *"The protocol isn't converging on bash specifically; it's converging on POSIX."* Source: [Dead Neurons — Forget MCP, Bash Is All You Need](https://deadneurons.substack.com/p/forget-mcp-bash-is-all-you-need), 2026-02.
- **MCP is composability-hostile at the protocol level** — Ronacher 2025-07: *"It isn't truly composable. It demands too much context."* Every tool call is a model inference pass, so composition cost is multiplicative rather than free. Source: [Armin Ronacher — Tools: Code is all you need](https://lucumr.pocoo.org/2025/7/3/tools/), 2025-07.
- **Simon Willison's declared stance** — *"I don't use MCP at all any more when working with coding agents. I find CLI utilities and libraries like Playwright Python to be a more effective way."* Reaffirmed 2025-12: *"the best possible tool for any situation is Bash."* Source: [Simon Willison — Code execution with MCP](https://simonwillison.net/2025/Nov/4/code-execution-with-mcp/), 2025-11; [Simon Willison — The year in LLMs](https://simonwillison.net/2025/Dec/31/the-year-in-llms/), 2025-12.
- **Hamel Husain's evals-skills synthesis** — all major eval vendors (Braintrust, LangSmith, Phoenix, Truesight) ship MCP servers; Husain's skills pack (`eval-audit`, `error-analysis`) is explicitly complementary. *"MCP gives access to traces and experiments. Skills teach what to do with them."* OpenAI Harness datapoint: 3 engineers, 5 months, ~1M lines with Codex agents; infrastructure around the agent (skill design + tool choice) drove outcomes more than model upgrades. Source: [Hamel Husain — Evals and Skills](https://hamel.dev/blog/posts/evals-skills/), 2026-03.
- **Unix-philosophy fit** — LLMs are text-native, so POSIX tools compose for free. Dead Neurons: *"Composition is free because the OS provides it. Strip out MCP and you still have a great agent; strip out bash and you have nothing."* Cowork shipped its agent with 4 engineers in 10 days; OpenClaw Pi runs a ~10-line system prompt. Source: [Korny Sietsma — LLMs and Unix tools](https://blog.korny.info/2025/07/11/llms-unix-tools), 2025-07; [Dead Neurons — Forget MCP, Bash Is All You Need](https://deadneurons.substack.com/p/forget-mcp-bash-is-all-you-need), 2026-02.

---

## Summary Checklist

Before you build or keep an MCP server, confirm every line:

- [ ] No first-party CLI covers this endpoint set (Pattern 1).
- [ ] Exposed tool count stays under the safe band for your window (Pattern 2).
- [ ] Cost-per-conversation for static tool definitions is acceptable (Pattern 3).
- [ ] Tool Search or a meta-tool gateway is enabled if descriptors exceed 10% (Patterns 4, 16).
- [ ] Fan-out/aggregate paths use PTC or Code Execution, not sequential calls (Patterns 5, 15).
- [ ] Per-call envelope cost vs payload ratio is reasonable (Pattern 7).
- [ ] Tool-usage audit shows ≥30% of exposed tools actually get called (Pattern 9).
- [ ] Static knowledge lives in a skill, not a tool (Patterns 10, 11).
- [ ] OAuth / multi-tenant / centralized-governance justifies keeping MCP (Pattern 12).
- [ ] Hybrid option (Pattern 14 or 15) has been scored against pure MCP.
- [ ] The rubric (Pattern 17) was run with actual numbers, not intuition.

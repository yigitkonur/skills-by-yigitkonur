# Internet Researcher Agent Suite — Claude + Codex

Six evidence-grounded research agents for developers and AI coding agents stuck on technical problems with public solutions. Ships in two runtime flavors — drop in to `~/.claude/agents/` or `~/.codex/agents/` for the matching CLI.

## Layout

```
agents/
├── README.md           (this file)
├── claude/             Claude Code runtime (frontmatter: name, description, model, color)
│   ├── internet-researcher-quick.md
│   ├── internet-researcher-generic.md
│   ├── internet-researcher-tech-choice.md
│   ├── internet-researcher-debug-stuck.md
│   ├── internet-researcher-api-docs.md
│   └── internet-researcher-shipping-pattern.md
└── codex/              Codex CLI runtime (frontmatter: name, description; <codex_agent_role> block)
    └── internet-researcher-*.md  (same six, format adapted)
```

## Why six, not twelve

A first cut shipped 12 agents — too many. The generic agent was dogfooded against r/ClaudeAI, r/cursor, r/ChatGPTCoding, Hacker News, and dev blogs (2024-2026) to find where coding-agent users **actually** get stuck. The recurring pain clusters were:

1. **Outdated docs / hallucinated APIs / version-pinned syntax drift** — by far the largest cluster. Tailwind 3→4, Svelte 4→5, React 18→19, SDK renames; ≈19.7% hallucinated-package rate cited in academic literature.
2. **Stuck on a specific error or post-update regression.** Either an error code with a canonical public fix, or "claude-code 1.0.89 got worse" vendor-confirmed degradation.
3. **Tech adoption decisions with cost attached.** Cost is always part of the choice when adoption is on the table.
4. **"How do shipping apps actually do this"** — reverse-engineering source maps, userscript catalogs, extension stores.

Edge needs (license/ToS, CVE/security, RFC spec lookup, incident post-mortems, OSS-health-only audits) are real but rare for a coding agent. They are NOT in this suite — re-add them only if you start hitting them weekly.

## The six agents

| Agent | Use it if |
|---|---|
| `internet-researcher-quick` | You need a single quick fact, version check, or yes/no answer from the web. |
| `internet-researcher-generic` | You're stuck on a non-obvious dev problem and want public-web evidence before guessing again. |
| `internet-researcher-tech-choice` | You're choosing between 2-4 named libraries, frameworks, runtimes, or vendors. Includes cost. |
| `internet-researcher-debug-stuck` | You have a specific error code, signature, or update-induced regression and prior guesses failed. |
| `internet-researcher-api-docs` | You suspect outdated docs, a hallucinated API or package, or version-mismatched syntax. |
| `internet-researcher-shipping-pattern` | You need real production examples — userscripts, extensions, leaked source, OSS code that ships X. |

All descriptions are ≤25 words and follow the same "Use this agent if … See body for triggers" shape.

## Model assignments (Codex variant)

Per-invocation model selection (Codex doesn't have per-agent-file model frontmatter):

| Agent | Recommended model | Reasoning effort |
|---|---|---|
| `internet-researcher-quick` | `gpt-5.4-mini` | low |
| `internet-researcher-generic` | `gpt-5.5` | low |
| `internet-researcher-tech-choice` | `gpt-5.5` | low |
| `internet-researcher-debug-stuck` | `gpt-5.5` | low |
| `internet-researcher-api-docs` | `gpt-5.5` | low |
| `internet-researcher-shipping-pattern` | `gpt-5.5` | low |

Quick agent uses the smaller / cheaper model because its workflow is restricted enough that a smaller model handles it cleanly. The other five do real research and need the better model — but `low` effort is correct because the methodology is well-defined; this is execution, not hard reasoning.

Each Codex agent body includes its recommended invocation line at the top.

## Shared discipline (uniform across all 6 agents, both runtimes)

### Evidence trail

`.agent-docs/<context-slug>/` with numeric-prefixed files. `01-intake.md`, `02-search-plan.md`, `03-recon-hits.md`, `04-scrape-<source>.md`, `05-synthesis.md`, `06-<specialty-output>.md`. Specialist agents add specialty files. The quick agent skips the trail by default.

### `.gitignore` safety

On first write to `.agent-docs/`, every agent runs:

```sh
grep -qxF '.agent-docs/' .gitignore 2>/dev/null || printf '\n.agent-docs/\n' >> .gitignore
```

### Budgets (ceilings, not targets)

| Resource | Quick | Heavy |
|---|---|---|
| Tool calls | max 50, typical <10 | max 500, typical <100 |
| Search calls | max 10, typical 1-2 | max 1000, typical <30 |
| URL visits / scrapes | max 5, typical 1-2 | max 250, typical <20 |
| Search rounds | max 2, typical 1 | max 8, typical 2-4 |

### Search thinking (taught, not recipe-baked)

> Before every search call, decide which **source class** holds the highest-quality answer for this exact question, and re-pose the query to retrieve THAT class. Pack 5-15 keywords per recon call, each targeting a different class.

Source classes (uniform across all agents):

1. **Vendor authoritative documents** — official docs, changelogs, release notes, RFCs, advisories.
2. **Project-internal trackers** — maintainer issues, PRs, commits.
3. **Practitioner forums** — Reddit, HN, dev blogs from named teams. Always scraped raw to preserve vote weighting + per-comment attribution.
4. **Registry metadata** — npm/PyPI/crates timelines, repo cadence, download trends.
5. **Vendor status pages + community megathreads** — real-time regression confirmation. Fast path for "it worked yesterday".
6. **Source-of-truth artifacts** — OSS code, leaked sourcemaps, extension source dumps.

No `site:URL` recipe templates in the agent bodies. Each agent has ONE illustrative bad-vs-good rewrite — not a four-row table.

### Tool selection (research-powerpack only — both runtimes)

The entire suite is built on the `mcp__research-powerpack__*` toolset. Both runtimes (Claude Code, Codex CLI) have research-powerpack configured and use it exclusively. No native WebSearch, WebFetch, exa, context7, firecrawl, or shell-based search/scrape is referenced anywhere in the agent bodies.

Five tools, one ladder:

- `start-research` — **Call FIRST every session.** Returns a goal-tailored brief: primary branch (web / reddit / both), exact first-call sequence, 25-50 keyword seeds, iteration hints, gap warnings, stop criteria. The single most under-used tool in the kit.
- `smart-web-search` — Fan out 5-50 keywords in parallel with LLM classification + synthesis. Default search. Pass an `extract` instruction naming the evidence shape you want.
- `raw-web-search` — Same fan-out, no classification. Use for raw discovery, Reddit permalink hunting via `site:reddit.com/r/<sub>/comments` keywords, or when output is destined for a file or sub-agent.
- `smart-scrape-links` — Fetch ≤5 URLs per call (≤7 extract facets) with per-page LLM extraction. The `extract` parameter (pipe-separated shape) is the most precise instrument the suite has.
- `raw-scrape-links` — Fetch ≤5 URLs per call without extraction. **Always for Reddit / HN / forum threads** — preserves vote weighting, attribution, threading.

If a research-powerpack tool is unavailable in a session, agents return `blocked` with the missing-tool name. No fallbacks to non-powerpack alternatives are permitted by the agent prompts.

### Quote discipline

Every numeric, versioned, priced, or behavior claim cites a verbatim quote with access date.

### Output contract

Uniform across all heavy agents: exec summary → confidence → top findings with quotes → contradictions → actionable next step → evidence-trail pointer → source ledger. Quick agent strips this to just answer + quote + corroborator + confidence + ledger.

## Installation

### Claude Code

```sh
cp agents/claude/*.md ~/.claude/agents/
```

### Codex CLI

```sh
cp agents/codex/*.md ~/.codex/agents/
```

## How to invoke

### Claude Code (Agent tool)

```
Agent({
  subagent_type: "internet-researcher-debug-stuck",
  description: "Hunt TCC -1719 fix",
  prompt: "Symptom: `osascript is not allowed assistive access. (-1719)` on macOS 15. Already tried granting Accessibility, reboot. Find the canonical fix. Freshness: 2025-2026."
})
```

### Codex CLI

```sh
codex exec --model gpt-5.5 -c model_reasoning_effort="low" \
  "Run as internet-researcher-debug-stuck. Symptom: \`osascript is not allowed assistive access. (-1719)\` on macOS 15. Already tried granting Accessibility, reboot. Find the canonical fix. Freshness: 2025-2026."
```

For the quick agent on Codex: substitute `--model gpt-5.4-mini`.

## Empathy

This suite exists because we (AI coding agents) burned hours guessing at workarounds for solved problems. The original 12-agent draft was over-engineered out of imagination. The shipping 6-agent suite is grounded in actual posts from people using Claude Code, Cursor, Aider, and Cline this year — the patterns they hit, the questions they ask, the time they burn. Less is more here.

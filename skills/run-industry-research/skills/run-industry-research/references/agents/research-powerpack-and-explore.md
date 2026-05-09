# Research-Powerpack and Parallel Explore

Concrete invocation patterns for the research-powerpack MCP and parallel Explore subagents — the two tool families this skill leans on most.

Read this in **Phase 1, 4, and 5** when dispatching research work.

## Tool inventory

### Research-powerpack MCP tools

| Tool | What it does | Use for |
|---|---|---|
| `mcp__research-powerpack__start-research` | Multi-source web research orchestrator. Takes a brief, returns a synthesized findings document. | Phase 1 discovery; Phase 4 entity-deep-dive starts |
| `mcp__research-powerpack__web-search` | Single targeted search query. Returns ranked links with snippets. | Phase 4-5 quick fact checks; gap filling |
| `mcp__research-powerpack__scrape-links` | Extract links from a page (e.g., review aggregators, category pages). | Phase 1 candidate harvesting; Phase 4 status-page indexing |

### Parallel Explore subagents

`Explore` is the read-only search agent (Glob + Grep + Read). For industry research it serves two roles:

1. **Local-corpus Explore** — search inside the evolving research corpus for cross-references, duplicate entities, source URLs already cited.
2. **Distributed-research Explore** — dispatch one Explore per sub-question or per entity, each running its own search rounds; results merge into the orchestrator.

### Fallback chain

When the MCP is unavailable:

| Lost capability | Fallback |
|---|---|
| `start-research` | Parallel Explore subagents (one per sub-question) running `WebSearch` + `WebFetch` |
| `web-search` | `WebSearch` direct |
| `scrape-links` | `WebFetch` to the page + manual link extraction in the output, OR `curl` |

State the fallback explicitly in the workflow. Do not silently degrade.

## When to use which tool

```
Need: discover entities in a category
├── Have: research-powerpack MCP
│   └── Use: start-research with sub-question brief
└── Have: only base tools
    └── Use: parallel Explore subagents, one per sub-question

Need: research one entity in depth (Phase 4)
├── Have: research-powerpack MCP
│   ├── Initial broad pass: start-research per entity
│   └── Targeted gap-filling: web-search + scrape-links
└── Have: only base tools
    └── Single Explore per entity, dispatched in parallel waves of ≤8

Need: cross-reference inside the growing corpus
└── Always: local-corpus Explore (read-only inside the corpus folder)

Need: extract a candidate list from a category review page
├── Have: scrape-links → use directly
└── Have: only base tools → WebFetch + parse
```

## Pattern A: discovery via start-research

Phase 1, full-MCP path.

```
mcp__research-powerpack__start-research:
  brief: |
    # Discovery brief: [topic-slug] category

    ## Goal
    Discover entities (products, projects, vendors) in the [topic] category.
    Output a candidate list with name, URL, vendor/maintainer, one-line description,
    apparent tier (incumbent / challenger / niche / adjacent), and which sub-question
    surfaced it.

    ## Sub-questions (decompose discovery to surface different candidate clusters)
    1. [Sub-question 1 — incumbents/leaders]
    2. [Sub-question 2 — challengers]
    3. [Sub-question 3 — open-source alternatives]
    4. [Sub-question 4 — geographic outliers]
    5. [Sub-question 5 — recent entrants in last 12 months]

    ## Constraints
    - Status check each candidate (active / dead / waitlist / acquired) with one-line evidence
    - Note duplicates / same product under different names
    - Flag adjacent solutions vs. direct competitors
    - Cap candidate count at ~30; tier the long-tail as "discovered-only"

    ## Hand-back format
    Markdown table with columns: name | url | vendor | tier-candidate | status | surfaced-by | notes
    Plus a short narrative section: in-scope rationale, out-of-scope boundary rule, watch-list
```

The MCP returns a research output file or summary. Capture it into `_meta/discovered-entities.md`.

## Pattern B: discovery via parallel Explore (no MCP)

```
Dispatch N agents in parallel (one per sub-question, max 8 per wave):

Agent 1 — sub-question 1
  - Use WebSearch with keywords: "[category name] best 2025", "[category] alternatives"
  - Run 5-8 queries with varied phrasing
  - For each candidate: WebFetch the homepage, check status (last update, pricing visible)
  - Return: candidate list with status notes

Agent 2 — sub-question 2 (challengers)
  - Use WebSearch: "[category] vs [incumbent]", "switched from [incumbent]"
  - Reddit/HN search for migration stories
  - Return: candidate list with migration-story URLs

[... up to 8 agents in parallel ...]

Orchestrator merges results into _meta/discovered-entities.md
```

Each Explore agent's prompt should be self-contained (it has no conversation context). Pattern:

```
Discover candidates in the [topic] category that match this sub-question:
"[sub-question text]"

Use WebSearch with these keyword shapes (run ≥5 queries, varying phrasing):
- "[category] best 2025"
- "[category] alternatives"
- "[category] open-source"
- "[category] vs [known competitor]"
- "[category] reddit"

For each candidate found:
- WebFetch the homepage
- Capture: name, URL, vendor/maintainer, one-line description, last public update date,
  visible pricing presence, status (active/dead/waitlist/acquired)

Return a markdown table of candidates plus a short narrative on:
- Which queries returned the most distinct candidates
- Any candidates that look adjacent rather than direct
- Any candidates whose status was hard to determine

Report under 500 words.
```

## Pattern C: per-entity research via start-research

Phase 4, full-MCP path. One MCP call per `core` entity (parallelizable in waves of 8).

```
mcp__research-powerpack__start-research:
  brief: |
    # Entity research: [entity-slug] in [topic-slug] corpus

    ## Goal
    Build the evidence pack for [entity name]. The corpus uses these subfolder
    categories (resolved from Phase 2 taxonomy):
    - 00-overview, 01-pricing, 02-platform, 03-integrations, 04-operations,
      05-security, 06-audience, 07-benchmarks, 08-buyer-fit, 09-sources
    [or whatever the resolved Phase 2 list is]

    ## Sub-questions per category
    1. Overview: what does [entity] sell, who is the target buyer, what is the positioning?
    2. Pricing: what are the public plans, native units, overages, hidden costs?
    3. Platform: what is the control surface, session model, state model?
    4. Integrations: what SDKs, MCP servers, agent-framework support?
    5. Operations: reliability, status page history, observability, limits?
    6. Security: stealth/proxy/captcha (if relevant), compliance, legal risk?
    7. Audience: Reddit/HN/forum sentiment, migration stories, complaints?
    8. Benchmarks: any published performance claims, test plan, reproducibility?
    9. Buyer fit: scenarios where it wins vs. loses, alternatives, do-not-choose-if
    10. Sources: source map and claims ledger

    ## Required source mix
    - Official docs, pricing pages, changelog
    - Status page if exists
    - GitHub repos / SDK code
    - Reddit search: "[entity] reddit"
    - HN search: "[entity] hackernews"
    - Review aggregators if available

    ## Output ownership
    Files under [entity-slug]/ only. Do not edit other entities or root files.
    Each file has a single concern. No placeholder content.

    ## Hand-back
    List of files created with one-line summary each, plus open gaps and source-quality concerns.
```

## Pattern D: targeted gap-filling via web-search

Phase 4 or 5, when the orchestrator needs a specific fact:

```
mcp__research-powerpack__web-search: "Browserbase pricing 2025"
→ returns ranked URLs and snippets

mcp__research-powerpack__web-search: "Anchor Browser switched from Browserbase reddit"
→ returns Reddit threads with migration discussion
```

Use this when:
- A specific number is missing from an entity pack
- A claim needs cross-validation
- A practitioner anecdote needs sourcing

## Pattern E: candidate-list extraction via scrape-links

Phase 1 supplement. Useful when a category-review site lists 30 entities you want to harvest:

```
mcp__research-powerpack__scrape-links: "https://www.g2.com/categories/[category]/products"
→ returns list of links from the page

mcp__research-powerpack__scrape-links: "https://github.com/[curated-list-repo]"
→ returns links from a curated list repo's README
```

Filter the returned links for plausible entity homepages, then status-check each via WebFetch.

## Parallel-wave dispatch rules

When dispatching multiple agents in parallel (Phase 1 discovery, Phase 4 entity research, Phase 5 cross-comparison):

1. **Maximum 8 agents per wave.** More than 8 overwhelms context budget.
2. **Disjoint write scopes.** Each agent owns exactly one folder. Two agents writing to the same folder produces conflicts.
3. **No subagent recursion.** Agents do not spawn subagents. Two-level orchestration only.
4. **Self-contained prompts.** Each agent's brief carries all context — they do not see the conversation.
5. **Process completed agents as they return.** Do not wait for the slowest before writing files. Start integrating Wave 1 results while Wave 2 runs.
6. **2-retry max on failure.** If an agent fails, retry once with a narrower brief. If it fails again, mark the entity as `insufficient-evidence` in `_meta/` and move on.
7. **Orchestrator reads outputs personally** before final synthesis. The orchestrator owns Phase 5 cross-synthesis and Phase 6 profile pages — those are not delegated.

## Combining MCP and Explore in one phase

A typical Phase 4 sequence for one entity:

```
1. mcp__research-powerpack__start-research → broad evidence pack draft
2. Read the draft; identify gaps (missing pricing scenario, missing Reddit signal)
3. mcp__research-powerpack__web-search → fill specific gaps
4. mcp__research-powerpack__scrape-links → harvest related pages if needed
5. Local Explore → cross-reference inside the corpus to avoid duplicating cross-product files
6. Write or refine the entity-pack files
```

## Tool-availability check

Before Phase 1, run a one-line probe:

```
# Check MCP availability
Probe: are the mcp__research-powerpack__* tools listed in the available tools?
```

Capture the result in `_meta/methodology-and-source-policy.md` so the corpus records which tools were used (and which fallbacks).

## Common failures

| Failure | Cause | Recovery |
|---|---|---|
| MCP returns sparse results | Brief too generic | Add concrete sub-questions and required source mix |
| MCP times out on a long brief | Single brief too broad | Split into 2-3 briefs run sequentially or in parallel |
| Parallel Explore agents overlap | Write scopes not disjoint | Re-dispatch with explicit "you own only [path]" |
| Agent returns 200 lines of unsourced prose | Brief didn't require source URLs per claim | Re-brief with "every claim cites a URL or local file" |
| One slow agent blocks the wave | Sequential read of agent results | Process completed agents as they return; don't gate on the last one |
| Same fact arrives 3 times | No de-duplication step | Add an explicit "check existing pack before writing" step in the brief |

## Worked-example tool log

The cloud-browsers corpus (293 files, 12 entities) used:

- **Phase 1:** 1 `start-research` call for category discovery, plus 5 `web-search` follow-ups per gap → 25 candidates → tiered to 12 core
- **Phase 4:** 12 parallel `start-research` calls (2 waves of 6 each), 1 per `core` entity. Average ~30 follow-up `web-search` calls across all entities for gap-filling
- **Phase 5:** 10 cross-criterion comparison agents (one per criterion folder), each a parallel Explore run reading completed entity packs locally
- **Phase 6:** 12 profile pages written by orchestrator personally (no agent delegation)

Total tool calls: ~60 MCP calls + ~40 fallback WebSearch when MCP rate-limited + ~150 local Explore reads.

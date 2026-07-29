# Research Power Pack And Research Agents

Portable invocation patterns for Research Power Pack tools, web-capable research agents, and local-corpus Explore.

Read this in **Phase 1, 4, and 5** when dispatching research work.

## Tool inventory

Tool names vary by runtime. Verify the available tool names before Phase 1 and record the result in `_meta/methodology-and-source-policy.md`.

### Research Power Pack API shapes

| Portable API | What it does | Use for |
|---|---|---|
| `plan-research` | Takes one `objective` string and returns a plan: decision-critical clusters, checkable evidence requirements, query ideas (≤100 global, ≤25 per cluster — ceilings, not quotas), a first wave of ≤12 queries, source-selection signals, reserves, gaps, budgets, and stop conditions. | Phase 1 discovery; Phase 4 entity-deep-dive starts |
| `web-search` | Takes `queries`: 1-50 complete retrieval queries. Returns up to 100 ranked, canonicalized sources with original/dispatched/relaxed lineage and cluster-capped consensus. `evidence_status` is always `leads-only`. Reddit discovery is a `site:reddit.com/r/.../comments` query, not a parameter. | Broad URL harvesting; Reddit permalink discovery; subagent triage; gap-driven follow-ups (expect multiple calls across 2-4 rounds) |
| `extract-evidence` | Takes `urls` (≤20) and `evidence_requirements` (≤20 checkable questions). Returns per-requirement status (`answered`, `partial`, `not-found`, `conflicting`) with exact quotations and code-derived locators, plus coverage, contradictions, and continuation state. Reddit permalinks route through the Reddit API (full threaded fetch) automatically. | Docs/blog extraction; fact checks; source-backed synthesis; Reddit/practitioner capture |
| `review-research` | No arguments. Reviews only the server's retained same-session trace and returns `ready`, `continue`, or `blocked` plus ≤3 scored next calls. | End-of-round check inside a single research task, before it reports back |

Search and extraction are separate stages, and only extraction produces
evidence. Use `web-search` when you need a ranked URL pool and haven't decided
what to read; use `extract-evidence` with explicit requirements whenever you
need actual content, quotations, or Reddit thread analysis. Two contract rules
travel with every corpus task: a search title or snippet is never a citation,
and a result carrying `continuation.required: true` must be finished by invoking
its exact `continuation.next_call` in the same session before the task writes
its files. Tiering and gap analysis remain the agent's own synthesis work.

### Web-capable research agents and local-corpus Explore

Use **web-capable research agents** for distributed web work when MCP tools are missing or when independent entity/criterion missions can run in parallel. The agent must have web search/fetch tools in its runtime and a self-contained brief.

Reserve **local-corpus Explore** for read-only search inside the generated corpus: cross-references, duplicate entities, source URLs already cited, broken links, and stale filenames.

### Fallback chain

When the MCP is unavailable:

| Lost capability | Fallback |
|---|---|
| `plan-research` | Web-capable research agents, one per sub-question, running `WebSearch` + `WebFetch` |
| `web-search` | `WebSearch` direct |
| `extract-evidence` | `WebFetch` to the page + manual quoting, OR `curl` — and record that quotations are no longer server-verified |
| `review-research` | Orchestrator reviews the round personally against the charter's stop conditions |

State the fallback explicitly in the workflow. Do not silently degrade.

## When to use which tool

```
Need: discover entities in a category
├── Have: Research Power Pack MCP
│   └── Use: plan-research with a sub-question-rich objective
└── Have: only base tools
    └── Use: web-capable research agents, one per sub-question

Need: research one entity in depth (Phase 4)
├── Have: Research Power Pack MCP
│   ├── Initial broad pass: plan-research per entity
│   └── Targeted gap-filling: web-search + extract-evidence
└── Have: only base tools
    └── One web-capable research agent per entity, dispatched in waves

Need: cross-reference inside the growing corpus
└── Always: local-corpus Explore (read-only inside the corpus folder)

Need: extract a candidate list from a category review page
├── Have: extract-evidence → use directly
└── Have: only base tools → WebFetch + parse
```

## Pattern A: discovery via plan-research

Phase 1, full-MCP path.

```
plan-research:
  objective: |
    # Discovery brief: [topic-slug] category

    ## Decision
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

    ## Completion standard
    A candidate table (name | url | vendor | tier-candidate | status | surfaced-by | notes)
    plus in-scope rationale, out-of-scope boundary rule, and watch-list
```

The plan comes back as clusters, requirements, and a bounded first wave of
queries. Execute that first wave with `web-search`, extract the surviving
candidates with `extract-evidence`, and capture the result into
`_meta/discovered-entities.md`. The idea bank is a ceiling — do not search all of it.

## Pattern B: discovery via web-capable research agents (no MCP)

```
Dispatch N agents in parallel (one per sub-question):

Agent 1 — sub-question 1
  - Use WebSearch with keywords: "[category name] best 2025", "[category] alternatives"
  - Run 5-8 queries with varied phrasing
  - For each candidate: WebFetch the homepage, check status (last update, pricing visible)
  - Return: candidate list with status notes

Agent 2 — sub-question 2 (challengers)
  - Use WebSearch: "[category] vs [incumbent]", "switched from [incumbent]"
  - Reddit/HN search for migration stories
  - Return: candidate list with migration-story URLs

[... recommended 6-8 agents in parallel; never exceed 20 ...]

Orchestrator merges results into _meta/discovered-entities.md
```

Each research agent's prompt should be self-contained (it has no conversation context). Pattern:

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

## Pattern C: per-entity research via plan-research

Phase 4, full-MCP path. One planning call per `core` entity (parallelizable in waves).

```
plan-research:
  objective: |
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
web-search:
  queries:
    - "site:browserbase.com pricing browser minutes"
    - "site:reddit.com/r/*/comments Anchor Browser Browserbase migration OR switched"
```

Then verify the facts against whichever URLs the search surfaced:

```
extract-evidence:
  urls:
    - "[pricing page URL from the search above]"
  evidence_requirements:
    - "What are the published plan names and prices?"
    - "What is the native billing unit, and what does an overage cost?"
    - "Which capabilities are gated behind an enterprise or sales-contact tier?"
```

Use this when:
- A specific number is missing from an entity pack
- A claim needs cross-validation
- A practitioner anecdote needs sourcing

A `not-found` on a fetched page is a real answer: record "not published as of
[date]" rather than leaving the pack section blank or filling it from a snippet.

## Pattern E: candidate-list extraction via extract-evidence

Phase 1 supplement. Useful when a category-review site lists 30 entities you want to harvest:

```
extract-evidence:
  urls:
    - "https://www.g2.com/categories/[category]/products"
  evidence_requirements:
    - "Which products are listed on this page, with their vendor URLs?"
    - "What category labels are applied to each listing?"
    - "Is there pagination, and what does it indicate about total count?"

extract-evidence:
  urls:
    - "https://github.com/[curated-list-repo]"
  evidence_requirements:
    - "Which projects are listed, with maintainer and repository URL?"
    - "What last-update signal does the page show per project?"
    - "How does the README describe each project in one line?"
```

Filter the returned links for plausible entity homepages, then status-check each via WebFetch.

## Parallel-wave dispatch rules

When dispatching multiple agents in parallel (Phase 1 discovery, Phase 4 entity research, Phase 5 cross-comparison):

1. **Recommended 6-8 agents per wave; never exceed 20.** Use 6-8 when integration quality or context pressure matters. Use up to 20 only when scopes are cleanly disjoint and output volume is manageable.
2. **Disjoint write scopes.** Each agent owns exactly one folder. Two agents writing to the same folder produces conflicts.
3. **No subagent recursion.** Agents do not spawn subagents. Two-level orchestration only.
4. **Self-contained prompts.** Each agent's brief carries all context — they do not see the conversation.
5. **Process completed agents as they return.** Do not wait for the slowest before writing files. Start integrating Wave 1 results while Wave 2 runs.
6. **2-retry max on failure.** If an agent fails, retry once with a narrower brief. If it fails again, mark the entity as `insufficient-evidence` in `_meta/` and move on.
7. **Orchestrator reads outputs personally** before final synthesis. The orchestrator owns Phase 5 cross-synthesis and Phase 6 profile pages — those are not delegated.

## Combining MCP and Explore in one phase

A typical Phase 4 sequence for one entity:

```
1. plan-research → clusters, requirements, bounded first-wave queries
2. web-search → run that first wave; triage the ranked leads
3. extract-evidence → verify the selected URLs against the plan's requirements
4. finish any continuation.next_call exactly, then read what came back and name the gaps
5. web-search + extract-evidence → fill specific gaps (pricing scenario, Reddit signal)
6. review-research → confirm coverage or take one scored next call
7. Local Explore → cross-reference inside the corpus to avoid duplicating cross-product files
8. Write or refine the entity-pack files
```

## Tool-availability check

Before Phase 1, run a one-line probe:

```
# Check MCP availability
Probe: which Research Power Pack tools are available (`plan-research`, `web-search`, `extract-evidence`, `review-research`), and which fallbacks are available (`WebSearch`, `WebFetch`, `curl`)?
```

Capture the result in `_meta/methodology-and-source-policy.md` so the corpus records which tools were used (and which fallbacks).

## Common failures

| Failure | Cause | Recovery |
|---|---|---|
| Plan returns generic clusters | Objective too vague | Restate the decision, constraints, and completion standard in the `objective` |
| A source comes back `pending` | The 60-second extraction budget closed | Invoke the exact `continuation.next_call`; never record pending as `not-found` |
| Requirement comes back `conflicting` | Sources genuinely disagree | Record both verified quotations in the pack; resolve in cross-synthesis, not silently |
| Parallel research agents overlap | Write scopes not disjoint | Re-dispatch with explicit "you own only [path]" |
| Agent returns 200 lines of unsourced prose | Brief didn't require verified quotations per claim | Re-brief with "every claim cites an `extract-evidence` quotation or a local file" |
| One slow agent blocks the wave | Sequential read of agent results | Process completed agents as they return; don't gate on the last one |
| Same fact arrives 3 times | No de-duplication step | Add an explicit "check existing pack before writing" step in the brief |

## Worked-example tool log

The cloud-browsers corpus (293 files, 12 entities) used:

- **Phase 1:** 1 planning call for category discovery, plus 5 `web-search` follow-ups per gap → 25 candidates → tiered to 12 core
- **Phase 4:** 12 parallel planning calls (2 waves of 6 each), 1 per `core` entity. Average ~30 follow-up `web-search` calls across all entities for gap-filling, each promising lead verified with `extract-evidence`
- **Phase 5:** 10 cross-criterion comparison agents (one per criterion folder), each a parallel Explore run reading completed entity packs locally
- **Phase 6:** 12 profile pages written by orchestrator personally (no agent delegation)

Total tool calls: ~60 MCP calls + ~40 fallback WebSearch when MCP rate-limited + ~150 local Explore reads.

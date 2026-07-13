---
name: run-research
description: "Use if answering one technical research question with current web + practitioner evidence."
---

# Technical Research

One technical question. Web + Reddit evidence. Source-backed synthesis.
Optional multi-agent fan-out when the question spans 3+ subdomains.

## When to use

Trigger on phrasings like:

- *"research X for me"*, *"do some research on…"*, *"find sources on…"*
- *"why does library Y do Z"*, *"is bug B fixed in version V"*, *"what changed between V1 and V2"*
- *"compare A vs B for production"*, *"should we migrate from X to Y"*, *"any gotchas with…"*
- *"what do practitioners say about…"*, *"any horror stories with…"*, *"reddit experience with…"*
- *"verify that vendor V still does W"*, *"current pricing/quota/CVE for…"*
- *"give me the current state of <fast-moving topic>"*

Do NOT use when:

- The user asks to research a **market, vendor category, or 5+ entities** with per-entity packs, comparison templates, or a reusable corpus. Use `run-deep-research`.
- The user asks to **find, shortlist, or compare GitHub repositories** for a concrete need. Use `run-github-scout`.
- The question is **answerable from the local codebase alone**, or a docs page already in context is sufficient — just answer it.
- The user **explicitly asked not to search the web**.

The fence between this skill and the corpus skills: `run-research` answers
**one question** and returns **one synthesis** (Markdown by default).
Corpus skills answer **N questions across N entities** and return a
**multi-file evidence corpus**. If the deliverable is a folder, you are
in the wrong skill.

## Research tool surface

Use the Research Powerpack MCP tools first. If unavailable or denied,
fall back to built-in web tools; if those fail, use `curl` and parse
manually.

| Capability | First choice | Fallback 1 | Fallback 2 |
|---|---|---|---|
| Research prelude | `mcp__research-powerpack__get-research-consultancy` | manual query plan | - |
| Targeted search | `mcp__research-powerpack__web-search` | `WebSearch` | `curl` |
| Page extraction | `mcp__research-powerpack__scrape-link` | `WebFetch` | `curl` + parse |

Short aliases used throughout this skill:

- `get-research-consultancy` -> `mcp__research-powerpack__get-research-consultancy`
- `web-search` -> `mcp__research-powerpack__web-search`
- `scrape-link` -> `mcp__research-powerpack__scrape-link`

There are only three tools: a planner, a keywords-only search, and an
extraction-always scrape. `web-search` never classifies, tiers, or
synthesizes — it always returns the same ranked URL pool, so there is no
"prefer smart vs raw" decision to make. Scope is chosen by how you write
`keywords`, not by a parameter: write plain probes for web evidence, and
write explicit `site:reddit.com/r/.../comments` probes for Reddit
permalink discovery. Mixing both intents in one keyword set wastes
ranking budget — split into separate calls instead.

`scrape-link` always requires `extract` and always runs LLM extraction,
including on Reddit permalinks — the Reddit API still fetches the full
threaded post + comments first, then extraction runs on top. For
sentiment or dissent work, write an `extract` that explicitly asks for
verbatim quotes with author/score attribution (e.g. `verbatim quotes
with author + score | agreement reasons | dissent reasons | migration
drivers`) so the threading detail survives extraction.

`get-research-consultancy` is the planner for substantive sessions. It
returns `gaps_to_watch` and `stop_criteria` — treat both as binding
contracts.

For tool-by-tool API and operational thresholds, read `references/tools.md`.
For prompting each tool well, read `references/prompting.md`.

## The research loop

Five steps. One pass minimum. Iterate until every gap is closed.

1. **Plan.** Call `get-research-consultancy` with a goal that names the
   topic, the user's use case, known unknowns to skip, what NOT to
   research, freshness window, and quote discipline. The goal is the
   highest-leverage prompting decision in the entire loop — a weak goal
   produces a generic brief, which produces wandering keywords, which
   produces shallow synthesis. See `references/prompting.md`.

2. **Reconnoiter.** Fan out 15-50 keywords with `web-search`. Write
   keywords as Google retrieval probes — name the source class, anchor on
   discriminating terms, use one operator. For Reddit permalink discovery,
   write explicit `site:reddit.com/r/.../comments` probes; there is no
   separate scope parameter. Adjective-rotation on the same noun phrase is
   wasted budget.

   **Fire search calls in parallel when intents differ.** Two `web-search`
   calls in one turn — one with plain web probes (vendor docs, GitHub,
   blogs, changelog), one with `site:reddit.com/r/.../comments` probes
   (sentiment, migration, dissent) — is the canonical reconnaissance
   pattern. The round runs in roughly the time of one call.

3. **Triage.** Read the ranked URL list. Aim for 5-15 candidate URLs to
   scrape. Sort by CONSENSUS score and source authority.

4. **Capture.** Use `scrape-link` with a defined `extract`
   (≤5 URLs per call, ≤7 facets per call). For Reddit threads, write an
   extract that preserves attribution and dissent (e.g. `verbatim quotes
   with author + score | agreement reasons | dissent reasons | migration
   drivers`) — the Reddit API path still returns the full threaded post
   and comments before extraction runs on top. Read every `## Not found`
   section returned; it tells you which gaps to chase next round.

5. **Synthesize.** Every numeric, versioned, priced, or error-string claim
   traces to a verbatim scraped quote. Snippet citations are forbidden —
   snippets lie; the page is canonical. Mark inference vs evidence
   explicitly. Surface contradictions; do not paper over disagreement.

Two to four search rounds per substantive session is normal. After each
capture, harvest `## Follow-up signals` and `## Not found` from
`scrape-link`, and re-run `web-search` with terms gathered from those
sections. Stop only when `gaps_to_watch` and `stop_criteria` are closed,
or when remaining gaps are explicitly unresolvable from available
sources.

## Multi-agent orchestration (deep single-question path)

Single-agent research is the default. Use the orchestrated path **only**
when one technical question genuinely spans 3+ distinct technical
subdomains that benefit from independent reading lenses — e.g. security +
performance + maintainer intent + migration experience.

Pattern: dispatch one subagent per subdomain in parallel, each with its
own `get-research-consultancy` goal and its own search intent. Each
returns a section synthesis. The orchestrator merges, reconciles
contradictions between sections, and produces the unified answer.

The output still defaults to **one** Markdown synthesis. If the user
explicitly asks for files, a small numbered folder is allowed; do not
build per-entity packs, product profiles, comparison templates, or
reusable source-ledger corpora here — those are corpus shapes and
belong in `run-deep-research`.

For the full orchestration protocol — subagent prompts, scope
allocation, merge strategy, and contradiction resolution — read
`references/orchestrator.md`. Below the threshold, stay single-agent
for coherence.

## Reference routing

| Question | Read |
|---|---|
| How do I drive a specific tool? Parameters, output formats, thresholds. | `references/tools.md` |
| How do I write a `get-research-consultancy` goal or a `scrape-link` `extract`? | `references/prompting.md` |
| What does an end-to-end research session look like for my scenario? | `references/workflows.md` |
| How do I cite, mark inference, surface contradictions, format output? | `references/synthesis.md` |
| A scrape timed out. A search returned 0 results. The provider cascade failed. Now what? | `references/failure-modes.md` |
| The question spans 3+ technical subdomains and needs parallel evidence gathering. | `references/orchestrator.md` |

## Output and citation contract

Default to in-chat Markdown unless the user asks for a file. Use JSON
only when explicitly requested.

| Request shape | Default output |
|---|---|
| quick fact check | 3-8 bullets with sources |
| bug / root cause | likely cause, fix, caveats, fallback |
| decision / comparison (≤4 options) | recommendation, confidence, table, flip conditions, counter-arguments |
| deep single-question research | 800-2,000 words plus source ledger |

For any non-trivial answer, include compact source notes:

- URL or source identifier
- source type (docs, changelog, issue, advisory, Reddit thread, blog)
- author/date when available
- access date or research date for time-sensitive claims
- claim supported
- confidence or caveat when source quality is weak

Minimum citation rules:

- Cite scraped pages, official docs, issues, posts, advisories, or other
  concrete sources. Never cite search snippets or tool-provided
  synthesis as evidence.
- For APIs, prices, CVEs, versions, model behavior, deprecations, and
  fast-moving libraries, verify before synthesizing. Prefer official
  docs, changelogs, release notes, and advisories for exact facts.
- Use practitioner sources for production behavior, not exact API truth.
- Separate confirmed facts from inference. Mark unresolved gaps instead
  of smoothing them into a confident answer.
- "Reddit consensus" is not a citation. Attribute Reddit evidence with
  username, subreddit, date, and preferably score/comment context.

Read `references/synthesis.md` for credibility tiers, contradiction
handling, and worked output examples.

## Operational guardrails

- Use `get-research-consultancy` first for substantive sessions. A quick
  fact check can skip it when the overhead does not pay back.
- Cap `scrape-link` at 5 URLs and 7 facets per call; split beyond that.
- Read every `## Not found` section and feed unresolved gaps into the
  next query.
- Plan for output volume before parallel `web-search` calls; large URL
  pools may need file-backed triage.
- Treat provider cascade failure as blocking or WAF behavior. Route
  around to mirrors, archives, postmortems, or quoted discussions —
  see `references/failure-modes.md`.

## Final checks

- `description` is single-line, starts with `Use if`, and
  is ≤100 characters
- `run-research` target-specific validator checks pass
- every reference file remains routed from `SKILL.md`
- output contract includes source attribution and unresolved gaps
- sibling redirects still name `run-deep-research` and
  `run-github-scout`

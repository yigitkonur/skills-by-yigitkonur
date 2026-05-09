---
name: run-research
description: "Use skill if you are answering one technical research question with current web evidence, Reddit practitioner experience, and source-backed markdown synthesis."
version: 1.0.0
---

# Technical Research

Research one technical question with current web evidence, Reddit
practitioner experience, and source-backed synthesis.

## Trigger boundary

Use `run-research` for one technical question:

- bug diagnosis, root-cause research, or version-specific behavior
- API, library, framework, model, CVE, pricing, or changelog lookup
- architecture or migration decision with web evidence
- security or performance investigation
- fact check that could be stale or contested
- practitioner experience, migration reports, regrets, production
  gotchas, or post-incident retrospectives

Skip when:

- The task is industry, market, vendor-category, buyer comparison, or
  5+ entity corpus research with per-entity packs, comparison templates,
  or reusable source ledgers. Use `run-industry-research`; in this repo,
  route the same corpus-shaped work to `run-corpus-research`.
- The task is GitHub repo discovery, shortlisting, or repo comparison.
  Use `run-github-scout`.
- The question is local-codebase only or answerable without web evidence.
- A single docs page already in context is sufficient.
- The user explicitly asked not to search the web.

## Research tool surface

Use the Research Powerpack MCP tools first. If they are unavailable or
denied, fall back to built-in web tools; if those fail, use `curl` and
parse the page manually.

| Capability | First choice | Fallback 1 | Fallback 2 |
|---|---|---|---|
| Research prelude | `mcp__research_powerpack__start_research` | manual query plan | - |
| Targeted search | `mcp__research_powerpack__smart_web_search` or `mcp__research_powerpack__raw_web_search` | `WebSearch` | `curl` |
| Page extraction | `mcp__research_powerpack__smart_scrape_links` or `mcp__research_powerpack__raw_scrape_links` | `WebFetch` | `curl` + parse |

Short aliases in this skill mean the MCP tools above:

- `start-research` -> `mcp__research_powerpack__start_research`
- `smart-web-search` -> `mcp__research_powerpack__smart_web_search`
- `raw-web-search` -> `mcp__research_powerpack__raw_web_search`
- `smart-scrape-links` -> `mcp__research_powerpack__smart_scrape_links`
- `raw-scrape-links` -> `mcp__research_powerpack__raw_scrape_links`

Scope selection:

| Scope | Use for |
|---|---|
| `web` | official docs, specs, bugs, CVEs, changelogs, pricing, API shape |
| `reddit` | lived experience, migrations, regret, production gotchas |
| `both` | only when opinion-heavy evidence and official facts both matter |

The decisive choice: if the output goes into context, prefer smart; if it
goes to a file or specialist reviewer, prefer raw. Reddit comment threads
are the exception: `raw-scrape-links` preserves vote-weighted dissent and
reply-thread structure that `smart-scrape-links` compresses away.

`start-research` is the planner for substantive sessions. It returns
`gaps_to_watch` and `stop_criteria`; treat both as binding contracts.

For tool-by-tool API and operational thresholds, read `references/tools.md`.
For prompting each tool well, read `references/prompting.md`.

## The research loop

Five steps. One pass minimum. Iterate until every gap is closed.

1. **Plan.** Call `start-research` with a goal that names the topic, the
   user's use case, known unknowns to skip, what NOT to research, freshness
   window, and quote discipline. See `references/prompting.md` for goal
   writing — it is the highest-leverage prompting decision in the entire
   loop. A weak goal produces a generic brief, which produces wandering
   keywords, which produces shallow synthesis.

2. **Reconnoiter.** Fan out 15–50 keywords. Default to `smart-web-search`
   when the output goes directly into context. Default to `raw-web-search`
   when subagent triage is planned, multiple search rounds are expected,
   or Reddit permalink discovery is the goal. Write keywords as Google
   retrieval probes — name the source class, anchor on discriminating
   terms, use one operator. Adjective-rotation on the same noun phrase is
   wasted budget.

   **Fire search calls in parallel when scopes differ.** Two
   `raw-web-search` calls in one turn - one `web` scoped (vendor docs,
   GitHub, blogs, changelog), one `reddit` scoped (sentiment, migration,
   dissent) - is the canonical reconnaissance pattern, not an exotic
   move. The round runs in roughly the time of one call. Mixing scopes
   inside one keyword set produces worse results because budgets
   compete.

3. **Triage.** Read tiered list (smart) or subagent-extract top URLs
   (raw). Aim for 5–15 candidate URLs to scrape. Sort by CONSENSUS score
   and source authority.

4. **Capture.** Use `raw-scrape-links` for Reddit threads (≤5 per call)
   and pages where the extraction shape is undecided — the Reddit API path
   preserves author, score, and indent depth. Use `smart-scrape-links` for
   docs and blogs with a defined `extract` (≤5 URLs per call, ≤7 facets
   per call). Read every `## Not found` section returned; it tells you
   which gaps to chase next round.

5. **Synthesize.** Every numeric, versioned, priced, or error-string claim
   traces to a verbatim scraped quote. Snippet citations are forbidden —
   snippets lie; the page is canonical. Mark inference vs evidence
   explicitly. Surface contradictions; do not paper over disagreement.

Two to four search rounds per substantive session is normal. After each
capture, harvest `## Follow-up signals`, `## Not found`, `## Gaps`, and
`## Suggested follow-up searches`. Stop only when `gaps_to_watch` and
`stop_criteria` are closed, or when remaining gaps are explicitly
unresolvable from available sources.

## Deep single-question path

Single-agent research is the default. Use the deep path only when one
technical question spans 3+ distinct technical subdomains that benefit
from independent reading lenses, such as security, performance,
maintainer intent, and migration experience.

The output still defaults to one markdown synthesis. If the user
explicitly asks for files, a small numbered folder is allowed; do not
build per-entity packs, product profiles, comparison-template corpora,
or reusable source-ledger corpora here.

Route corpus-shaped requests away: 5+ vendors/entities, product or
category landscapes, buyer comparisons, market or industry research,
reusable evidence packs, and multi-file corpora belong in
`run-industry-research`; in this repo, route the same work to
`run-corpus-research`.

For deep single-question orchestration, read `references/orchestrator.md`.
Below the threshold, stay single-agent for coherence.

## Reference routing

| Question | Read |
|---|---|
| How do I drive a specific tool? Parameters, output formats, thresholds. | `references/tools.md` |
| How do I write a `start-research` goal or a smart `extract`? | `references/prompting.md` |
| What does an end-to-end research session look like for my scenario? | `references/workflows.md` |
| How do I cite, mark inference, surface contradictions, format output? | `references/synthesis.md` |
| A scrape timed out. A search returned 0 results. Now what? | `references/failure-modes.md` |
| A single question spans 3+ technical subdomains and needs parallel evidence gathering. | `references/orchestrator.md` |

## Output and citation contract

Default to in-chat Markdown unless the user asks for a file. Use JSON
only when explicitly requested.

| Request shape | Default output |
|---|---|
| quick fact check | 3-8 bullets with sources |
| bug / root cause | likely cause, fix, caveats, fallback |
| decision / comparison | recommendation, confidence, table, flip conditions, counter-arguments |
| deep single-question research | 800-2,000 words plus source ledger |

For any non-trivial answer, include compact source notes:

- URL or source identifier
- source type
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

Read `references/synthesis.md` for detailed credibility tiers,
contradiction handling, and output examples.

## Operational guardrails

- Use `start-research` first for substantive sessions. A quick fact check
  can skip it when the overhead does not pay back.
- Cap `smart-scrape-links` at 5 URLs and 7 facets per call; split beyond
  that.
- Read every `## Not found` section and feed unresolved gaps into the
  next query.
- Plan for output volume before parallel raw searches; large raw results
  may need file-backed triage.
- Treat provider cascade failure as blocking or WAF behavior. Route
  around to mirrors, archives, postmortems, or quoted discussions.

## Final checks

- description is single-line, quoted, starts with `Use skill if you are`,
  and is <=30 words
- `run-research` target-specific validator checks pass
- every reference file remains routed from `SKILL.md`
- output contract includes source attribution and unresolved gaps
- sibling redirects still name `run-industry-research` and
  `run-github-scout`

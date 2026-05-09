---
name: run-research
description: This skill should be used when the user asks to "research", "look up", "compare libraries", "investigate a bug across versions", "audit dependencies", "find community sentiment", "decide between X and Y", "check Reddit for", "what's new in", or any technical question that requires web evidence, Reddit practitioner experience, and multi-source synthesis. Use whenever the answer depends on information published or changed after training cutoff. Skip when the question is local-codebase only, when a single docs page already in context is sufficient, or when the user has explicitly asked you not to search the web.
version: 1.0.0
---

# Technical Research

Drive the research-powerpack toolkit (`start-research` plus the 2×2 of
raw/smart × search/scrape) to answer technical questions whose accurate
answer requires web evidence, Reddit practitioner experience, and
multi-source synthesis.

## Trigger boundary

Use this skill when:

- The answer depends on information published or changed since training
  cutoff (libraries, APIs, prices, models, security advisories).
- The user wants community sentiment, lived experience, migration reports,
  or post-incident retrospectives — not just docs.
- Any non-trivial claim should be triangulated across three or more
  independent sources.
- The question is comparative ("X vs Y") and the comparison axes span
  multiple sources.

Skip when:

- The question is local-codebase only (use Explore-class agents).
- A single docs page already in context is sufficient (use WebFetch).
- The user explicitly asked not to search the web.

## The toolkit at a glance

Five tools. Two axes. One planner.

```
                 RAW (capture)              SMART (synthesize)
   SEARCH    raw-web-search             smart-web-search
              URL pool + audit           tiered + gap analysis
              context-pollutant          context-compressing

   SCRAPE    raw-scrape-links           smart-scrape-links
              full markdown +            Matches + Not found +
              Reddit threading           Follow-up + Contradictions
              evidence grade             analysis-ready

           + start-research = stopping condition
```

The decisive choice: **if the output goes into context, prefer smart; if
it goes to a file or subagent, prefer raw.** Reddit comment threads are
the canonical exception — `raw-scrape-links` preserves vote-weighted
dissent and reply-thread structure that `smart-scrape-links` compresses
away.

`start-research` is the planner: call it first, every session. It returns
a goal-tailored brief whose `gaps_to_watch` and `stop_criteria` are the
only structured stopping condition the toolkit provides. Treat them as
binding contracts.

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
   `raw-web-search` calls in one turn — one web-scoped (vendor docs,
   GitHub, blogs, changelog), one Reddit-scoped (sentiment, migration,
   dissent) — is the canonical reconnaissance pattern, not an exotic
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

**Two to four search rounds per substantive session is normal**, not
excessive. After every capture, harvest the next round's seeds:

- From `smart-scrape-links`: read `## Follow-up signals` (referenced
  URLs and concepts the extractor surfaced) and `## Not found` (which
  facets a source failed to answer — those gaps drive the next query).
- From `smart-web-search`: read `## Gaps` (open questions with IDs) and
  `## Suggested follow-up searches` (refine queries tied to gap IDs).

Feed harvested terms into round 2 search. Do not paraphrase queries
already run; the classifier tracks them. Loop search–capture–synthesize
until every `gaps_to_watch` item from `start-research` is closed and
the last search round surfaces no new terms. Then stop and write up.

## When to escalate to multi-agent

Single-agent is the default. Escalate when:

- The question has five or more distinct comparison axes that benefit from
  focused attention (e.g., security plus performance plus ergonomics plus
  pricing plus ecosystem in one mission).
- Time budget exceeds roughly 90 minutes of agent work.
- Domain experts in different verticals need to contribute independently
  (security review uses a different reading lens than performance
  benchmarking).

For multi-agent orchestration, read `references/orchestrator.md`. Below
the escalation threshold, single-agent is cheaper and produces more
coherent synthesis.

## Reference routing

| Question | Read |
|---|---|
| How do I drive a specific tool? Parameters, output formats, thresholds. | `references/tools.md` |
| How do I write a `start-research` goal or a smart `extract`? | `references/prompting.md` |
| What does an end-to-end research session look like for my scenario? | `references/workflows.md` |
| How do I cite, mark inference, surface contradictions, format output? | `references/synthesis.md` |
| A scrape timed out. A search returned 0 results. Now what? | `references/failure-modes.md` |
| I have ≥5 axes and need to dispatch parallel researchers. | `references/orchestrator.md` |

## Guardrails

These rules apply across every loop. Violation produces unreliable
synthesis.

- Never cite a URL from a search snippet alone. Snippets are misleading by
  design; only scraped page content is evidence.
- Persistence is structural, not exceptional. Tool results above ~50KB
  persist to file. When "Output too large" appears, subagent-extract — do
  not paste the persisted file into context.
- Parallel calls amplify output volume, not just speed. Two parallel
  `raw-web-search` calls with 25 keywords each can return >100KB of
  context-polluting snippets in seconds. Plan for the output side before
  fanning out.
- Provider cascade failure (Jina → Scrape.do → Kernel all failing on one
  URL) means WAF or interstitial blocking, not bug. Route around — try
  the postmortem, the mirror, the web archive — do not retry.
- Match facet shape to page type. Specs from docs (verbatim config keys,
  command syntax, version strings); sentiment from Reddit (attributed
  quotes with vote counts, dissent); verdicts from blogs (recommendation
  logic, comparison axes). Asking for sentiment from a docs page produces
  nothing useful.
- Cap `smart-scrape-links` at 5 URLs and 7 facets per call. Beyond either,
  split. Observed: 9 URLs times out repeatedly; 4–5 URLs at ≤7 facets
  succeed in roughly 50 seconds.
- The `## Not found` section returned by `smart-scrape-links` is not
  optional reading. It tells you which facets a source did not answer,
  which directly determines the next search query.
- Search aggressively. Two parallel `raw-web-search` calls in one turn,
  then a refined round 2 after triage, is normal — not excessive.
  Single-call sessions are usually under-researched.
- `gaps_to_watch` and `stop_criteria` from `start-research` are binding.
  The loop ends when every gap is closed, not when fatigue sets in.

## Quick start

The literal first call to make:

```
start-research(
  goal: "<one paragraph: topic, your use case, known unknowns,
         skip list, freshness window, quote discipline>"
)
```

If the goal is two sentences and names only the topic, stop. Read
`references/prompting.md` first. The five to ten minutes spent sharpening
the goal are the highest-leverage minutes in the session.

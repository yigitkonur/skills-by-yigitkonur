# Prompting the toolkit

Three forces shape every good prompt to this toolkit:

1. **Specificity about the user.** Who is asking, what for, what they
   already know. Generic goals get generic briefs.
2. **Specificity about the page or source.** The extractor adapts to page
   type (docs / reddit / blog / cve) — but only if hinted or implied.
3. **Specificity about irrelevance.** State what NOT to research. Without
   a skip list, seeds wander into adjacent topics.

The single most-asked-for output: `## Not found with reason`. Explicitly
request it. The extractor will tell you which sources failed which facets,
and that *changes which question you ask next*.

The rest of this file is concrete: how to write a `start-research` goal,
how to fan out keywords, how to shape `extract` for `smart-web-search`,
how to shape `extract` for `smart-scrape-links` by page type, with worked
examples and anti-patterns.

---

## Writing the start-research goal

A weak goal produces a generic brief, which produces wandering keywords,
which produces shallow synthesis. The five to ten minutes spent sharpening
the goal are the highest-leverage minutes in the session.

### Weak goal (anti-example)

```
Compare Claude Code and OpenAI Codex CLI in 2026.
```

What's wrong: names only the topic. The planner cannot calibrate
`primary_branch`, freshness, or skip-list. It produces 30 generic seeds
and `gaps_to_watch` that are vague.

### Strong goal (template)

A complete goal has six components:

1. **Decision context.** What decision is being made?
2. **User profile.** Who is asking and under what constraints?
3. **"Done" definition.** What deliverable closes the session?
4. **Known knowns.** What is already settled — do not re-confirm.
5. **Wanted unknowns.** What specifically should this session learn?
6. **Skip list + freshness + quote discipline.** What to ignore, time
   horizon, citation rules.

Worked example (the same Claude Code vs Codex question, properly framed):

```
Decide between Claude Code and OpenAI Codex CLI for solo dev use over the
next 6–12 months.

User context: solo dev, MacOS + Linux (no Windows), mixed React/TS frontend
+ Node/Python backend, $20–200/month budget, values reliability and rate-limit
headroom over peak benchmark scores.

Done = (1) feature matrix limited to facets that materially affect day-to-day
work, (2) personal "pick X if Y else Z" recommendation, (3) lock-in /
switching cost list per tool.

Already known and not worth re-confirming: both have CLIs, MCP, hooks, IDE
extensions, similar headline coding benchmarks.

What to learn: non-obvious differentiators (footguns, bugs, lock-in),
limit asymmetry under sustained use, regressions / postmortems / pricing
changes in the last 90 days, unique features one tool genuinely lacks.

Skip: enterprise SSO, SOC2, custom training, multi-tenant deployment.

Freshness: weight last 90 days; treat >6mo as historical only.

Quote discipline: every numeric / versioned / priced claim traces to a
verbatim quote from a scraped page (not snippet).
```

What this produces: specific seeds aimed at recent regressions,
sustained-use limit reports, and unique-feature audits. Skip list keeps
the planner away from enterprise content. Freshness window biases seeds
toward changelog and recent-thread terms. Quote discipline appears in
`stop_criteria`.

### Goal-writing checklist

Before submitting, verify every component:

- [ ] Names the decision, not just the topic
- [ ] Names user profile (role, stack, constraints, preferences)
- [ ] Defines "done" with a concrete deliverable shape
- [ ] Lists known knowns to skip
- [ ] Lists wanted unknowns explicitly
- [ ] Includes skip list
- [ ] Specifies freshness window
- [ ] States quote discipline

If any component is missing, the planner will guess — usually generically.

### When to re-call start-research

Rare. Usually a goal update is enough. Re-call when:

- Scope materially expands (new axis the original goal did not anticipate).
- The session pivots from one decision to another.
- Four or more search rounds in and still uncovering blind spots — the
  goal was probably under-specified.

---

## Writing keyword fan-outs (Google retrieval probes)

Keywords are not topic labels. They are Google retrieval probes —
pinpoints into specific source classes.

### The four canonical rewrite pairs

```
Bad:    "<feature> support"
Better: site:<official-docs-domain> "<feature>" "<platform-or-version>"
        Reason: pins to canonical source, version-anchored.

Bad:    "<product> pricing"
Better: site:<vendor-domain> "<product>" pricing "enterprise" OR "free tier"
        Reason: vendor docs only; OR forces both tier types.

Bad:    "<library> bug fix"
Better: "<exact error text>" "<library>" "<version>" site:github.com
        Reason: error string is the highest-signal anchor.

Bad:    "<tool> reviews"
Better: site:reddit.com/r/<community>/comments "<tool>" "migration" OR "regression"
        Reason: Reddit-permalink-only, sentiment-loaded keywords.
```

### The fan-out rule

A 20+ keyword fan-out should cover ≥5 source classes:

- Official docs (`site:docs.<vendor>.com`)
- Vendor announcements (`site:<vendor>.com` + "announcement" / "launch")
- Source repo (`site:github.com/<org>/<repo>`)
- Issue trackers (`site:github.com/<org>/<repo>/issues` + error text)
- Reddit permalinks (`site:reddit.com/r/<sub>/comments` + sentiment)
- HN / blogs (`site:news.ycombinator.com` + topic; `site:<author>.com`)
- Changelog / release notes (`site:<vendor>.com` + "changelog" / "release notes")
- Pricing (`site:<vendor>.com` + "pricing" / plan names)
- Comparison (no `site:`, "X vs Y" with quoted phrase)
- CVE / security (`site:nvd.nist.gov` or `site:github.com/security/advisories`)

Adjective rotation on the same noun phrase ("X feature", "X feature 2026",
"X feature support") wastes budget. Each keyword should hit a different
source class.

### The 7-angle framework

When the topic does not naturally fan out across source classes, use the
7-angle framework:

1. Direct topic — `"Next.js middleware authentication 2026"`
2. Specific technical term — `"Next.js middleware matcher config"`
3. Problems / debugging — `"Next.js middleware redirect loop fix"`
4. Best practices — `"Next.js middleware best practices production"`
5. Comparison — `"Next.js middleware vs API routes authentication"`
6. Official docs — `site:nextjs.org middleware`
7. Advanced / production — `"Next.js middleware chain multiple matchers production"`

### Operators that cut through noise

- `"exact phrase"` — error messages, function names
- `site:docs.python.org` — restrict to authoritative domains
- `-site:medium.com -site:w3schools.com` — exclude content farms
- `intitle:"migration guide"` — phrase must appear in title
- `filetype:pdf` — find specs and papers
- `OR` — match variant terms
- Year tokens (`2025`, `2026`) — filter stale results for fast-moving
  ecosystems

### Negative-signal keywords for Reddit

For `scope: "reddit"` searches, at least 25% of keywords should carry
negative signal:

- `"regret"`
- `"switched from"`
- `"broke in production"`
- `"don't use"`
- `"problems with"`
- `"avoid"`

People who succeed rarely post; people who fail explain exactly what went
wrong.

### Worked example: Bun vs Deno comparison

Bad fan-out (10 keywords, 1 source class):

```
"Bun vs Deno comparison"
"Bun vs Deno performance"
"Bun vs Deno features"
"Bun vs Deno 2026"
"Bun vs Deno benchmarks"
"Bun vs Deno migration"
"Bun vs Deno production"
"Bun vs Deno typescript"
"Bun vs Deno node compatibility"
"Bun vs Deno reviews"
```

Same query with adjectives swapped. Will return overlapping results.

Strong fan-out (10 keywords, 6 source classes):

```
site:bun.sh/docs "deno" compatibility OR migration
site:docs.deno.com "bun" interop OR comparison
"@types/bun" OR "@types/deno" site:github.com issues
site:reddit.com/r/javascript/comments "bun" "deno" "switched"
site:reddit.com/r/typescript/comments "bun" production OR regression
site:news.ycombinator.com "bun" OR "deno" 2025 OR 2026
"npm install" "bun install" benchmark site:github.com
"node compatibility" bun deno changelog 2025
site:bun.sh/blog OR site:deno.com/blog comparison
"package.json" "deno.json" interop bug
```

Each probe targets a different evidence layer. Result diversity is the
goal.

---

## Multi-call search dispatch

Search calls are cheap. Plan to fire them in parallel within a turn and
across rounds. The Claude vs Codex session this skill was authored from
used 4 parallel scrape calls and 2 parallel search rounds — the
single-call session is the unusual case, not the norm.

### Parallel within a turn

Two search calls in one turn run in roughly the time of one. Use
parallel dispatch when:

- **Scopes differ.** Web-scoped (vendor docs + GitHub + blogs +
  changelogs) and Reddit-scoped (sentiment + migration + dissent) are
  orthogonal source classes. One call per scope.
- **Keyword angles compete for budget within a single call.** With 50
  keywords across truly orthogonal facets, splitting into 2× 25-keyword
  calls produces better tier coverage than one 50-keyword call with
  mixed signal.
- **Raw plus smart in the same round.** Raw call to populate the URL
  pool for round 2; smart call to triage immediately.

The canonical reconnaissance pattern for any comparison or survey:

```
parallel in one turn:
  - raw-web-search (web-scoped, 25 keywords across vendor docs / GitHub /
    blogs / HN / changelog / pricing)
  - raw-web-search (Reddit-scoped, 15 keywords with negative-signal
    discipline: "regret", "switched from", "broke in production")
```

### Across rounds

Round 1 reconnaissance is rarely sufficient for a substantive question.
After capturing the first batch of pages, every smart-* call returns
explicit seeds for round 2:

- `smart-scrape-links` → `## Follow-up signals` (concepts and URLs the
  extractor surfaced) and `## Not found` (which facets a source did not
  answer — those gaps drive the next query).
- `smart-web-search` → `## Gaps` and `## Suggested follow-up searches`
  (refine queries tied to gap IDs).

Feed harvested terms into round 2 search. Do not paraphrase queries
already run; the classifier tracks them.

**Two to four rounds per substantive session is normal.** The cost of
an extra search call is much less than the cost of a missed source.

### When parallel hurts

- **Output volume risk.** Two parallel `raw-web-search` calls of 25+
  keywords each can return >100KB of context-polluting snippets. Plan
  the subagent-extract step before fanning out.
- **The same keywords twice.** If two calls would share >50% of
  keywords, run one call instead. Parallelism gives no benefit when
  budgets are not orthogonal.
- **Search-only when scrape would close the gap.** If round 1 already
  produced HIGHLY_RELEVANT URLs that would answer the question, scrape
  them first; round 2 search runs after scrape harvests new terms.

---

## Writing the smart-web-search extract

`extract` for `smart-web-search` tells the *classifier* what relevance
means. It does not tell an extractor what fields to pull (the classifier
sees only titles and snippets).

### Template

```
extract: "<topic> for <use case> — <evidence type>, not <noise type>.
Highly relevant: <source class A>, <source class B>.
Maybe relevant: <source class C>.
Not relevant: <noise class A>, <noise class B>."
```

### Worked example

Bad:

```
extract: "MCP OAuth"
```

The classifier has no signal to tier on. It produces uniformly mediocre
tiers.

Strong:

```
extract: "OAuth 2.1 support in TypeScript MCP frameworks for production —
runnable code, error reports, and version-specific behaviour. Highly
relevant: vendor docs (modelcontextprotocol.io, sdk repos), GitHub
issues with errors, Reddit threads with active sentiment. Maybe relevant:
blog walkthroughs from last 6 months. Not relevant: marketing pages,
listicles, conference talks without code."
```

This produces a HIGHLY_RELEVANT tier biased toward GitHub issues and
vendor docs; marketing pages drop to OTHER quietly.

### Anti-patterns

- **Topic without use case.** "OAuth in MCP" tells the classifier nothing
  about what kind of evidence wins.
- **Use case without noise list.** Without "not relevant: marketing", the
  marketing tier creeps into MAYBE.
- **Asking for synthesis from smart-search.** Smart-search reads titles
  and snippets, not bodies. It cannot synthesize evidence; only triage
  candidates.

---

## Writing the smart-scrape-links extract

`extract` for `smart-scrape-links` tells the *extractor* which facets to
pull from each page body. The extractor classifies each page (docs /
reddit / blog / cve / etc.) and adapts emphasis.

### Base template

```
Page type hint: <docs | github-thread | reddit | blog | cve | changelog>.

extract:
- <facet 1> with <evidence shape: verbatim numbers / quoted attribution / etc.>
- <facet 2> ...
- <facet 3> ...
(5–7 facets max)

Discipline:
- Quote verbatim where numbers, version strings, prices, error text, or
  config keys appear.
- For absent facets, list under Not found with a one-line reason for why
  this page should/shouldn't have answered it.
- Surface contradictions across the document or with prior context.
```

### Page-type-aware variants

Specs from a docs page need different emphasis than sentiment from a
Reddit thread. The extractor adapts when the page type is hinted, and
adapts better when the right evidence shape is requested.

**docs page** (vendor reference, API docs):

```
Page type hint: official docs.
extract:
- supported platforms with verbatim names and versions
- command syntax verbatim (every shell snippet)
- config keys verbatim with their accepted values
- supported model/runtime/version matrix
- rate limits or quotas with exact numbers
- recent (last 90 days) changelog headlines verbatim with dates

Discipline: Preserve config-key names, command syntax, and version strings
exactly. If absent, list under Not found with a one-line reason.
```

**Reddit thread** (sentiment, lived experience):

```
Page type hint: reddit.
extract:
- attributed quotes with handle and score (e.g., u/foo (+12): "...")
- recurring complaints across multiple commenters
- recurring praise across multiple commenters
- dissent (high-vote contrarian opinions)
- vote-weighted distribution of sentiment

Discipline: Do not compress votes away. Preserve comment depth in
attribution. Surface contradictions across commenters.
```

**GitHub issue / PR**:

```
Page type hint: github-thread.
extract:
- maintainer decisions with handle and date
- accepted-fix commit hashes if any
- stacktraces verbatim
- affected versions verbatim
- workarounds with code samples
- resolved-in version

Discipline: Preserve stacktrace formatting. Cite commit hashes when
present.
```

**CVE / security advisory**:

```
Page type hint: cve.
extract:
- CVE-ID verbatim
- CVSS score verbatim
- affected version ranges verbatim
- patched versions verbatim
- mitigation steps
- exploit availability (if stated)

Discipline: Never paraphrase impact statements. Quote exact wording.
```

**Blog / opinion / comparison post**:

```
Page type hint: blog.
extract:
- author's verdict with one-sentence justification
- comparison axes the author used
- recommendation logic (if X then Y)
- quoted lived-experience claims
- author's caveats and disclosed biases

Discipline: Preserve recommendation logic verbatim. Surface contradictions
with the author's own earlier claims if any.
```

**Changelog / release notes**:

```
Page type hint: changelog.
extract:
- date headers verbatim (YYYY-MM-DD)
- version numbers verbatim
- new feature names with one-sentence descriptions
- deprecations and removal timelines
- breaking changes with migration notes

Discipline: Preserve every date and version string verbatim. Do not
paraphrase.
```

### Anti-patterns

- **More than 7 facets.** Extractor fragments attention; quality drops on
  every facet.
- **Asking for "everything important."** Vague extracts produce vague
  extractions.
- **Forgetting verbatim discipline.** Default behaviour is summary;
  explicitly request quote-preservation for numbers, versions, prices,
  and error strings.
- **Forgetting to ask for `## Not found with reason`.** Without it, you
  do not know which facets a source failed.
- **Mixing page types in one call without hinting.** The extractor adapts
  per URL, but explicit hints help when sources are heterogeneous.

---

## Eight worked goal examples

Real research scenarios. Each shows a sample `goal` paragraph for
`start-research`. The full search/scrape calls for each are in
`workflows.md`.

### 1. Bug investigation across versions

```
Investigate why <library> v3.2.1 throws "<exact error text>" on Node 20+
when prior v3.1.x worked. User context: production app, can't easily
downgrade Node. Done = root cause + fix or workaround. Skip: basic
getting-started. Freshness: last 12 months. Quote discipline:
stacktraces verbatim.
```

### 2. Library / tool comparison

(See the Claude Code vs Codex example above.)

### 3. Architecture decision research

```
Decide whether to adopt <pattern X> or <pattern Y> for <system component>.
User context: 50-engineer team, 3-year-old codebase, currently using
<incumbent pattern>. Done = decision memo with tradeoff matrix and
6-month risk projection. Known: both patterns work in principle. What
to learn: real adoption stories at 50+ engineering scale, regrets,
migration costs. Skip: tutorials. Freshness: last 24 months for adoption
stories; latest for benchmarks. Quote discipline: production-incident
reports must be verbatim.
```

### 4. Fact check / claim verification

```
Verify the claim that "<exact claim>" appears in <source>. User context:
writing a technical brief; need primary-source quote with date. Done =
quoted text + URL + scrape date OR confirmation the claim cannot be
substantiated. Skip: tertiary sources, blog repetition. Freshness: any.
Quote discipline: only verbatim primary-source quotes count.
```

### 5. Production incident research

```
Resolve <production symptom> appearing on <stack> after <recent change>.
User context: incident triage, 30-min budget. Done = top 3 likely root
causes with evidence + recommended next debugging step. Skip: deep
architecture analysis. Freshness: very recent (last 30 days) for
similar incidents. Quote discipline: error logs and config snippets
verbatim.
```

### 6. Security advisory audit

```
Audit <dependency tree> against current CVEs. User context: pre-release
security gate. Done = list of unpatched CVEs in deps, severity,
mitigation status. Skip: speculative advisories. Freshness: published in
last 18 months. Quote discipline: CVE-IDs, CVSS scores, affected ranges
verbatim.
```

### 7. Performance investigation

```
Compare <approach A> vs <approach B> for <workload> at <scale>. User
context: backend perf review, decision lasts 12 months. Done = benchmark
summary with cited numbers + recommendation + caveats. Known: both
approaches work correctly. What to learn: numbers from production, not
synthetic benchmarks. Skip: marketing claims. Freshness: last 18 months.
Quote discipline: every benchmark number verbatim with workload spec.
```

### 8. Redirect landscape scans

Do not turn landscape scans into `run-research` goals. Route market,
industry, vendor-category, 5+ entity, reusable evidence pack, and
multi-file corpus requests to `run-industry-research`.

If a landscape request contains one narrow technical question, rewrite
only that question as a `run-research` goal.

---

## Cross-tool prompting principles (recap)

- **Specificity about user, source, and irrelevance.** All three or none.
- **Match facet shape to page type.** Specs from docs verbatim; sentiment
  from Reddit attributed; verdicts from blogs with reasoning.
- **Cap `smart-scrape-links` at ≤5 URLs and ≤7 facets per call.** Beyond
  either, split.
- **Ask for `## Not found with reason` explicitly every time.** It
  changes which question you ask next.
- **Never cite from a search snippet.** Only scraped page content is
  evidence.
- **Watch for `## Contradictions`.** Surfaces unannounced when relevant;
  gold for sentiment work.

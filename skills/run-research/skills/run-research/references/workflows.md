# Research Workflows

These workflows show how the research loop adapts to different question types. They're starting points — let the evidence guide you to go deeper or stop early.

**Every workflow begins with `start-research`** (unless noted). The brief's `primary_branch` tells you whether to lead with `scope:"web"`, `scope:"reddit"`, or fire both in parallel. Fire the brief's `first_call_sequence` verbatim on round 1.

---

## Workflow 1: Bug Fix — "I hit an error I don't recognize"

**Typical `primary_branch`:** `web` (bug / spec lookup)
**Start:** `start-research` → `web-search scope:"web"` (error messages are the most searchable content on the internet)

```
1. start-research
   goal: "Root cause and fix for <exact error or symptom>, including affected versions and workarounds"

2. web-search (scope: "web", 10–15 queries from brief seeds + these angles)
   queries:
   - Exact error in quotes: '"TypeError: Cannot read properties of undefined" react hooks'
   - Error + framework + version: '"Cannot read properties of undefined" useEffect React 19 fix'
   - Site-targeted: 'site:stackoverflow.com "Cannot read properties" react'
   - GitHub issues: 'site:github.com/facebook/react/issues "Cannot read properties"'
   - Year-pinned: 'react hooks undefined error fix 2026'
   extract: "find the root cause and fix for this error in React hooks"

3. scrape-links (top 3–5 URLs from HIGHLY_RELEVANT)
   extract = "root cause | fix code before and after | version affected | environment conditions | workarounds"

4. Is the fix clear? → Apply it. Done.
   Fix unclear or conflicting? → Continue:

5. web-search (scope: "reddit", 5–8 queries with negative signal)
   - '"<error message>" r/reactjs'
   - '<library> <symptom> workaround fix'
   - '<library> breaking change <version>'
   - '<library> regret production'

6. scrape-links (3–5 best reddit permalinks from HIGHLY_RELEVANT — auto-routed to Reddit API)
   extract = "verified fixes | OP follow-up | version details | stacktraces | environment details"

7. Still stuck? → Synthesize from all evidence and form a diagnosis
```

**Adapt when:**
- Zero search results → error is likely in your own code, not a known issue
- Recent library update → scrape the changelog/release page
- Intermittent bug → gather more context from profiling data
- Multiple conflicting fixes → cross-reference against your specific version + environment

---

## Workflow 2: Library Comparison — "Should I use A or B?"

**Typical `primary_branch`:** `web` (or `both` for mature contested areas)
**Start:** `start-research` → parallel `web-search` calls (discover candidates + sentiment in one turn)

```
1. start-research
   goal: "Compare <A> vs <B> for <use case>, covering features, performance, maintenance, and migration stories"

2. Parallel web-search calls in the same turn:
   2a. web-search (scope: "web", 20–30 queries from brief seeds)
       queries:
       - '<A> vs <B> benchmark comparison 2026'
       - 'best <category> library <language> 2026'
       - '<A> alternatives'
       - 'site:npmtrends.com <A> <B>'
       - '<A> <B> migration guide'
       - 'site:<A-docs> performance'
       extract: "compare <A> vs <B> for <use case> — features, performance, limitations, maintenance activity"
   2b. web-search (scope: "reddit", 8–12 queries — heavy on negative signal)
       queries:
       - '<A> vs <B> production experience'
       - 'switched from <A> to <B> why'
       - '<A> problems issues production'
       - '<B> gotchas limitations'
       - '<A> regret complex queries performance'
       - '"don't use <A>" OR "avoid <A>"'
       extract: "lived experience with <A> and <B> — migration drivers, regrets, dissent, production breakers"

3. scrape-links (mixed batch: 3–5 comparison articles / READMEs / npm pages + 5–8 reddit permalinks)
   extract = "features | bundle size | performance benchmarks | limitations | maintenance activity | community size | migration drivers | verbatim quotes"
   # Reddit URLs auto-routed to the Reddit API; non-reddit URLs flow through the scraper in parallel

4. Round 2 if confidence medium or gaps unclosed: use web-search's `## Suggested follow-up searches` + scrape `## Follow-up signals` to build next web-search

5. Output: Decision matrix + recommendation
```

**Adapt when:**
- Clear winner after step 3 (strong consensus) → brief validation, then recommend
- All options have major issues → expand candidate list, run another round
- Decision depends on a specific technical detail → scrape official docs for that detail

---

## Workflow 3: Architecture Decision — "How should I design this?"

**Typical `primary_branch`:** `both` (options-docs + practitioner experience both matter)
**Start:** `start-research` → parallel `web-search` calls for landscape + experience

```
1. Frame the decision: constraints, scale targets, team composition, risk tolerance, reversibility.

2. start-research
   goal: "Choose between <pattern A> and <pattern B> for <constraint>, at <scale>, with <team-size> engineers"

3. Parallel web-search calls:
   3a. web-search (scope: "web", 15–20 queries)
       queries:
       - '<pattern A> vs <pattern B> trade-offs 2026'
       - 'site:martinfowler.com <pattern>'
       - '<pattern> production experience case study'
       - '<pattern> failure modes problems at scale'
       - '<pattern> at scale <N> users cost'
       - '"modular monolith" vs microservices team size'
       extract: "trade-offs, scale thresholds, team size recommendations, failure modes"
   3b. web-search (scope: "reddit", 7–10 queries — focus on experience and regret)
       queries:
       - '<option A> regret went back to <previous>'
       - 'r/ExperiencedDevs <decision category>'
       - '<option A> operational cost hidden small team'
       - '<option B> failure mode production'
       extract: "lived experience, regret, reversal stories, hidden operational cost"

4. scrape-links (mixed batch: 3–5 authoritative URLs + 5–8 reddit permalinks from r/ExperiencedDevs, r/softwarearchitecture)
   extract = "decision criteria | trade-offs | scale thresholds | when NOT to use | team size recommendations | cost analysis | verbatim regret quotes"

5. Round 2 if gaps_to_watch unclosed: targeted search + scrape on the specific disagreement

6. Output: Trade-off matrix + recommendation with confidence + conditions that would flip it
```

**Adapt when:**
- Sources agree strongly → shorter validation, move to implementation
- Sources conflict on a key point → targeted search + scrape to resolve the specific disagreement
- Decision is hard to reverse → add an extra verification round

---

## Workflow 4: Fact Check — "Is this still true?"

**Typical `primary_branch`:** `web`
**Start:** `web-search scope:"web"` directly (skip `start-research` for simple fact checks)

```
1. web-search (scope: "web", 3–5 queries)
   queries:
   - '<claim> <official source> 2026'
   - 'site:<official-docs> <specific feature>'
   - '<topic> deprecated OR removed OR changed <year>'
   extract: "verify whether <claim> is still true as of 2026"

2. scrape-links (2–3 authoritative URLs)
   extract = "current status | version | date | changes since <original claim date> | caveats"

3. Done for most fact checks.
   If claim is contested:

4. web-search (scope: "reddit", 2–3 queries)
   - '<claim> true false 2026'
   - '<topic> changed updated'

5. scrape-links (best 1–2 reddit permalinks if needed)
```

**This workflow is intentionally short.** Most fact checks need 2 tool calls, not 10.

---

## Workflow 5: Production Incident — "Something is broken NOW"

**Speed is everything. Minimum viable research. Skip `start-research` — latency matters.**

```
1. web-search (scope: "web", 3 focused queries)
   queries:
   - '"<exact error>" <stack> fix'
   - '<service> <symptom> production fix'
   - 'site:stackoverflow.com "<error code>" <framework>'
   extract: "immediate fix steps and workarounds"

2. scrape-links (top 2–3 URLs)
   extract = "fix steps | workaround | root cause"

3. Apply the most plausible fix. If it works → done.
   If not:

4. web-search (scope: "reddit", 2 queries)
   - '"<error>" <framework> fix'
   - '<framework> <symptom> workaround'

5. scrape-links (best 1–2 reddit permalinks — auto-routed)
```

---

## Workflow 6: Security Audit — "Is this secure?"

**Typical `primary_branch`:** `web` (CVE databases + advisories lead; practitioners supplement)
**Start:** `start-research` → `web-search scope:"web"` with security-focused sources

```
1. start-research
   goal: "Identify known vulnerabilities, mitigations, and best practices for <library/framework/pattern> as of 2026"

2. web-search (scope: "web", 7–10 queries)
   queries:
   - 'OWASP <topic> cheat sheet 2026'
   - 'site:nvd.nist.gov <library>'
   - '<library> CVE vulnerability'
   - '<framework> <attack type> prevention'
   - '<topic> security best practices <language> 2026'
   extract: "CVEs, vulnerabilities, mitigation steps, security best practices"

3. scrape-links (3–5 URLs: OWASP, NVD, Snyk, official advisories)
   extract = "CVE IDs | CVSS scores | affected versions | patched versions | mitigation steps | recommended practices | prohibited practices"

4. web-search (scope: "reddit", 5–7 queries targeting r/netsec, r/AskNetsec)
   - '<library> security vulnerability'
   - '<attack type> prevention <framework>'
   - 'r/netsec <topic> 2026'

5. scrape-links (3–5 best reddit permalinks from security subreddits)
   extract = "real-world exploit patterns | mitigation verdicts | maintainer responses | practitioner audits"

6. Output: Prioritized findings with severity + specific fix steps
```

**Critical rule:** Security claims need 3-source verification — official advisory + practitioners + independent analysis. Single blog posts are not sufficient for security decisions.

---

## Workflow 7: Performance Investigation — "Why is this slow?"

**Typical `primary_branch`:** `web` (profiling guides + practitioner war stories)

```
1. start-research
   goal: "Diagnose <symptom> in <stack/component>, covering profiling approach, common bottlenecks, and optimization techniques"

2. web-search (scope: "web", 5–7 queries)
   queries:
   - '<framework> performance profiling production'
   - '<specific symptom> slow <language>'
   - '<component> optimization benchmarks'
   extract: "profiling approaches, common bottlenecks, optimization techniques"

3. scrape-links (3–5 URLs: profiling guides, optimization articles)
   extract = "profiling tools | diagnosis steps | common bottlenecks | optimization techniques | before-after benchmarks"

4. web-search (scope: "reddit", 3–5 queries)
   - '<framework> slow performance fix'
   - '<component> optimization real experience'
   - '<framework> p99 latency production'

5. scrape-links (3–5 reddit permalinks)
   extract = "war stories | specific numbers | fixes that worked | fixes that didn't"
```

---

## Workflow 8: Technology Landscape Scan — "What's the state of X?"

**Typical `primary_branch`:** `reddit` (community pulse is the best starting point for state-of-ecosystem questions)

```
1. start-research
   goal: "Map the current state of <technology> in 2026 — active projects, recent changes, adoption trends, pain points"

2. web-search (scope: "reddit", 7–10 queries)
   - '<technology> state of 2026'
   - 'what changed in <technology> recently'
   - '<technology> new features 2026'
   - '<technology> vs alternatives 2026'
   - 'r/<relevant-sub> <technology> updates'

3. scrape-links (3–5 most active recent reddit permalinks — auto-routed to Reddit API)
   extract = "recent changes | community consensus | emerging alternatives | pain points | migration patterns"

4. web-search (scope: "web", 3–5 queries)
   queries:
   - '<technology> changelog 2026'
   - '<technology> roadmap upcoming features'
   - '<technology> release notes latest'
   extract: "recent changes, roadmap, adoption trends"

5. scrape-links (2–3 URLs: changelogs, roadmaps)
   extract = "new features | breaking changes | deprecations | roadmap | release dates | adoption trends"
```

---

## Adapting Workflows

Workflows are starting points. Adapt based on what each step reveals:

| What you find | What to do |
|---|---|
| `web-search` returns excellent, clear results | Skip further rounds — scrape and conclude |
| `web-search scope:"web"` returns nothing relevant | Broaden terms, then try `scope:"reddit"` (niche topics live on Reddit) |
| Reddit threads are all 3+ years old | Results may be stale — verify against current official docs |
| Sources contradict each other | See `references/synthesis.md` for resolution patterns |
| All sources agree | High confidence — stop researching |
| First fix doesn't work | Run a second targeted round with what you learned |
| Classifier `## Gaps` lists items the brief flagged in `gaps_to_watch` | Round 2 must close those specific gaps before stopping |

The most common mistake is over-researching a question that was answered in step 2. The second most common mistake is under-researching a question that deserved the full loop.

# Research Workflows

These workflows show how the research loop adapts to different question types. They're starting points — let the evidence guide you to go deeper or stop early.

## Workflow 1: Bug Fix — "I hit an error I don't recognize"

**Start:** `web-search` (error messages are the most searchable content on the internet)

```
1. web-search
   - Exact error in quotes: `'"TypeError: Cannot read properties of undefined" react hooks'`
   - Error + framework + version: `'"Cannot read properties of undefined" useEffect React 19 fix'`
   - Site-targeted: `'site:stackoverflow.com "Cannot read properties" react'`
   - GitHub issues: `'site:github.com/facebook/react/issues "Cannot read properties"'`
   - Year-pinned: `'react hooks undefined error fix 2025'`

2. scrape-links (top 3-5 URLs)
   what_to_extract = "root cause|fix code before and after|version affected|environment conditions|workarounds"

3. Is the fix clear? → Apply it. Done.
   Fix unclear or conflicting? → Continue:

4. search-reddit (3-5 queries)
   - `'"[error message]" r/reactjs'`
   - `'[library] [symptom] workaround fix'`
   - `'[library] breaking change [version]'`

5. get-reddit-post (2-5 threads with "solved" signals)

6. Still stuck? → deep-research with the buggy code attached
   Ask for systematic diagnosis, not just "what's wrong"
```

**Adapt when:**
- Zero search results → error is likely in your own code, not a known issue
- Recent library update → scrape the changelog/release page
- Intermittent bug → deep-research with reproduction details + all involved files
- Multiple conflicting fixes → deep-research to synthesize and diagnose your specific case

---

## Workflow 2: Library Comparison — "Should I use A or B?"

**Start:** `web-search` (discover candidates and comparison resources first)

```
1. web-search (7-15 keywords covering every angle)
   - `'[A] vs [B] benchmark comparison 2025'`
   - `'best [category] library [language] 2025'`
   - `'[A] alternatives'`
   - `'site:npmtrends.com [A] [B]'`
   - `'[A] [B] migration guide'`
   - `'"switched from [A]" [language]'`
   - `'[A] production experience serverless'`

2. scrape-links (3-5 URLs: comparison articles, READMEs, npm pages)
   what_to_extract = "features|bundle size|performance benchmarks|limitations|maintenance activity|community size"

3. search-reddit (8-12 queries — heavy on negative signal)
   - `'[A] vs [B] production experience'`
   - `'switched from [A] to [B] why'`
   - `'[A] problems issues production'`
   - `'[B] gotchas limitations'`
   - `'r/[language] [category] recommendation 2025'`
   - `'[A] regret complex queries performance'`
   - `'"don't use [A]" OR "avoid [A]"'`
   - `'[B] production ready'`

4. get-reddit-post (5-8 highest-signal threads)
   fetch_comments=true, use_llm=false

5. deep-research (1-2 questions)
   - Synthesize all findings with YOUR constraints
   - Attach your code showing how the library will be used
   - Include everything you learned in KNOWN
   - Ask: "Which fits MY constraints? What are the migration costs? What specific risks for MY use case?"

6. Output: Decision matrix + recommendation
```

**Adapt when:**
- Clear winner after step 2 (strong consensus) → brief Reddit validation, then recommend
- All options have major issues → expand candidate list, run another search round
- Decision depends on a specific technical detail → scrape official docs for that detail

---

## Workflow 3: Architecture Decision — "How should I design this?"

**Start:** `web-search` for landscape, then `deep-research` for synthesis

```
1. Frame the decision: constraints, scale targets, team composition, risk tolerance, reversibility

2. web-search (10-20 keywords)
   - `'[pattern A] vs [pattern B] trade-offs 2025'`
   - `'site:martinfowler.com [pattern]'`
   - `'[pattern] production experience case study'`
   - `'[pattern] failure modes problems at scale'`
   - `'[pattern] at scale [N] users cost'`
   - `'"modular monolith" vs microservices team size'`

3. scrape-links (3-5 authoritative URLs)
   what_to_extract = "decision criteria|trade-offs|scale thresholds|when NOT to use|team size recommendations|cost analysis"

4. search-reddit (7-10 queries — focus on experience and regret)
   - `'[option A] regret went back to [previous]'`
   - `'r/ExperiencedDevs [decision category]'`
   - `'[option A] operational cost hidden small team'`
   - `'[option B] failure mode production'`

5. get-reddit-post (5-8 threads from r/ExperiencedDevs, r/softwarearchitecture)

6. deep-research (2-3 structured questions)
   - Rich KNOWN from steps 2-5
   - Attach architecture docs or current code
   - Ask about trade-offs, failure modes, and the specific conditions that change the answer

7. Output: Trade-off matrix + recommendation with confidence + conditions that would flip it
```

**Adapt when:**
- Sources agree strongly → shorter validation, move to implementation
- Sources conflict on a key point → targeted search + scrape to resolve that specific disagreement
- Decision is hard to reverse → add an extra verification round

---

## Workflow 4: Fact Check — "Is this still true?"

**Start:** `web-search` (go directly to authoritative sources)

```
1. web-search (3-5 keywords)
   - `'[claim] [official source] 2025'`
   - `'site:[official-docs] [specific feature]'`
   - `'[topic] deprecated OR removed OR changed [year]'`

2. scrape-links (2-3 authoritative URLs)
   what_to_extract = "current status|version|date|changes since [original claim date]|caveats"

3. Done for most fact checks.
   If claim is contested:

4. search-reddit (2-3 queries)
   - `'[claim] true false 2025'`
   - `'[topic] changed updated'`
```

**This workflow is intentionally short.** Most fact checks need 2 tool calls, not 10.

---

## Workflow 5: Production Incident — "Something is broken NOW"

**Speed is everything. Minimum viable research.**

```
1. web-search (3 focused keywords)
   - `'"[exact error]" [stack] fix'`
   - `'[service] [symptom] production fix'`
   - `'site:stackoverflow.com "[error code]" [framework]'`

2. scrape-links (top 2-3 URLs)
   what_to_extract = "fix steps|workaround|root cause"

3. Apply the most plausible fix. If it works → done.
   If not:

4. search-reddit (2 queries, with date_after for recency)
   - `'"[error]" [framework] fix'`
   - `'[framework] [symptom] workaround'`
```

---

## Workflow 6: Security Audit — "Is this secure?"

**Start:** `web-search` with security-focused sources

```
1. web-search (7-10 keywords)
   - `'OWASP [topic] cheat sheet 2025'`
   - `'site:nvd.nist.gov [library]'`
   - `'[library] CVE vulnerability'`
   - `'[framework] [attack type] prevention'`
   - `'[topic] security best practices [language] 2025'`

2. scrape-links (3-5 URLs: OWASP, NVD, Snyk, official docs)
   what_to_extract = "CVE IDs|CVSS scores|affected versions|mitigation steps|recommended practices|prohibited practices"

3. search-reddit (5-7 queries targeting r/netsec, r/AskNetsec)
   - `'[library] security vulnerability'`
   - `'[attack type] prevention [framework]'`
   - `'r/netsec [topic] 2025'`

4. get-reddit-post (3-5 threads from security subreddits)

5. deep-research (1-2 questions)
   - Attach auth middleware, route handlers, or security-sensitive code
   - Ask for prioritized remediation plan
   - Specify compliance requirements (SOC2, HIPAA, PCI-DSS)

6. Output: Prioritized findings with severity + specific fix steps
```

**Critical rule:** Security claims need 3-source verification — official docs + practitioners + independent analysis. Single blog posts are not sufficient for security decisions.

---

## Workflow 7: Performance Investigation — "Why is this slow?"

```
1. web-search (5-7 keywords)
   - `'[framework] performance profiling production'`
   - `'[specific symptom] slow [language]'`
   - `'[component] optimization benchmarks'`

2. scrape-links (3-5 URLs: profiling guides, optimization articles)
   what_to_extract = "profiling tools|diagnosis steps|common bottlenecks|optimization techniques|before-after benchmarks"

3. search-reddit (3-5 queries)
   - `'[framework] slow performance fix'`
   - `'[component] optimization real experience'`

4. deep-research (1-2 questions)
   - Attach the slow code + profiler output
   - Include current metrics (p50, p95, p99) and target
   - Ask for prioritized fix list ordered by expected impact
```

---

## Workflow 8: Technology Landscape Scan — "What's the state of X?"

**Start:** `search-reddit` (community pulse check is the best starting point)

```
1. search-reddit (7-10 queries)
   - `'[technology] state of 2025'`
   - `'what changed in [technology] recently'`
   - `'[technology] new features 2025'`
   - `'[technology] vs alternatives 2025'`
   - `'r/[relevant-sub] [technology] updates'`

2. get-reddit-post (3-5 most active recent threads)

3. web-search (3-5 keywords)
   - `'[technology] changelog 2025'`
   - `'[technology] roadmap upcoming features'`
   - `'[technology] release notes latest'`

4. scrape-links (2-3 URLs: changelogs, roadmaps)
   what_to_extract = "new features|breaking changes|deprecations|roadmap|release dates|adoption trends"
```

---

## Adapting Workflows

Workflows are starting points. Adapt based on what each step reveals:

| What you find | What to do |
|---|---|
| web-search returns excellent, clear results | Skip Reddit — scrape and conclude |
| web-search returns nothing relevant | Broaden terms, then try search-reddit (niche topics live on Reddit) |
| deep-research gives a confident answer | Verify one key claim with scrape-links, then stop |
| Reddit threads are all 3+ years old | Results may be stale — verify against current official docs |
| Sources contradict each other | See `references/synthesis.md` for resolution patterns |
| All sources agree | High confidence — stop researching |
| First fix doesn't work | Run a second targeted round with what you learned |

The most common mistake is over-researching a question that was answered in step 2. The second most common mistake is under-researching a question that deserved the full loop.

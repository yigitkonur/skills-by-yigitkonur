# Research workflows

Workflows are recipes — patterns for common research scenarios. Each fits
the **Plan → Reconnoiter → Triage → Capture → Synthesize** template,
names the exact tool call at every step, and ends with explicit stop
criteria.

Use the decision worksheet first. The right workflow saves rounds.

---

## Decision worksheet

Four yes/no questions route to the right workflow:

1. **Is this an active production incident or sub-30-minute fact check?**
   - Yes → Workflow 5 (Production incident) or Workflow 4 (Fact check).
     Skip `get-research-consultancy`.
   - No → continue.

2. **Choosing between options or making a design decision?**
   - Comparing tools → Workflow 2 (Library comparison).
   - Choosing a pattern → Workflow 3 (Architecture decision).
   - Otherwise → continue.

3. **Diagnosing a failure?**
   - Bug across versions → Workflow 1 (Bug investigation).
   - Performance degradation → Workflow 7 (Performance investigation).
   - Otherwise → continue.

4. **What kind of mapping?**
   - Security exposure → Workflow 6 (Security audit).
   - State of an ecosystem, market, vendor category, or 5+ entities →
     redirect to `run-deep-research`.

Every workflow except 4 and 5 starts with `get-research-consultancy`.

---

## Workflow 1: Bug investigation across versions

**When to use.** A library throws an error that prior versions did not.
Production app cannot easily downgrade. Need root cause + fix or
workaround.

**Plan.**

```
goal: "Investigate why <library> v<X.Y.Z> throws '<exact error text>'
on <runtime>+ when prior v<A.B.C> worked. User context: production app,
can't easily downgrade. Done = root cause + fix or workaround. Skip:
basic getting-started. Freshness: last 12 months. Quote discipline:
stacktraces verbatim."
```

**Reconnoiter.** `web-search` with exact-error queries — these
typically return high-CONSENSUS GitHub issues that should land in the
URL pool for round 2.

```
keywords: [
  '"<exact error text>" "<library>" site:github.com/<org>/<repo>/issues',
  '"<library>" "node 20" OR "node 21" breaking change',
  'site:github.com/<org>/<repo>/pull "<error text>"',
  'site:reddit.com/r/node/comments "<library>" "<error text>"',
  '"<library>" CHANGELOG "v<X.Y>"',
  'site:stackoverflow.com "<library>" "<error text>"',
  ... (~10 more across source classes)
]
```

**Triage.** Sort by CONSENSUS. Pick top 3–5 GitHub issues, top 2–3
changelog entries, top 1–2 Reddit threads.

**Capture.** Two parallel calls:

- `scrape-link` on GitHub issues + changelog (≤5 URLs):
  ```
  Page type hint: github-thread or changelog.
  extract:
  - exact error text verbatim
  - affected version ranges verbatim
  - maintainer decisions with date
  - accepted-fix commit hash if any
  - workarounds with code samples
  - resolved-in version

  Discipline: Quote stacktraces verbatim. List Not found with reason.
  ```
- `scrape-link` on Reddit threads (auto-routes through the Reddit API
  for full threaded comments):
  ```
  extract: verbatim quotes with author + score | recurring workaround
  reports | affected version reports
  ```

**Synthesize.** Diagnosis with evidence chain. Before/after fix code.
Caveats. Fallback. Start with immediate stabilization (what to deploy
in 15 minutes) if production-affecting.

**Stop criteria.** The fix is verified by ≥2 independent sources
(maintainer + practitioner), or the gap is documented as unresolvable
from available evidence.

---

## Workflow 2: Library / tool comparison

**When to use.** Choosing between two or more tools for a defined use
case over a defined time horizon. The Claude Code vs OpenAI Codex CLI
research from this skill's authoring session is the canonical example
— see the worked goal in `prompting.md`.

**Plan.**

```
goal: "Decide between <A> and <B> for <use case> over the next <N>
months. User context: <stack, budget, OS, preferences>. Done = (1)
feature matrix limited to facets that materially affect day-to-day work,
(2) personal 'pick X if Y else Z' recommendation, (3) lock-in /
switching cost list per tool. Already known: <basics>. What to learn:
non-obvious differentiators, limit asymmetry under sustained use, recent
regressions / postmortems / pricing changes. Skip: enterprise SSO, SOC2,
multi-tenant. Freshness: last 90 days; >6mo as historical only.
Quote discipline: every numeric/versioned/priced claim verbatim."
```

**Reconnoiter.** Naturally two orthogonal keyword clusters. Fan out
twice in parallel:

- `web-search` (20–30 keywords across vendor docs, GitHub repos,
  changelogs, blogs, HN, comparison posts).
- `web-search` (10–15 Reddit-permalink keywords with negative-signal:
  "switched from", "regret", "limit", "broke", "migration").

Expect persistence to file. Plan a subagent triage step from the start.

**Triage.** Subagent reads both URL lists, returns top 8–15 URLs
deduplicated by facet:

- Vendor docs / overview pages
- Sandbox / permissions / sub-features pages
- Pricing / plans pages
- Changelog / postmortems
- Comparative blog posts (HN-discussed, recent)
- Reddit comparison threads (switcher experiences, rate-limit reports)

**Capture.** Three parallel calls:

- `scrape-link` on vendor A docs (≤5 URLs):
  ```
  extract: features by facet | sandbox/permissions verbatim | pricing
  tiers verbatim | install commands | recent changelog headlines verbatim.
  Discipline: preserve config keys, command syntax, version strings.
  List Not found with reason.
  ```
- `scrape-link` on vendor B docs (same shape).
- `scrape-link` on Reddit comparison threads (≤5 threads):
  ```
  extract: verbatim quotes with author + score | agreement reasons |
  dissent reasons | migration drivers
  ```
  Reddit threading is the evidence — the Reddit API fetches full
  threaded comments before extraction, so vote-weighted dissent and
  switcher quotes are preserved rather than compressed away.

If the vendor-docs `scrape-link` call times out, split per the
`failure-modes.md` playbook.

**Synthesize.** Feature matrix with verbatim quotes per cell. "Pick X if
Y else Z" recommendation. Lock-in / switching costs. Mark inference vs
evidence. Surface contradictions (the Claude Code vs Codex session
surfaced "Codex is hands-off" vs "Codex asks for approval constantly" as
a `## Contradictions` finding — both quotes verbatim, the contradiction
itself revealed a Windows-only bug).

**Stop criteria.** Every comparison axis closed with ≥2 source quotes
(one vendor, one practitioner). Recommendation has explicit conditions
that would flip it.

---

## Workflow 3: Architecture decision research

**When to use.** Choosing between architectural patterns at a defined
team size and scale.

**Plan.**

```
goal: "Decide between <pattern A> and <pattern B> for <component> at
<scale> with <team size>. User context: <team, codebase, incumbent>.
Done = decision memo with tradeoff matrix and 6-month risk projection.
Known: both work in principle. What to learn: real adoption stories at
<scale>, regrets, hidden operational costs, migration friction. Skip:
tutorials. Freshness: last 24 months for adoption; latest for
benchmarks. Quote discipline: production-incident reports verbatim."
```

**Reconnoiter.** Two orthogonal keyword clusters.

- `web-search` (15–20 keywords): `martinfowler.com`, `microservices.io`,
  vendor docs, "case study", "post-mortem", "at scale", "failure modes".
- `web-search` (7–10 Reddit-permalink keywords): r/ExperiencedDevs,
  r/softwarearchitecture, "regret went back to", "hidden operational
  cost", "<pattern> at <team-size> team".

**Triage.** Sort both lists by CONSENSUS; pick the top URLs across
source classes, checking the brief's `gaps_to_watch` for anything still
uncovered.

**Capture.**

- `scrape-link` on authoritative architecture pages (≤5 URLs):
  ```
  extract: decision criteria | trade-offs | scale thresholds | when
  NOT to use | team size recommendations | cost analysis | author's
  recommendation logic.
  Discipline: preserve recommendation logic verbatim.
  ```
- `scrape-link` on Reddit threads from r/ExperiencedDevs and similar
  (≤5 threads):
  ```
  extract: verbatim quotes with author + score | regret narratives |
  hidden operational costs | migration friction reports
  ```

**Synthesize.** Trade-off matrix with cited sources per cell.
Recommendation with confidence level. Conditions that would flip the
decision. Reversibility analysis.

**Stop criteria.** Every brief `gaps_to_watch` item closed. Decision
includes explicit reversal conditions.

---

## Workflow 4: Fact check / claim verification

**When to use.** Verify a single claim against primary sources. Skip
`get-research-consultancy` — overhead outweighs value for sub-5-call
sessions.

**Plan.** Inline (no `get-research-consultancy` call):

> Verify "<exact claim>" against the primary source. Need quoted text,
> URL, scrape date, or confirmation that the claim cannot be substantiated.

**Reconnoiter.** `web-search` (3–5 keywords):

```
keywords: [
  '<claim> site:<official-source>',
  'site:<official-source> "<key phrase from claim>"',
  '<topic> deprecated OR removed OR changed <year>',
  '<claim> CHANGELOG OR "release notes"'
]
```

**Triage.** Top 2–3 URLs by CONSENSUS.

**Capture.** `scrape-link` (≤3 URLs):

```
extract: current status of <claim> verbatim | version | date | changes
since <original claim date> | caveats.
Discipline: only verbatim primary-source quotes count.
```

**Synthesize.** One paragraph. Quoted text + URL + scrape date, OR
explicit "claim cannot be substantiated from primary sources".

**Stop criteria.** Two tool calls answered the question, OR the claim
is contested — escalate to one Reddit-permalink `web-search` call to
gather dissent.

This workflow is intentionally short. Most fact checks need 2 tool
calls, not 10.

---

## Workflow 5: Production incident research

**When to use.** Live incident. Speed is everything. Minimum viable
research.

**Plan.** No `get-research-consultancy`. Latency matters more than
tailoring.

**Reconnoiter.** `web-search` (3 focused keywords):

```
keywords: [
  '"<exact error>" "<stack>" fix',
  '"<service>" "<symptom>" production fix',
  'site:stackoverflow.com "<error code>" "<framework>"'
]
```

**Triage.** Top 2–3 URLs. Read.

**Capture.** `scrape-link` on top 2–3 URLs:

```
extract: root cause | fix steps | workarounds | error text verbatim
```

**Synthesize.** Most plausible fix. Apply.

**If first fix does not work:** one more `web-search` (2–3
Reddit-permalink keywords with negative signal), one more `scrape-link`
on top 1–2 permalinks. Stop after 5 minutes regardless — escalate to
human.

**Stop criteria.** Symptom resolved, OR 5 tool calls reached without
resolution → escalate.

---

## Workflow 6: Security advisory audit

**When to use.** Auditing a dependency tree against known CVEs and
practices. Pre-release security gate.

**Plan.**

```
goal: "Audit <dependency tree or library> against current CVEs and
security advisories. User context: <pre-release / ongoing audit>.
Done = list of unpatched CVEs, severity, mitigation status, plus
practitioner-confirmed exploit patterns. Skip: speculative advisories.
Freshness: published in last 18 months. Quote discipline: CVE-IDs,
CVSS scores, affected ranges verbatim."
```

**Reconnoiter.** Two rounds.

- `web-search` (7–10 keywords): NVD, MITRE, OWASP, Snyk, vendor security
  advisories, GitHub security advisories.
- Second round: `web-search` (5–7 Reddit-permalink keywords) targeting
  r/netsec, r/AskNetsec, r/cybersecurity for real-world exploit
  experience.

**Triage.** All top-CONSENSUS URLs across both rounds. Security claims
need ≥3-source verification.

**Capture.**

- `scrape-link` on advisories (≤5 URLs):
  ```
  Page type hint: cve.
  extract: CVE-ID verbatim | CVSS score verbatim | affected version
  ranges verbatim | patched versions verbatim | mitigation steps |
  exploit availability if stated.
  Discipline: never paraphrase impact statements.
  ```
- `scrape-link` on r/netsec threads (≤5 permalinks):
  ```
  extract: verbatim quotes with author + score | reported exploit
  experience | mitigation reports | dissent on severity
  ```

**Synthesize.** Prioritized findings table: CVE-ID, severity, affected
range, fix, exploit observed in wild (yes/no/unknown). Mark inference
vs evidence sharply for security work.

**Stop criteria.** Every relevant CVE has 3-source confirmation
(advisory + practitioner + at least one independent analysis). Security
claims with single-source backing must be flagged as preliminary.

---

## Workflow 7: Performance investigation

**When to use.** Comparing approaches at a defined workload and scale.

**Plan.**

```
goal: "Compare <approach A> vs <approach B> for <workload> at <scale>.
User context: <component, p99 target, budget>. Done = benchmark summary
with cited numbers + recommendation + caveats. Known: both work
correctly. What to learn: numbers from production, not synthetic
benchmarks. Skip: marketing claims. Freshness: last 18 months.
Quote discipline: every benchmark number verbatim with workload spec."
```

**Reconnoiter.** Mostly vendor/blog keywords; Reddit for war stories.

- `web-search` (15–20 keywords): vendor docs, benchmark posts,
  conference talks, profiling guides.
- `web-search` (7–10 Reddit-permalink keywords): r/programming,
  r/<language>, "p99 latency", "memory bloat", "saved <%> by switching".

**Triage.** Benchmarks with disclosed methodology > marketing
comparisons.

**Capture.**

- `scrape-link` on benchmark posts (≤5 URLs):
  ```
  extract: results with verbatim numbers | methodology | hardware specs
  | versions tested | workload spec | caveats | author's verdict.
  Discipline: every benchmark number verbatim with workload spec.
  Reject any benchmark without disclosed methodology (note in Not found).
  ```
- `scrape-link` on Reddit threads (≤5 permalinks):
  ```
  extract: verbatim quotes with author + score | reported numbers |
  workload context | migration outcome
  ```

**Synthesize.** Benchmark summary table. Recommendation conditional on
workload match. Explicit caveats where benchmarks did not match the
user's scale.

**Stop criteria.** Every numeric claim sourced. Recommendation includes
the workload conditions under which it holds.

---

## Redirect: landscape and corpus requests

Do not run ecosystem landscape scans in `run-research`. Requests such as
"state of X", "market map", "category landscape", "compare 8 vendors",
"build an evidence pack", or "research alternatives to X" are
corpus-shaped. Use `run-deep-research`.

If the user asks one narrow technical question inside a landscape, such
as "is library A still maintained enough for production use?", keep that
as `run-research` and answer only that question.

---

## Adapting workflows

Workflows are starting points. Adapt based on what each step reveals.

| What you find | What to do |
|---|---|
| Search returns excellent, clear results | Skip further rounds — scrape and conclude |
| Search returns nothing relevant | Broaden terms; try Reddit-permalink keywords; see `failure-modes.md` |
| Reddit threads all 3+ years old | Results may be stale — verify against current official docs |
| Sources contradict each other | See `synthesis.md` for resolution patterns |
| All sources agree | High confidence — stop researching |
| First fix does not work | Run a second targeted round with what you learned |
| `scrape-link` `## Not found` lists items the brief flagged in `gaps_to_watch` | Round 2 must close those specific gaps before stopping |
| `scrape-link` `## Contradictions` surfaces unannounced | The disagreement may BE the answer — surface it in synthesis |

The most common mistake is over-researching a question that was answered
in step 2. The second most common mistake is under-researching a
question that deserved the full loop.

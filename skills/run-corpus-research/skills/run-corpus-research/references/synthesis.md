# Synthesis Discipline

How the orchestrator turns scattered subagent outputs into a
decision-grade master summary, profile pages, and cross-entity
comparisons. Read this in **Phase 7** before the master summary;
also consulted across Wave 3 for cross-entity discipline.

## The orchestrator's personal-read gate

Before writing the master summary, read every `<entity-slug>/` core
pack in full and every `_cross/<axis-slug>/` folder in full. No
delegation. No subagent-of-subagent for synthesis.

Master summaries written without personal reading have a
recognizable texture: one paragraph per agent file stitched
together with transitions. They lack cross-domain insight. The
decider can read the files; the master summary's job is to add
what the agent files cannot — emergent recommendations,
contradictions across files, the conditions under which the
recommendation flips.

### The personal-read gate procedure

Before writing the master summary, run this procedure:

1. **Read every `<entity-slug>/` core pack in full.** Per entity,
   this is ~10-15 files. Total reading: roughly 30-60 minutes for
   5-8 core entities.
2. **Read every `_cross/<axis-slug>/` folder in full.** Per axis,
   ~5-12 files.
3. **Note recurring patterns across entities.** Things mentioned in
   3+ entity packs are usually load-bearing for the master summary
   (e.g., "every entity I read has reliability gaps in the same
   region — this is a category-wide finding, not entity-specific").
4. **Note disagreements across files.** When entity A's pack claims
   X and the cross-axis comparison claims not-X, the disagreement
   is decision-relevant; surface it.
5. **Note `## Not found` patterns.** If multiple entities have
   "insufficient evidence" entries on the same axis, the axis
   itself may not be supportable from public sources — surface this
   as a methodology limitation in the master summary.
6. **Note unanswered questions.** If during reading you find
   yourself thinking "the decider would want to know X", and X is
   not answered anywhere, X is an open gap.
7. **Note tier-promotion candidates.** If a `secondary` entity's
   pack reveals decision-flipping evidence, log it in
   `_meta/07-dispatch-log.md` and consider a Wave 4 mission.

The reading IS the synthesis. The master summary writes the
emergent insights surfaced during the read; it does not regenerate
them.

## Source credibility

| Source type | Trust level | Best for |
|---|---|---|
| Official docs (current version) | Highest | How things should work; exact API; config syntax |
| Official changelog / release notes | Very high | What changed; breaking changes; version-specific facts |
| Official postmortems / incident reports | Very high | What broke; why; what changed in response |
| Maintainer responses (issues, PRs) | High | Known bugs; intended behavior; workarounds |
| Scraped benchmarks with disclosed methodology | High | Performance claims (verify workload conditions match) |
| `## Synthesis` from `smart-web-search` | Moderate-high for analysis; low for facts | Trade-off reasoning. Never cite as evidence — it reads titles+snippets, not bodies |
| Highly-upvoted Reddit (100+ votes, specifics) | Moderate-high | How things actually work in production |
| Stack Overflow accepted + highly voted | Moderate-high | Common solutions (check date) |
| Recent blog by named practitioner with specifics | Moderate | Single data point, useful if detailed |
| Low-engagement Reddit | Low-moderate | Unvalidated individual opinion |
| Vendor marketing or comparison pages | Low | Extract facts only; ignore assessments |

## Citation discipline

The hard rule: **only scraped page content is evidence.** Search
snippets are leads, not citations. The `## Synthesis` block from
`smart-web-search` is a planning aid — its rank-citations point to
URLs not yet scraped.

For each non-trivial claim in any corpus file, capture:

- The verbatim quote.
- The URL.
- The scrape date.
- Source-specific attribution: Reddit username + score + date;
  GitHub issue number + maintainer handle; blog author + date;
  CVE-ID + CVSS score.

Compliant citations:

> "<Vendor> requires its agent to be run inside the workspace
> directory and inherits the workspace's write permissions." —
> docs.example.com/setup (scraped 2026-05-08).

> u/practitioner_alpha (+47, 2026-04, r/relevantsubreddit): "We
> hit the rate limit at exactly 800 requests/min, never the
> claimed 1000."

Non-compliant:

- "According to <Vendor>, X is supported." (no quote, no URL)
- "Reddit consensus is..." (no attribution, no source)
- "The docs say X." (no quote, no URL)
- A URL alone with no quote — implies the page was read; verify
  or re-scrape.

## Inference vs evidence

Claims fall in three categories:

- **Direct evidence.** A verbatim scraped quote supports the claim.
- **Aggregate evidence.** Multiple sources agree; cite ≥3 with
  quotes.
- **Inference.** The claim is reasonable but no source states it
  directly. Mark with explicit qualifier ("inferred from <X> and
  <Y>", "no source confirms but suggested by <Z>").

Never blend. Inference paragraphs should look visibly different
from evidence paragraphs.

## The smart-* output sections as synthesis aids

Every Wave 2 subagent's run-research session produces structured
output sections. The orchestrator can use these directly:

- **`## Matches`** populates the claims ledger. Each claim with
  verbatim quote becomes a row in `<entity-slug>/09-sources.md`.
- **`## Not found`** flags evidence gaps. Every "insufficient
  evidence" entry in the corpus should link back to a `## Not
  found` line — they are the same thing, captured in the corpus.
- **`## Follow-up signals`** could seed a Wave 4 promoted research
  if the unscraped URLs are decision-flipping.
- **`## Contradictions`** surfaces disagreements within a single
  page or across the call. These must be surfaced in synthesis;
  silent picking is a failure.

Wave 3 synthesizers should look for `## Contradictions` sections in
per-entity Wave 2 outputs. The contradictions tell the synthesizer
where deciders will face trade-offs.

## Resolving contradictions

When sources disagree, do not silently pick. Understand why they
disagree:

- **Different versions.** Source A describes v3; source B describes
  v4. Recent version's docs win for "how it works now".
- **Different scale.** "X is fine" (small scale) vs "X fell over"
  (large scale). Both right in their context. Match to decider's
  scale.
- **Different context.** Architecture differences cause apparent
  contradictions. Name the context variable.
- **Official docs vs community experience.** Docs describe intended
  behavior; community reveals actual behavior. Trust community for
  "does it work in practice"; trust docs for "how is it supposed
  to work".
- **Smart-search synthesis vs scraped facts.** Always trust scraped
  pages over smart-search synthesis for specific facts.
- **Nobody agrees.** The answer is genuinely context-dependent.
  Do not force one recommendation; name the variables that
  determine which is best.

## Cross-entity synthesis discipline (Wave 3 outputs)

A good cross-entity comparison file is not concatenation. It
answers:

- Which entities are directly comparable, adjacent, or not
  comparable?
- Which wins for which scenario? (Conditional rankings, not flat.)
- Which ranking is source-backed; which is provisional?
- What unknown would change the answer?
- What should the decider test next to resolve open uncertainty?

Every Wave 3 cross file must include:

1. Scope and capture date.
2. Short recommendation with confidence level.
3. Matrix or ranking.
4. Evidence confidence per row.
5. Important contradictions (surfaced; not resolved unless
   resolution is unambiguous).
6. Scenario-specific guidance.
7. Tests or data needed to change the recommendation.
8. Sources (links to per-entity files).

## Profile pages — the 10-section template

Profile pages are decision-grade synthesis-with-links. They are
not the entity's overview file (that lives in
`<entity-slug>/00-overview.md` and is shorter, more atomic). The
profile page is the buyer's first-or-second read.

Section ordering:

1. **Metadata** — entity name, vendor/maintainer, scrape date,
   profile author (orchestrator), scope.
2. **Executive summary** — 3-5 sentences. What this entity is, its
   strongest fit, its weakest fit.
3. **Headline findings** — 5-9 bullets. The most decision-flipping
   facts surfaced.
4. **Best-fit scenarios** — when to choose this, with conditions.
5. **Do-not-choose-if scenarios** — when to avoid, with conditions.
6. **Pack map** — links into the evidence pack subfolders, with
   one-line "what's here" per link.
7. **Deep profile** — narrative synthesis, 200-500 lines, with
   inline links to pack files.
8. **Numbers table** — 5-10 quantitative facts with caveats and
   pack-file citations.
9. **Open gaps** — what could not be answered and why.
10. **Sources** — list of authoritative URLs from the pack's
    `09-sources.md`.

Length target: 300-700 lines. Below 300 means under-synthesis;
above 700 means duplicating pack content.

## Master summary (`_meta/00-master-summary.md`)

The orchestrator's signature artifact. Read by the decider first.

Required sections:

1. **Document index** — every file in the corpus with one-line
   description. Decider's navigation map.
2. **Critical findings** — 3-7 points. Each cites the source file
   and evidence depth. The corpus's load-bearing claims.
3. **Cross-domain insights** — findings that emerged from reading
   multiple files together. The orchestrator's signature value.
4. **Action items** — concrete next steps with priority.
5. **Coverage scope** — what was researched; what was deliberately
   excluded.
6. **Open gaps** — what could not be answered and why.
7. **Recommendation** — with confidence level and explicit
   conditions that would flip it.

## Output formats by question type

The master summary's "Recommendation" section adapts to the
question type:

### Decision memo

```
RECOMMENDATION: [Clear choice]
CONFIDENCE: [High/Medium/Low] based on [N sources, agreement level]
WHY: [2-3 sentences connecting evidence to recommendation]
TRADE-OFFS:
  - Choosing this: [specific benefit, sourced] but [specific drawback, sourced]
  - Alternative: [what you'd gain] at the cost of [what you'd lose]
CONDITIONS: This assumes [decider's constraints]. If [variable]
            changes, reconsider [alternative].
```

### Market map

```
LANDSCAPE: [N core, M secondary, K discovered-only]
LEADERS: [entity, evidence] with strongest cases
EMERGING: [entity, evidence] worth watching
DECLINING / DEPRECATED: [entity, evidence]
GAPS IN MARKET: [unmet decider needs]
```

### Advisory (security / compliance)

```
| <Risk> | Severity | Affected | Mitigation | Source |
|---|---|---|---|---|
PRIORITY: [Highest unmitigated risk first]
REMEDIATION: [Concrete steps with deadlines]
RESIDUAL RISK: [What remains exposed and why]
```

### Multi-axis comparison

```
| Axis | Entity A | Entity B | Entity C | Source |
|---|---|---|---|---|
BEST FOR <scenario A>: <entity> because <reason>
BEST FOR <scenario B>: <entity> because <reason>
AVOID <entity> when <condition> because <evidence>
```

## Master summary anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Stitched, not synthesized | One paragraph per entity glued with transitions | Write cross-domain findings — things visible only after reading multiple files together |
| Buries the recommendation | Reader finishes 4 pages without knowing what to do | Lead with the recommendation; details support it |
| Recommendation without conditions | "Use X" without naming when not to | Conditional ranking is the norm; name what would flip the answer |
| Missing contradictions | Cross-axis files surfaced disagreements; master summary smooths them | Surface contradictions explicitly; name the source-credibility tier on each side |
| Generic action items | "Consider all options carefully" | Concrete next steps with priority and decider-specific framing |
| No coverage scope | Reader cannot tell what was researched and what wasn't | Explicit "what was researched / what was deliberately excluded" section |
| Hidden gaps | "Comprehensive coverage" framing masks specific data gaps | "Open gaps" section with the specific data the corpus could not answer |
| Inflation by quotes | Long verbatim quotes in the master summary | Quote in pack files; cite paths in the master summary; preserve density |
| No fresh-context test | Master summary illegible to a fresh reader | Write so a decider with no session history can act on it |
| Missing the meta-finding | Patterns visible across entities go unsaid | Cross-domain insights section names category-wide patterns |

## The fresh-context self-review gate

Before delivering the master summary, run a mental self-review with
no prior session memory:

- Open the summary as if reading it for the first time.
- For each non-trivial claim: where is the evidence? Can a quote,
  URL, scrape date, attribution be located in the corpus?
- For each numeric / versioned / priced claim: is this verbatim
  from a scrape, or paraphrased?
- For each contradiction: is the disagreement surfaced clearly,
  or silently picked?
- For each inference: is it visibly marked as inference?

Any "no" is a fix-before-delivery item.

The most common failures:

- A claim sourced from a search snippet rather than a scraped page.
- A version number from memory not in any scraped source.
- A contradiction smoothed over in prose ("most sources agree...").
- An inference written in the same voice as direct evidence.
- A profile page that duplicates pack content instead of
  synthesizing it.
- A master summary that stitches per-entity findings rather than
  surfacing emergent insights.

## Verification checklist (synthesis-quality)

Before declaring the corpus complete:

- [ ] Master summary exists at `_meta/00-master-summary.md` with
      all 7 required sections.
- [ ] Every `core` entity has a profile page at corpus root with
      the 10-section template.
- [ ] Every `_cross/<axis-slug>/` has a `00-overall-comparison.md`
      with matrix, ranking, evidence confidence, contradictions.
- [ ] Key claims confirmed by 2+ independent sources.
- [ ] No unresolved contradictions (resolved, surfaced, or
      explicitly flagged as unresolvable).
- [ ] Version-specific claims checked against changelog.
- [ ] Sources actually independent (not citing each other).
- [ ] Recency appropriate for the domain.
- [ ] Smart-search `## Synthesis` claims about specific facts
      verified against scraped pages.
- [ ] `## Not found` sections from Wave 2 are reflected in the
      pack's "insufficient evidence" entries.
- [ ] Every numeric / versioned / priced claim has a verbatim
      quote.

**Verification effort matches stakes.** Quick fact check → 1
source. Library adoption → 2-3 sources. Architecture decision →
full triangulation. Security claim → never trust a single source.

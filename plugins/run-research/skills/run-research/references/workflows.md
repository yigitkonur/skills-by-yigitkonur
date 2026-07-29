# Adaptive research workflows

Use these as call-shape recipes, not fixed call counts. Let extracted gaps and
the session review determine whether another round has enough expected value.

For every sequence below, an `extract-evidence` result with
`continuation.required: true` inserts an extraction-continuation loop before
review or synthesis:

```text
extract-evidence -> exact continuation.next_call in same conversation/session
                -> repeat until settled or caller budget is exhausted
```

Pending work is a non-error partial result. Preserve completed findings and do
not call a pending requirement `not-found`. See `resumable-extraction.md`.

## 1. Known public URL

Sequence:

```text
extract-evidence -> required continuation loop -> optional review-research -> synthesize
```

Call the URL directly with one to five checkable requirements. Skip planning
and search. Review is useful only if the caller wants the server to assess this
trace or suggest corroboration; it may reasonably say the single source is not
independent enough.

Stop after the source answers the narrow question, or report the explicit
not-found/gated/fetch limitation.

## 2. Quick current fact

Sequence:

```text
web-search (2-5 exact queries) -> extract-evidence (2-3 sources)
-> required continuation loop -> synthesize
```

Prefer an official current source plus one independent corroborator. Use exact
version, plan, price, date, API, or error terms. Skip planning unless the
question expands.

Stop when the fact is grounded at the stakes-appropriate source level. A
routine documentation fact can need one authoritative source; contested price,
security, or compatibility facts need more.

## 3. Broad comparison or architecture decision

Sequence:

```text
plan-research
-> first-round web-search
-> authority-diverse extract-evidence calls
-> required continuation loops
-> review-research
-> selected advisory next call or synthesis
```

The objective should name user constraints and reversal conditions. Keep
official capability, pricing, failure/maintenance, and practitioner evidence in
separate clusters. Execute at most the selected first wave, not all query ideas.

Extract the same decision-critical fields across options, but do not force
symmetry when a source genuinely lacks an answer. Review after the first
evidence round. Stop on complete high/medium coverage with no unresolved
conflict, or state the critical blocked gap.

## 4. Version-specific bug

Planning is optional. Start with exact-error and exact-version queries:

```json
{
  "queries": [
    "\"exact error text\" package-name 4.2 site:github.com/issues",
    "package-name 4.1 4.2 breaking change release notes",
    "site:github.com/org/repo/pulls \"exact symbol\""
  ]
}
```

Extract issue/PR chronology, maintainer statements, affected/fixed versions,
commit/release, workaround, and environment. Add practitioner evidence only to
test field behavior.

Conflicting version ranges require another authoritative verification round.
Do not collapse “reported fixed” and “released fixed” into one fact.

## 5. Migration

Plan separate authority lenses:

- official supported path and compatibility matrix;
- repository issues and actual breaking changes;
- field failures, rollback paths, and hidden operational cost.

Search official/repository/community probes, then extract concrete steps and
preconditions. Review should prioritize an unresolved rollback or data-loss
risk above convenience gaps.

The synthesis must distinguish vendor-supported procedure from practitioner
workarounds and say which migration conditions remain unverified.

## 6. Pricing or quota

Plan only if several plans/products or contract conditions matter. Otherwise
use quick-fact routing.

Evidence requirements should request:

- source date or visible effective date;
- currency and region;
- billing interval;
- included quota and unit;
- overage/rate-limit behavior;
- tax, eligibility, exclusions, and future-tense announcements.

Prefer current official pricing and terms. Treat cached articles and search
snippets as leads only. Mark historical prices as historical; never merge them
with current claims.

## 7. Security advisory or CVE

Use a plan when exposure depends on several packages, platforms, or authority
classes. Keep vendor/advisory, repository fix, and field exploitation separate.

Extract exact CVE, CVSS, CWE/CPE where present, affected and fixed ranges,
mitigation, advisory authority, and publication/update dates. High/medium
security gaps cannot become ready without authoritative evidence.

Do not infer exploitability from severity alone. If advisories conflict, search
for the most current vendor or coordinating-authority update.

## 8. Product launch and reception

Plan at least two branches:

- shipped facts from official announcements, docs, releases, or repositories;
- observed reception from attributed practitioner sources.

Keep future promises separate from shipped behavior. Search practitioner
sources after the product terms and versions are known. Extract attributed
experiences, environments, and dates; do not turn engagement into population
sentiment.

## 9. Reddit/forum sentiment

Discover actual post permalinks with targeted queries, then pass them to
`extract-evidence`. Requirements should ask for attributable positions,
reasons, dissent, environment, and observed outcome.

Report:

- number of comments actually fetched/classified when available;
- attributed original quotations and permalinks/IDs;
- recurring themes as counts within that sample;
- sampling and recency limitations.

Never invent population percentages or call a small thread “community
consensus.”

## 10. Academic synthesis

Plan clusters around claim, method, dataset/sample, baselines, numeric results,
limitations, and replication/contradiction. Search papers, proceedings,
repositories, datasets, and credible replications as separate authority
classes.

Extract exact claims and results with method context. Do not compare numbers
whose datasets or evaluation protocols differ without saying so. Review should
favor missing methodological comparability over adding more topical papers.

## 11. Long document

Call `extract-evidence` directly if the URL is known. Write focused requirements
that provide lexical and structural selection signals. Read `covered_ranges`,
`omitted_ranges`, and completeness.

Long sources are more likely to cross the response budget. Follow the exact
same-session continuation until settled when time permits. Cached accepted
content can let later calls resume extraction without another provider fetch;
the extracted findings themselves are never cached.

A finding does not imply the entire document was examined. If omitted ranges
could change a high-priority answer, keep the requirement partial and narrow a
follow-up requirement instead of claiming full coverage.

## 12. Non-English source

Use normal routing. Require original-language quotations as canonical evidence.
Treat `translation_en` as generated assistance, not a replacement quote.

If a term is ambiguous, include the original term in follow-up queries and use
an authoritative bilingual/technical source rather than silently choosing a
translation.

## 13. Contradictory sources

Do not ask the review model to choose truth by style. Extract both sides with
verified quotations, dates, versions, and source roles. Search for a resolver
that changes the information state: current release note, maintainer decision,
official terms, or coordinating advisory.

If no resolver exists, stop with an explicit contradiction and the variable
that may explain it.

## 14. Provider or model outage

- sibling URL/query failures do not cancel successful work;
- search zero-results are valid statuses, not automatic tool errors;
- a planning outage returns a concise degraded plan;
- a review-model outage uses deterministic review and only retained validated
  continuation material;
- a response-budget cutoff returns pending sources and an exact non-error
  extraction continuation;
- total extraction failure is not raw-content success.

Continue through surviving provider paths when useful. Stop as blocked when the
missing capability is required for a critical gap.

## 15. Stateless or expired session

Primary tools still work. `review-research` returns unavailable history and no
invented strategic next call. An extraction result can still contain its own
required `continuation.next_call`; execute it in the same available transport
scope when affordable. If `resume_available` is false, the call is valid but
may repeat retrieval. Continue manually from outputs in host context, or begin
a new plan if a new retained trace is useful.

Never assume state from another conversation, transport session, process, or
replica.

## 16. Diminishing returns

After each round, ask whether it added a new candidate source or verified
finding. Two consecutive zero-yield rounds are a stop condition. At the round
cap, a critical gap is blocked; low-priority residual limitations can accompany
a ready answer.

Do not rephrase executed queries to create the appearance of progress.

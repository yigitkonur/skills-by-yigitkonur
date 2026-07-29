# Synthesize verified evidence

The final answer belongs to the calling agent. Planning and review guide the
process; search discovers leads; only quotation-validated extraction records
support claims.

## Evidence classes

Keep three classes visibly separate:

1. **Direct evidence**: a statement supported by an exact source quotation,
   URL, and code-derived locator.
2. **Cross-source synthesis**: a conclusion produced by comparing several
   direct evidence records. Cite every material side.
3. **Inference**: a reasoned implication no source states directly. Label it
   and name the evidence it depends on.

Plans, review reasons, search titles/snippets, diagnostic excerpts, generated
translations, and unverified model statements are not direct evidence.

## Source authority

Match source type to claim rather than using one universal ranking:

| Claim | Prefer | Use with care |
|---|---|---|
| Current supported API/config/version | official docs and current releases | old tutorials, snippets |
| Change chronology and intent | release notes, repository commits/issues/PRs, maintainer statements | third-party summaries |
| Security scope/fix | vendor/coordinating advisories, official repository fix | unsourced scanner pages |
| Pricing/terms | current official pricing and legal/plan terms | cached comparison posts |
| Production behavior | detailed independent reports and attributed practitioners | vague engagement-heavy opinion |
| Performance | disclosed method/workload/environment and reproducible data | marketing benchmarks |
| Academic claim | paper plus method/sample/result/limitations and replication | abstract-only summaries |

Independence matters. Five pages repeating one announcement are one evidence
lineage, not five confirmations.

## Citation record

For each non-trivial claim retain:

- source URL and type;
- exact original-language quotation;
- block/line locator (and heading when supplied);
- author/date only when validated;
- research/access date for time-sensitive claims;
- which requirement it answers;
- completeness and caveats.

If an English translation is useful, label it generated and keep the original
quotation beside it.

Do not cite a source merely because it appeared in search or extraction output.
Cite the specific verified finding that supports the claim.

## Interpret requirement statuses

- `answered`: sufficient verified evidence was found in the examined material;
  still consider authority and independence.
- `partial`: evidence exists but omitted material, weak scope, missing fields,
  failed packs, gating, or other limits prevent full closure.
- `not-found`: the fetched/examined source does not support the requirement; a
  useful negative result, not the opposite claim.
- `conflicting`: verified findings disagree; preserve both sides.

Use top-level independent-source counts as a triangulation signal, not a vote.

## Interpret pending source work

`pending` is source-level `retrieval_status` or `extraction_status`, never a
requirement status. It means retrieval or extraction did not finish inside the
bounded response and says nothing about whether the source contains the answer.
Follow the exact same-session continuation when affordable; otherwise expose
the unfinished source and requirement as a gap.

## Resolve contradictions

First test whether disagreement comes from:

- different versions or dates;
- different platforms/configurations;
- different workloads/scale;
- intended behavior versus field behavior;
- historical versus current/future-tense claims;
- primary authority versus a derivative source.

Then seek a resolver with higher information value: current release note,
maintainer decision, official terms, coordinating advisory, or a source that
states the missing condition.

If no resolver exists, present both verified sides and name the variable that
may explain the disagreement. Never average incompatible facts or silently
pick the more convenient source.

## Sentiment

Sentiment evidence is a sample, not a poll. Report:

- source/thread and date;
- comments actually fetched/classified when available;
- within-sample counts for classifications;
- attributed quotations and dissent;
- sampling, moderation, recency, and platform limitations.

Do not report a population percentage unless the source itself describes a
valid population study and the extracted method supports it.

## Output shapes

### Decision or comparison

Lead with the recommendation, confidence, and the conditions under which it
holds. Use a small comparison table only for decision-critical fields. For each
field, attach direct evidence or mark the gap. End with reversal conditions and
remaining limitations.

### Bug or migration

Present observed symptom/constraint, evidence-backed cause or supported path,
affected/fixed versions, concrete next step, fallback/rollback, and what remains
unverified. Separate “fix committed,” “fix released,” and “fix observed in the
field.”

### Security

Present authoritative identifier/scope, severity as sourced, affected/fixed
versions, mitigation, exploit evidence if stated, and residual uncertainty.
Never infer exploitability from score alone.

### Pricing

Present currency, region, billing interval, quota/unit, overage, eligibility,
tax/exclusions, and source date. Separate current, historical, and announced
future terms.

### Insufficient evidence

Say what was verified, which high-value gaps remain, why they could not be
closed, and what conclusion is safe despite them. Do not turn a blocked review
into a confident recommendation.

If the caller's budget ends with `continuation.required: true`, identify the
pending sources/requirements separately from terminal not-found or failed
sources. Completed schema-v2 findings remain usable; unfinished work cannot
support an absence claim.

## Fresh-context gate

Before delivery, re-read the answer as if the research trace were unavailable:

- Can every numeric, versioned, priced, security, or exact-behavior claim be
  traced to a verified quotation and URL?
- Did any search snippet, title, plan, review sentence, or diagnostic excerpt
  become evidence?
- Are translations, inference, and direct quotations distinguishable?
- Are contradictions visible?
- Does source completeness justify the strength of each statement?
- Are sources actually independent and current enough for the topic?
- Did the answer retain limitations even if the session verdict was ready?
- Did any pending extraction become a false not-found or disappear from the
  limitations, and were all affordable exact continuations completed first?

Fix every unsupported claim before delivering. A cleanly stated uncertainty is
more useful than fabricated completeness.

# Research Powerpack v9 tools

Use the four public tools as deep modules. Their JSON `structuredContent` is
canonical; the accompanying Markdown is intentionally shorter.

## `plan-research`

Input:

```json
{
  "objective": "What must be learned, compared, verified, or decided, including constraints and the completion standard."
}
```

Use for non-trivial work. Skip for one quick fact or a known URL.

Important output fields:

- `status`: `complete` or deterministic `degraded`.
- `clusters[]`: decision-critical questions, priority, evidence requirements,
  source preferences, selection signals, and zero to 25 distinct query ideas.
- `first_round.queries[]`: the selected first wave with cluster and purpose;
  maximum 12.
- `first_round.inspect_for[]`: positive/negative source signals and a selection
  limit for each cluster.
- `first_round.evidence_requirements[]`: initial checkable requirements.
- `reserve_queries[]`: useful unselected probes, not an obligation to search.
- `gaps[]` and `stop_conditions[]`: the uncertainty and completion contract.
- `budgets`: declared idea, first-wave, follow-up, URL, and round ceilings.

The planner can generate at most 100 ideas globally and 25 per cluster. These
are ceilings, not quotas. A narrow objective should produce far fewer. Do not
search the entire idea bank.

A degraded plan is usable but conservative. It should remain concise and must
not be mistaken for completed research.

## `web-search`

Input:

```json
{
  "queries": [
    "site:example.com/docs \"exact flag\" v4",
    "\"exact error text\" package-name 4.2 site:github.com"
  ]
}
```

Limits: one to 50 complete queries, each at most 500 characters. Unknown input
properties are invalid.

Important output fields:

- `evidence_status` is always `leads-only`.
- `queries[]` exposes `input`, actual `dispatched`, optional `relaxed`, status,
  result count, and warnings.
- `sources[]` contains up to 100 ranked, canonicalized sources with title,
  snippet, kind, normalized score, best position, matched queries, and matched
  plan cluster IDs.
- `omitted_source_count` states how many structured results were excluded.
- `warnings[]` reports provider fallback, relaxation, and partial behavior.

The Markdown rendering shows only the top 20. Use structured sources for
programmatic selection.

Interpretation rules:

- `ok` with zero useful sources is not provider failure.
- a relaxed query is not an exact-query match; preserve the disclosed lineage;
- several paraphrases in one cluster cannot inflate cluster contribution;
- the normalized score ranks discovery consensus, not factual accuracy;
- titles and snippets are untrusted leads and never citable evidence.

## `extract-evidence`

This is the only public tool whose output uses `schema_version: "2"`. Its input
is unchanged.

Input:

```json
{
  "urls": [
    "https://example.com/release-notes",
    "https://www.reddit.com/r/example/comments/abc123/topic/"
  ],
  "evidence_requirements": [
    "Which exact versions are affected and fixed?",
    "What workaround is explicitly documented?"
  ]
}
```

Limits: one to 20 public HTTP(S) URLs, one to 20 requirements, each requirement
at most 1,000 characters, and at most 10,000 combined requirement characters.
Unknown input properties are invalid.

Routing is automatic:

- Reddit post permalinks use the Reddit API for the post and fetched comment
  sample;
- web pages use Jina Reader, then sequential Scrape.do basic, JavaScript, and
  JavaScript plus US-geo modes;
- web pages may use Kernel as a final browser-render fallback;
- documents are Jina-only and never enter a proxy/browser-render path.

Different URLs advance concurrently and accepted source content enters map
extraction immediately. Provider modes remain sequential for each URL. A
60-second response ceiling means a large or slow call can return useful
completed evidence plus explicit pending work.

Important output fields per source:

- `retrieval_status`: `fetched`, `blocked`, `failed`, or `pending`.
- `extraction_status`: `complete`, `partial`, `not-applicable`, or
  `extraction-failed`, plus `pending` for admitted/unstarted work that did not
  finish inside the response budget.
- `source`: type, trusted/validated metadata, language, and completeness.
- `requirements[]`: stable requirement ID/text, `answered`, `partial`,
  `not-found`, or `conflicting`, plus findings.
- every finding citation includes an exact original-language `quote` and a
  code-derived `locator` with block and line range; a generated English
  translation is separate.
- `follow_up_signals[]`, `covered_ranges[]`, `omitted_ranges[]`, and warnings
  make incompleteness explicit.

Top-level `coverage[]` aggregates requirement status and independent source
count. `contradictions[]` contains only verified findings. `output_truncated`
means lower-value records were omitted with counts; it must not be interpreted
as full coverage.

Top-level `continuation` reports whether work remains, durability/scope of its
one-hour encrypted retrieval checkpoint, every pending input position, and an
exact next tool call. When `continuation.required` is true and caller budget
permits, invoke non-null `continuation.next_call` unchanged in the same
conversation/session before review or synthesis. Repeat as needed.

Semantics:

- a fetched source that genuinely does not contain an answer is a successful
  negative result;
- gated teaser/metadata evidence may be returned only as partial;
- fabricated or case-changed quotations are rejected;
- unsupported dates/authors remain `null`;
- raw source text is never a successful fallback extraction;
- pending retrieval has empty requirement records and is never `not-found`;
- completed evidence plus pending work is `partial` and non-error;
- even zero completed sources is non-error when a retryable continuation
  exists;
- the tool is an error only when there is no usable evidence and no viable
  continuation.

Read `resumable-extraction.md` for the exact schema-v2 continuation shape,
T+34/T+35/T+55 cutoffs, cache contents, and research-ledger distinction.

## `review-research`

Input:

```json
{}
```

Pass no properties. Review sees only the bounded in-process trace retained for
the current stateful MCP scope; it does not see the host conversation.

Important output fields:

- `mode`: model-assisted `full` or `deterministic-degraded`.
- `history`: availability, scope, in-process persistence, timestamps, and an
  honest unavailable reason.
- `progress`: rounds, calls, in-flight work, coverage counts, and stale rounds.
- `verdict`: `ready`, `continue`, or `blocked`.
- `coverage`, `quality_issues`, `contradictions`, and `remaining_gaps`.
- `next_calls[]`: at most three advisory options that already validate against
  `web-search` or `extract-evidence`, each with value score, confidence,
  purpose, and target gaps.
- `stop_reason`: completion, diminishing returns, round cap, capability block,
  unavailable history, or `null`.

Only candidates with value score at least 60 and confidence at least 0.65 are
exposed. Across all options there are at most eight proposed queries and five
proposed URLs. `ready` always has no next calls.

Do not call review repeatedly against unchanged state expecting a different
answer; the server returns the cached identical result. When operations are in
flight, wait rather than launch duplicate work.

## State limits that affect callers

- Review trace retention is in-process only: idle expiry one hour, absolute
  expiry four hours. Restart or replica movement can lose it.
- The separate retrieval checkpoint can be Redis-backed, encrypted, and reused
  for one absolute hour. It stores accepted source content/stage metadata, not
  requirements or extracted evidence. `resume_available` reports whether that
  durability exists for the current continuation.
- A plan selects one to four research rounds; the server never exceeds four.
- Two consecutive zero-yield rounds trigger diminishing returns.
- Stateless or expired history returns a non-throwing blocked review with no
  invented guidance.
- The trace is convenience state, not an authorization or durable workflow
  store. Keep any facts needed for the final answer in the host context.

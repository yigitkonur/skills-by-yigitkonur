# Resumable schema-v2 extraction

`extract-evidence` has a hard 60-second transport budget. It returns completed
evidence promptly and represents unfinished work explicitly instead of making a
20-URL worst case look complete.

## Contents

- [Caller protocol](#caller-protocol)
- [Continuation shape](#continuation-shape)
- [Pending is not failure or absence](#pending-is-not-failure-or-absence)
- [Why calls can return pending](#why-calls-can-return-pending)
- [Checkpoint store versus research ledger](#checkpoint-store-versus-research-ledger)
- [Retry and review discipline](#retry-and-review-discipline)

## Caller protocol

After every `extract-evidence` call:

1. Read canonical `structuredContent`; confirm `schema_version` is `"2"`.
2. Preserve completed findings, citations, coverage, and contradictions.
3. Inspect `continuation.required`.
4. When it is `true` and the task still has enough time, invoke
   `continuation.next_call` exactly as returned in the same MCP
   conversation/session.
5. Repeat until no continuation is required, or stop with a visible limitation
   because the caller's own budget is exhausted.
6. Review research coverage only after affordable required continuations have
   settled.

Do not edit, merge, broaden, or regenerate continuation arguments. In
particular, keep the returned `evidence_requirements` unchanged. A modified call
is new work and may not reuse the intended checkpoint lineage.

The Markdown rendering ends with `Continue extraction` and a fenced JSON value
that exactly matches `continuation.next_call`; nothing follows it. Prefer the
structured field over parsing that rendering.

## Continuation shape

```ts
continuation: {
  required: boolean;
  resume_available: boolean;
  resume_scope:
    | "verified-conversation"
    | "client-conversation"
    | "subject-in-session"
    | "transport-session"
    | "unavailable";
  cache_ttl_seconds: 3600;
  pending_sources: Array<{
    input_index: number;
    url: string;
    phase: "retrieval" | "extraction";
    reason:
      | "deadline"
      | "provider-in-progress"
      | "provider-cooldown"
      | "retrieval-interrupted"
      | "extraction-not-started"
      | "extraction-timeout";
    next_stage:
      | "jina"
      | "scrapedo-basic"
      | "scrapedo-javascript"
      | "scrapedo-javascript-us"
      | "kernel"
      | "reddit"
      | "extraction";
    retry_after_seconds: number | null;
    checkpoint_saved: boolean;
  }>;
  next_call: {
    tool: "extract-evidence";
    arguments: {
      urls: string[];
      evidence_requirements: string[];
    };
  } | null;
}
```

`pending_sources` preserves every original input position with a zero-based
`input_index`. The next call canonical-deduplicates pending URLs while retaining
their first-input order. Canonical duplicate inputs therefore share work
without losing positional status.

## Pending is not failure or absence

Retrieval and extraction status both admit `pending` in schema v2.

- Pending retrieval has empty requirement records. Never translate it to
  `not-found`.
- Completed evidence plus pending work is top-level `partial` with
  `isError: false`.
- Zero completed sources is still a non-error partial result when a retryable
  continuation exists.
- A terminal `failed` result is an error only when there is no usable evidence
  and no viable continuation.
- `checkpoint_saved: false` means durability was not established. It does not
  invalidate evidence already returned.
- `resume_available: false` means the next call may need to repeat retrieval;
  it does not authorize skipping a required continuation.

The complete MCP envelope remains capped at 200K characters after JSON
encoding. A maximum-size request with unusually escape-heavy URLs or
requirements can make the exact continuation itself impossible to encode
under that cap. In this irreducible case, the tool returns a bounded error that
instructs the caller to retry the same requirements with smaller URL batches.
This is an envelope limitation, not evidence that the sources failed or lacked
the requested information.

If the caller cannot afford another call, synthesize only completed verified
evidence and list pending requirements/sources as limitations.

## Why calls can return pending

Independent URL pipelines overlap, while provider fallbacks remain sequential
for each URL:

```text
cache -> Jina -> Scrape.do basic -> Scrape.do JavaScript
      -> Scrape.do JavaScript plus US geo -> Kernel -> extraction
```

Reddit permalinks use their own Reddit stage. Documents remain Jina-only.
Accepted content starts extraction immediately without waiting for sibling
URLs. Output still follows original input order.

The server uses these latest cutoffs:

| Elapsed time | Latest action |
|---:|---|
| 0–0.75s | validate and canonicalize URLs, run static SSRF checks, and perform bounded batched checkpoint lookup and lease bootstrap; cache delay fails open at this cutoff |
| 34s | stop admitting new provider attempts |
| 35s | interrupt retrieval; map permits must already be acquired |
| 51s | start optional reduction only if it can finish |
| 55s | interrupt map/reduce work and freeze results |
| 58s | finish checkpointing, validation, rendering, and ledger recording |
| 60s | transport ceiling |

Provider stages are individually capped within the remaining retrieval budget:
DNS 1.5s, Jina web 8s, Jina document 30s, Scrape.do basic 5s,
Scrape.do JavaScript 7s, Scrape.do JavaScript plus US geo 7s, Reddit 15s, and
Kernel 8s plus cleanup reserve. An admitted map lifecycle gets at most 20s and
must finish by 55s; optional reduction gets at most 4s.

These are ceilings, not expected latency. Work returns earlier when complete.
Optional reduction may be skipped; validated per-source findings remain usable
and the response discloses the limitation.

Provider admission uses fair process-global gates, so concurrent tool calls do
not multiply provider limits. Map extraction admits one pack per source before
supplemental packs, with up to 12 map lifecycles under the total LLM limit of
16. These scheduling rules explain why a queued source may be pending even when
another source in the same call completed.

## Checkpoint store versus research ledger

Do not conflate the two state systems.

| State | Purpose | Persistence | Contents |
|---|---|---|---|
| Evidence resume checkpoint | Continue unfinished retrieval/extraction without repeating accepted source retrieval | Redis-backed when available; encrypted, compressed, absolute one-hour TTL | Retrieval stage/outcomes, attempt metadata, warnings, fetch time, and bounded accepted cleaned content or a sparse block projection |
| Research session ledger | Let `review-research` assess coverage, gaps, rounds, and stopping | Bounded `in-process-only`; lost on restart/replica movement | Privacy-projected plan/search/extraction observations, never page bodies |

Resume checkpoints do **not** store evidence requirements, prompts, model
outputs, extracted findings, citations, credentials, or ledger events.
Extraction outputs are recomputed against cached accepted content.

When accepted content is too large for the checkpoint envelope, the server may
store a strictly decoded, structure-aware sparse block projection instead. It
is bound to the originating ordered requirements, preserves original source
coordinates and inherited structural context, and reports omitted ranges. The
projection is resumable source material, not previously extracted evidence.

Scope is strongest with a verified subject plus conversation ID, then a
transport-bound client subject plus conversation, subject plus transport
session, and transport session alone. With no stable scope, resume is disabled
and disclosed. Client-reported identity scopes cache reuse only; it is not
authorization.

Keeping the exact call in the same conversation/session gives the server the
best chance of resolving the same encrypted checkpoint and the same research
trace. Never move a continuation into a parallel agent and assume state follows.

## Retry and review discipline

- A continuation after accepted retrieval re-runs extraction from cached source
  content and makes no source-provider call when the checkpoint is available.
- A provider cooldown can include `retry_after_seconds`; honor it when the
  caller's budget permits.
- Another request may hold the source lease. Follow the returned continuation
  rather than issuing concurrent duplicate retrieval.
- A disconnected caller aborts work and does not receive an ordinary partial
  response. Start a fresh call only from state actually available to the host.
- `review-research` is not a substitute for a required extraction continuation.
  Pending required work must keep the trace from being treated as ready.
- Review history can disappear even while a Redis retrieval checkpoint remains
  reusable. Continue extraction from the exact returned call, then manage
  coverage manually if review reports unavailable history.

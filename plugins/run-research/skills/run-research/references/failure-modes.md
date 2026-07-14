# Failure modes

Things go wrong. Some failures are tool failures; some are
research-discipline failures wearing a tool-failure mask. This file is the
recovery playbook.

The pattern: every failure has a *diagnosis* (what went wrong) and a
*recovery* (what to do next). Skipping diagnosis and going straight to
retry is the most expensive anti-pattern in the toolkit.

---

## "Result too large" persistence

**Symptom:** Tool result exceeds maximum tokens. Output is saved to a
file under `.claude/projects/.../tool-results/`. The runtime returns
instructions for reading or subagent-extracting it.

**Diagnosis:** Normal behavior, not error. Output volume exceeded ~50KB,
which is structural for any of:

- `web-search` with 25+ keywords across multiple parallel calls
- `scrape-link` on 2+ non-Reddit pages with heavy chrome
- Any large parallel fan-out

**Recovery:**

1. Read the file persistence message — it includes a pre-formatted
   subagent prompt.
2. Spawn a subagent (Explore-class for read-only analysis) with the
   suggested prompt.
3. Have the subagent return only the curated subset (top URLs, key
   quotes, structured summary) — never the full file content.

**Anti-patterns:**

- Reading the persisted file directly into context with `Read`. Defeats
  the purpose; you re-overflow.
- Re-running the same call hoping for smaller output. The volume is
  structural.
- Lowering the keyword count without a strategy. If you have 25 distinct
  probes, run 25 — but plan for the persistence step.

**Prevention:**

- For `web-search`: if expecting >25 keywords, plan a subagent-extract
  step from the start.
- `web-search` already returns a token-optimized, de-duplicated URL list
  rather than raw snippets — if it still overflows, split the keyword
  batch across two calls instead of shrinking it blindly.

---

## scrape-link timeout

**Symptom:** `Operation timed out` after 50–60 seconds.

**Diagnosis:** Too many URLs, too many facets, or both. Observed ceiling:
5 URLs at ≤7 facets succeeds in roughly 50 seconds; 9 URLs times out
repeatedly.

**Recovery:**

1. Split the call into batches of 4 URLs each.
2. If still timing out, reduce the `extract` to ≤5 facets.
3. If still timing out, split further into single-URL calls and
   subagent-extract the batch results.

**Anti-patterns:**

- Retrying the same 9-URL call. It will time out again.
- Adding more facets to "save a call." Quality drops sharply past 7
  facets.
- Falling back to a single URL per call as the default. Wasteful; 4–5
  URLs per call is the sweet spot.

**Prevention:**

- Cap `scrape-link` at 5 URLs per call as a hard rule.
- For 10 URLs, dispatch two parallel 5-URL calls.

---

## Provider cascade failure

**Symptom:** A specific URL returns errors across all providers. Example:
"Jina Reader: blocked. Scrape.do proxy: timed out. Kernel: blocked."

**Diagnosis:** WAF or interstitial blocking on that domain. Not a bug.
Common on:

- `docs.anthropic.com` (rate-limit / WAF observed)
- Some `chatgpt.com` paths
- Many enterprise-gated docs portals
- Pages behind aggressive Cloudflare challenges

**Recovery:**

1. Find an alternate URL for the same content:
   - Vendor blog post that covered the same announcement.
   - GitHub mirror of the docs (`raw.githubusercontent.com/...`).
   - Web archive snapshot (`web.archive.org/web/*/<url>`).
   - Postmortem replacing the changelog.
   - Reddit discussion thread quoting the canonical content.
2. Scrape the alternate URL.
3. Note the provenance gap in synthesis (cite the alternate; mark
   inference where the canonical source is missing).

**Anti-patterns:**

- Retry loop on the same URL. The block is persistent.
- Pretending the canonical URL was scraped. Lying about provenance breaks
  downstream trust.
- Giving up on the topic. Alternate sources almost always exist for
  important content.

**Prevention:** Once a domain blocks, route around it for the rest of
the session. Note it for next session.

---

## Search returns empty for all keywords

**Symptom:** `web-search` returns 0 results across every keyword.

**Diagnosis:** Two possibilities:

1. Keywords too narrow — every probe used `site:` plus an exact phrase
   that no page contains.
2. Topic genuinely not on the open web — internal product, niche library,
   very recent release.

**Recovery:**

1. Drop the `site:` operator on 30% of keywords.
2. Replace exact phrases with quoted shorter substrings.
3. Try a batch of `site:reddit.com/r/.../comments` keyword probes — the
   topic might exist in community discussion even if not in vendor docs.
4. Broaden one axis: instead of "X feature in Y v3.2", try "X feature in
   Y" or "X feature".
5. If still empty, the topic may genuinely not have web evidence yet.
   Fall back to source code, vendor announcements, or surface the gap to
   the user.

**Anti-patterns:**

- Adding more `site:` operators "to find the right source." Tightening,
  not loosening, makes the problem worse.
- Treating empty results as confirmation of a hypothesis. Empty is not
  the same as non-existent.

---

## get-research-consultancy returns generic brief

**Symptom:** The brief lists 25 keyword seeds that are all variants of
the topic noun phrase. `gaps_to_watch` is one or two vague items.
`primary_branch` is `web` by default. No tailored iteration hints.

**Diagnosis:** The goal was under-specified. Specifically, missing one or
more of:

- User context
- Known knowns to skip
- Skip list
- Freshness window

**Recovery:**

1. Rewrite the goal with the six components from `prompting.md`:
   - Decision context
   - User profile
   - "Done" definition
   - Known knowns
   - Wanted unknowns
   - Skip list + freshness + quote discipline
2. Re-call `get-research-consultancy` with the new goal.
3. The new brief will have specific seeds across source classes, sharper
   `gaps_to_watch`, and likely a different `primary_branch`.

**Anti-patterns:**

- Proceeding with the generic brief and trying to compensate with manual
  keyword rewrites. The brief is the contract for the whole session;
  fixing it upstream is cheaper than fixing every downstream call.

---

## Reddit thread returns 0 comments

**Symptom:** `scrape-link` on a Reddit permalink returns the post
but `## Top comments` is empty or missing.

**Diagnosis:** Three possibilities:

1. Thread is locked, deleted, or mod-removed (common on r/news adjacent
   subs).
2. Permalink has query string parameters confusing the API router.
3. Thread is genuinely zero-comment (rare; usually means a fresh post
   with no engagement).

**Recovery:**

1. Strip query string parameters from the permalink (everything after
   `?`).
2. Search for re-posts: `site:reddit.com "<post title>"` — popular
   discussions often get reposted.
3. Search for quote-tweets and mirrors: the thread title with the
   subreddit name removed.
4. If the discussion is dead and no mirrors exist, drop this source and
   find others.

**Anti-patterns:**

- Citing a 0-comment thread as community sentiment. It is not.

---

## Conflicting verbatim quotes across sources

**Symptom:** Source A says "version 3 supports X." Source B says
"version 3 does not support X." Both have verbatim quotes with dates.

**Diagnosis:** This is data, not error. Sources disagree because:

- Different sub-versions (3.0.0 vs 3.0.1).
- Different platforms or build configurations.
- The feature was added or removed between source A and source B's
  dates.
- One source is wrong — but only one.

**Recovery:**

1. Surface the contradiction in synthesis. Cite both quotes with
   attribution and date.
2. Tier by source credibility — vendor docs > maintainer comments >
   active forums > blogs > marketing.
3. Look for a definitive resolver — the official changelog covering the
   relevant version range, or a maintainer's reply on the issue tracker.
4. If the contradiction is unresolvable from available evidence, mark it
   as such in synthesis. The user can decide.

**Anti-patterns:**

- Picking one source silently. Hidden contradictions break downstream
  trust.
- "Resolving" by averaging. Contradictions are not noise; they are
  information.

---

## Synthesis cites a URL but not a verbatim quote

**Symptom:** The synthesis says "According to <vendor>, X is supported
[URL]." No quoted text.

**Diagnosis:** Two possibilities:

1. The agent cited from a search snippet (a snippet is not evidence).
2. The agent cited from a page that was scraped but did not extract the
   relevant verbatim text — the agent paraphrased.

**Recovery:**

1. Verify the page was actually scraped (not just listed in search
   results).
2. If not scraped: scrape it now and find the verbatim text.
3. If scraped but paraphrased: re-scrape with `scrape-link` and a
   verbatim-discipline `extract`.
4. Replace the paraphrase with the quoted text.

**Anti-patterns:**

- Treating search snippets as quotable. Snippets are designed to be
  misleading — Google composes them from page text fragments without
  context.
- Paraphrasing a quote because the original is "too technical." If the
  original is what the source said, that is what should be cited.

---

## Anti-bot / Cloudflare / SPA rendering failures

**Symptom:** `scrape-link` returns minimal content or boilerplate
("Just a moment...", "Please enable JavaScript", an empty body).

**Diagnosis:**

- Cloudflare challenge page (the JS challenge could not be solved).
- Heavy client-side rendering with no SSR (SPA shell only).
- Paywall.

**Recovery:**

1. Try a cached or CDN version (Google cache, archive.org).
2. Find an alternate URL with the same content.
3. If the page is critical and no alternative exists, `WebFetch` may
   succeed on simple SPAs because it uses a different rendering path.
4. As a last resort, ask the user for the page content directly.

---

## When to stop the loop

The most underdiagnosed failure mode: not knowing when to stop. The
agent keeps searching out of habit.

**Stop when:**

- Every `gaps_to_watch` item from `get-research-consultancy` is closed.
- The last search round surfaced no new terms (no harvest from
  `## Follow-up signals`).
- The agreed time or effort budget has been reached.

**Do not stop when:**

- Tired but gaps remain. Open gaps mean unfinished work.
- One strong source seemed to cover everything. Triangulation requires
  ≥3 independent sources for any non-trivial claim.

**Surface remaining gaps explicitly** if stopping with gaps still open.
Do not paper over them.

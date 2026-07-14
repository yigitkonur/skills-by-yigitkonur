# Synthesizing research findings

Synthesis transforms scattered data into decisions. The difference
between a bibliography and a recommendation is synthesis — connecting
dots, resolving contradictions, and naming the variable that changes the
answer.

This file is the single-agent synthesis discipline. For multi-agent
orchestrator synthesis (where multiple researcher agents produce
parallel documents and the orchestrator personally reads all of them),
see `orchestrator.md`.

---

## Source credibility

Not all sources carry equal weight. Use this hierarchy when sources
conflict.

| Source | Trust level | Best for |
|---|---|---|
| Official docs (current version) | Highest | How things should work, exact API, config syntax |
| Official changelog / release notes | Very high | What changed, breaking changes, version-specific facts |
| Official postmortems / incident reports | Very high | What broke, why, what changed in response |
| GitHub issues/PRs (maintainer responses) | High | Known bugs, intended behavior, workarounds |
| Scraped benchmarks with disclosed methodology | High | Performance claims (check workload conditions match yours) |
| `get-research-consultancy` brief (`gaps_to_watch`, `iteration_hints`) | Planning input only | Session shaping. Never cite as evidence; it is generated before any page is scraped. |
| Highly-upvoted Reddit (100+ votes, specific details) | Moderate-high | How things actually work in production |
| Stack Overflow accepted + highly voted | Moderate-high | Common solutions (check date) |
| Recent blog by named practitioner with specifics | Moderate | Single data point, useful if detailed |
| Low-engagement Reddit | Low-moderate | Unvalidated individual opinion |
| Vendor marketing or comparison pages | Low | Extract facts only, ignore assessments |

### Recency matters more for some topics

| Topic area | Advice half-life | Verify if older than |
|---|---|---|
| JS frameworks, CSS, Node ecosystem | 6–12 months | 6 months |
| Cloud service pricing | 3–6 months | 3 months |
| AI/ML tooling and pricing | 3–6 months | 3 months |
| Security practices | 1–2 years | 1 year |
| Database features | 2–3 years | 2 years |
| Algorithms, data structures | 10+ years | rarely |

---

## Citation discipline

The hard rule: **only scraped page content is evidence.** Search
results (URLs, titles, and CONSENSUS scores from `web-search`) and the
`get-research-consultancy` brief are leads, not citations. `web-search`
never synthesizes or classifies — it only ranks URLs — so there is no
synthesis block to treat even as a planning aid; the brief's
`gaps_to_watch` and `iteration_hints` are the only pre-scrape planning
input, and they point at questions to close, not facts to cite.

### Source ledger fields

For non-trivial answers, maintain compact source notes with:

- URL or source identifier
- source type
- author/date when available
- access date or research date for time-sensitive claims
- claim supported
- confidence or caveat when source quality is weak

### What a citation looks like

For each non-trivial claim, capture:

- The verbatim quote.
- The URL.
- The scrape date.
- Source-specific attribution where it exists: Reddit username + score
  + date; GitHub issue number + maintainer handle; blog author + date;
  CVE-ID + CVSS score.

Compliant citations:

> "Codex CLI is OpenAI's coding agent that you can run locally from
> your terminal." — developers.openai.com/codex/cli (scraped 2026-05-08).

> u/sreekanth850 (+16, 2026-04, r/ChatGPTCoding): "Claude has been
> terrible recently. Using both, codex with 5.4 is far better."

> Anthropic April 23 postmortem: "three separate issues in the Claude
> Code harness caused complex but material problems which directly
> affected users." — simonwillison.net/2026/Apr/24/recent-claude-code-quality-reports/
> (scraped 2026-05-08).

Non-compliant:

- "According to Anthropic, ..." (no quote, no URL).
- "Reddit consensus is ..." (no attribution, no specific source).
- "The docs say X." (no quote, no URL).
- A URL alone with no quote — implies the page was read; verify or
  re-scrape.

### Inference vs evidence

Claims fall in three categories:

- **Direct evidence.** A verbatim scraped quote supports the claim.
- **Aggregate evidence.** Multiple sources agree; cite ≥3 with quotes.
- **Inference.** The claim is reasonable but no source states it
  directly. Mark with explicit qualifier ("inferred from <X> and <Y>",
  "no source confirms but suggested by <Z>").

Never blend. Inference paragraphs should look visibly different from
evidence paragraphs. The reader's trust is calibrated by how cleanly
inference is marked.

### Snippets, banned

`web-search` returns a ranked, de-duplicated URL list (titles, links,
CONSENSUS scores) — not page bodies, and no Google-composed snippet
text to quote from either way. Never cite from a URL you have not
scraped. If a claim looks interesting from the title or CONSENSUS
ranking alone, scrape the page with `scrape-link` and find the verbatim
text. If the page does not contain it (sometimes it does not), the
claim is unsupported.

---

## Resolving contradictions

When sources disagree, do not just pick one. Understand why they
disagree.

**Different versions.** Most common cause. Source A describes v3
behavior; source B describes v4. Check which version applies. Recent
version's docs win for "how it works now."

**Different scale.** "Redis is fine" (someone running 100 req/s) vs
"Redis fell over" (someone running 100K req/s). Both right in their
context. Match the user's scale.

**Different context.** "Use JWT" (stateless API) vs "Use sessions"
(monolith with SSR). Architecture determines correctness. Name the
context variable.

**Official docs vs community experience.** Docs describe intended
behavior. Community reveals actual behavior — including undocumented
limits, silent failure modes, and configuration gotchas the docs do not
mention. Trust community for "does it work in practice?" Trust docs for
"how is it supposed to work?"

**Search ranking vs scraped facts.** Always trust scraped official docs
over a `web-search` CONSENSUS ranking for specific facts (version
numbers, pricing, API signatures). CONSENSUS ranks URL relevance; it
carries no page-body content and no analysis.

**Nobody agrees.** Usually means the answer is genuinely
context-dependent. Do not force a single recommendation. Present the
options, name the variables that determine which is best, apply them to
the user's situation.

### Using `## Contradictions` from scrape-link

`scrape-link` sometimes surfaces a `## Contradictions` section when
commenters or sources disagree within a single page or across the
batch. This is a free signal — the extractor noticed disagreement that
might otherwise have stayed buried in dense prose.

Read every `## Contradictions` section. For sentiment work in
particular, it is gold: the disagreement IS the answer. Example from
the Claude Code vs Codex research that authored this skill: a
contradiction surfaced over whether Codex is "hands-off" (one
commenter, +20 votes) or "asks for permission constantly" (different
commenter, +20 votes). Both quotes verbatim, both verifiable. The
contradiction itself revealed a Windows-only bug in the
`--dangerously-bypass-approvals-and-sandbox` flag — neither commenter
alone described the bug, but the disagreement plus a third source's
"works fine on WSL2" closed the loop.

---

## Building consensus maps

For complex topics with many sources, map the landscape:

- **Strong consensus (80%+ agree).** Present as the recommendation.
  Note minority objections if they are substantive.
- **Moderate consensus (50–80%).** Present as "the common approach,
  with caveats." List dissenting perspectives and conditions.
- **No consensus (<50%).** Present as "multiple valid approaches." List
  trade-offs. Recommend based on user-specific constraints, not vote
  count.
- **Evolving consensus.** Old sources say X, new sources say Y. Present
  Y as current direction. Explain what changed (new version, new tool,
  changed best practice).

---

## Output formats

Match the format to the request type. The shapes below are templates;
adapt for the specific session.

### For decisions

```
RECOMMENDATION: [Clear choice]
CONFIDENCE: [High/Medium/Low] based on [N sources, agreement level]
WHY: [2-3 sentences connecting evidence to recommendation]
TRADE-OFFS:
  - Choosing this: [specific benefit, sourced] but [specific drawback, sourced]
  - Alternative: [what you'd gain] at the cost of [what you'd lose]
CONDITIONS: This assumes [your constraints]. If [variable] changes,
            reconsider [alternative].
```

### For bug fixes

```
LIKELY CAUSE: [Diagnosis with evidence chain]
FIX: [Specific steps, before → after code]
VERIFIED BY: [Which sources confirm]
CAVEATS: [When this fix doesn't apply]
FALLBACK: [What to try if this fails]
```

### For comparisons

```
| Criterion | Option A | Option B | Source |
|---|---|---|---|
| [Key factor] | [Data with quote] | [Data with quote] | [URL + scrape date] |
...

BEST FOR [context A]: Option A because [reason]
BEST FOR [context B]: Option B because [reason]
AVOID: [Option] when [condition] because [specific evidence]
```

### For security advisories

```
| CVE | Severity | Affected | Fixed in | Mitigation | Exploit observed |
|---|---|---|---|---|---|

PRIORITY: [Highest unpatched CVE first]
REMEDIATION: [Concrete steps with deadlines]
RESIDUAL RISK: [What is still exposed and why]
```

### For uncertainty

When data is insufficient, say so:

```
WHAT I FOUND: [Summary of limited findings]
GAPS: [What couldn't be found or verified]
CONFIDENCE: Low — [N sources, disagreement/sparse coverage]
PRELIMINARY DIRECTION: [Best guess based on available data]
TO INCREASE CONFIDENCE: [Specific next steps]
```

### For "it depends"

When the answer is genuinely context-dependent:

```
The answer depends on [2-3 specific factors]:

IF [your scale] < 10K req/s AND [team size] < 5:
  → Use [simpler option] because [reason, evidence]

IF [your scale] > 10K req/s OR [need feature X]:
  → Use [more complex option] because [reason, evidence]

YOUR SITUATION: Based on [known constraints], [recommendation] applies.
```

---

## The fresh-context self-review gate

Before delivering synthesis, run a mental self-review with no prior
session memory.

Open the synthesis as if reading it for the first time. For each
non-trivial claim, ask: "where is the evidence? Can I find a quote, URL,
scrape date, attribution?"

For each numeric / versioned / priced claim, ask: "is this verbatim from
a scrape, or paraphrased?"

For each contradiction, ask: "is the disagreement surfaced clearly, or
silently picked?"

For each inference, ask: "is it visibly marked as inference?"

Any "no" is a fix-before-delivery item. The most common failures:

- A claim sourced from a search snippet rather than a scraped page.
- A version number from memory that was not in any scraped source.
- A contradiction smoothed over in prose ("most sources agree...").
- An inference written in the same voice as direct evidence.

Self-review takes 5–10 minutes. It catches more bugs than any other
discipline in this skill.

---

## Verification checklist

Before finalizing any recommendation:

- [ ] Key claims confirmed by 2+ independent sources.
- [ ] No unresolved contradictions (resolved, surfaced, or explicitly
      flagged).
- [ ] Version-specific claims checked against official docs/changelog.
- [ ] Sources actually independent (not citing each other).
- [ ] Recency appropriate for the technology area.
- [ ] `web-search` CONSENSUS rankings never treated as a substitute for
      a scraped-page claim about a specific fact.
- [ ] `## Not found` sections reviewed; gaps closed or explicitly
      flagged.
- [ ] Every numeric / versioned / priced claim has a verbatim quote.

**Verification effort matches stakes.** Quick fact check → 1 source is
fine. Library adoption → 2–3 sources. Architecture decision → full
triangulation (official docs + practitioners + independent analysis).
Security claim → never trust a single source.

# Evidence And Synthesis

How to turn web research, Reddit/practitioner signal, and local evidence packs into an audit-ready industry corpus.

## Source Hierarchy

| Source type | Best for | Caveat |
|---|---|---|
| Official docs, API references, pricing pages | Product facts, limits, billing units, setup, supported features. | Marketing/docs can omit failures and gated terms. |
| Changelogs, release notes, status pages | Freshness, incidents, release cadence, operational history. | Status pages may under-report real user impact. |
| GitHub repos, issues, discussions | Open-source health, bugs, maintainer response, community friction. | Issues overrepresent problems. |
| Legal, security, privacy, trust pages | Compliance, retention, acceptable use, license, data handling. | Sales/security claims may require contract review. |
| Reddit, HN, forums, reviews | Practitioner experience, migrations, pricing pain, reliability complaints. | Bias, astroturfing, sparse samples, and adjacent confusion are common. |
| Analyst reports, market data, filings | Market size, funding, macro trends, public-company facts. | Often gated, lagging, or too broad for product decisions. |

Use the strongest source for the claim type. For pricing, official pages beat blog summaries. For lived experience, direct practitioner threads beat vendor case studies.

## Claims Ledger

Every important file should feed a claims ledger:

| Claim | Type | Evidence | Confidence | Caveat | Follow-up |
|---|---|---|---|---|---|
| Product supports X API. | Confirmed fact | Official docs URL, captured date. | High | Version may change. | Recheck before implementation. |
| Vendor is best at Y. | Vendor claim | Homepage or blog URL. | Low | No independent benchmark. | Run buyer test. |
| Users complain about pricing. | Practitioner report | Reddit/HN/review URL with date. | Medium | Sample may be biased. | Search broader category. |

Claim types:

- confirmed fact
- vendor/project claim
- practitioner report
- inference
- contradicted
- unverified

## Pricing And Unit Economics

For SaaS, platforms, APIs, data providers, and usage-based products:

1. Preserve native units first.
2. Identify included quotas, overages, hard caps, free tiers, trials, and enterprise gating.
3. Normalize only when public variables are sufficient.
4. Model scenarios, not just plan prices.
5. Include hidden cost variables: retries, storage, logs, data transfer, add-ons, support, proxy/CAPTCHA, seats, model/API costs, usage spikes, and compliance needs.
6. If a variable is missing, write `insufficient public data` and name the variable.

## Open-Source Health

For open-source projects:

- stars and downloads are weak signals unless paired with release cadence and issue response
- inspect license, governance, maintainer count, open issues, stale PRs, security advisories, docs freshness, examples, test suite, CI, and dependency health
- distinguish project popularity from production readiness
- capture forks, commercial backing, and cloud-hosted product links separately

## Reddit And Practitioner Evidence

Required fields for direct audience evidence:

- source URL and venue
- author or username when public
- date
- product/entity mentioned
- direct or adjacent relevance
- sentiment and topic label
- short direct quote when useful
- bias note, such as founder reply, promotional account, angry support case, or competitor comparison

Rules:

- Do not say "Reddit consensus" without a source ledger.
- If direct evidence is sparse, say so.
- Use adjacent evidence only when labeled adjacent.
- Preserve enough direct comments to support synthesis, but avoid long non-Reddit quotations.

## Cross-Category Synthesis

A good cross-category file does more than merge notes. It should answer:

- Which entities are directly comparable, adjacent, or not comparable?
- Which entity wins for each scenario and why?
- Which ranking is source-backed, and which is provisional?
- What pricing, benchmark, compliance, or reliability unknown would change the answer?
- What should the buyer test next?

Each cross-category `00-overall-comparison.md` should include:

1. Scope and capture date.
2. Short recommendation.
3. Matrix or ranking.
4. Evidence confidence.
5. Important contradictions.
6. Scenario-specific guidance.
7. Tests or data needed to change the recommendation.
8. Sources.

## Root README

The root README is an entry point, not a full report. It should include:

- scope and capture date
- start-here table
- entity index
- cross-category rollup index
- evidence-layer explanation
- caveats and unresolved gaps

Do not put volatile pricing tables in the README unless the user explicitly wants that. Link to the pricing rollup instead.

## Final Verification

Run these checks before declaring completion:

- file count under cap
- no hidden junk files
- no broken local markdown links
- all core entities have a profile and evidence pack
- all cross-category rollups exist
- all source maps and claims ledgers exist or gaps are explicit
- no placeholder text such as TODO, TBD, or "fill later"
- no stale links to renamed folders
- root README and main profiles point to current folder names

## Completion Statement

The final handoff should state:

- corpus path
- total files and entity count
- top entry points
- critical findings
- unresolved gaps
- verification run and any checks not run

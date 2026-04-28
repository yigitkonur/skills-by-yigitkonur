# Template Authoring

How to write the maximalist `_PRODUCT_TEMPLATE.md` and per-criterion `_COMPARISON_TEMPLATE_<criterion>.md` files that define the comprehensiveness boundary for the corpus.

This is the **keystone reference** of the run-industry-research skill. Read this in **Phase 2** — before any entity-pack file is written.

## Why templates exist

Without templates, depth varies per entity: the orchestrator researches `EntityA` thoroughly because they happen to know it well, but `EntityB` ends up shallow because the searches returned less. The corpus then can't compare entities — they're not measured against the same axes.

Templates fix this by setting the **minimum coverage every entity pack and every cross-criterion comparison must address.** A template section with no evidence becomes an explicit "insufficient evidence" entry naming the gap — which is itself a finding the buyer needs.

The templates are deliberately **maximalist and overcrowded.** A maximalist template forces depth. A thin template (≤15 sections) produces a shallow corpus.

## When to author templates

| Phase | What's done | What's not |
|---|---|---|
| Phase 0 — Charter | Scope + scale chosen | Templates not yet drafted |
| Phase 1 — Discovery | Entity list AND deep category understanding | Templates not yet drafted |
| **Phase 2 — Template authoring** | **Templates written here** | Entity files NOT yet created |
| Phase 3 — Architecture | Tree plan derived from templates | Entity files NOT yet created |
| Phase 4 — Evidence packs | Entity files filled per template | — |

If you find yourself writing entity-pack content before Phase 2 is locked, stop. Template-driven discipline cannot be retrofitted.

## The deep category pre-pass

Before you can write a maximalist template, you must understand the category deeply. This pre-pass happens at the end of Phase 1 (Discovery) — it's the second output of discovery, alongside the entity list.

The pre-pass answers:

| Question | Why it matters for the template |
|---|---|
| What axes do real buyers compare on? | Determines the cross-criterion list (becomes one comparison template each) |
| What pricing primitives are native to this category? | Pricing template needs the right unit (browser-hour, GB-second, per-API-call, per-seat, per-credit, etc.) |
| What practitioner channels matter here? | Audience template needs the right venues (Reddit subreddit names, HN, specific forums, Discord servers) |
| What regulatory or compliance angles apply? | Security/compliance template needs the right regimes (HIPAA, SOC2, GDPR, PCI, FERPA, etc.) |
| What benchmark / performance traditions exist? | Benchmarks template needs the right reproducibility expectations (public leaderboards? vendor-only claims? buyer-run pilots?) |
| What does the lock-in / exit-path landscape look like? | Buyer-fit template needs the right migration scenarios |
| What recent shifts has the category seen? | Overview template needs the right framing |

A 1-2 paragraph "category-understanding note" captures these answers and is shown alongside the discovered-entities list at the end of Phase 1. Without this note, Phase 2 templates default to generic and miss vertical-specific depth.

## The maximalist `_PRODUCT_TEMPLATE.md`

### Structure

```markdown
# [Topic-Slug] Product Template

A maximalist menu of the evidence every product/entity in the [topic] category
should be evaluated against. Subagents researching one entity choose which
files to create within each section based on the evidence they find — but
every section must be addressed in every `core` pack (with content or with
a one-paragraph "insufficient evidence" note that names the data gap).

## Template metadata

| Field | Value |
|---|---|
| Category | [topic] |
| Archetype | [SaaS / OSS / dev-infra / data-provider / regulated / consumer] |
| Buyer | [who decides; what they care about most] |
| Author date | YYYY-MM-DD |
| Source-policy | [link to _meta/methodology-and-source-policy.md] |

## Section menu

### 00-overview/

What every overview pack must address (subagent picks 1-N filenames):

- Executive brief — positioning in 200-400 words; differentiation claim; primary use case
- Product taxonomy — what layer/category does this entity live in? what does it NOT compete with?
- Positioning vs. closest comparator — name the obvious competitor; one-paragraph delta
- Evidence grade and confidence — how well-sourced is this pack? what's the weakest link?
- [Add vertical-specific overview questions: e.g., for OSS, "project age and bus factor"; for data providers, "data provenance"]

### 01-[pricing-or-economics-slug]/

What every pricing pack must address:

- Public plan matrix — every published plan with native units, included quotas, hard caps
- Unit economics — what does one [native unit] actually cost? what is the unit?
- Scenario cost models — at least 3 scenarios spanning small/medium/large workloads
- Overages and add-ons — every cost beyond the base plan (proxy GB, retries, storage, support, seats, etc.)
- Hidden costs and gated pricing — enterprise-gated terms; volume discounts; trial-to-paid traps
- Pricing risk register — pricing changes in last 18 months; rate-of-change concern
- [Add vertical-specific pricing questions: e.g., for usage-based APIs, "per-call vs. per-batch economics"; for OSS, "hosted-vs-self-host TCO comparison"]

### 02-[platform-or-product-slug]/

What every platform/product pack must address:

- Control surface — every API, SDK, CDP, UI, MCP server with version and stability label
- [Domain primitive] model — for cloud browsers: session lifecycle; for data APIs: query model; for OSS: extension/plugin model
- State / persistence — what survives across sessions / runs / deployments
- Auth and identity — how the buyer's user/credential boundary integrates
- Observability and artifacts — what's emitted: logs, traces, replays, screenshots, metrics
- Lock-in and exit path — what's portable; what's proprietary; one-paragraph migration story
- [Add vertical-specific platform questions]

### 03-[integrations-or-ecosystem-slug]/

What every integrations pack must address:

- Official SDKs and clients — every language with version, repo URL, last-update date
- MCP server / agent-framework integrations — every named integration with evidence
- LLM provider / model integrations (if applicable)
- Workflow tools and templates — every published example/template
- Example quality and runnability — verify at least 2 examples actually run
- Community projects — distinguish from official; assess maintenance health

### 04-[operations-or-reliability-slug]/

What every ops pack must address:

- Reliability claims and SLAs — every published SLA with the gating tier
- Status page evidence — last 90 days of incidents; incident-density rate
- Concurrency, scaling, regions — every published limit; every region; failover behavior
- Observability for buyers — what's exposed to the buyer (logs, traces, dashboards)
- Failure modes and recovery — top 5 published or practitioner-reported failures
- Status, incidents, and changelog evidence — link to all three; capture date

### 05-[security-or-compliance-or-stealth-slug]/

What every security/compliance pack must address. Section names ADAPT to the vertical:
- For SaaS: proxy/captcha/stealth + privacy/compliance + acceptable use + legal risk
- For OSS: license + governance + supply-chain security + maintainer security posture
- For data providers: data rights + redistribution + privacy + retention + legal jurisdiction
- For regulated: every required certification (HIPAA, SOC2, etc.) with audit date
- [Generic minimums: vendor security claims; independent verification; AUP; legal restrictions]

### 06-[audience-or-community-slug]/

What every audience pack must address:

- Direct evidence inventory — Reddit, HN, forums, review sites, GitHub issues with URLs and dates
- Practitioner sentiment — themes from direct evidence; pricing pain; reliability complaints; migration stories
- Promotional bias and signal quality — flag founder-replies, promotional accounts, astroturfing
- Adjacent evidence — when direct is sparse; explicitly labeled adjacent
- Direct comment dump (when warranted) — verbatim with attribution and bias label
- [Add vertical-specific audience questions: GitHub issue velocity for OSS; G2/Capterra for B2B SaaS; App Store reviews for consumer]

### 07-[benchmarks-or-performance-slug]/

What every benchmarks pack must address:

- Public benchmark claims — every vendor-published number with source and date
- Independent benchmark presence — third-party tests; reproducibility status
- Latency, throughput, cold-start, replay characteristics — measured or claimed
- Reproducibility risk — what would prevent a buyer from reproducing?
- Buyer-run test plan — concrete tests the buyer should run before committing

### 08-[buyer-fit-or-adoption-slug]/

What every buyer-fit pack must address:

- Scenario fit matrix — top 5-10 buyer scenarios, with fit rating and rationale
- Best defaults by workload — when to choose this entity
- Do-not-choose-if — concrete failure scenarios
- Migration and exit paths — into and out of this entity
- Competitor and alternative map — direct, indirect, adjacent, substitute
- Decision recommendation — opinionated, source-linked, scenario-conditional

### 09-[sources-or-verification-slug]/

What every source-verification pack must address:

- Source map — every URL cited in this entity's pack, with capture date and source-quality rating
- Claims ledger — every important claim classified (confirmed / vendor / practitioner / inference / contradicted / unverified)
- Open gaps and follow-up tests — concrete, buyer-actionable

## Insufficient-evidence handling

When a section's evidence is too sparse for its own file:

1. Fold it into the closest existing file in the same numbered subfolder as a one-paragraph note
2. Name the specific data gap (e.g., "No public information on enterprise pricing tiers")
3. Add the gap to `09-sources/03-open-gaps-and-follow-up-tests.md`

Do NOT:
- Create a stub file with a "TBD" placeholder
- Silently drop the section
- Pad with vendor-page text that doesn't actually answer the section's question

## Filename guidance for subagents

Subagents pick filenames within each section based on the shape of the evidence they find. The template lists *sections and questions*; agents land on `01-meaningful-title.md` based on what THEIR entity supports.

Examples (showing how two agents legitimately diverge on filenames in the same section):

- `airtop/05-security/01-proxy-stealth-captcha-and-compliance.md` (one bundled file because all three topics are sparse)
- `hyperbrowser/05-security/01-proxy-stealth-and-captcha-claims.md` + `02-fingerprinting-and-anti-bot-evidence.md` + `03-privacy-and-compliance.md` + `04-acceptable-use-and-legal-risk.md` (four files because evidence is rich)

Both are correct. The template prescribed the section ("security: proxy/stealth/captcha/compliance/AUP/legal"); each agent shaped the files to its evidence.
```

### Sizing

A strong `_PRODUCT_TEMPLATE.md` is **200-400 lines, intentionally overcrowded.** If your draft is shorter than 200 lines, you have under-specified the minimums. If shorter than 30 distinct sections (across all subfolders combined), you have not done the deep category pre-pass.

For reference, the cloud-browsers `_meta/product-folder-research-brief.md` (the equivalent template) is 162 lines and lists ~50 distinct file/section candidates across 10 subfolders — and that was a tight version. A more maximalist template for a richer category may run 300-500 lines.

## The per-criterion `_COMPARISON_TEMPLATE_<criterion>.md`

One template per cross-criterion. For `compact` corpora, a single master `_meta/_COMPARISON_TEMPLATE.md` covering all criteria is acceptable.

### Structure (single criterion)

```markdown
# [Topic-Slug] Comparison Template — [criterion-name]

The cross-criterion comparison template prescribes the axes, matrix columns,
ranking dimensions, and source expectations for the `_cross-<scope>/[criterion]/`
folder. The Phase 5 cross-comparison agent fills this in based on the
already-completed entity packs.

## Comparison metadata

| Field | Value |
|---|---|
| Criterion | [pricing / capabilities / integrations / security / audience / benchmarks / buyer-fit / sources] |
| Buyer question | [the specific decision this comparison helps answer] |
| Scenario baseline | [the concrete scenario used for like-for-like comparison] |
| Comparison date | YYYY-MM-DD |
| Verification status | verified / partial / mixed / stale |

## Files this folder must contain

Every cross-criterion folder produces:
- `00-overall-comparison.md` — the headline comparison + ranking + recommendations
- One or more granular files (listed below) — each addressing a sub-axis

## Required matrix axes

For [criterion], the matrix MUST include columns for:
- [axis 1] — [definition + source expectation]
- [axis 2] — [definition + source expectation]
- [axis 3] — [definition + source expectation]
- [...]

## Required ranking dimensions

The comparison must rank entities on:
- [dimension 1] — [scoring rubric]
- [dimension 2] — [scoring rubric]
- [...]

Each ranking carries a confidence label (high / medium / low) and a
"what would change this ranking" note.

## Required granular files

Beyond `00-overall-comparison.md`, the folder must contain:
- `01-[specific-question].md` — addresses [question]
- `02-[specific-question].md` — addresses [question]
- `[...]`

The agent MAY add more granular files when evidence supports them. The agent
MAY NOT skip any file in the required list.

## Source expectations

Every claim cites:
- The relevant entity-pack file(s) it summarizes
- The original source URL where the entity-pack file was sourced
- The capture date
- The source-quality rating

## "Tests that would change the recommendation" section

Every `00-overall-comparison.md` ends with a section listing the concrete
tests/data the buyer could run that would flip the recommendation.
```

### Sizing

Each `_COMPARISON_TEMPLATE_<criterion>.md` is typically 100-250 lines. The cloud-browsers `_meta/comparison-template.md` (which is a single master template covering all criteria) is 246 lines.

### When per-criterion vs. master

| Corpus scale | Recommendation |
|---|---|
| `compact` (1-10 entities) | Single master `_meta/_COMPARISON_TEMPLATE.md` |
| `standard` (10-40 entities) | Per-criterion (8-12 templates) |
| `deep` / `tiered` (40+ entities) | Per-criterion, mandatory |

The per-criterion approach lets each comparison template carry vertical-specific axes (pricing has different axes than security has different axes than audience), which a master template tends to underspecify.

## Templates set the comprehensiveness boundary

This is the central concept. Read carefully:

- The template lists every section every entity pack must address.
- Subagents fill the template; they cannot silently skip sections.
- Sections with no evidence become explicit "insufficient evidence" entries that name the data gap.
- The orchestrator audits template coverage in Phase 7 — if any section in any `core` pack is unaddressed, verification fails.

This is what produces depth uniformly across the corpus. One agent can't shortcut research because the template requires evidence (or an explicit gap-name). The corpus is comparable because every entity is measured on the same axes.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Template written after entity research | Defeats the purpose; depth already varies | Phase 2 first, always. Re-do if necessary. |
| Template is short and generic (≤15 sections) | Forces shallow corpus | Re-do Phase 1 deep category pre-pass; expand to 30+ sections |
| Template prescribes exact filenames | Removes evidence-driven naming flexibility | Template lists sections + questions; agents pick filenames |
| Template lists sections without "questions to answer" per section | Subagents under-specify what evidence belongs there | Every section has a 1-line "what evidence belongs here" |
| Comparison template has no required matrix axes | Cross files devolve into prose summaries | Required axes + required ranking dimensions + required granular files |
| Templates copied from another vertical without adapting | Misses vertical-specific axes | Use category-taxonomies.md archetype as skeleton; adapt to vertical |
| Template author skips the deep category pre-pass | Template is generic; corpus is shallow | Phase 1 produces TWO outputs: entity list AND category-understanding note |
| Subagents allowed to ignore template sections | "Insufficient evidence" handling not enforced | Mission brief explicitly requires every template section addressed |
| Master comparison template used at `deep` scale | Underspecifies per-criterion axes | Per-criterion templates for `deep` and larger |

## Worked-example artifacts

The cloud-browsers corpus already implements this pattern. Inspect the actual artifacts:

| Artifact | Path | Lines | Role |
|---|---|---|---|
| Master comparison template (single, multi-criterion) | `/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/_meta/comparison-template.md` | 246 | The Phase 2 cross-comparison template; covers metadata, scope, headline findings, platform matrix, pricing matrix, ops matrix, integrations matrix, audience matrix, benchmarks matrix, buyer-fit matrix |
| Per-product research brief (acts as `_PRODUCT_TEMPLATE.md`) | `/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/_meta/product-folder-research-brief.md` | 162 | The Phase 2 entity-pack template; lists ~50 distinct file candidates across 10 subfolders with required questions per file |
| Comparison-research brief | `/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/_meta/comparison-research-brief.md` | 156 | Phase 5 mission brief that references the comparison template |
| Profile-enhancement brief | `/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/_meta/profile-enhancement-brief.md` | 159 | Phase 6 mission brief that references the profile-page pattern |

Read the actual `comparison-template.md` and `product-folder-research-brief.md` before authoring your own templates. They are battle-tested examples of the maximalist style this skill mandates.

The cloud-browsers templates were tight (162 + 246 lines). For richer or more regulated categories — fintech, healthcare, security tooling — your templates will likely run 300-500 lines because the vertical demands more axes (compliance, audit, certifications, regional variations).

## Validation checklist

Before locking the templates and proceeding to Phase 3:

- [ ] `_PRODUCT_TEMPLATE.md` has a section for every numbered subfolder you plan to use
- [ ] Each section names "what evidence belongs here" in 1 line
- [ ] Total distinct sections across all subfolders ≥ 30
- [ ] Total template length 200-400 lines (or 400-500 for rich verticals)
- [ ] Insufficient-evidence handling is explicitly stated in the template
- [ ] Filename guidance is explicitly stated (subagents pick names)
- [ ] One `_COMPARISON_TEMPLATE_<criterion>.md` per cross-criterion (or one master for `compact`)
- [ ] Every comparison template lists required matrix axes + required ranking dimensions + required granular files
- [ ] Every comparison template has a "tests that would change the recommendation" section
- [ ] Templates were written AFTER the deep category pre-pass, not before discovery
- [ ] Templates were shown to the user as Phase 2 artifact before Phase 3 starts

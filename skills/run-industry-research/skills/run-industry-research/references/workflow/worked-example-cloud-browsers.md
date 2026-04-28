# Worked Example: AI-Native Cloud Browsers

An annotated walkthrough of a complete research corpus produced by this skill: the AI-native cloud browsers category (12 vendors, 293 files, ~145 directories).

Use this as a discipline mirror, **not a slug template.** Every category has different category names, different evidence emphasis, different audience signal density. Copy the *method*, not the *folders*.

Read this when you want to see the phases applied end-to-end on a real category.

## Where the corpus lives

```
/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/
```

This was produced for the cloud-browser category (vendors that run real Chrome/Chromium browsers in cloud datacenters for AI agents). The category has well-defined buyers (engineering teams building agent workflows), a competitive incumbent (Browserbase), a fast-rising challenger (Anchor Browser), and meaningful Reddit discussion.

## Phase 0 — Charter (what was clarified)

**Outcome:** Buy-side decision support for engineering teams choosing a cloud browser for AI agent workflows.

**Audience:** Senior engineers / engineering managers evaluating 2-4 finalists.

**Geography:** Global, English-language sources.

**Corpus scale chosen:** `standard` (10-40 entities target, expected file count 80-350). Final: 12 core entities, 293 files. Within band.

## Phase 1 — Discovery (how the entity list emerged)

**Sub-questions decomposed:**

1. Which AI-native cloud browser platforms exist as commercial SaaS in 2025?
2. Which incumbent traditional browser-automation services have repositioned for AI agents?
3. Which open-source projects compete in the same space (with optional hosted offerings)?
4. Which adjacent categories overlap (computer-use platforms, agent runtimes, scraping APIs)?
5. Which platforms are gated/waitlist-only and might be over-counted in marketing?

**Discovery searches that mattered:**

- `"cloud browser AI agent" 2025` → surfaced Airtop, Anchor, Hyperbrowser
- `Browserbase alternatives reddit` → surfaced Anchor as the top recommendation, plus migration stories
- `headless browser AI agent open source` → surfaced Steel.dev, Browser-Use (library, deferred to discovered-only)
- `Cloudflare browser rendering` → surfaced Cloudflare Browser Run (originally listed as adjacent, promoted to core)
- `agent browser waitlist 2025` → surfaced Meteor (formerly Browse.dev) — kept as core despite gated access because its WebVoyager benchmark claim mattered to comparisons

**Tier outcome:**

| Tier | Count | Examples |
|---|---|---|
| `core` | 12 | airtop, anchor-browser, browserbase, browsercloud, bright-data-agent-browser, cloudflare-browser-run, hyperbrowser, kernel, meteor, notte, scrapybara, steel-dev |
| `secondary` | ~8 | (folded into discovered list as the file budget held — every secondary that surfaced got cross-checked but did not get a full pack) |
| `discovered-only` | ~5 | Browser-Use (library not service), Selenium Grid (traditional, not AI-native), several waitlist-only that lacked sources |

**The `_meta/discovered-products.md` file** captured all 25+ candidates with status, tier, surface URL, and adjacency notes. It was read by every Phase 4 agent so they knew the boundary of the corpus.

## Phase 2 — Template authoring (taxonomy + maximalist templates)

**Archetype selected:** SaaS / vendor category from `references/architecture/category-taxonomies.md`.

**Why not OSS or dev-infra:** the entities are commercial vendors with public pricing, not open-source projects with maintainer dynamics. Dev-infra was close, but the buyer-decision shape (per-session pricing, Reddit migration stories, bot-detection concerns) is SaaS-shaped, not infrastructure-shaped.

**Resolved category list per entity** (the actual subfolder names that ended up on disk after the rename):

```
00-overview      — positioning, taxonomy, evidence grade
01-pricing       — public pricing, unit economics, scenario costs
02-platform      — control surface, session model, persistence, observability
03-integrations  — SDKs, MCPs, agent frameworks
04-operations    — reliability, status, limits, failure modes
05-security      — proxy, stealth, captcha, compliance, legal risk
06-audience      — Reddit/HN/practitioner sentiment + direct comments
07-benchmarks    — performance claims, test plans, reproducibility
08-buyer-fit     — scenario fit, alternatives, decision recommendation
09-sources       — source map, claims ledger, open gaps
```

**Adaptations from the canonical SaaS list:**

- `02-platform` (not `02-product-capabilities/`) because for cloud browsers the platform shape (session/state/auth) is the dominant axis, not feature breadth
- `05-security` (not `05-security-compliance-legal`) because stealth/proxy/captcha is the heavy substance and rolls up the legal-risk concern
- `06-audience` (not `06-audience-reviews-reddit`) because Reddit/HN dominates the audience signal — review-site presence is sparse for this category
- `07-benchmarks` instead of `07-benchmarks-performance-tests` — same content, shorter slug after rename pass

**Cross-product folder uses the same 10 slugs** so the schema is uniform — `_cross-product/01-pricing/`, `_cross-product/05-security/`, etc.

### The actual templates this corpus used

The Phase 2 templates the cloud-browsers corpus produced (battle-tested examples to inspect before authoring your own):

| Template artifact | Path | Lines | Role |
|---|---|---|---|
| Master comparison template | `_meta/comparison-template.md` | 246 | Multi-criterion comparison axes — covers metadata, scope, headline findings, platform matrix, pricing matrix, ops matrix, integrations matrix, audience matrix, benchmarks matrix, buyer-fit matrix |
| Per-product research brief (acts as `_PRODUCT_TEMPLATE.md`) | `_meta/product-folder-research-brief.md` | 162 | Lists ~50 distinct file/section candidates across 10 subfolders with required questions per file |
| Comparison-research brief | `_meta/comparison-research-brief.md` | 156 | Phase 5 mission brief that references the comparison template |
| Profile-enhancement brief | `_meta/profile-enhancement-brief.md` | 159 | Phase 6 mission brief that references the profile-page pattern |

The `product-folder-research-brief.md` opens with a sentence that captures the discipline:

> "Create only the folders/files that are justified by evidence. The menu below is **maximal** so agents can choose the right shape. Do not create empty placeholders. Each file must be independently useful and source-attributed."

That sentence is the template-authoring contract in 30 words. Read both `comparison-template.md` and `product-folder-research-brief.md` end-to-end before you write your own templates.

For a richer or more regulated category — fintech, healthcare, security tooling — your templates will likely run 300-500 lines (vs. cloud-browsers' 162 + 246 = 408 combined) because the vertical demands more axes (compliance, audit, certifications, regional variations).

## Phase 3 — Architecture (file-count expectation derived from templates)

**File-budget estimate (before file creation):**

```
root_and_meta_files       = 1 + 5      = 6   (README + 5 _meta/ files)
core_entities × avg       = 12 × 18    = 216 (12 entities × ~18 files each: README + 9 subfolders × ~1.7 files)
cross_count × avg         = 10 × 5     = 50  (10 criteria folders × 5 files each: README + 0-comparison + ~3 specific)
profile_pages             = 12         = 12
                          ─────────────────
total estimate                          = 284
```

Final actual: **293 files**. Estimate within 4% — file budget held.

**Tree shape (after Phase 3 plan, before any pack writing):**

```
01-ai-native-cloud-browsers/
├── README.md
├── _cross-product/
│   ├── 00-overview/
│   ├── 01-pricing/
│   ├── 02-platform/
│   ├── 03-integrations/
│   ├── 04-operations/
│   ├── 05-security/
│   ├── 06-audience/
│   ├── 07-benchmarks/
│   ├── 08-buyer-fit/
│   ├── 09-sources/
│   └── README.md
├── _meta/
│   ├── comparison-research-brief.md
│   ├── comparison-template.md
│   ├── discovered-products.md
│   ├── product-folder-research-brief.md
│   └── profile-enhancement-brief.md
├── airtop/                       ← evidence pack
│   ├── 00-overview/, 01-pricing/, ..., 09-sources/
│   └── README.md
├── airtop.md                     ← profile page (Phase 6)
├── anchor-browser/, anchor-browser.md
└── ...                           ← 10 more (entity, entity.md) pairs
```

## Phase 4 — Evidence packs (parallel waves, template-driven)

**Two waves of 6 entity-research agents** ran the per-entity deep dives. (For a 12-entity corpus we could have run a single wave of 12; we ran two waves of 6 so the orchestrator could integrate Wave 1 results before dispatching Wave 2. With the current 20-per-wave cap, a single wave would also have been valid.) Each agent owned one `[entity-slug]/` folder. Wave 1 covered the 6 most-cited entities (Airtop, Browserbase, Hyperbrowser, Anchor Browser, Steel.dev, Notte). Wave 2 covered the remaining 6 (Bright Data, BrowserCloud, Cloudflare Browser Run, Kernel, Meteor, Scrapybara).

**Mission brief shape** — each agent received `_meta/product-folder-research-brief.md` as the **comprehensiveness contract** (every section in its menu must be addressed in content or in an "insufficient evidence" entry), plus the discovered-entities scope boundary and the source-hierarchy rules. Average pack size: 17-23 files per entity. Average research time per agent: ~15 minutes.

**Filename divergence across agents (correct, not a bug):** the template prescribed the section ("05-security covers proxy, stealth, captcha, compliance, AUP, legal risk"), but each agent picked filenames based on the evidence found:
- `airtop/05-security/01-proxy-stealth-captcha-and-compliance.md` (one bundled file because evidence was sparse)
- `hyperbrowser/05-security/01-proxy-stealth-and-captcha-claims.md` + `02-fingerprinting-and-anti-bot-evidence.md` + `03-privacy-and-compliance.md` + `04-acceptable-use-and-legal-risk.md` (four files because evidence was rich)

Both are correct. The template prescribed the section; each agent shaped the files to its evidence. Two agents researching the same vertical legitimately land different filenames inside the same numbered subfolder.

**One pack tier-promoted mid-research:** Cloudflare Browser Run was originally tagged `secondary` (waitlist-only, sparse public docs) but Wave 2 surfaced enough engineering blog posts and Cloudflare Workers integration evidence to promote it. The pack got the full subfolder treatment.

**Notable per-entity adaptation:** Bright Data's pack has a heavier `05-security/` (proxy origin is the company's identity) and `06-audience/02-direct-comment-dump.md` is 247 lines because Reddit had unusually rich practitioner discussion of their proxy offerings.

## Phase 5 — Cross-entity synthesis (10 cross-criterion files)

**Each `_cross-product/<criterion>/` folder** received its own agent who:

1. Read every `core` entity's matching subfolder (12 reads)
2. Built a `00-overall-comparison.md` with ranking + confidence + scenario-specific guidance
3. Authored 3-6 granular comparison files per criterion folder (e.g., `_cross-product/01-pricing/02-native-billing-units-and-conversions.md`, `03-scenario-cost-models.md`, `04-hidden-costs-overages-and-gated-pricing.md`, `05-cost-risk-ranking.md`)

**Largest cross file:** `_cross-product/06-audience/00-overall-comparison.md` at 425 lines — practitioner sentiment was the highest-signal axis for this category.

**Most contested ranking:** `_cross-product/05-security/05-claim-evidence-gap-ranking.md` — vendor stealth claims diverged sharply from practitioner-reported bot-detection rates, requiring a separate file just for the gap.

## Phase 6 — Profile pages (12 root-level decision pages)

**Authored personally by orchestrator** (no delegation) after reading every `core` pack.

**Profile-page lengths:**

| Entity | Lines | Why this length |
|---|---|---|
| `airtop.md` | 479 | Substantial vendor with rich pricing model + agent integrations to summarize |
| `anchor-browser.md` | 631 | Largest because Anchor dominates Reddit migration stories; required heavy audience-evidence synthesis |
| `bright-data-agent-browser.md` | 608 | Different vertical positioning (proxy-network-first); security section elevated |
| `browserbase.md` | 628 | Incumbent — required substantial "where they win vs. where challengers eat into them" framing |
| `cloudflare-browser-run.md` | 544 | Sub-feature of Workers — required clear positioning vs. parent product |
| `hyperbrowser.md` | 509 | Mid-tier challenger with broad integration story |
| `kernel.md` | 517 | App-runtime angle (browsers as a runtime layer) — distinct narrative |
| `meteor.md` | 517 | Gated access; profile compensated for lighter pack with stronger benchmark synthesis |
| `notte.md` | 517 | Hosted OSS hybrid — boundary explanation needed |
| `scrapybara.md` | 553 | Browser-VM hybrid; positioning section longer |
| `steel-dev.md` | 487 | OSS-first; license-and-self-host narrative |
| `browsercloud.md` | 551 | New entrant; "what's verified vs. what's promised" framing |

Average: 549 lines. Range 479-631.

**Linking discipline:** every profile page has 30-60 markdown links into its evidence pack. Profile = synthesis with links; pack = atomic evidence files.

## Phase 7 — Verification (what the gate caught)

**Verification commands run:**

```bash
find 01-ai-native-cloud-browsers -type f | wc -l
# 293 — within budget

find 01-ai-native-cloud-browsers -name '.DS_Store' -o -name '*.tmp'
# (empty — no junk files)

# Markdown link integrity (per-file resolution loop)
# Initial run: 81 broken links
# Cause: substitution applied a filename rename globally that should have been scoped
# Fix: rename the actual files in the 4 affected products + adjust 1 notte filename
# Re-run: 0 broken across 2,903 markdown links checked
```

**Source-ledger presence:** every `core` entity has a `09-sources/01-source-map.md`. Five entities also have separate `02-claims-ledger.md` and `03-open-gaps-and-follow-up-tests.md` (the rest collapsed claims+gaps into one file because their evidence was thinner).

**Stale-slug check** (added when the corpus was renamed for navigability):

```bash
grep -rE '(05-stealth-security-compliance|06-audience-reddit|07-benchmarks-performance|...)' \
  --include='*.md' /Users/yigitkonur/research/browser-system/
# (empty — no stale references after rename pass)
```

## What the corpus deliberately did NOT do

- **No Porter's Five Forces.** Buyers care about per-session pricing, bot-detection rates, and Reddit migration stories — not generic competitive frameworks. The taxonomy adapted to the buyer's decision, not to academic frameworks.
- **No SWOT per vendor.** The `08-buyer-fit/` files use scenario-fit + do-not-choose-if framing, which is more actionable than SWOT for a buyer.
- **No HTML output.** Multi-file markdown corpus is the deliverable. Polishing into a battlecard or slide deck is a downstream task.
- **No vendor-neutral tone.** The profile pages are opinionated about fit and risk — but every opinion ties to specific evidence. "Vendor-neutral" reads as marketing.
- **No exhaustive feature matrix.** Cross-product comparisons are organized by buyer decision criterion, not by feature checklist. Feature lists are in entity packs (`02-platform/01-control-surface-*.md`); cross files compare the *consequences* of those features.
- **No stale entity inclusion.** Two waitlist-only candidates that didn't show progress in 6 months were tiered down to `discovered-only`. Don't research what hasn't shipped.

## What to imitate

- **Sub-question decomposition before discovery searching** — surfaced 25 candidates from 5 distinct angles
- **Tiering before researching** — saved budget by not building packs for entities that didn't deserve them
- **Resolved category names before file creation** — the rename pass that came later cost ~3K substitutions because slug names had been chosen too quickly; pick names you can live with
- **Profile pages as synthesis-with-links, not duplicates** — the 549-line average length came from real multi-category integration, not padding
- **Read every pack personally before cross-synthesis** — orchestrator-only Phase 5 produces materially better cross files than agent-only Phase 5
- **Run the verification commands literally** — the link check found 81 broken links the orchestrator's eyes missed

## What to NOT imitate

- **The exact slugs.** `06-audience` is right for cloud browsers (Reddit-dominant signal). For a B2B SaaS with G2/Capterra signal, use `06-audience-reviews`. For an OSS ecosystem, use `06-community-github-discussions`. The slug must say what the file answers in the buyer's language for THAT vertical.
- **The cross-product file count (10).** That number reflects this category's 10 decision criteria. Yours may have 6 or 14.
- **The profile-page length range (479-631 lines).** That reflects each entity's evidence density. Compact entities should not be padded to hit 500 lines.

## Pointer to the corpus itself

If you have file system access, the corpus is at:

```
/Users/yigitkonur/research/browser-system/01-ai-native-cloud-browsers/
```

Read three things in order to internalize the pattern:

1. **`README.md`** — the navigation entry point
2. **`airtop.md`** (profile page) and **`airtop/README.md`** (pack index) side-by-side — to see synthesis vs. pack distinction
3. **`_cross-product/06-audience/00-overall-comparison.md`** — to see cross-criterion synthesis at scale (425 lines, 12-entity comparison with confidence levels)

Then start Phase 0 of your own corpus with confidence that the discipline is reproducible.

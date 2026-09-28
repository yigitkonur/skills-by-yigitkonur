# Opportunities Engine & Action Workflows — QA Test Specification Suite

> **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)  
> **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)  
> **Test Framework:** Code-Grounded Gherkin Cases (Executable via Ego Browser Node.js Heredocs)  
> **Directory Scope:** `.agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/`

---

## 1. Executive Summary & Architecture Overview

The **Opportunities Engine** is Zeo Geo-Radar's generative discovery and strategic prioritization hub. It analyzes raw generative engine measurement outputs (Google AI Overviews, Perplexity, ChatGPT, Claude) across monitored queries and competitor citations, calculating an actionable, prioritized backlog of high-impact optimization opportunities.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               OPPORTUNITIES ENGINE ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  Data Layer: Brand Measurement (prompts, answers, sources, competitors)                │
│         │                                                                              │
│         ▼                                                                              │
│  Discovery Engine: generateOpportunities(profile)                                      │
│  ├── 1. Forum / Reddit Gaps (Unmentioned threads, high search volume)                  │
│  ├── 2. Outreach Editorial Gaps (Domain authority publications citing rivals)          │
│  └── 3. Content Creation Gaps (High-demand prompt queries where brand visibility <20%) │
│         │                                                                              │
│         ▼                                                                              │
│  Dynamic Impact Scoring: calculateOpportunityImpact(op, profile)                       │
│  ├── composite = (0.35 * S_gap) + (0.35 * S_vol) + (0.20 * S_comp) + (0.10 * S_feas)  │
│  └── Tier Assignment: High (>=75), Medium (>=50), Low (<50)                            │
│         │                                                                              │
│         ▼                                                                              │
│  Presentation Layer: renderOpportunitiesPage(profile)                                  │
│  ├── List View: Status tabs (active/archived/dismissed), Sort & Category Filters       │
│  ├── Card Anatomy: Category badge, Impact tier, Entity tag, Title, Teaser, Perf bar    │
│  ├── Card Actions: Draft Brief, Archive, Dismiss (with reasons & 10s undo), Restore    │
│  └── Detail View: Counter nav, Action CTA banner, 3 accordions (Checklist/Why/Sources) │
│         │                                                                              │
│         ▼                                                                              │
│  Execution Bridges:                                                                    │
│  ├── Push to Content Studio: ContentStudio.createBriefFromOpportunity(seed)            │
│  └── State Persistence: LocalStorage + ZEO_DATA_PROVIDER RPC commands                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Engineering & UX Invariants
1. **Mathematical Impact Formula:**
   $$\text{Composite Score} = \text{round}\Big(0.35 \times S_{\text{gap}} + 0.35 \times S_{\text{vol}} + 0.20 \times S_{\text{comp}} + 0.10 \times S_{\text{feasibility}}\Big)$$
2. **Event Bubbling Isolation:** Clicks on `.op-card-actions` (including `.op-draft-btn`, `.op-archive-btn`, `.op-dismiss-btn`, `.opp-dismiss-pop`, and action margins) strictly prevent card root click delegation (`opp-select-detail`). Only direct clicks on the card body transition `cfg.viewMode` to `"detail"`.
3. **10-Second Undo Toast Expiration:** Dismissal triggers a 10,000ms toast with Undo CTA (`opp-undo`). At $t = 9.5\text{s}$, the toast remains active with `.show` class and the Undo button restores the card; after $t = 10.5\text{s}$, the toast timer settles, unmounts the Undo button, and keeps the card permanently dismissed.
4. **Honest Empty State vs Golden Trophy:** When `allOpps.length === 0`, the Golden Trophy banner (`🏆`) is gated behind 5 strict mathematical criteria ($\ge 5$ prompts, $\ge 20$ answers, $\ge 85\%$ visibility, $\ge 60\%$ citation share, and outranking top competitor). Accounts failing any criterion display the honest diagnostic empty state with remediation CTAs.
5. **Competitor Modal Validation:** Requires both competitor name and domain; inputs stripped by `cleanDomain()` (e.g. `https://`) trigger an error toast and preserve modal state.

---

## 2. Standardized Vocabulary & Placeholder Dictionary

All test cases in this directory adhere to the following unified parameter definitions:

| Placeholder | Meaning | Example Values |
|---|---|---|
| `[DOMAIN]` | Target monitored brand domain | `daikin.com.tr`, `example.com` |
| `[COUNTRY]` | Target market / geographical ccTLD | `US`, `TR`, `UK`, `DE` |
| `[LANGUAGE]` | User interface localization language | `en`, `tr` |
| `[OPPORTUNITY_ID]` | Unique identifier for opportunity record | `op-reddit-1`, `op-outreach-2`, `op-content-5` |
| `[OPP_TYPE]` | Strategic taxonomy category | `reddit`, `outreach`, `content` |
| `[SCORE_TIER]` | Impact tier classification | `high` ($\ge 75$), `medium` ($50-74$), `low` ($< 50$) |
| `[COMPETITOR_NAME]` | Name of tracked rival brand | `Mitsubishi Electric`, `Competitor Alpha` |
| `[COMPETITOR_DOMAIN]` | Domain of tracked rival brand | `mitsubishielectric.com.tr`, `competitor-alpha.com` |

---

## 3. Traceability & Source Coverage Matrix

The 13 modular test cases below provide **100% comprehensive coverage** for all 20 source scenarios (`TC-OPP-01` to `TC-OPP-20`) defined in the parent specification:

| Modular Test Case File | Source Scenario(s) Covered | Core Verification Scope |
|---|---|---|
| [`01-gherkin-case-backlog-load-and-categories.md`](./01-gherkin-case-backlog-load-and-categories.md) | `TC-OPP-01`, `TC-OPP-02` | Backlog initial render, category indicator rails & badges (`reddit`, `outreach`, `content`), composite impact formula, High/Med/Low tiers |
| [`02-gherkin-case-status-tabs-and-archival-lifecycle.md`](./02-gherkin-case-status-tabs-and-archival-lifecycle.md) | `TC-OPP-03`, `TC-OPP-07` | Status tabs (`active`, `archived`, `dismissed`), counter badge synchronization, archival and restoration lifecycle |
| [`03-gherkin-case-category-filtering-and-zero-result-recovery.md`](./03-gherkin-case-category-filtering-and-zero-result-recovery.md) | `TC-OPP-04`, `TC-OPP-18` | Category popover filtering, zero-result empty card with "Reset filters" CTA, instant full backlog restoration |
| [`04-gherkin-case-sorting-engine.md`](./04-gherkin-case-sorting-engine.md) | `TC-OPP-05` | Re-ordering backlog by Impact Score (descending), Performance Score, and Strategy Type |
| [`05-gherkin-case-action-bubbling-isolation.md`](./05-gherkin-case-action-bubbling-isolation.md) | `TC-OPP-08`, `TC-OPP-15` | Event bubbling isolation on `.op-card-actions` and child buttons, preventing card detail view transition |
| [`06-gherkin-case-dismissal-reasons-and-10s-toast-boundary.md`](./06-gherkin-case-dismissal-reasons-and-10s-toast-boundary.md) | `TC-OPP-06`, `TC-OPP-16` | 3 dismissal reasons (`out_of_scope`, `already_completed`, `irrelevant`), 10s undo toast expiration boundary (9.5s valid vs 10.5s expired) |
| [`07-gherkin-case-detail-view-navigation-and-stepper.md`](./07-gherkin-case-detail-view-navigation-and-stepper.md) | `TC-OPP-09`, `TC-OPP-20` | Detail view mounting, `N / Total` counter stepper, back button return, safe fallback on invalid/out-of-bounds IDs |
| [`08-gherkin-case-detail-interactive-checklist.md`](./08-gherkin-case-detail-interactive-checklist.md) | `TC-OPP-10` | Implementation Guide accordion, dashed to solid green checkbox toggle, strike-through text, progress counter updates |
| [`09-gherkin-case-detail-references-grid.md`](./09-gherkin-case-detail-references-grid.md) | `TC-OPP-11` | References 2x3 CSS grid, publisher emojis, article titles, domain badges, snippet previews, `target="_blank"` security |
| [`10-gherkin-case-competitor-mapping-modal-validation.md`](./10-gherkin-case-competitor-mapping-modal-validation.md) | `TC-OPP-12`, `TC-OPP-17` | Competitor modal opening, input validation & domain sanitization boundaries (`https://`), error toast defense, backlog recalculation |
| [`11-gherkin-case-push-to-content-studio-handoff.md`](./11-gherkin-case-push-to-content-studio-handoff.md) | `TC-OPP-13` | "Draft Brief" execution bridge (`createBriefFromOpportunity`), seed protocol assembly, route switch to `workflows`, AEO editor launch |
| [`12-gherkin-case-golden-trophy-qualification-vs-diagnostic-state.md`](./12-gherkin-case-golden-trophy-qualification-vs-diagnostic-state.md) | `TC-OPP-19` | 5 mathematical qualification criteria for Golden Trophy (🏆) vs honest diagnostic empty state with remediation CTAs |
| [`13-gherkin-case-csv-export.md`](./13-gherkin-case-csv-export.md) | `TC-OPP-14` | "Export CSV" trigger, spreadsheet formula injection defense (`'`), UTF-8 BOM encoding, browser download confirmation |

---

## 4. Execution & Reporting Guidelines

### 4.1 Ego Browser 5-Phase Lifecycle
All tests must be executed following the 5-phase lifecycle:
1. **Phase 1: Task Space Isolation** (`useOrCreateTaskSpace('e2e-opportunities-engine')`)
2. **Phase 2: Navigation & Hydration** (`openOrReuseTab('[APP_URL]/#/[SLUG]/opportunities')`)
3. **Phase 3: Semantic Observation & Interaction** (`snapshotText()`, `click()`, `fillInput()`)
4. **Phase 4: State Assertion (Single IIFE)** (`js(() => { ... })`)
5. **Phase 5: Dedicated Teardown Round** (`completeTaskSpace('e2e-opportunities-engine', { keep: false })`)

### 4.2 MacBook Remote Execution & Screenshot Artifact Protocol
1. Ego Browser runs directly on the designated developer MacBook or high-throughput host.
2. During test execution, visual evidence (`.png`) is captured directly into `/tmp/ego-test/opportunities-*`.
3. Test executors pull screenshots to the local repository runner via SCP before committing evidence:
   ```bash
   scp macbook:/tmp/ego-test/opportunities-*/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/[matching-result-directory]/
   ```
4. **Important:** Result directories (e.g. `01-gherkin-result-case-backlog-load-and-categories/`) are created dynamically by the test runner during execution. **Do not create empty result directories ahead of time.**

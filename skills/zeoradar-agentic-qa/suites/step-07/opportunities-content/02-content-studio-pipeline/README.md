# Content Studio Pipeline & AI Article Generator — QA Test Specification Suite

> **Module:** Workflows & Content Studio (`assets/content-studio.js`, `assets/content-studio.css`)  
> **Parent Contracts:** Issue #46 (Content Studio Pipeline, Facts Grounding & AI Streaming) & Issue #91 (Revision History & Archival)  
> **Test Framework:** Code-Grounded Gherkin Cases (Executable via Ego Browser Node.js Heredocs)  
> **Directory Scope:** `.agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/`

---

## 1. Executive Summary & Architecture Overview

The **Content Studio** is Zeo Geo-Radar's enterprise Generative Engine Optimization (AEO) authoring and publishing environment. It bridges discovery insights from the Opportunities Engine and verified Brand Hub ground truths into publish-ready, citation-optimized articles, structured data briefs, and search engine-aligned URL slugs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CONTENT STUDIO PIPELINE OVERVIEW                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  Ingestion Sources:                                                                    │
│  ├── 1. Opportunities Engine Handoff (createBriefFromOpportunity)                      │
│  ├── 2. 4-Step Interactive Creation Wizard (openWizard('create'))                     │
│  └── 3. Content Optimization Wizard (openWizard('optimize'))                           │
│         │                                                                              │
│         ▼                                                                              │
│  Grounding & Fact Compliance Layer:                                                    │
│  ├── Brand Hub Ground Truths: getBrandHubFacts(profile) -> # BRAND GROUND TRUTH       │
│  └── Competitive Citation Gaps: targetQuery, outrank competitor -> # CITATION GAPS    │
│         │                                                                              │
│         ▼                                                                              │
│  AI Article Generation Pipeline:                                                       │
│  ├── Dispatches POST /api/chat with { stream: true }                                  │
│  ├── SSE Stream Reader: parses "data: {...}" chunks -> delta.content                   │
│  ├── Realtime Typewriter Output: updates #wizLiveTokenOutput & streamingTokens counter │
│  └── Resilient Error Traps: HTTP 401/403 (Auth), HTTP 429 (Quota/Rate Limit), Retry ↻  │
│         │                                                                              │
│         ▼                                                                              │
│  AEO Rich Text Editor & Live Canvas:                                                   │
│  ├── Sticky Toolbar: Bold, Italic, Link, H1, H2, Blockquote, AI Rewrite               │
│  ├── Floating Selection Toolbar: requestAnimationFrame positioning + AI Rewrite       │
│  ├── Contenteditable Canvas: #edContentBody with real-time word/readability metrics    │
│  └── Multi-Tab Inspector Sidebar:                                                      │
│      ├── Tab 'workflow': Brief Outline (.ed-outline-list), AEO Checklist               │
│      ├── Tab 'aeo_stats': 0-100 AEO Score, Structural Stats, Engine Alignment Meters   │
│      └── Tab 'history': Immutable Revision Timeline, Snapshot create, Version restore  │
│         │                                                                              │
│         ▼                                                                              │
│  SEO Metadata & URL Slug Optimizer:                                                    │
│  ├── 2-Column Split Interface: Target slug + editable domain prefix                   │
│  ├── 6-Point Deterministic Evaluation Criteria Accordion (0-100 Score)                │
│  └── Alternative Slugs Generator, Descriptiveness & Entity Breakdown, JSON Export     │
│         │                                                                              │
│         ▼                                                                              │
│  Persistence & Archival Lifecycle:                                                     │
│  ├── LocalStorage fallback: zeo-content-studio-projects:[wid]:[pid]                    │
│  ├── RPC Command: dispatchCommand('save-content-project')                              │
│  └── Database Schema: public.content_studio_projects, public.content_studio_revisions  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Engineering & UX Invariants
1. **Brand Hub Fact Grounding:** Brief seeds automatically inject the `.brief-fact-compliance-box` (`BMD-BSH-02`), binding enterprise SLAs and data residency claims into AI generation prompts.
2. **SSE Streaming & Partial Draft Rescue:** Real-time token consumption via `reader.read()` and `#wizLiveTokenOutput`. If a stream is interrupted mid-transmission after buffering tokens, `finalizeDraft(fullContent)` rescues the partial draft with zero data loss.
3. **HTTP 429 Rate Limit Recovery:** API quota and rate limits trigger an explicit `.wiz-error-box` notice with an actionable "Retry Generation ↻" CTA that cleanly re-dispatches the stream.
4. **Caret Block Formatting & Collapsed Protection:** Clicking H1/H2 with a collapsed caret formats the enclosing paragraph. Clicking AI Rewrite with a collapsed selection triggers a protective guidance toast.
5. **Floating Toolbar RAF Geometry:** `#edFloatBar` dynamically mounts on text selection, clamping horizontally within viewport boundaries ($10\text{px} \le x \le \text{viewportWidth} - 10\text{px}$) and inverting below the selection when near the top edge. Dismisses immediately on click-away.
6. **Immutable Revision Audit Trail:** Restoring an older revision never deletes or overwrites history; it creates a brand-new sequential head revision (`v(N+1).0`) with full attribution. Dirty uncommitted canvas scratch edits are safely replaced.
7. **6-Point Deterministic Slug Heuristics:** Evaluates Length (25–45), Meaningful Entities ($\ge 2$), Natural Language ($3–6$ words), Format (lowercase, no `--`), Stop Words filter, and Single Topic Intent. Alternative suggestions deduplicate identical input matches.

---

## 2. Standardized Vocabulary & Placeholder Dictionary

All test cases in this directory adhere to the following unified parameter definitions:

| Placeholder | Meaning | Example Values |
|---|---|---|
| `[DOMAIN]` | Target monitored brand domain | `daikin.com.tr`, `example.com` |
| `[COUNTRY]` | Target market / geographical ccTLD | `US`, `TR`, `UK`, `DE` |
| `[LANGUAGE]` | User interface localization language | `en`, `tr` |
| `[OPPORTUNITY_ID]` | Unique opportunity seed ID | `op-reddit-1`, `op-content-3` |
| `[ARTICLE_TITLE]` | Title of generated or edited article | `"Position [BRAND] in Discussions"` |
| `[TARGET_SLUG]` | URL slug string evaluated or applied | `enterprise-generative-engine-optimization-framework` |
| `[REVISION_ID]` | Version revision tag | `v1.0`, `v2.0`, `v3.0` |
| `[TOPIC]` | Selected article topic or search theme | `"Enterprise AI Search Optimization"` |

---

## 3. Traceability & Source Coverage Matrix

The 14 modular test cases below provide **100% comprehensive coverage** for all 20 source scenarios (`TC-CS-01` to `TC-CS-20`) defined in the parent specification:

| Modular Test Case File | Source Scenario(s) Covered | Core Verification Scope |
|---|---|---|
| [`01-gherkin-case-opportunity-handoff-and-fact-compliance.md`](./01-gherkin-case-opportunity-handoff-and-fact-compliance.md) | `TC-CS-01` | Seed ingestion (`createBriefFromOpportunity`), Brand Hub facts box (`BMD-BSH-02`), citation sources box, outline H2s, auto-mount editor |
| [`02-gherkin-case-wizard-topic-selection-and-progressive-disclosure.md`](./02-gherkin-case-wizard-topic-selection-and-progressive-disclosure.md) | `TC-CS-02` | Wizard Step 1, searchable rich-select `#wizTopic`, progressive unlock of dependent fields (`.wiz-disabled-banner`), top-cited pages chips (up to 20) |
| [`03-gherkin-case-wizard-title-generation-and-selection.md`](./03-gherkin-case-wizard-title-generation-and-selection.md) | `TC-CS-03` | Wizard Step 2, candidate titles generation (4 cards), `Recommended ⚡` badge, radio selection, "Suggest new titles" cycling |
| [`04-gherkin-case-ai-sse-streaming-and-typewriter.md`](./04-gherkin-case-ai-sse-streaming-and-typewriter.md) | `TC-CS-04`, `TC-CS-15` | Wizard Step 4 `POST /api/chat`, SSE delta chunk parsing, typewriter `#wizLiveTokenOutput`, background generation resilience across subtabs |
| [`05-gherkin-case-stream-disconnection-and-partial-draft-rescue.md`](./05-gherkin-case-stream-disconnection-and-partial-draft-rescue.md) | `TC-CS-13` | Mid-stream network abort: partial tokens rescued into editor canvas via `finalizeDraft(fullContent)` vs immediate error trap with retry box |
| [`06-gherkin-case-ai-gateway-http-errors-and-rate-limit-retry.md`](./06-gherkin-case-ai-gateway-http-errors-and-rate-limit-retry.md) | `TC-CS-05`, `TC-CS-14` | Gateway errors: HTTP 401/403 auth notice, HTTP 429 rate limit state machine, actionable "Retry Generation ↻" recovery |
| [`07-gherkin-case-markdown-editor-toolbar-formatting.md`](./07-gherkin-case-markdown-editor-toolbar-formatting.md) | `TC-CS-06`, `TC-CS-16` | Sticky formatting toolbar (Bold, Italic, Link, H1, H2, Blockquote); caret behavior on collapsed block format vs AI Rewrite guidance toast |
| [`08-gherkin-case-floating-selection-toolbar-and-clamping.md`](./08-gherkin-case-floating-selection-toolbar-and-clamping.md) | `TC-CS-07`, `TC-CS-17` | Dynamic `#edFloatBar` on selection via RAF, boundary clamping geometry ($10\text{px} \le x \le W - 10\text{px}$), top inversion, click-away auto-dismissal |
| [`09-gherkin-case-live-document-metrics-and-engine-alignment.md`](./09-gherkin-case-live-document-metrics-and-engine-alignment.md) | `TC-CS-08` | AEO Stats tab: structural stats (words, headings, paragraphs, readability); 4 AI engine alignment meters (Perplexity, ChatGPT, Claude, Gemini) |
| [`10-gherkin-case-revision-history-snapshots-and-immutability.md`](./10-gherkin-case-revision-history-snapshots-and-immutability.md) | `TC-CS-09`, `TC-CS-10` | Manual snapshot creation, `v(N+1).0` sequential version tags, immutable version restore creating new head revision without history truncation |
| [`11-gherkin-case-revision-restoration-with-dirty-unsaved-edits.md`](./11-gherkin-case-revision-restoration-with-dirty-unsaved-edits.md) | `TC-CS-18` | Restoring historical revision over uncommitted canvas scratch text; scratch edits safely discarded in favor of restored version |
| [`12-gherkin-case-slug-optimizer-6-criteria-audit.md`](./12-gherkin-case-slug-optimizer-6-criteria-audit.md) | `TC-CS-11`, `TC-CS-19` | URL Slug Optimizer 2-column layout, 6 deterministic evaluation criteria (Length, Entities, Words, Format, Stopwords, Intent) & penalty math |
| [`13-gherkin-case-slug-collision-deduplication-and-apply-sync.md`](./13-gherkin-case-slug-collision-deduplication-and-apply-sync.md) | `TC-CS-20` | Duplicate input slug filtered out of alternative suggestions; "Apply Slug" syncs DOM input, updates state, pushes history, triggers toast |
| [`14-gherkin-case-document-and-brief-archival-lifecycle.md`](./14-gherkin-case-document-and-brief-archival-lifecycle.md) | `TC-CS-12` | Archiving active project/brief from table row actions; segregated Archived filter pill view; Restore CTA returning asset to active draft backlog |

---

## 4. Execution & Reporting Guidelines

### 4.1 Ego Browser 5-Phase Lifecycle
All tests must be executed following the 5-phase lifecycle:
1. **Phase 1: Task Space Isolation** (`useOrCreateTaskSpace('e2e-content-studio-pipeline')`)
2. **Phase 2: Navigation & Hydration** (`openOrReuseTab('[APP_URL]/#/[SLUG]/workflows')`)
3. **Phase 3: Semantic Observation & Interaction** (`snapshotText()`, `click()`, `fillInput()`)
4. **Phase 4: State Assertion (Single IIFE)** (`js(() => { ... })`)
5. **Phase 5: Dedicated Teardown Round** (`completeTaskSpace('e2e-content-studio-pipeline', { keep: false })`)

### 4.2 MacBook Remote Execution & Screenshot Artifact Protocol
1. Ego Browser runs directly on the designated developer MacBook or high-throughput host.
2. During test execution, visual evidence (`.png`) is captured into `/tmp/ego-test/content-*`.
3. Test executors pull screenshots to the local repository runner via SCP before committing evidence:
   ```bash
   scp macbook:/tmp/ego-test/content-*/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/02-content-studio-pipeline/[matching-result-directory]/
   ```
4. **Important:** Result directories (e.g. `01-gherkin-result-case-opportunity-handoff-and-fact-compliance/`) are created dynamically by the test runner during execution. **Do not create empty result directories ahead of time.**

# Test Suite 01: AI Engine Benchmark Matrix, Query-Level Visibility & Citation Drawer

## 1. Module Overview & Architectural Grounding

The **AI Engine Benchmark Matrix, Query-Level Visibility & Citation Drawer** subsystem (`assets/aei.js`, `assets/aei.css`, `assets/radar.js`) forms the core of Zeo Geo-Radar's Answer Engine Insights (AEI) architecture (Spec 11). It provides multi-platform competitive visibility benchmarking across five leading AI engines (ChatGPT, Perplexity, Gemini, Claude, and Google AI Mode), deep query-level retrieval forensics, a 3-stage generative pipeline, and an authoritative slide-in citation drawer.

### System Architecture Flow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        VISIBILITY & ENGINE BENCHMARK ARCHITECTURE                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Client Navigation (/#/app/:slug/visibility)                                          │
│        │                                                                               │
│        ▼                                                                               │
│   [window.renderAeiPage(p)] ◄──► [window.aeiState]                                     │
│        │                                                                               │
│        ├── 1. Global Filter Bar: Active Brand, Engine Chips, Timeframe, Region        │
│        ├── 2. Workspace Navigation Tabs: Performance | Studio | Perception             │
│        │                                                                               │
│        ├──► WORKSPACE 1: Performance & SOV (`workspace === 'performance'`)             │
│        │    ├─ KPI Headline Strip (Visibility Score, AI SOV, Avg Position, Cites)      │
│        │    ├─ AI Engine Visibility Trajectory (In-card pills: 7d, 30d, 90d, custom)   │
│        │    ├─ Baseline Multi-Engine Bar Cockpit (ChatGPT, PPX, GEM, Claude, AIM)     │
│        │    ├─ Multi-Engine Platform Benchmark Matrix (Brand × Engine grid)           │
│        │    │    ├─ Own brand row pinned at top (`tr.is-me-row .aei-me-tag`)           │
│        │    │    ├─ Zero-Visibility Cell Handling (`0%` indicates lost probe)          │
│        │    │    ├─ Unmeasured Engine Cell (`–` em-dash indicates unprobed platform)   │
│        │    │    └─ Cell Click ──► Drilldown to Studio (`data-action="aei-matrix-drilldown"`)
│        │    └─ Geographic Search Demand Heatmap (Measured vs Unmeasured Probes)        │
│        │                                                                               │
│        ├──► WORKSPACE 2: Prompts & Citations Studio (`workspace === 'studio'`)         │
│        │    ├─ Master Prompt Table (45% left pane): Debounced Search (150ms), Intent   │
│        │    │    └─ Mini indicator dots (Won #1, Mentioned, Lost, Unmeasured)          │
│        │    └─ Generative Retrieval Pipeline Detail (55% right pane):                  │
│        │         ├─ Execution Engine Selector Tabs (All Engines vs Individual)         │
│        │         ├─ Stage 1: Synthesized Answer Inspector (Markdown, Badges, Mentions) │
│        │         │    └─ Turkish Diacritics Case-Folding (`buildTurkishRegexPattern`)  │
│        │         ├─ Stage 2: Hierarchical Query Fanout Tree (Seed → Hop → Cite)        │
│        │         │    ├─ Pure Parametric Detection (`.aei-parametric-notice.card`)     │
│        │         │    └─ Multi-Hop Query Latency & Publisher Attribution Branching     │
│        │         └─ Stage 3: Root Domain Authority & Co-Citation Overlap Bar           │
│        │              ├─ Co-Citation Split Bar (`.aei-co-my` vs `.aei-co-rival`)       │
│        │              └─ eTLD+1 Authority Tiers (`High`, `Medium`, `Low`, `.gov`/`.edu`)│
│        │                                                                               │
│        └──► AUTHORITATIVE CITATION DRAWER (`openCitationDrawer(rawUrl, force)`)        │
│             ├─ Backdrop + Slide-in Panel (`#citationDrawerHolder`, `role="dialog"`)   │
│             ├─ Client Cache Gate: `state.citationDetailCache[norm]` vs Network Fetch   │
│             ├─ Data Provider Telemetry Fetch (`dp.loadResource("citationDetail")`)     │
│             ├─ Telemetry View: Domain, Category Badge, Occurrences, First/Last Seen    │
│             ├─ Empty Occurrences Graceful State (Newly discovered unindexed domains)   │
│             ├─ Historical Occurrence Footprint Table (Date, Engine, Prompt ID, Rank)   │
│             ├─ Triple Dismissal Path (Escape Key, Close Button, Backdrop Click)        │
│             ├─ Focus Trapping & Restoration (`previousActiveCitationEl.focus()`)       │
│             └─ URL Normalization & Sanitization (`normalizeCitationUrl`, `esc()`)      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Test Cases

This directory contains 12 focused, code-grounded Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-navigation-url-sync-and-initial-boot.md` | TC-VIS-01 | Default Workspace Boot, URL Search Parameter Synchronization & Engine Toggle Lock | VIS-01, VIS-02, VIS-03 |
| `02-gherkin-case-multi-engine-benchmark-matrix-rendering.md` | TC-VIS-02 | Benchmark Matrix Anatomy, Own Brand Row Pinning & Unmeasured/Zero Cell Formats | VIS-04, VIS-18, VIS-20 |
| `03-gherkin-case-matrix-cell-drilldown-to-studio.md` | TC-VIS-03 | Matrix Cell Drilldown Transition to Studio Workspace & Filter Scoping | VIS-05, VIS-19, VIS-20 |
| `04-gherkin-case-geographic-demand-heatmap-and-probe-modal.md` | TC-VIS-04 | Regional Search Demand Heatmap, Measured Country Filtering & Probe Provisioning Modal | VIS-06, VIS-07 |
| `05-gherkin-case-studio-search-debounce-and-intent-filtering.md` | TC-VIS-05 | Studio Master List Debounced Search (150ms), Intent Filtering & Mini Engine Indicators | VIS-08, VIS-09 |
| `06-gherkin-case-stage-1-synthesized-answer-and-model-tabs.md` | TC-VIS-06 | Stage 1 Synthesized Answer Inspector, Position Badges & In-Card Engine Selector Tabs | VIS-10, VIS-11, VIS-22 |
| `07-gherkin-case-turkish-diacritics-and-case-folding-regex.md` | TC-VIS-07 | Turkish Character Case-Folding Regex (`buildTurkishRegexPattern`) & Mention Highlighting | VIS-10, VIS-23 |
| `08-gherkin-case-stage-2-query-fanout-cascade-and-latencies.md` | TC-VIS-08 | Stage 2 Hierarchical Fanout Cascade Tree, Hop Latencies & Citation Leaf Nodes | VIS-12, VIS-24 |
| `09-gherkin-case-pure-parametric-response-detection.md` | TC-VIS-09 | Pure Parametric Response Detection Notice Card & Hallucinated Leaf Suppression | VIS-13, VIS-21 |
| `10-gherkin-case-stage-3-root-domain-authority-and-cocitation-bar.md` | TC-VIS-10 | Stage 3 Root Domain Rollups, Authority Tiers & Co-Citation Overlap Split Bar | VIS-25 |
| `11-gherkin-case-citation-drawer-telemetry-and-caching.md` | TC-VIS-11 | Authoritative Citation Drawer Mount, Telemetry Resolution, Cache Gating & Footprint Table | VIS-14, VIS-15, VIS-26, VIS-27 |
| `12-gherkin-case-citation-drawer-a11y-focus-trap-and-security.md` | TC-VIS-12 | Citation Drawer Accessibility (ARIA), Keyboard Focus Trapping, Triple Dismissal & XSS Defense | VIS-16, VIS-17, VIS-28, VIS-29, VIS-30 |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite utilize standardized, bracketed placeholders. The table below defines each placeholder, system mapping, and test variants:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[DOMAIN]` | Web origin or brand domain under test | Base URL parameter in `openOrReuseTab` or project config | `[DOMAIN]` (e.g. `daikin.com.tr`) |
| `[COUNTRY]` | ISO 3166-1 alpha-2 regional code for search demand and probes | Region selector `select[data-action-change="aei-select-region"]` or country card | `all`, `TR`, `US`, `GB`, `DE`, `FR` |
| `[LANGUAGE]` | IETF language tag for UI localization and regex engine | App shell language toggle or `state.lang` | `en` (English), `tr` (Turkish) |
| `[ENGINE_NAME]` | AI engine platform key in Answer Engine Insights | Engine chip `button.aei-engine-chip[data-engine]` | `chat_gpt`, `perplexity`, `gemini`, `claude`, `aimode` |
| `[SORT_COLUMN]` | Table column identifier targeted for matrix or rollup sorting | Table header `th.num` or sortable attribute | `brand`, `chat_gpt`, `perplexity`, `citations`, `authority` |
| `[SORT_ORDER]` | Direction of table column sort | Data attribute or state parameter | `asc` (Ascending), `desc` (Descending) |
| `[CITATION_URL]` | Normalized external publisher citation URL | `[data-action="open-citation-drawer"]` `data-url` attribute | `[CITATION_URL]` (e.g. `tr.wikipedia.org/wiki/Daikin`) |
| `[PROMPT_QUERY]` | Search term input into Studio Master search | Input `input#aeiStudioSearchInput` | `[PROMPT_QUERY]` (e.g. `klima`, `ısı pompası`) |
| `[INTENT_CATEGORY]`| Search intent classification for prompt clustering | Intent chip `button.aei-intent-chip[data-intent]` | `all`, `info`, `comm`, `trans`, `nav` |
| `[AUTHORITY_TIER]`| Domain authority classification level | Badge class `.aei-tier-pill` | `high`, `med`, `low` |

---

## 4. Ego Browser / MacBook Execution Model

### Physical Topology & Gateway
E2E testing is executed using `ego-browser nodejs` on the physical MacBook gateway connected via SSH.

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     Linux Host (Development)     │           │      MacBook Gateway (Live)     │
│                                 │   SSH     │                                 │
│  - Test Suite & Gherkin Specs   │──────────►│  - Ego Browser Runtime (Node)   │
│  - Storage / Result Directories │           │  - Active Display / GPU Render  │
│  - SCP Evidence Downloader      │◄──────────│  - Local Screenshot Cache       │
└─────────────────────────────────┘    SCP    └─────────────────────────────────┘
```

### Execution Lifecycle Protocol
1. **Heredoc Dispatch**: The test script is executed remotely via:
   ```bash
   ssh macbook "ego-browser nodejs <<'EOF'
     const task = await useOrCreateTaskSpace('e2e-visibility-matrix-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/app/[SLUG]/visibility', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-visibility-matrix-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/visibility/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/visibility/case-*.png ./01-gherkin-result-case-<slug>/screenshots/
   ```
4. **Result Directory Specification**:
   - Each Gherkin case corresponds to an execution result directory named `0X-gherkin-result-case-<slug>/`.
   - Result directories are **NEVER created as empty placeholders**. They are instantiated only by the test execution runner upon executing the suite.
   - A complete result directory contains:
     - `result.md` (Execution outcome, timing, environment specs, pass/fail status)
     - `evidence.json` (Structured DOM dumps, console errors, state snapshots)
     - `screenshots/*.png` (Visual evidence downloaded from MacBook)
     - `network/*.json` (Recorded HTTP / RPC telemetry)

---

## 5. Traceability & Code Coverage Matrix

| Original Scenario ID | Original Title | New Modular Gherkin Case | Real Code Reference & Gap Hardening |
|:---|:---|:---|:---|
| VIS-01 | Default Workspace Load | `01-gherkin-case-navigation-url-sync-and-initial-boot.md` | `assets/aei.js:106` `readUrlParams`, `assets/aei.js:30` default `aeiState` |
| VIS-02 | Engine Chip Toggle Off | `01-gherkin-case-navigation-url-sync-and-initial-boot.md` | `assets/aei.js:2065` `aei-toggle-engine`, `syncUrlParams` URL update |
| VIS-03 | Engine Deselection Lock | `01-gherkin-case-navigation-url-sync-and-initial-boot.md` | `assets/aei.js:2071` `idx !== -1 && st.filters.engines.length > 1` lock |
| VIS-04 | Matrix Row Structure | `02-gherkin-case-multi-engine-benchmark-matrix-rendering.md` | `assets/aei.js:424` `tr.is-me-row`, `.aei-me-tag` ("You"/"Siz") |
| VIS-05 | Matrix Drilldown | `03-gherkin-case-matrix-cell-drilldown-to-studio.md` | `assets/aei.js:2100` `aei-matrix-drilldown` sets `st.workspace = "studio"` |
| VIS-06 | Geographic Country Filter | `04-gherkin-case-geographic-demand-heatmap-and-probe-modal.md` | `assets/aei.js:2088` `aei-select-map-country` updates `st.filters.region` |
| VIS-07 | Geographic Probe Modal | `04-gherkin-case-geographic-demand-heatmap-and-probe-modal.md` | `assets/aei.js:2092` `aei-open-probe-modal` launches overlay modal |
| VIS-08 | Studio Debounced Search | `05-gherkin-case-studio-search-debounce-and-intent-filtering.md` | `assets/aei.js:2184` debounced input listener (`150ms`) |
| VIS-09 | Studio Intent Filtering | `05-gherkin-case-studio-search-debounce-and-intent-filtering.md` | `assets/aei.js:2116` `aei-studio-filter-intent` updates `st.studioIntentFilter` |
| VIS-10 | Verified Brand Mention | `06-gherkin-case-stage-1-synthesized-answer-and-model-tabs.md` | `assets/aei.js:806` `highlightAnswerText`, `mark.aei-mention-brand` |
| VIS-11 | Engine Selector Tabs | `06-gherkin-case-stage-1-synthesized-answer-and-model-tabs.md` | `assets/aei.js:2151` `aei-studio-select-engine` switches displayed engine answer |
| VIS-12 | Stage 2 Fanout Tree | `08-gherkin-case-stage-2-query-fanout-cascade-and-latencies.md` | `assets/aei.js:1447` `.aei-node.root`, `.aei-branch`, `.aei-node.fanout` |
| VIS-13 | Parametric Detection | `09-gherkin-case-pure-parametric-response-detection.md` | `assets/aei.js:1430` `.aei-parametric-notice.card` zero-query gate |
| VIS-14 | Citation Drawer Open | `11-gherkin-case-citation-drawer-telemetry-and-caching.md` | `assets/radar.js:4402` `openCitationDrawer`, `#citationDrawerHolder` |
| VIS-15 | Citation Drawer Data | `11-gherkin-case-citation-drawer-telemetry-and-caching.md` | `assets/radar.js:4531` `.zr-citation-detail-content`, `.bh-tv-kpis` |
| VIS-16 | Citation Drawer Close | `12-gherkin-case-citation-drawer-a11y-focus-trap-and-security.md` | `assets/radar.js:4465` `closeCitationDrawer`, `previousActiveCitationEl.focus()` |
| VIS-17 | Citation Drawer Escape | `12-gherkin-case-citation-drawer-a11y-focus-trap-and-security.md` | `assets/radar.js:6314` keydown `Escape` listener intercept |
| VIS-18 | Matrix Row & Column Structure | `02-gherkin-case-multi-engine-benchmark-matrix-rendering.md` | `assets/aei.js:415` `table.tbl.aei-matrix-tbl`, 5 PLATFORMS header columns |
| VIS-19 | Drilldown from 0% Cell | `03-gherkin-case-matrix-cell-drilldown-to-studio.md` | `assets/aei.js:445` cell carries `data-action` regardless of 0% or unmeasured |
| VIS-20 | Unmeasured Cell State | `02-gherkin-case-multi-engine-benchmark-matrix-rendering.md` | `assets/aei.js:430` `cellScoreStr = "–"`, safe drilldown without JS exceptions |
| VIS-21 | Parametric Notice Isolation | `09-gherkin-case-pure-parametric-response-detection.md` | `assets/aei.js:1429` `!hasAnyQueriesOrSources` suppresses synthetic leaves |
| VIS-22 | In-Card Engine Re-render | `06-gherkin-case-stage-1-synthesized-answer-and-model-tabs.md` | `assets/aei.js:1290` `.aei-pipe-engine-tab`, rebinds model badge and text |
| VIS-23 | Turkish Case-Folding Regex | `07-gherkin-case-turkish-diacritics-and-case-folding-regex.md` | `assets/aei.js:781` `buildTurkishRegexPattern`, dotted/dotless I matching |
| VIS-24 | Fanout Hop Latency Tags | `08-gherkin-case-stage-2-query-fanout-cascade-and-latencies.md` | `assets/aei.js:1472` `qLatHtml` latency tags and depth tracking |
| VIS-25 | Co-Citation Split Bar | `10-gherkin-case-stage-3-root-domain-authority-and-cocitation-bar.md` | `assets/aei.js:1527` `.aei-domain-tbl`, `1620` `.aei-co-my` vs `.aei-co-rival` |
| VIS-26 | Drawer 0 Occurrences Edge | `11-gherkin-case-citation-drawer-telemetry-and-caching.md` | `assets/radar.js:4562` `occs.length === 0` renders empty state notice |
| VIS-27 | Drawer In-Memory Cache | `11-gherkin-case-citation-drawer-telemetry-and-caching.md` | `assets/radar.js:4418` `state.citationDetailCache[norm]` cache hit bypass |
| VIS-28 | Drawer Accessibility & ARIA | `12-gherkin-case-citation-drawer-a11y-focus-trap-and-security.md` | `assets/radar.js:4591` `role="dialog"`, `aria-modal="true"`, auto-focus close |
| VIS-29 | Drawer Triple Dismissal | `12-gherkin-case-citation-drawer-a11y-focus-trap-and-security.md` | Close button, backdrop overlay click, and Escape key listener |
| VIS-30 | URL Normalization & XSS | `12-gherkin-case-citation-drawer-a11y-focus-trap-and-security.md` | `normalizeCitationUrl` query/hash strip, `esc(norm)` title rendering |

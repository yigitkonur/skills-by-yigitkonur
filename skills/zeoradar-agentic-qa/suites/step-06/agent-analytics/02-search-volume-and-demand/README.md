# Suite 02: Search Volume Curves, Probabilistic Demand & Intent Modeling

## 1. Overview & Architecture

This suite specifies end-to-end and modular Gherkin QA test cases for the **Prompt Volumes & Search Demand Analytics** module of Zeo Geo-Radar. It exercises the client component (`assets/volumes-analytics.js`, `assets/volumes.css`), mathematical scaling algorithms, intent-driven semantic autocomplete, 95% confidence interval estimation (`volComputeConfidence`), projection modeling (`conservative`, `median`, `aggressive`), bulk watchlist staging, and demographics visualization.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SEARCH VOLUME & DEMAND ANALYTICS ARCHITECTURE                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   Client Navigation (/#/app/:slug/volumes)                                             │
│        │                                                                               │
│        ▼                                                                               │
│   [window.renderVolumesPage(p)] ◄──► [window.volumesState]                             │
│        │                                                                               │
│        ├── 1. Universal Search & Intent Cockpit (`.vol-explore-cockpit`)               │
│        │    ├─ Universal Search Input (`#volUniversalSearchInput`) with ⌘K shortcut    │
│        │    ├─ Semantic Autocomplete Dropdown: Grouped by Intent (Info/Comm/Trans/Nav) │
│        │    ├─ Intent Filter Bar: All Intents | Info | Commercial | Transactional | Nav│
│        │    └─ Bulk Watchlist Staging Toolbar: Multi-select checkboxes & bulk save     │
│        │                                                                               │
│        ├── 2. Top 25 Detected Consumer Prompts Table (`.vol-prompt-table`)             │
│        │    ├─ Prompt Query & Active Keyword Highlight                                 │
│        │    ├─ Intent Badge (`.vol-intent-badge`: info, comm, trans, nav)              │
│        │    ├─ AI Prompt Volume with 95% Confidence Interval (`volComputeConfidence`)  │
│        │    │    ├─ High Confidence (>= 10,000 AIV): ±11% margin, 1.8k samples         │
│        │    │    ├─ Moderate Confidence (3,000-9,999 AIV): ±15% margin, 650 samples   │
│        │    │    └─ Modeled Estimate (< 3,000 AIV): ±22% margin, 180 samples           │
│        │    ├─ Google Volume Benchmark (GV) & Comparison                               │
│        │    └─ Engine Distribution (GPT %, PPX %, GEM %, CLD %) & 30-Day Trend Rate    │
│        │                                                                               │
│        ├── 3. Primary Sub-Navigation Tabs (`.volumes-tab-nav`)                         │
│        │    ├─ Overview & Trends (`state.activeTab === 'overview'`): Dual-Mode SVG     │
│        │    │    └─ Non-linear Square Root Scale (`MAXH * Math.sqrt(v / max)`)         │
│        │    ├─ Watchlists (`state.activeTab === 'watchlists'`): Management & Conflicts │
│        │    ├─ Demographics (`state.activeTab === 'demographics'`): Donut, Cohorts, Map│
│        │    └─ Hierarchy Mindmap (`state.activeTab === 'mindmap'`): Interactive Nodes  │
│        │                                                                               │
│        └── 4. Interactive Modals & Data Provenance Gate                                │
│             ├─ Methodology Modal (`.vol-method-modal`): Poisson CI & Model Selector    │
│             ├─ Execution Details Modal (`.vol-md-modal`): Citations accordion          │
│             └─ Provenance Gate: Strict live/demo separation, zero synthetic dates      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Vocabulary & Placeholders

The test scenarios in this suite utilize standardized placeholder tokens to decouple test logic from specific test tenants, locales, and environments:

| Placeholder Token | Description & Permitted Values | Example Values |
|---|---|---|
| `[DOMAIN]` | Active project domain under test | `[DOMAIN]` (e.g. `daikin.com.tr`) |
| `[COUNTRY]` | 2-letter ISO country code | `US`, `TR`, `GB`, `DE` |
| `[LANGUAGE]` | UI localization preference (`en` or `tr`) | `en` (English), `tr` (Türkçe) |
| `[KEYWORD_TERM]` | Target search term or prompt query | `[KEYWORD_TERM]` (e.g. `klima`, `ısı pompası`, `vrv sistemleri`) |
| `[INTENT_CATEGORY]` | Search intent classification key | `info` (Informational), `comm` (Commercial), `trans` (Transactional), `nav` (Navigational) |
| `[PROJECTION_MODEL]` | Selectable statistical projection curve | `median`, `conservative`, `aggressive` |
| `[CHART_MODE]` | SVG chart rendering mode | `bar`, `line` |
| `[CONFIDENCE_TIER]` | Statistical sampling confidence tier | `high` (>= 10k AIV), `moderate` (3k-9.9k AIV), `modeled` (< 3k AIV) |
| `[DEMOGRAPHIC_CARD]`| Demographic analysis card identifier | `gender`, `age`, `income`, `regional` |

---

## 3. Test Case Inventory & Traceability Matrix

This directory decomposes the monolithic test specification into 12 atomic, executable Gherkin test cases. Every requirement from the original specification is mapped below:

| Case ID & File Name | Target Feature / Focus | Originating Scenario & Section | Coverage Rationale |
|---|---|---|---|
| `01-gherkin-case-universal-search-and-intent-filters.md` | Universal search input, ⌘K shortcut & intent pills | Scenario 1 (§3) & §2.1 | Validates primary cockpit filter bar and dynamic prompt table filtering. |
| `02-gherkin-case-turkish-diacritic-semantic-autocomplete.md` | Autocomplete with Turkish diacritics & intent clusters | Scenario 2, 9 (§3) & §4.4 | Tests `.toLocaleLowerCase("tr")` handling (`İ`, `ı`, `ş`, `ç`) and intent capping. |
| `03-gherkin-case-probabilistic-confidence-intervals.md` | 95% Confidence Intervals & statistical sampling tiers | Scenario 3 (§3) & §4.1 | Verifies `volComputeConfidence` margins (`±11%`, `±15%`, `±22%`) via `Scenario Outline`. |
| `04-gherkin-case-projection-models-localstorage-persistence.md` | Projection models (`conservative`/`median`/`aggressive`) | Scenario 3, 8 (§3) & §4.2 | Proves methodology modal switching, `localStorage` persistence, and input defense. |
| `05-gherkin-case-dual-chart-visualization-and-trend-curves.md` | Dual-mode SVG chart (Bar vs Line) & weekly intervals | Scenario 4 (§3) & §2.3 | Exercises SVG paths/rects, coordinate hover tooltips, and `VOL_WEEK_LABELS`. |
| `06-gherkin-case-sqrt-scale-boundary-and-extreme-skew.md` | Square root scale boundaries & extreme skew defense | Scenario 7 (§3) & §4.5 | Tests zero/negative volume defense, min 4px clamping, and 50k vs 50 legibility. |
| `07-gherkin-case-watchlist-multi-select-staging-toolbar.md` | Master select-all, staging toolbar & bulk save modal | Scenario 5 (§3) & §2.2 | Tests batch selection, sticky toolbar count updates, and bulk save workflow. |
| `08-gherkin-case-filtered-watchlist-staging-boundary.md` | Staging boundary conditions with active filters | Scenario 10 (§3) & Code Critique | Validates `vol-head-check` behavior across filtered views and selection clearing. |
| `09-gherkin-case-watchlist-name-conflict-and-duplication.md` | Watchlist duplicate name conflict & atomic duplication | Scenario 11 (§3) & §4.6 | Tests `duplicate_list_name` error mapping, optimistic rollback, and server copy. |
| `10-gherkin-case-demographics-cohorts-and-heatmap.md` | Demographics donut, age/income cohorts & map zoom | Scenario 6 (§3) & §2.4 | Tests chart/table toggles, SVG choropleth world map, and zoom controls. |
| `11-gherkin-case-hierarchy-mindmap-navigation.md` | Interactive hierarchy mindmap pan/zoom canvas | §1.3 (Tab 5), §2.5 | Validates semantic expansion nodes, depth (1-3) controls, and node tooltips. |
| `12-gherkin-case-data-provenance-live-workspace-guard.md` | Strict live provider mode boundary & no template leaks | Scenario 12 (§3) & §1.5 | Proves zero `VOL_PROMPT_TEMPLATES` leakage and honest unmeasured states in live mode. |

---

## 4. Execution Model: Ego Browser & MacBook Architecture

Zeo Geo-Radar test automation operates under a distributed execution architecture:
1. **Ego Browser on MacBook**:
   - The browser automation engine (`ego-browser`) executes on an external macOS runner (`macbook`).
   - Browser sessions adhere to a strict 5-phase lifecycle:
     1. `useOrCreateTaskSpace("zeo-radar-step06-volumes-...")`
     2. `openOrReuseTab(targetUrl)`
     3. User interactions (clicks, keyboard input, toggles)
     4. Synchronous DOM and state assertions (`tab.js(...)`)
     5. `completeTaskSpace()` in a dedicated final block.
2. **Evidence Collection via SCP**:
   - Screenshots captured on the MacBook host (e.g. `/tmp/ego-shots/*.png`) are transferred to the local repository test results directory via SCP:
     ```bash
     scp macbook:/tmp/ego-shots/*.png ./02-gherkin-result-case-<slug>/
     ```
   - **Crucial Rule**: Result directories (e.g. `02-gherkin-result-case-<slug>/`) are created on demand **only when tests are actively executed**, never pre-created as empty directories.

---

## 5. Element Catalog & CSS Selectors Reference

### Search Cockpit & Intent Bar
- `.volumes-analytics-page`: Root page container.
- `#volUniversalSearchInput`: Universal search text input (`⌘K`).
- `#volUniversalDropHost .volumes-search-dropdown`: Clustered suggestions dropdown.
- `.vol-intent-pill[data-action="vol-set-intent"]`: Intent filter pills (`all`, `info`, `comm`, `trans`, `nav`).

### Prompts Table & Staging
- `table.vol-prompt-table`: Top 25 consumer prompts table.
- `input.vol-head-check[data-action="vol-toggle-select-all"]`: Master select-all checkbox.
- `input.vol-row-check[data-action="vol-toggle-select-prompt"]`: Individual row staging checkbox.
- `.vol-num-with-ci`: Volume cell displaying projected value and confidence range.
- `.vol-ci-pill[data-action="vol-open-methodology"]`: Confidence tier pill opening methodology modal.
- `.vol-bulk-toolbar`: Sticky bottom action bar when 1+ prompts are staged.

### Visualization & Trends
- `.vol-kw-workspace-head`: Active keyword workspace header.
- `button.vol-toggle-btn[data-mode="bar|line"]`: Chart mode toggles.
- `svg.vol-svg-chart`: Main SVG chart canvas.
- `.vol-filter-rail`: Secondary filtering bar (Date Range, Platform, Region).

### Modals & Demographics
- `.modal.vol-method-modal`: Statistical methodology explanation modal.
- `input[name="volProjectionModel"]`: Projection model radio buttons.
- `.modal.vol-md-modal`: Bulk save watchlist and execution details modal.
- `.demographics-card-regional`: Regional world choropleth heatmap card.
- `button[data-action="vol-zoom-in|vol-zoom-out|vol-zoom-reset"]`: Heatmap zoom controls.

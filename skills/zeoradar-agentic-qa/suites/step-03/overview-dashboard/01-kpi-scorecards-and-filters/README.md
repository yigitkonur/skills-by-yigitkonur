# Overview Dashboard — KPI Scorecards & Filters Test Suite

## 1. Directory Purpose & Scope
This test directory contains modular, code-grounded Gherkin test specifications for the **KPI Scorecards & Executive Filter Bar** of the Zeo Geo-Radar Overview Dashboard (`assets/dashboards.js`, `assets/radar.js`, `assets/overview.css`).

The suite verifies:
- Shell-level filters (Date Range calendar popover, Answer Engine multi-selects, Topic cluster filters, Global filter reset).
- In-card overview timeframe segmented buttons (`7d`, `14d`, `30d`, `90d`) and frequency controls.
- Core KPI metric cards (Overall Visibility Score `visScore`, AI Share of Voice `shareOfVoice`, Average Position / Category Rank `avgPosition`, and Sentiment Health `sentimentData`).
- Single-run baseline states vs multi-run delta toggling (`.ov-baseline-tag`).
- Adversarial invariants (Zero-engine deselection division-by-zero immunity, high-frequency date clicking race immunities, single-market regional filter fallbacks, and low-sample sentiment guardrails).
- Collapsible technical telemetry drawer (`ov-toggle-tech-drawer`).

---

## 2. Standard Vocabulary & Parameterized Placeholders

All test cases in this directory utilize standardized, bracketed placeholders to allow execution across different brands, markets, and engine selections:

| Placeholder | Category | Meaning & Allowed Values | Example in Test Execution |
|---|---|---|---|
| `[APP_URL]` | Infrastructure | Base application origin URL | `https://zeoradar.endpoints.lol` |
| `[SLUG]` | Routing | URL route slug for brand workspace | `daikin` |
| `[DOMAIN]` | Environment | Target brand domain under test | `daikin.com.tr` |
| `[BRAND]` | Environment | Target brand display name | `Daikin` |
| `[COUNTRY]` | Localization | ISO alpha-2 country code for market scope | `TR`, `US`, `GB`, `DE` |
| `[LANGUAGE]` | Localization | ISO 639-1 UI language preference | `tr`, `en` |
| `[DATE_RANGE]` | Area-Specific | Timeframe range identifier for overview chart | `7d`, `14d`, `30d`, `90d` |
| `[ENGINE_SELECTION]`| Area-Specific | Set of active AI answer engines | `ChatGPT, Perplexity, Gemini, Claude, Google AI Mode` |
| `[TOPIC_CLUSTER]` | Area-Specific | Specific topic cluster key or name | `[TOPIC_CLUSTER]`, `klima-modelleri`, `isi-pompalari` |
| `[BASELINE_MODE]` | Area-Specific | Baseline comparison mode in hero card | `prev` ("vs Previous Period"), `baseline90d` ("vs 90D Baseline") |
| `[METRIC_KEY]` | Area-Specific | KPI scorecard metric identifier | `visibility`, `sov`, `rank`, `sentiment` |

---

## 3. Test Cases Inventory & Traceability Matrix

This directory contains 11 modular test cases, mapped 1:1 against the legacy monolithic specification `01-kpi-scorecards-and-filters.md`:

| Case File | Test Case Title | Original Section Mapped | Critical Invariant Tested |
|---|---|---|---|
| `01-gherkin-case-kpi-strip-hydration.md` | Core KPI Scorecards Initial Hydration & Values | §3.1 – §3.4 | Non-empty calculations for `visScore`, `shareOfVoice`, `avgPosition`, `sentimentData` |
| `01-gherkin-case-timeframe-pills-switching.md` | In-Card Timeframe Segmented Pills & Dropdown | §2.4 | Synchronous `state.ov.range` update and active `.ov-tf-btn.active` styling |
| `01-gherkin-case-timeframe-thrashing-race.md` | High-Frequency Date Range Thrashing Immunity | §5.2 | Rapid clicking (<50ms) desynchronization and axis tick integrity |
| `01-gherkin-case-shell-date-picker-popover.md` | Shell Date Range Calendar Popover & Presets | §2.1 | Presets (`snap`, `7`, `14`, `30`), calendar day range selection, and apply |
| `01-gherkin-case-engine-multiselect-filter.md` | Shell Answer Engine Multi-Select Filter | §2.2 | Multi-engine toggle, count badge `.cnt`, and clear filter action |
| `01-gherkin-case-zero-engines-empty-state.md` | Zero Engines Deselection & Empty State Invariant | §5.1 | Zero-division protection, skeleton `.ov-skeleton-wrap`, em-dash `"–"`, reset trigger |
| `01-gherkin-case-topic-cluster-filter-and-reset.md` | Topic Cluster Filter Mutation & Global Reset | §2.3, §5.4 | Topic filtering, prompt count telemetry badge, `.freset` full restoration |
| `01-gherkin-case-baseline-mode-toggle.md` | Single-Run Baseline Guard & Multi-Run Toggle | §3.5, §5.5 | Single-run honest indicator `"Baseline established (1 run)"` vs multi-run delta |
| `01-gherkin-case-sentiment-low-sample-guard.md` | Low-Sample Sentiment Scorecard Guard (<3 Claims)| §3.4, §5.6 | Em-dash `"–"` display with pending tooltip `title` when polarized claims < 3 |
| `01-gherkin-case-tech-telemetry-drawer.md` | Collapsible Technical Telemetry Drawer | §3.5 | Accordion open/close, progress badge, and 4-metric validation grid |
| `01-gherkin-case-single-market-regional-filter.md` | Single-Market Regional Filter Scoping Fallback | §5.3 | Unrepresented region filtering fallback without uncaught exceptions |

---

## 4. Execution Model: Ego Browser & MacBook Gateway
All test cases are designed for automated or manual execution using **Ego Browser** on a connected physical MacBook or local headless Chromium environment:
1. **Automation Runner**: Executed via `ego-browser nodejs` heredocs following the 5-phase lifecycle:
   - Phase 1: Task space isolation (`useOrCreateTaskSpace`)
   - Phase 2: SPA navigation and authentication bypass (`openOrReuseTab`, `zeoBypassLogin`)
   - Phase 3: Semantic observation and user interactions (`snapshotText`, `click`, `fillInput`)
   - Phase 4: Deterministic DOM and state assertions (`js`)
   - Phase 5: Clean teardown (`completeTaskSpace` with `keep: false` in a dedicated final heredoc)
2. **Artifact & Evidence Protocol**:
   - Screenshots and network logs captured during test runs are saved in matching result directories (e.g. `01-gherkin-result-case-<short-slug>/`).
   - When running on a remote MacBook, artifacts are pulled via `scp` to the repository reports tree before publishing.

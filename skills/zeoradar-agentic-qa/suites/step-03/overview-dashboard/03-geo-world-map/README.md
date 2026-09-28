# Overview Dashboard — Geo World Map Test Suite

## 1. Directory Purpose & Scope
This test directory contains modular, code-grounded Gherkin test specifications for the **Interactive Vector World Map & Regional Heatmap Engine** of the Zeo Geo-Radar platform (`assets/vector-map-loader.js`, `data/worldmap.js`, `assets/radar.js`, `assets/volumes-analytics.js`, `assets/radar.css`, `assets/volumes.css`).

The suite verifies:
- Asynchronous on-demand loading via `VectorMapLoader` (in-memory caching `window.WORLD_SVG`, deduplication, and zero-tile-server architecture).
- Resilient network error handling: graceful transition from `.map-loading-placeholder` to accessible `.map-error-placeholder` (`role="alert"`), and zero-reload retry recovery via `button[data-action="retry-map"]`.
- Choropleth classification into 4 semantic design token buckets (`.heat-q1` to `.heat-q4`) based on search volume share ratios.
- Target-centered dynamic zoom & pan engine (`applyMapZoom`), bounding box centering (`tr.getBBox()`), and strict geometric zoom clamping between 1.0x and 9.0x.
- Interaction with active tracked markets (`#tr.tracked`) vs untracked foreign country paths (`#us`, `#de`), accompanied by single-market scope disclaimers (Türkiye location_code 2792).
- Regional metric tab switching (`Visibility`, `Sentiment`, `Share of Voice`) and side ranked country table synchronization (`table.heatmap-tbl`).
- Dual-surface parity between the shell Regions tab (`#mapPane`) and the Prompt Volumes Regional Heatmap (`#volHeatmapHost`).

---

## 2. Standard Vocabulary & Parameterized Placeholders

All test cases in this directory utilize standardized placeholders:

| Placeholder | Category | Meaning & Allowed Values | Example in Test Execution |
|---|---|---|---|
| `[APP_URL]` | Infrastructure | Base application origin URL | `https://zeoradar.endpoints.lol` |
| `[SLUG]` | Routing | URL route slug for brand workspace | `daikin` |
| `[DOMAIN]` | Environment | Target brand domain under test | `daikin.com.tr` |
| `[BRAND]` | Environment | Target brand display name | `Daikin` |
| `[COUNTRY]` | Localization | ISO alpha-2 country code | `TR`, `US`, `GB`, `DE` |
| `[LANGUAGE]` | Localization | UI language preference | `tr`, `en` |
| `[ISO_CODE]` | Area-Specific | Lowercase country ISO identifier in SVG path | `tr`, `us`, `de`, `gb`, `fr` |
| `[ZOOM_DIR]` | Area-Specific | Direction of map zoom step | `in`, `out` |
| `[ZOOM_FACTOR]` | Area-Specific | Floating zoom multiplier | `1.0`, `1.7`, `2.89`, `9.0` |
| `[REGION_METRIC]` | Area-Specific | Active regional metric tab | `Visibility`, `Sentiment`, `Share of Voice` |
| `[HEAT_BUCKET]` | Area-Specific | Choropleth quantile CSS class | `.heat-q1`, `.heat-q2`, `.heat-q3`, `.heat-q4` |

---

## 3. Test Cases Inventory & Traceability Matrix

This directory contains 11 modular test cases, mapped 1:1 against the legacy monolithic specification `03-geo-world-map.md`:

| Case File | Test Case Title | Original Section Mapped | Critical Invariant Tested |
|---|---|---|---|
| `01-gherkin-case-vector-map-loader-caching.md` | Vector Map Loader On-Demand Caching | §2.1, §2.2 | In-memory cache `window.WORLD_SVG`, zero redundant fetches |
| `01-gherkin-case-network-failure-retry-recovery.md` | Network Failure Simulation & Retry Recovery | §2.2, §7.1 | `.map-error-placeholder` role="alert", retry button recovery |
| `01-gherkin-case-tracked-market-path-highlight.md` | Tracked Market Path Highlighting & Tooltip | §3.2, §3.3 | `#tr` path has `.tracked` class, SVG native `<title>` present |
| `01-gherkin-case-choropleth-quantile-classification.md` | Choropleth Heatmap Quantile Buckets | §3.3 | 4-tier quantile classification based on search share ratio |
| `01-gherkin-case-geometric-zoom-clamping.md` | Geometric Zoom Clamping (1.0x to 9.0x) | §4.1, §7.3 | Min 1.0x / Max 9.0x clamping, base viewBox restoration |
| `01-gherkin-case-target-centered-bounding-box.md` | Target-Centered Bounding Box Centering | §4.1 | Centering on active market `tr.getBBox()`, margin boundary clamping |
| `01-gherkin-case-side-country-demand-table.md` | Side Ranked Country Demand Table | §5 | Synchronized ranking, volume `fmtVol`, share `fmtPct`, delta |
| `01-gherkin-case-untracked-country-interaction.md` | Untracked Country Path Interaction & Scope Notice| §7.2 | Exception-free interaction on untracked paths, market scope notice |
| `01-gherkin-case-region-metric-tab-switching.md` | Region Metric Tab Switching & Alignment | §3.4, §7.6 | Tabs `Visibility`, `Sentiment`, `SOV`, active `.on`, values sync |
| `01-gherkin-case-dual-surface-map-parity.md` | Dual-Surface Map Parity (Regions vs Volumes) | §7.5 | Shared `VectorMapLoader` cache across `#mapPane` and `#volHeatmapHost` |
| `01-gherkin-case-viewport-resize-aspect-ratio.md` | Viewport Resize & Aspect Ratio Preservation | §7.4 | $1000 \times 600$ `data-vb0` ratio preserved across window resizing |

---

## 4. Execution Model: Ego Browser & MacBook Gateway
All test cases are designed for automated or manual execution using **Ego Browser** on a connected physical MacBook or local headless Chromium environment:
1. **Automation Runner**: Executed via `ego-browser nodejs` heredocs following the 5-phase lifecycle:
   - Phase 1: Task space isolation (`useOrCreateTaskSpace`)
   - Phase 2: SPA navigation and authentication bypass (`openOrReuseTab`, `zeoBypassLogin`)
   - Phase 3: Semantic observation and user interactions (`snapshotText`, `click`)
   - Phase 4: Deterministic DOM and state assertions (`js`)
   - Phase 5: Clean teardown (`completeTaskSpace` with `keep: false` in a dedicated final heredoc)
2. **Artifact & Evidence Protocol**:
   - Screenshots and network logs captured during test runs are saved in matching result directories (e.g. `01-gherkin-result-case-<short-slug>/`).
   - Remote MacBook artifacts are retrieved via SCP to the repository reports tree before compiling final QA reports.

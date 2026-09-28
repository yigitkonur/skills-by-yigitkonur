# Overview Dashboard — Visibility Trend Chart Test Suite

## 1. Directory Purpose & Scope
This test directory contains modular, code-grounded Gherkin test specifications for the **Longitudinal Visibility Trend Chart & Activity Twin Charts** of the Zeo Geo-Radar Overview Dashboard (`assets/dashboards.js`, `assets/radar.js`, `assets/overview.css`).

The suite verifies:
- Dual visualization modes: Continuous SVG trend curves (`ovLineSVG`) vs engine-by-engine vertical bar columns (`ovKpiBars`).
- Interactive SVG mechanics: Hit detection layer (`rect.ov-hit`), dynamic crosshair line (`line.ov-cross`), per-series hover dots (`circle.ov-dot`), and floating tooltip card (`div.ov-tip`).
- Coordinate precision & boundary clamping algorithms ($x \ge 4\text{px}$ left-edge clamping, right-edge collision flip).
- Baseline integrity rules: Flat $m = 0$ baseline replication (`ovBaselineSeries`) on single runs, NaN-free SVG paths, and persistent synthetic disclaimer badge (`.ov-demo-badge`).
- Unmeasured engine guard (F3 Rule): Platform with 0 responses displays `"–"` with `unmeasuredEngineTitle()` and omits vertical bar sticks.
- Website Activity twin charts (`ovActivityCard`: AI Bot Citations vs AI Referral Visits) with series checkboxes, compare toggle switch (`ov-compare`), and daily vs weekly granularity aggregations.

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
| `[CHART_MODE]` | Area-Specific | Visualization mode for visibility chart | `line`, `bar` |
| `[DATE_RANGE]` | Area-Specific | Timeframe range identifier | `7d`, `14d`, `30d`, `90d` |
| `[FREQ]` | Area-Specific | Time bucket granularity | `daily`, `weekly` |
| `[ACTIVITY_CHART]`| Area-Specific | Activity twin chart identifier | `cit` (AI Bot Citations), `ref` (AI Referral Visits) |
| `[ENGINE_KEY]` | Area-Specific | Platform series key | `ChatGPT`, `Perplexity`, `Gemini`, `Claude`, `Google AI Mode` |

---

## 3. Test Cases Inventory & Traceability Matrix

This directory contains 11 modular test cases, mapped 1:1 against the legacy monolithic specification `02-visibility-trend-chart.md`:

| Case File | Test Case Title | Original Section Mapped | Critical Invariant Tested |
|---|---|---|---|
| `01-gherkin-case-line-mode-svg-rendering.md` | Line Mode SVG Trend Chart Rendering | §2.1, §3.1 | SVG viewBox 600x160, grid lines, path area fill, sub-pixel precision |
| `01-gherkin-case-chart-mode-switching.md` | Line vs Bar Mode Segmented Switching | §2.1 | Segmented toggle `[data-action="toggle-overview-mode"]`, `.black` active class |
| `01-gherkin-case-bar-mode-engine-breakdown.md` | Bar Chart Mode Engine-by-Engine Breakdown | §3.3 | Column sticks with height formula, platform token colors, engine icons |
| `01-gherkin-case-unmeasured-engine-f3-rule.md` | Unmeasured Engine Representation (F3 Rule) | §3.3, §6.2 | 0 answers renders `"–"` with tooltip, no bar stick drawn (prevents 0% conflation) |
| `01-gherkin-case-crosshair-snapping-and-dots.md` | Interactive Crosshair Snapping & Hover Dots | §3.2 | Hover on `rect.ov-hit` snaps crosshair & dots to nearest time bucket |
| `01-gherkin-case-tooltip-boundary-clamping.md` | Floating Tooltip Coordinate Boundary Clamping | §3.2, §6.3 | Left clamp $x \ge 4\text{px}$, right flip $lx = px - tw - 14$, mouseleave dismissal |
| `01-gherkin-case-missing-days-longitudinal-baseline.md` | Longitudinal Baseline & Missing Days Integrity | §6.1 | $m = 0$ flat line replication via `ovBaselineSeries`, NaN-free SVG paths |
| `01-gherkin-case-activity-twin-charts-rendering.md` | Website Activity Twin Charts Rendering | §4 | AI Bot Citations & AI Referral Visits cards, series checkboxes |
| `01-gherkin-case-activity-disable-all-series.md` | Disabling All Series Checkboxes in Activity | §6.4 | Uncheck all series, $maxV = 0 \to 1$ guard, crash-free hover with 0 series |
| `01-gherkin-case-activity-compare-switch-toggle.md` | Activity Twin Charts Comparative Switch | §4, §6.5 | Comparative overlay switch `.ct-switch[data-action="ov-compare"]`, `.on` class |
| `01-gherkin-case-frequency-granularity-aggregation.md` | Frequency Granularity Invariant (Daily vs Weekly)| §6.6 | Weekly aggregation $n = \max(2, \text{round}(\text{days}/7))$, bilingual dates |

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

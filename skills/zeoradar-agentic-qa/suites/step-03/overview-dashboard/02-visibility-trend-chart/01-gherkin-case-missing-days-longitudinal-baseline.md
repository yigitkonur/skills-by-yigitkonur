# Test Case: Longitudinal Baseline & Missing Days Integrity

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-07`
- **Purpose**: Verify that when a brand dataset contains a single published snapshot or gaps in intermediate daily measurements, the longitudinal trend engine generates an honest, horizontal baseline curve ($m = 0$) across all $n$ dates via `ovBaselineSeries`, prevents broken or `NaN` SVG path definitions, and renders the synthetic disclaimer badge `.ov-demo-badge`.

---

## 2. Tester Brief
When historical daily crawl data is incomplete or consists solely of an initial snapshot, naive interpolation often draws distorted diagonal slopes or outputs broken SVG path syntax (e.g. `d="M NaN NaN L ..."`).
Zeo Geo-Radar defends data integrity by:
1. Replicating the verified snapshot value horizontally across all date intervals when only a baseline exists ($m = 0$).
2. Guaranteeing that SVG `path` coordinates consist strictly of finite floating-point numbers.
3. Rendering `.ov-demo-badge` with the disclaimer: `"Simulated trend — from latest snapshot"`.

The tester inspects SVG path definitions and baseline series outputs on single-snapshot workspaces.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Workspace State**: Single published run (`ovPublishedRunCount(p) === 1`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Longitudinal Baseline Curve and Missing Days Defense
  As a quality auditor
  I want single-run or sparse time series to render continuous, valid horizontal paths
  So that users never see broken SVG rendering, NaN coordinates, or ungrounded historical spikes.

  Scenario Outline: Validating SVG path syntax across sparse time ranges
    Given the user is on the Overview Dashboard with a single published baseline run
    When the user selects the timeframe "<Range>"
    Then the trend chart SVG path "d" attribute must not contain "NaN" or "undefined"
    And the path must contain at least 4 valid coordinate points
    And the disclaimer badge ".ov-demo-badge" must be present in the hero card
    And the first and last Y-coordinates of the path should be equal, reflecting a horizontal baseline

    Examples:
      | Range |
      | 7d    |
      | 14d   |
      | 30d   |
      | 90d   |
```

---

## 5. Visual Checks
- **Trend Line**: Flat horizontal line spanning the full width of the chart.
- **Gradient Fill**: Uniform height area fill below the baseline curve.
- **Badge**: `.ov-demo-badge` rendered next to the delta indicator.

---

## 6. Data and Network Checks
- **SVG Path Syntax Verification**:
  ```javascript
  const pathCheck = await js(String.raw`(() => {
    const chartSvg = document.querySelector('.ov-kpi-chart svg.ov-chart');
    if (!chartSvg) return { error: 'Chart SVG not found' };

    const path = chartSvg.querySelector('path[stroke="var(--accent)"]');
    const d = path?.getAttribute('d') || '';
    const hasNan = d.includes('NaN') || d.includes('undefined');
    const parts = d.split(/\s+/).filter(Boolean);

    return {
      hasNan,
      partsCount: parts.length,
      hasDemoBadge: !!document.querySelector('.ov-demo-badge'),
      noError: !window.__lastError
    };
  })()`);
  if (pathCheck.hasNan || pathCheck.partsCount < 4 || !pathCheck.hasDemoBadge) {
    throw new Error('Longitudinal baseline path assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-missing-days-longitudinal-baseline/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of baseline horizontal paths captured in result directory.
  - SCP sync from MacBook to host before final test report compilation.
